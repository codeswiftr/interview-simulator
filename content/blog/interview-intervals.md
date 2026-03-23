---
title: "Interval Problems for Coding Interviews: Patterns and Solutions"
description: "Master interval interview problems: merge intervals, insert interval, meeting rooms I & II, minimum arrows to burst balloons, non-overlapping intervals — with templates and edge cases."
date: "2026-03-20"
category: "Algorithm Guides"
---

# Interval Problems for Coding Interviews: Patterns and Solutions

Interval problems form a distinct category in coding interviews that rewards pattern recognition over brute force. Once you internalize three or four core patterns, a wide class of problems becomes immediately tractable. This guide covers the essential interval techniques with clean implementations and the mental models for applying them.

## The Core Abstraction

An interval `[start, end]` represents a range. Most interval problems reduce to one of these operations:
1. **Merging** overlapping intervals
2. **Inserting** a new interval into a sorted, non-overlapping list
3. **Scheduling** — finding minimum resources or maximum non-overlapping intervals
4. **Sweeping** — processing events in sorted order

The crucial first step for almost every interval problem: **sort by start time**.

## Pattern 1: Merge Intervals

**Problem (LC 56)**: Given a list of intervals, merge all overlapping ones.

```python
def merge(intervals):
    intervals.sort(key=lambda x: x[0])
    merged = []

    for interval in intervals:
        if merged and interval[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], interval[1])
        else:
            merged.append(list(interval))

    return merged
```

**Key insight**: After sorting, you only need to compare the current interval against the last merged interval. If they overlap (`current.start <= last.end`), extend the end. Otherwise, push the current interval as a new entry.

**Complexity**: O(n log n) for sorting, O(n) merge pass.

**Edge cases**: Intervals that share only an endpoint (e.g., `[1,2]` and `[2,3]`) — decide whether to merge based on problem definition. Usually `start <= end` means they touch and should merge.

## Pattern 2: Insert Interval

**Problem (LC 57)**: Insert a new interval into a sorted, non-overlapping list. Merge as needed.

```python
def insert(intervals, newInterval):
    result = []
    i = 0
    n = len(intervals)

    # Add all intervals that come before newInterval
    while i < n and intervals[i][1] < newInterval[0]:
        result.append(intervals[i])
        i += 1

    # Merge all overlapping intervals with newInterval
    while i < n and intervals[i][0] <= newInterval[1]:
        newInterval[0] = min(newInterval[0], intervals[i][0])
        newInterval[1] = max(newInterval[1], intervals[i][1])
        i += 1
    result.append(newInterval)

    # Add remaining intervals
    result.extend(intervals[i:])
    return result
```

**Mental model**: Three phases — copy prefix (no overlap), merge middle (overlap), copy suffix (no overlap). Each phase terminates with a clear condition.

## Pattern 3: Meeting Rooms I

**Problem (LC 252)**: Given meeting time intervals, determine if a person can attend all meetings.

```python
def canAttendMeetings(intervals):
    intervals.sort(key=lambda x: x[0])
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i-1][1]:
            return False
    return True
```

This is just "do any two intervals overlap after sorting?" The simplest interval problem — if you're stuck on this one in an interview, that's a red flag. Know it cold.

## Pattern 4: Meeting Rooms II (Minimum Rooms)

**Problem (LC 253)**: Find the minimum number of conference rooms required.

The elegant heap solution tracks the earliest-ending ongoing meeting:

```python
import heapq

def minMeetingRooms(intervals):
    if not intervals:
        return 0

    intervals.sort(key=lambda x: x[0])
    heap = []  # min-heap of end times

    for start, end in intervals:
        if heap and heap[0] <= start:
            heapq.heapreplace(heap, end)
        else:
            heapq.heappush(heap, end)

    return len(heap)
```

**Alternative: sweep line**. Create events `(time, type)` where type is +1 for start, -1 for end. Sort events (end before start at same time to free rooms first). Sweep and track the running count — the maximum is your answer.

```python
def minMeetingRooms(intervals):
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))
    events.sort(key=lambda x: (x[0], x[1]))  # end (-1) before start (+1) at same time

    rooms = max_rooms = 0
    for _, delta in events:
        rooms += delta
        max_rooms = max(max_rooms, rooms)
    return max_rooms
```

The heap approach is O(n log n); the sweep approach is also O(n log n) but is conceptually cleaner and generalizes to other resource-counting problems.

## Pattern 5: Non-Overlapping Intervals

**Problem (LC 435)**: Remove the minimum number of intervals to make the rest non-overlapping.

This is equivalent to finding the maximum set of non-overlapping intervals (the classic interval scheduling problem). Sort by **end time** and greedily take intervals that don't overlap with the last taken:

```python
def eraseOverlapIntervals(intervals):
    if not intervals:
        return 0

    intervals.sort(key=lambda x: x[1])  # sort by end time
    count = 0
    end = intervals[0][1]

    for i in range(1, len(intervals)):
        if intervals[i][0] < end:
            count += 1  # must remove this one
        else:
            end = intervals[i][1]

    return count
```

**Why sort by end time?** Greedy proof: among all intervals starting after the current point, picking the one that ends earliest leaves maximum room for future intervals. This is the activity selection proof from algorithm textbooks.

## Pattern 6: Minimum Number of Arrows

**Problem (LC 452)**: Balloons are represented as intervals on the x-axis. Arrows shot vertically burst all balloons they pass through. Find minimum arrows.

This reduces to counting non-overlapping groups:

```python
def findMinArrowShots(points):
    if not points:
        return 0

    points.sort(key=lambda x: x[1])  # sort by end
    arrows = 1
    end = points[0][1]

    for start, stop in points[1:]:
        if start > end:  # strictly greater — touching balloons both pop
            arrows += 1
            end = stop

    return arrows
```

Notice this is nearly identical to the non-overlapping intervals solution. The difference is the overlap condition: `start > end` vs `start >= end`. This detail trips up candidates — read the problem carefully.

## The Sweep Line Pattern

For more complex problems, model each interval as two events: a "start" event and an "end" event. Sorting all events together and processing them in order generalizes to:

- **Skyline problem** (LC 218): max height at each x coordinate
- **Employee free time** (LC 759): find gaps in merged schedules
- **Rectangle area II** (LC 850): area of union of rectangles

The sweep line reduces a 2D or temporal problem to a 1D scan with a priority queue or sorted structure tracking the "active" intervals.

## Interval Problem Decision Tree

```
Can any two intervals overlap?
  → Sort by start, check adjacent pairs (Meeting Rooms I)

Minimum resources for all intervals simultaneously?
  → Sort by start + min-heap of end times (Meeting Rooms II)

Maximum non-overlapping subset?
  → Sort by end, greedy (Activity Selection / Non-Overlapping Intervals)

Merge all overlaps into one list?
  → Sort by start, linear merge pass

Insert one interval into sorted list?
  → Three-phase linear scan
```

## Common Mistakes

**Forgetting to sort first.** Nearly every interval problem requires a sorted input. If your solution passes without sorting on small examples, it will fail on unsorted inputs.

**Off-by-one on overlap definition.** `[1,2]` and `[2,3]` — do they overlap? Depends on whether the problem uses open or closed intervals. Confirm from examples.

**Mutating input.** `merged[-1][1] = max(...)` modifies the list in-place. If the input must be preserved, copy intervals before processing.

**Heap approach for meeting rooms**: `heapreplace` only when the heap is non-empty and the condition holds. Forgetting the non-empty check causes a crash on the first iteration.

Interval problems reward deliberate pattern recognition. Once you've internalized sort-by-start vs sort-by-end, the heap pattern, and the sweep line template, you can tackle any variant that appears in an interview.
