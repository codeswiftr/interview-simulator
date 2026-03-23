---
title: "A* Search Algorithm: Pathfinding for Interviews"
date: 2026-03-21
excerpt: "Master A* search and heuristic design for pathfinding interview questions—understanding when A* beats Dijkstra."
tags: [algorithms, graph-search, a-star, pathfinding, interview-prep]
---

# A* Search Algorithm: Pathfinding for Interviews

A* is the gold standard for pathfinding in interviews. It combines Dijkstra's optimality with heuristic-guided search to find shortest paths faster.

## How A* Works

A* maintains two values for each node:
- `g(n)`: Actual cost from start to n
- `h(n)`: Estimated cost from n to goal (heuristic)
- `f(n) = g(n) + h(n)`: Total estimated cost

A* always expands the node with the lowest f(n).

## Implementation

```python
import heapq

def a_star(graph, start, goal, heuristic):
    open_set = [(heuristic(start, goal), 0, start)]
    came_from = {}
    g_score = {start: 0}
    
    while open_set:
        f, g, current = heapq.heappop(open_set)
        
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]
        
        for neighbor, cost in graph[current]:
            tentative_g = g_score[current] + cost
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score, tentative_g, neighbor))
    
    return None  # No path found
```

## Heuristic Design

The heuristic is critical. It must be:

1. **Admissible:** Never overestimates the true cost (guarantees optimality)
2. **Consistent:** h(n) ≤ cost(n, n') + h(n') for all neighbors n' (guarantees efficiency)

### Common Heuristics for Grids

**Manhattan Distance** (4-directional movement):
```python
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
```

**Euclidean Distance** (any direction):
```python
def euclidean(a, b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
```

**Chebyshev Distance** (8-directional movement):
```python
def chebyshev(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
```

## A* vs Dijkstra

Dijkstra is A* with h(n) = 0. A* with an admissible heuristic:
- Explores fewer nodes
- Finds the optimal path
- Still O(E log V) worst case, but typically much faster in practice

## A* vs BFS

BFS is A* with uniform edge costs and h(n) = 0. Use A* when:
- Edge costs vary
- You have a good heuristic

## Bidirectional A*

Search from both start and goal, meeting in the middle:

```python
def bidirectional_a_star(graph, start, goal, heuristic):
    # Two priority queues, two g_scores, two came_from maps
    # Expand from both sides alternately
    # Check if current node is in other side's closed set
    # Implementation follows similar pattern to unidirectional
    pass
```

## Interview Tips

1. **Implement Dijkstra first.** A* is a natural extension. Show you understand both.

2. **Discuss admissibility.** Explain why your heuristic never overestimates.

3. **Edge cases:** No path exists, start equals goal, negative edges (A* doesn't handle these).

4. **Common follow-ups:** "What if we need the k shortest paths?" (Yen's algorithm), "How to handle dynamic obstacles?" (D* Lite).

## Time Complexity

Worst case: O(E log V) with a binary heap
Best case: O(E) with a perfect heuristic
Space: O(V)
