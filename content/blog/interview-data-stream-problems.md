---
title: "Data Stream Problems: Median, Running Stats, and Reservoir Sampling"
description: "Interview patterns for data streams — finding median from a data stream with two heaps, running mean/variance, reservoir sampling for random sampling, count-min sketch, and designing streaming analytics systems."
date: "2026-03-20"
category: "Algorithms"
---

# Data Stream Problems: Median, Running Stats, and Reservoir Sampling

Data stream problems appear at senior engineer interviews and at companies dealing with high-volume real-time data. The constraint is: you can't store all the data, so you must compute statistics incrementally. This guide covers the key patterns: median maintenance with heaps, running statistics, and probabilistic data structures for scale.

## Pattern 1: Median from Data Stream

"Design a data structure that can add numbers and return the median at any time in O(log n) per add and O(1) per median query."

The key insight: the median is the middle element. Maintain two heaps:
- Max-heap of the lower half (largest element at top)
- Min-heap of the upper half (smallest element at top)

Keep them balanced (size differs by at most 1). The median is either the top of the larger heap, or the average of both tops.

```python
import heapq

class MedianFinder:
    def __init__(self):
        self.lo = []  # Max-heap (negate values for Python's min-heap)
        self.hi = []  # Min-heap

    def addNum(self, num):
        # Add to lo, then balance
        heapq.heappush(self.lo, -num)

        # Ensure all lo values <= all hi values
        if self.hi and -self.lo[0] > self.hi[0]:
            heapq.heappush(self.hi, -heapq.heappop(self.lo))

        # Balance sizes (lo can have at most 1 more than hi)
        if len(self.lo) > len(self.hi) + 1:
            heapq.heappush(self.hi, -heapq.heappop(self.lo))
        elif len(self.hi) > len(self.lo):
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def findMedian(self):
        if len(self.lo) > len(self.hi):
            return -self.lo[0]
        return (-self.lo[0] + self.hi[0]) / 2
```

**Time:** O(log n) per add, O(1) per query. **Space:** O(n).

The invariants to maintain: (1) every element in lo ≤ every element in hi, (2) sizes differ by at most 1.

## Pattern 2: Running Mean and Variance (Welford's Algorithm)

For running mean and variance without storing all values:

```python
class RunningStats:
    def __init__(self):
        self.count = 0
        self.mean = 0.0
        self.M2 = 0.0  # Sum of squared deviations

    def add(self, x):
        self.count += 1
        delta = x - self.mean
        self.mean += delta / self.count
        delta2 = x - self.mean  # Note: updated mean
        self.M2 += delta * delta2

    @property
    def variance(self):
        return self.M2 / (self.count - 1) if self.count > 1 else 0

    @property
    def std_dev(self):
        return self.variance ** 0.5
```

Welford's algorithm is numerically stable (no cancellation errors from large numbers) and O(1) per element. This is the standard industrial algorithm for streaming statistics.

## Pattern 3: Reservoir Sampling

"Given a stream of unknown length, sample k elements uniformly at random without knowing n in advance."

```python
import random

def reservoir_sample(stream, k):
    reservoir = []

    for i, item in enumerate(stream):
        if i < k:
            reservoir.append(item)
        else:
            # Replace element j in reservoir with probability k/(i+1)
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = item

    return reservoir
```

**Proof of uniformity:** For the n-th item (n > k), the probability of it being in the reservoir is k/n. For any existing reservoir item, the probability of it surviving is (1 - k/n × 1/k) = (n-k)/n. By induction, all n items have probability k/n of being in the final reservoir.

Reservoir sampling is used in distributed systems when you need to sample from a data stream too large to store, like sampling 1% of log lines or random A/B test assignment from a stream.

## Pattern 4: Sliding Window Maximum

"Given a sliding window of size k, find the maximum in each window as it slides."

Using a deque (monotonically decreasing queue):

```python
from collections import deque

def maxSlidingWindow(nums, k):
    dq = deque()  # Stores indices; values are decreasing
    result = []

    for i, num in enumerate(nums):
        # Remove elements outside the window
        if dq and dq[0] < i - k + 1:
            dq.popleft()

        # Remove elements smaller than current (they can never be max)
        while dq and nums[dq[-1]] < num:
            dq.pop()

        dq.append(i)

        # Window is full
        if i >= k - 1:
            result.append(nums[dq[0]])

    return result
```

O(n) overall — each element is added and removed from the deque at most once.

## Pattern 5: Count-Min Sketch (Approximating Frequencies)

For counting item frequencies in a high-volume stream without storing all items:

```python
import hashlib

class CountMinSketch:
    def __init__(self, width=1000, depth=5):
        self.width = width
        self.depth = depth
        self.table = [[0] * width for _ in range(depth)]
        self.hash_funcs = [
            lambda x, seed=i: int(hashlib.md5(f"{x}{seed}".encode()).hexdigest(), 16)
            for i in range(depth)
        ]

    def add(self, item):
        for i, h in enumerate(self.hash_funcs):
            self.table[i][h(item) % self.width] += 1

    def estimate(self, item):
        return min(
            self.table[i][h(item) % self.width]
            for i, h in enumerate(self.hash_funcs)
        )
```

Count-Min Sketch uses O(width × depth) space to estimate frequencies with bounded error. The estimate is always an overcount; the error bound is ε × n where ε = e/width with probability 1 - (1/e)^depth.

Used in: network traffic analysis (top IP addresses), ad frequency capping, trending topics.

## Pattern 6: HyperLogLog (Approximate Cardinality)

Counting distinct elements in a stream without storing all elements. HyperLogLog uses O(log log n) space to estimate cardinality within ~2% error.

The idea: hash each element; track the maximum number of leading zeros in any hash. More leading zeros implies more distinct elements were hashed. Multiple hash functions and averaging reduce variance.

Used in: Redis's HyperLogLog data type (`PFADD`, `PFCOUNT`), counting unique visitors, distinct query counts.

## Interview Design Question: Real-Time Analytics Pipeline

"Design a system to compute the 99th percentile API latency in real-time across 10K requests/second."

Key decisions:
- **Exact computation:** Store all latencies in a sorted structure. Too expensive at 10K/s.
- **T-Digest:** A streaming percentile algorithm that maintains a compact summary structure with configurable accuracy. Mergeable across nodes.
- **Fixed window with buckets:** Histogram with predefined buckets (0-10ms, 10-50ms, etc.). Prometheus uses this. Fast, but bucket granularity limits precision.
- **Sliding window:** Use a circular buffer of the last N milliseconds; compute percentile over it. Works for moderate rates; memory-bounded.

Production answer: Prometheus histogram with percentile estimation from buckets for monitoring dashboards; T-Digest for high-accuracy streaming percentiles when exact percentile SLAs must be monitored.
