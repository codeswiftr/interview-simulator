# Elastic Engineering Deep Dive: Search and Observability at Petabyte Scale

Elasticsearch sits at the center of some of the largest data workloads in enterprise engineering — powering full-text search for e-commerce platforms, aggregating logs from millions of containers, and enabling sub-second analytics over petabytes of time-series data. Understanding how it actually works at the engine level is what separates engineers who configure YAML from those who can diagnose a 10-second query, design a mapping that scales to a billion documents, and justify architectural decisions to a skeptical interviewer. This post covers the internals that matter most.

## The Inverted Index: Lucene's Core Abstraction

Elasticsearch is built on Apache Lucene, and Lucene's fundamental data structure is the **inverted index**. Unlike a forward index (document → list of terms), an inverted index maps each term to the list of documents containing that term. When you search for `error AND timeout`, Lucene looks up both terms in the inverted index and intersects their document lists using a skip-list-accelerated merge algorithm — in microseconds, even across hundreds of millions of documents.

Lucene writes data in immutable units called **segments**. When documents are indexed, they accumulate in an in-memory buffer. Periodically (controlled by `refresh_interval`, default 1 second), this buffer is flushed to a new segment on disk. The segment is immediately searchable — this is what "near real-time" search means in Elasticsearch. The segment itself is never modified; updates are implemented as a delete (marking the old document's ID in a `.del` file) plus an insert into a new segment.

This immutability creates a problem: over time, thousands of small segments accumulate. Each search query must check every segment, so query latency grows with segment count. Lucene addresses this through **segment merging**: a background process continuously merges smaller segments into larger ones, then deletes the originals. The merge policy (controlled by `index.merge.policy.*` settings) determines when merges trigger. The default `TieredMergePolicy` groups segments into tiers by size and merges within tiers — preventing large segments from being merged repeatedly.

The tradeoff: merges consume CPU and I/O. Under heavy indexing load, merges may fall behind, causing segment count to grow and query performance to degrade. You can observe this with `GET /_cat/segments?v` — if you see hundreds of segments per shard, consider increasing `index.merge.scheduler.max_thread_count` or temporarily reducing indexing throughput.

## BM25 Relevance Scoring: Beyond Simple Keyword Matching

Elasticsearch uses **BM25** (Best Match 25) as its default relevance scoring algorithm. Understanding BM25 is essential for tuning search quality and for answering the inevitable interview question: "How does Elasticsearch decide which documents to rank first?"

BM25 is a probabilistic ranking function built on two intuitions: **term frequency saturation** and **document length normalization**. In pure TF-IDF, a term appearing 100 times in a document scores proportionally higher than one appearing 10 times. BM25 applies a saturation function — the benefit of additional occurrences diminishes as frequency grows. This prevents documents stuffed with repeated keywords from dominating results.

The BM25 formula for a single term query:

```
score(D, Q) = IDF(Q) × (tf(D,Q) × (k1 + 1)) / (tf(D,Q) + k1 × (1 - b + b × |D| / avgdl))
```

Where `k1` (default 1.2) controls term frequency saturation, `b` (default 0.75) controls length normalization, `|D|` is document length in terms, and `avgdl` is the average document length across the index. Higher `b` penalizes longer documents more aggressively — appropriate for fields where length correlates with verbosity rather than relevance (like product descriptions). Set `b: 0.0` for fields where length is irrelevant (like categorical tags).

**Field boosts** allow you to signal that matches in certain fields carry more relevance weight:

```json
GET /products/_search
{
  "query": {
    "multi_match": {
      "query": "wireless noise cancelling headphones",
      "fields": ["title^3", "description^1", "tags^2"],
      "type": "best_fields"
    }
  }
}
```

The `^3` multiplier on `title` means a match in the title contributes three times more to the score than a match in `description`. Interview tip: boosts are applied at query time, not index time, so you can tune them without re-indexing.

## Index Mapping, Custom Analyzers, and Shard Routing

An index mapping defines how documents are stored and indexed. The mapping — critically — **cannot be changed after index creation** for most field types. Adding new fields is allowed; changing a field's type (e.g., from `text` to `keyword`) requires creating a new index and reindexing all data.

Here is a production-grade mapping for a log index with custom analyzers and relevance boosting:

```json
PUT /application-logs
{
  "settings": {
    "number_of_shards": 5,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "log_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "log_word_delimiter"]
        },
        "path_analyzer": {
          "type": "custom",
          "tokenizer": "path_hierarchy"
        }
      },
      "filter": {
        "log_word_delimiter": {
          "type": "word_delimiter_graph",
          "split_on_numerics": false,
          "preserve_original": true
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "message": {
        "type": "text",
        "analyzer": "log_analyzer",
        "boost": 2.0
      },
      "service.name": {
        "type": "keyword"
      },
      "log.file.path": {
        "type": "text",
        "analyzer": "path_analyzer",
        "fields": {
          "keyword": { "type": "keyword" }
        }
      },
      "@timestamp": {
        "type": "date",
        "format": "strict_date_optional_time"
      },
      "log.level": {
        "type": "keyword",
        "boost": 1.5
      }
    }
  }
}
```

The `word_delimiter_graph` filter handles log messages with mixed-case identifiers like `NullPointerException` — it splits on case boundaries and preserves the original token. The `path_hierarchy` tokenizer indexes `/var/log/app/service.log` as `/var`, `/var/log`, `/var/log/app`, and `/var/log/app/service.log` — enabling prefix path searches that would otherwise require wildcard queries.

**Shard routing** is why shard count is immutable. By default, Elasticsearch routes documents to shards using a hash: `shard = hash(document_id) % number_of_primary_shards`. If you change the number of primary shards, every document's routing target changes — existing documents become unfindable without a full reindex. Size shards at 10-50GB for general workloads; for time-series data, use ILM (Index Lifecycle Management) with rollover to cap shard size automatically.

## The Observability Stack: ECS and the Pipeline Architecture

Elastic's observability stack follows a clear data pipeline: **Beats → Logstash → Elasticsearch → Kibana (BELK)**, though in modern deployments Beats often ship directly to Elasticsearch via Elastic Agent, bypassing Logstash for simple use cases.

**Beats** are lightweight data shippers. Filebeat tails log files; Metricbeat collects system and application metrics; Packetbeat analyzes network traffic. Each Beat runs on the source host with minimal resource overhead — typically under 50MB RAM.

The **Elastic Common Schema (ECS)** is the normalization layer that makes this pipeline valuable at scale. ECS defines a shared vocabulary for field names: `@timestamp` always means event time, `service.name` always identifies the emitting service, `event.action` always describes what happened. When every log and metric follows ECS, a single Kibana query can correlate a web server log (`http.response.status_code: 503`) with the corresponding infrastructure metric (`system.cpu.total.pct > 0.95`) and APM trace (`transaction.duration.us > 5000000`) — across different services, written by different teams.

Without ECS, each team invents its own field names. One team logs `status_code`, another logs `responseCode`, a third logs `http_status`. Cross-service correlation becomes a field-mapping problem that grows quadratically with team count.

## What Interviewers Are Really Testing

Elastic interviews at senior level typically probe three dimensions: your understanding of the read path (how an inverted index answers a query, why segment count affects performance, how BM25 ranks results), your understanding of the write path (segment lifecycle, merge strategy, refresh vs. flush semantics), and your operational judgment (shard sizing, mapping immutability implications, when to use custom analyzers).

The answer that distinguishes senior candidates is not "Elasticsearch uses Lucene" — it is "we set `b: 0.0` on our tags field because tag count does not indicate document relevance, and we saw a 15% improvement in precision after that change." Concrete operational reasoning grounded in mechanical understanding is what earns the offer.
