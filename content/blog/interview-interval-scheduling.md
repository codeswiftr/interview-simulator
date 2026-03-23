---
title: "Interval Problems: The Complete Interview Playbook"
description: "All interval problem patterns for coding interviews — merge intervals, insert interval, meeting rooms, minimum platforms, interval scheduling maximization, and sweep line technique."
date: "2026-03-20"
category: "Algorithms"
---

# Interval Problems: The Complete Interview Playbook

Interval problems appear at every interview level and across multiple problem categories — scheduling, calendars, resource allocation, and data stream processing. The patterns are more varied than they appear, and mixing them up costs you in interviews. This guide gives you the complete toolkit: every pattern, when to use it, and how to code it cleanly.

## The Fundamental Operations

Before patterns, internalize the three fundamental operations on two intervals [a, b] and [c, d]:

**Overlap check:** `a <= d and c <= b` — if both are true, the intervals overlap.
**No overlap:** `b < c or d < a` — left ends before right starts, or right ends before left starts.
**Merge:** `[min(a, c), max(b, d)]`

## Pattern 1: Merge Intervals

"Given a list of intervals, merge all overlapping intervals."

```python
def merge(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for start, end in intervals[1:]:
        if start <= merged[-1][1]:  # Overlaps with last merged
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    return merged
```

**Time:** O(n log n) for sort. **Space:** O(n).

Key: sort by start time, then greedily extend the last interval if the current one overlaps.

## Pattern 2: Insert Interval

"Insert a new interval into a sorted, non-overlapping list. Merge if necessary."

```python
def insert(intervals, newInterval):
    result = []
    i = 0
    n = len(intervals)

    # Add all intervals that end before newInterval starts
    while i < n and intervals[i][1] < newInterval[0]:
        result.append(intervals[i])
        i += 1

    # Merge overlapping intervals with newInterval
    while i < n and intervals[i][0] <= newInterval[1]:
        newInterval[0] = min(newInterval[0], intervals[i][0])
        newInterval[1] = max(newInterval[1], intervals[i][1])
        i += 1

    result.append(newInterval)

    # Add remaining intervals
    result.extend(intervals[i:])
    return result
```

Three-phase approach: before, overlap, after. Clean and linear O(n).

## Pattern 3: Meeting Rooms I (Can Attend All?)

"Given meeting time intervals, determine if a person can attend all meetings."

```python
def canAttendMeetings(intervals):
    intervals.sort(key=lambda x: x[0])
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i-1][1]:
            return False  # Overlap found
    return True
```

O(n log n). Sort by start, check consecutive pairs.

## Pattern 4: Meeting Rooms II (Minimum Rooms)

"Find the minimum number of conference rooms required."

**Approach 1 — Two sorted arrays:**

```python
def minMeetingRooms(intervals):
    starts = sorted(i[0] for i in intervals)
    ends = sorted(i[1] for i in intervals)

    rooms = 0
    max_rooms = 0
    s = e = 0

    while s < len(intervals):
        if starts[s] < ends[e]:
            rooms += 1
            s += 1
        else:
            rooms -= 1
            e += 1
        max_rooms = max(max_rooms, rooms)

    return max_rooms
```

**Approach 2 — Min-heap:**

```python
import heapq

def minMeetingRooms(intervals):
    intervals.sort(key=lambda x: x[0])
    heap = []  # Stores end times of ongoing meetings

    for start, end in intervals:
        if heap and heap[0] <= start:
            heapq.heapreplace(heap, end)  # Reuse a room
        else:
            heapq.heappush(heap, end)  # Need a new room

    return len(heap)
```

The heap approach is intuitive: always assign the room that frees up earliest. The size of the heap at the end is the minimum rooms needed.

## Pattern 5: Interval Scheduling Maximization

"Select the maximum number of non-overlapping intervals."

This is the classic greedy interval scheduling problem. Sort by **end time** and greedily pick intervals that don't conflict with the last selected.

```python
def eraseOverlapIntervals(intervals):
    intervals.sort(key=lambda x: x[1])  # Sort by END time
    count = 0
    last_end = float('-inf')

    for start, end in intervals:
        if start >= last_end:
            last_end = end  # Select this interval
        else:
            count += 1  # Erase this interval

    return count  # Minimum erasures = total - maximum selected
```

**Why sort by end time?** Selecting the interval that ends earliest leaves the most room for future intervals. This greedy choice is provably optimal (exchange argument).

## Pattern 6: Sweep Line for Maximum Overlap

"Find the maximum number of overlapping intervals at any point in time."

```python
def maxOverlap(intervals):
    events = []
    for start, end in intervals:
        events.append((start, 1))   # +1 at start
        events.append((end, -1))    # -1 at end

    events.sort(key=lambda x: (x[0], x[1]))  # Tie-break: -1 before +1

    max_overlap = current = 0
    for _, delta in events:
        current += delta
        max_overlap = max(max_overlap, current)

    return max_overlap
```

The sweep line technique: convert intervals to events, sort by time, and maintain a running count. The maximum count at any point is the answer.

## Pattern 7: Employee Free Time

"Find all free time intervals across multiple employees' schedules."

Flatten all intervals, sort, merge, then find gaps between merged intervals.

```python
def employeeFreeTime(schedule):
    all_intervals = sorted([iv for emp in schedule for iv in emp], key=lambda x: x.start)

    merged = [all_intervals[0]]
    for iv in all_intervals[1:]:
        if iv.start <= merged[-1].end:
            merged[-1].end = max(merged[-1].end, iv.end)
        else:
            merged.append(iv)

    free = []
    for i in range(1, len(merged)):
        free.append(Interval(merged[i-1].end, merged[i].start))

    return free
```

## Choosing the Right Pattern

| Problem type | Technique |
|---|---|
| Merge overlapping | Sort by start, extend last |
| Insert and merge | Three-phase: before, overlap, after |
| Can all attend? | Sort by start, check consecutive |
| Minimum rooms | Min-heap of end times |
| Maximum non-overlapping | Sort by END, greedy select |
| Maximum simultaneous overlap | Sweep line events |
| Free intervals between scheduled | Merge, then find gaps |

The most common mistake: using the wrong sort key. Merge/can-attend problems sort by start. Maximization problems sort by end. Mixing these up produces wrong answers that pass some test cases, trapping you in debugging.
