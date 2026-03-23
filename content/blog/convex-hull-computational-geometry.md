---
title: "Convex Hull & Computational Geometry for Interviews"
date: 2026-03-21
excerpt: "Master convex hull algorithms—Graham scan, Jarvis march, and geometry interview patterns that appear in tech screens."
tags: [algorithms, computational-geometry, convex-hull, interview-prep]
---

# Convex Hull & Computational Geometry for Interviews

Computational geometry questions test your ability to reason about spatial relationships. The convex hull—the smallest convex polygon containing all points—is a classic problem.

## Problem Definition

Given n points on a 2D plane, find the smallest convex polygon that contains all points.

## Graham Scan

O(n log n) algorithm using angular sorting and a stack:

```python
def convex_hull_graham(points):
    if len(points) < 3:
        return points
    
    # Find bottommost point (or leftmost if tie)
    start = min(points, key=lambda p: (p[1], p[0]))
    points.remove(start)
    
    # Sort by polar angle with start point
    def polar_angle(p):
        return math.atan2(p[1] - start[1], p[0] - start[0])
    
    points.sort(key=polar_angle)
    points.insert(0, start)
    
    # Cross product: positive if counterclockwise turn
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    stack = []
    for p in points:
        while len(stack) >= 2 and cross(stack[-2], stack[-1], p) <= 0:
            stack.pop()
        stack.append(p)
    
    return stack
```

## Jarvis March (Gift Wrapping)

O(nh) where h is the number of hull points. Better when the hull has few points:

```python
def convex_hull_jarvis(points):
    n = len(points)
    if n < 3:
        return points
    
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    # Find leftmost point
    hull = []
    leftmost = min(range(n), key=lambda i: points[i][0])
    p = leftmost
    
    while True:
        hull.append(p)
        q = (p + 1) % n
        for i in range(n):
            if cross(points[p], points[i], points[q]) > 0:
                q = i
        p = q
        if p == leftmost:
            break
    
    return [points[i] for i in hull]
```

## Andrew's Monotone Chain

Often cleaner to implement—sort by x-coordinate and build upper/lower hulls:

```python
def convex_hull_monotone(points):
    points = sorted(set(points))
    if len(points) <= 1:
        return points
    
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    return lower[:-1] + upper[:-1]
```

## Interview Applications

### Point in Polygon
Use ray casting—count intersections of a horizontal ray with polygon edges.

### Line Segment Intersection
Check if two segments intersect using orientation tests.

### Closest Pair of Points
Divide and conquer—O(n log n) solution.

## Interview Tips

1. **Handle edge cases.** Three collinear points, duplicate points, all points on a line.

2. **Know your cross product.** Positive = counterclockwise, negative = clockwise, zero = collinear.

3. **Numerical precision.** Using integers or fractions avoids floating-point issues.

4. **Common follow-ups:** "Find the diameter of the point set" (rotating calipers), "Is this point inside the convex hull?" (binary search on hull edges).
