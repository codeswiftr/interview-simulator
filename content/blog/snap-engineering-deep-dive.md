# Snap Inc Engineering Deep Dive: AR at Scale, Ephemeral Infrastructure, and What Interviewers Actually Test

Snap's engineering surface area is deceptive. From the outside it looks like a messaging app. From the inside, it is a real-time computer vision platform, a geospatial aggregation system serving 400 million users, an ephemeral media pipeline processing billions of assets daily, and a mobile rendering engine running ML inference at 60fps — all shipped inside a single camera-first product. The engineering challenges that fall out of those constraints are unusual, and Snap's interviewers know it. They are not looking for generalists who can answer LeetCode problems. They are looking for engineers who understand the specific trade-offs that come from operating a camera and AR platform at global scale.

This guide covers four technical domains where Snap has made distinctive engineering decisions, followed by what those decisions tell you about how to prepare.

---

## Lens Studio and the AR Rendering Pipeline

Snap's Lens Studio is not just a creative tool — it is the runtime that powers every AR experience in Snapchat, and it runs in-process on the device. That constraint — 60fps, on a mobile CPU/GPU, with ML inference happening in the same frame budget — shapes every decision in the rendering stack.

Snap built a custom rendering engine called Spectacles Rendering Engine (SRE) that runs on top of Metal on iOS and Vulkan on Android. The decision to own the rendering engine rather than use a general-purpose engine like Unity or Unreal comes down to one thing: latency. General-purpose engines carry overhead for features Snap does not need (physics simulation, audio spatialization, multiplayer networking) and abstract away the GPU pipeline in ways that make per-frame budget control harder. By owning the renderer, Snap can make precise decisions about when to flush the command buffer, how to schedule ML inference relative to rasterization, and how to manage texture memory across the frame.

The ML inference side is equally constrained. Snap runs face landmark detection, segmentation, and object detection models on-device. Their approach is to compile models to CoreML on iOS and TFLite delegate on Android, then pin them to the Neural Engine or GPU depending on the model size and the thermal budget of the device. A key engineering decision Snap has documented publicly is their use of a lightweight keypoint detector as a pre-filter — rather than running the full segmentation model on every frame, they run a cheap 2D face detection pass first and only invoke the heavier model when a face is confirmed in the frame. This cascaded approach drops average inference time by roughly 40% across their Lens library.

The on-device rendering and inference loop looks approximately like this:

```
Frame N (camera buffer ready):
  1. [CPU] Run lightweight face detector (~2ms)
  2. [Neural Engine] If face detected: run landmark model (~5ms)
  3. [GPU] Upload geometry and updated landmark data to command buffer
  4. [GPU] Execute Lens shader graph (deferred shading, custom blending)
  5. [CPU] Composite Lens output over camera preview
  6. Present to display (target: 16.7ms total for 60fps)
```

The frame budget discipline here is what Snap engineers actually live with. When a Lens exceeds its budget on a target device, the Lens Studio toolchain surfaces per-stage timing in a profiling panel and gates the Lens from publishing if p95 frame time exceeds threshold. That is a systems-level quality gate that has no analogue at most consumer software companies.

---

## Ephemeral Media Infrastructure: Delete-on-View at 4 Billion Snaps Per Day

Snap's core product promise is ephemerality — content that disappears after being viewed. That is trivial to describe and surprisingly hard to build reliably at scale. Four billion Snaps per day means roughly 46,000 objects created per second, each with a deletion lifecycle that must be tracked accurately, honored under network failures, and auditable for compliance without retaining the content itself.

Snap's approach separates the media payload from the lifecycle metadata. When a Snap is sent, the encrypted media is written to blob storage (Snap has used both S3-compatible storage and their own GCS buckets for different content tiers). The metadata — sender, recipient list, view state, expiry conditions — is written to a separate distributed store. The blob storage path is never directly exposed to clients. Instead, clients receive a signed ephemeral URL with a TTL shorter than the expected view window.

The delete pipeline runs as a consumer off a lifecycle event stream. When the recipient's client confirms a view event, the confirmation is written to a Kafka topic. A downstream consumer processes the event, marks the metadata record as viewed, and enqueues a delete job for the blob. The delete job is idempotent — it checks the metadata record before issuing the delete call, so retry-on-failure does not result in double-processing. The key engineering discipline here is that the blob delete is asynchronous and best-effort, but the metadata record is the authoritative source of truth. If a blob delete fails and retries exhaust, the blob becomes orphaned but inaccessible — the URL is expired, the key is not re-derivable, and the metadata record is marked deleted. Compliance audits operate on the metadata layer, not the blob layer.

A simplified version of the delete-on-read pattern:

```python
def process_view_event(event: ViewEvent, metadata_store: MetadataStore, blob_store: BlobStore):
    record = metadata_store.get(event.snap_id)

    if record is None or record.status == "deleted":
        return  # Already processed, idempotent exit

    # Mark viewed before issuing blob delete
    # This ensures metadata is consistent even if blob delete fails
    metadata_store.mark_viewed(event.snap_id, viewer_id=event.viewer_id)

    if record.all_recipients_viewed():
        # Enqueue async blob delete — do not block the view confirmation path
        deletion_queue.enqueue(DeleteJob(
            blob_key=record.encrypted_blob_key,
            snap_id=event.snap_id,
            deadline=datetime.utcnow() + timedelta(hours=24)
        ))
```

The CDN layer adds another dimension. Short-lived content cannot be cached with standard TTLs — a cached Snap that has already been viewed but is still in CDN edge cache would allow a second view, violating the product contract. Snap solves this with signed URL invalidation: each signed URL embeds the current view count in the HMAC signature. After a view event is confirmed, the signature parameters change and all prior URLs become invalid at the CDN layer without requiring a cache purge. This is a key reason Snap has historically preferred Fastly's real-time purge API over Cloudfront for Snap media — sub-100ms global purge propagation versus the minutes-range TTLs on CloudFront's invalidation path.

---

## Snap Map: Real-Time Geospatial Aggregation for 400 Million Users

Snap Map launched in 2017 and represented a genuinely hard systems problem: display a real-time heat map of user-generated Snaps, aggregated to protect individual privacy, across the entire world, for hundreds of millions of concurrent users, with a UI that renders smoothly at any zoom level.

The core data structure is an H3 hexagonal grid, originally developed at Uber and now widely adopted for geospatial indexing. H3 tiles the world in hexagons at 16 resolution levels. At each zoom level, a point maps to a single hex cell, and hex cells at adjacent levels have a well-defined containment relationship. Snap Map uses H3 to aggregate Snap counts by cell at each resolution level rather than exposing raw point data. This gives them three things simultaneously: natural privacy aggregation (you cannot see individual locations, only cell-level density), hierarchical tile caching (zooming in or out invalidates only the changed resolution level's cells), and efficient spatial queries (H3 cell IDs are compact integers that index efficiently in columnar stores).

The write path: when a user posts a Story to Snap Map, a geospatial service computes the H3 cell IDs at all relevant resolution levels and increments the count for each cell in a Redis cluster. The Redis layer holds the hot working set — the currently-visible cells for all active clients. A downstream aggregation job computes the heatmap intensity bands and writes pre-rendered tile data to a CDN. Map clients request tiles rather than raw counts, which means the CDN absorbs nearly all read traffic at scale.

Privacy-preserving aggregation is a hard requirement. Snap's published policy requires that individual user locations are never exposed. Their engineering implementation enforces this at the aggregation level: cells below a minimum Snap density threshold are suppressed entirely from the public heat map. This is a k-anonymity floor — no cell renders unless at least k distinct Snaps have been posted to it within the display window. The value of k is not public, but the mechanism is a standard privacy-by-design pattern worth knowing for system design interviews.

---

## Android-First: Why Snap Rewrote Their App in Native Kotlin

In 2020, Snap completed a full rewrite of their Android app from React Native back to native Kotlin. The decision is worth understanding in detail because it reflects a specific engineering trade-off that comes up in mobile system design.

React Native's cross-platform benefits are real: a single codebase serving iOS and Android, faster iteration speed for product features, and a shared JavaScript runtime for business logic. Snap adopted React Native around 2018 for exactly these reasons. By 2019, the costs had accumulated: startup time on mid-range Android devices (the dominant global segment) was measurably worse than native, camera preview latency was higher because every frame had to cross the JavaScript bridge, and the AR Lens experience could not be integrated cleanly into the React Native rendering model without a custom native module that effectively recreated a native camera stack anyway.

The decisive factor was the camera. Snap is a camera-first product, and the camera stack is Snap's primary differentiator. On Android, camera2 API and (later) CameraX give native Kotlin apps direct access to the hardware buffer pipeline. A native Kotlin camera implementation can get the frame data from the sensor into the AR pipeline with one copy; a React Native app crosses the bridge at least twice per frame. At 30fps that overhead is manageable; at 60fps on mid-range hardware it is not.

The rewrite was scoped carefully. Snap migrated screen by screen, running the old app and new app in parallel with feature flags controlling which code path served each user. Performance metrics — startup time, camera-to-viewfinder latency, frame drop rate — were tracked per screen and gated the migration. The approach is a useful case study in safe incremental migration of a high-stakes production system.

---

## Interview Implications

Snap's engineering culture prizes camera expertise, performance discipline, and product craft. Their hiring process reflects that. Here is what to expect and how to prepare:

**System design questions at Snap skew toward media and geospatial problems.** Design a system for ephemeral message storage, or design a real-time location heat map for millions of users. For both, interviewers will probe your data model, your deletion/expiry lifecycle, your CDN and caching strategy, and your privacy-preserving aggregation approach. Knowing H3, signed URLs, Kafka-driven delete pipelines, and k-anonymity will make you fluent in the right vocabulary.

**Mobile performance is a first-class topic.** Even if you are interviewing for a backend role, expect questions about how your backend decisions affect client behavior. Frame rate budgets, battery drain, cold start latency — Snap engineers think about these even when they work on infrastructure.

**AR and computer vision basics matter.** You do not need to be a graphics PhD, but you should understand what a rendering pipeline is, why inference-on-device is preferable to server-side inference for real-time camera features, and what the trade-offs are between model accuracy and latency. Snap's Lens team in particular will probe this in interviews.

**The privacy and ephemerality design space is a differentiator.** Most companies build systems to store data indefinitely. Snap builds systems that are designed to destroy data reliably. The engineering patterns for guaranteed deletion — signed URL invalidation, idempotent delete jobs, metadata-as-source-of-truth — are not standard interview preparation material. Candidates who can reason about them clearly stand out.

Snap is not the right fit for engineers who want to work on CRUD APIs with straightforward persistence requirements. It is a strong fit for engineers who want to work at the intersection of real-time systems, mobile performance, and product-driven privacy constraints. If that intersection sounds interesting, knowing how Snap actually built these systems is the preparation that moves candidates from technically competent to genuinely compelling.
