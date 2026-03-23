---
title: "Pinterest Visual Search System Design"
description: "How Pinterest's visual search works—image embedding generation, approximate nearest neighbor search, multi-modal retrieval, and the infrastructure behind searching 300 billion pins."
date: "2026-03-21"
category: "System Design"
---

# Pinterest Visual Search System Design

Pinterest's visual search lets users search by image—take a photo of furniture you like and find similar items to buy. With 300 billion pins, it's one of the largest visual search systems in the world. This design question combines computer vision, vector search, and large-scale serving infrastructure.

## Requirements

**Functional:**
- Search by image: find visually similar pins
- Search within a region of an image (crop and search)
- Combined text + image search ("blue velvet sofa" + photo of a sofa)
- Product recommendations based on pinned items
- Visual autocomplete in search bar

**Non-functional:**
- 300B pins indexed
- P99 visual search < 500ms
- Support 10M visual searches per day
- Freshness: new pins searchable within 24 hours

## Image Embedding Generation

The core of visual search: represent every image as a fixed-dimension vector (embedding) such that similar images have similar (close) vectors.

**Model**: Pinterest uses a custom CNN trained on their dataset. Base architecture (ResNet-50/EfficientNet) pretrained on ImageNet, fine-tuned on Pinterest engagement data.

The fine-tuning objective: pins that users save together or engage with in the same session should have similar embeddings. This teaches the model Pinterest-specific aesthetics rather than generic ImageNet categories.

```python
# Embedding generation
def generate_embedding(image_url):
    image = download_and_preprocess(image_url)  # resize to 224x224, normalize
    embedding = cnn_model.forward(image)          # returns 256-dim vector
    return l2_normalize(embedding)                # normalize for cosine similarity
```

Output: 256-dimensional float32 vector per image.

## Embedding Index

300 billion pins × 256 dims × 4 bytes = ~300TB of raw vectors. This can't fit in a single machine and can't be searched with exact nearest neighbors in reasonable time.

**Approximate Nearest Neighbor (ANN) search**:

Pinterest uses a proprietary implementation, but publicly available systems include:
- **FAISS** (Facebook): GPU-accelerated, multiple index types (IVF, HNSW)
- **ScaNN** (Google): state-of-the-art accuracy/speed tradeoff
- **Annoy** (Spotify): tree-based, memory-efficient

**HNSW (Hierarchical Navigable Small World)** is the preferred algorithm:
- Build a multi-layer graph where each node connects to its nearest neighbors
- Search by starting at the top layer (coarse), greedy descend to find approximate nearest neighbors
- Recall@100 > 99%, 10x faster than exhaustive search

**Sharding**: 300B embeddings split across 1,000 shards (~300M per shard). Search query runs on all shards in parallel, results merged. Each shard held by a dedicated ANN search service.

```
Query embedding → Scatter to 1000 shards (parallel)
                → Each shard: ANN search → top-100 local results
                → Gather → Merge 100K results → re-rank → top-50
```

## Visual Feature Extraction for Crop Search

Pinterest's "Lens" feature: tap a region of a pin to search within that region. Useful for searching specific items within a scene photo.

Implementation:
1. User selects crop region (bounding box)
2. Extract just the region (resized to 224x224)
3. Generate embedding for the cropped region
4. Search embedding index

The model handles partial images gracefully because it was trained on diverse image crops. A full-room photo and a cropped sofa from that photo both produce meaningful embeddings.

## Multi-Modal Search

Combining text + image queries ("find me blue velvet sofas, similar to this photo"):

**Two-tower approach** with shared embedding space:
- Image tower: CNN → 256-dim embedding
- Text tower: BERT → 256-dim embedding
- Train with contrastive learning: image and its caption should be close in embedding space

At search time:
```python
query_embedding = 0.6 * image_embedding + 0.4 * text_embedding
# weighted blend based on query confidence
```

Text-only searches: use text tower only. Image-only: use image tower. Combined: blend embeddings. The unified embedding space means text queries and image queries can retrieve the same items.

## Object Detection and Tagging

Before embedding generation, run object detection (YOLO or Pinterest's proprietary model) to:
1. Identify objects in the image (furniture, clothing, food, etc.)
2. Generate bounding boxes for each object
3. Assign product category tags

These tags enable filtering in the ANN search ("search within furniture" restricts to embeddings from furniture-tagged pins). This improves precision dramatically — searching for a lamp shouldn't return food pins with similar color profiles.

## Serving Architecture

```
Visual Search Request (image + optional text)
        ↓
Embedding Service (CNN inference, < 50ms on GPU)
        ↓
Query Router → 1000 ANN Shards (parallel scatter, 50ms)
        ↓
Result Aggregator → Re-rank with diversity model
        ↓
Enrichment Service → Fetch pin metadata, author, price
        ↓
Personalization Filter → Adjust ranking by user preferences
        ↓
Response
```

Total latency budget: 50ms embedding + 50ms ANN + 50ms enrichment + 50ms re-rank = ~200ms. Within P99 target.

## Embedding Freshness

New pins must be searchable within 24 hours:
1. Pin created → embedding generation job enqueued
2. GPU worker processes embedding generation (< 1s per image)
3. New embedding written to ANN index (batched insert, every 30 minutes)
4. New pin searchable within the next index refresh cycle

The ANN index is append-only for new embeddings. Periodic full rebuilds (weekly) to rebalance the index and remove deleted pins.

## Interview Tips

Key points for visual search system design:

1. **Embedding model fine-tuning** — not just ImageNet; train on platform-specific engagement data
2. **HNSW/ANN structure** — explain why exhaustive search is infeasible at 300B scale
3. **Sharding ANN index** — parallel scatter-gather
4. **Multi-modal unified embedding space** — text and image in the same space
5. **Object detection for category filtering** — improves precision dramatically

The sharding + scatter-gather pattern is the key scalability insight. ANN algorithms don't distribute inherently — you need to explicitly shard and merge. Mentioning recall@K (not just speed) shows you understand the accuracy-speed tradeoff in ANN search.
