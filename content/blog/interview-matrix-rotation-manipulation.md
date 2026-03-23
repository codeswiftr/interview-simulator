---
title: "2D Matrix Problems: Rotation, Spiral Order, and Graph Traversal"
description: "Master the essential 2D matrix patterns for coding interviews: in-place rotation, spiral traversal, word search, island counting, and matrix BFS/DFS."
date: "2026-03-20"
category: "Algorithms"
---

Matrix problems are a staple of coding interviews because they test spatial reasoning, index manipulation, and graph traversal simultaneously — all in a familiar structure. Once you see through the surface-level 2D array representation to the underlying graph, most matrix problems reduce to patterns you already know.

## Rotate a Matrix 90 Degrees In-Place

Rotating an n×n matrix clockwise 90 degrees without extra space is a classic. The key insight: **transpose, then reverse each row**.

```python
def rotate(matrix):
    n = len(matrix)

    # Step 1: Transpose (flip along main diagonal)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

    # Step 2: Reverse each row
    for row in matrix:
        row.reverse()
```

For counterclockwise rotation: reverse each row first, then transpose. For 180-degree rotation: apply 90-degree rotation twice, or reverse all rows and then all columns.

**Why this works:** A 90° clockwise rotation maps `(i, j) → (j, n-1-i)`. Transposition gives `(i,j) → (j,i)`. Row reversal maps `(j,i) → (j, n-1-i)`. Combined: `(i,j) → (j, n-1-i)`. Correct.

**Interview follow-up:** Can you do it in a single pass? Yes — cycle through the four cells in each "layer" of the rotation, shifting them simultaneously:

```python
def rotate_single_pass(matrix):
    n = len(matrix)
    for layer in range(n // 2):
        first, last = layer, n - 1 - layer
        for i in range(first, last):
            offset = i - first
            top = matrix[first][i]
            matrix[first][i] = matrix[last-offset][first]
            matrix[last-offset][first] = matrix[last][last-offset]
            matrix[last][last-offset] = matrix[i][last]
            matrix[i][last] = top
```

## Spiral Order Traversal

Traverse an m×n matrix in spiral order (outer ring, then inner rings):

```python
def spiral_order(matrix):
    result = []
    if not matrix:
        return result

    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1

    while top <= bottom and left <= right:
        # Left to right on top row
        for col in range(left, right + 1):
            result.append(matrix[top][col])
        top += 1

        # Top to bottom on right column
        for row in range(top, bottom + 1):
            result.append(matrix[row][right])
        right -= 1

        # Right to left on bottom row (if still valid)
        if top <= bottom:
            for col in range(right, left - 1, -1):
                result.append(matrix[bottom][col])
            bottom -= 1

        # Bottom to top on left column (if still valid)
        if left <= right:
            for row in range(bottom, top - 1, -1):
                result.append(matrix[row][left])
            left += 1

    return result
```

The boundary conditions (`if top <= bottom` and `if left <= right`) handle the case where we've already covered all elements — without them you'll double-count cells in non-square matrices.

**Spiral matrix II** (generate spiral): same logic, but write 1..n² into the matrix instead of reading.

## Word Search (DFS with Backtracking)

Given a grid of characters and a word, determine if the word exists as a path (any adjacent non-repeating cells):

```python
def word_search(board, word):
    rows, cols = len(board), len(board[0])

    def dfs(r, c, idx):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if board[r][c] != word[idx]:
            return False

        # Mark visited
        temp, board[r][c] = board[r][c], '#'

        found = (dfs(r+1, c, idx+1) or dfs(r-1, c, idx+1) or
                 dfs(r, c+1, idx+1) or dfs(r, c-1, idx+1))

        # Restore
        board[r][c] = temp
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False
```

**Optimization:** Check early if the word can exist (character frequency). If the board has fewer 'z's than the word needs, return False immediately.

## Island Counting (BFS/DFS Flood Fill)

Count connected components of '1's in a binary grid:

```python
def num_islands(grid):
    if not grid:
        return 0

    rows, cols = len(grid), len(grid[0])
    count = 0

    def bfs(r, c):
        queue = [(r, c)]
        grid[r][c] = '0'  # Mark visited
        while queue:
            row, col = queue.pop(0)
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == '1':
                    grid[nr][nc] = '0'
                    queue.append((nr, nc))

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                bfs(r, c)

    return count
```

Use `from collections import deque` and `deque.popleft()` for true O(1) queue operations. `list.pop(0)` is O(n).

**Variations to know:**
- Max area island: track size during flood fill
- Surrounded regions: islands not touching the border
- Pacific Atlantic water flow: BFS from both edges inward
- Number of enclaves: land cells you can't reach from boundary

## Matrix BFS for Shortest Path

BFS finds shortest paths in unweighted grids — this is fundamentally the same as BFS on a graph:

```python
from collections import deque

def shortest_path_binary_matrix(grid):
    n = len(grid)
    if grid[0][0] == 1 or grid[n-1][n-1] == 1:
        return -1

    queue = deque([(0, 0, 1)])  # (row, col, distance)
    grid[0][0] = 1  # Mark visited

    directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

    while queue:
        r, c, dist = queue.popleft()
        if r == n-1 and c == n-1:
            return dist
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0:
                grid[nr][nc] = 1  # Mark visited
                queue.append((nr, nc, dist + 1))

    return -1
```

**Key pattern:** Mark cells visited when you enqueue them, not when you dequeue. Marking on dequeue causes O(n²) duplicate enqueues.

## Index Manipulation Tricks

**Checking bounds:** Bundle the four bounds checks into a helper or use a guard list:
```python
def in_bounds(r, c, rows, cols):
    return 0 <= r < rows and 0 <= c < cols
```

**Direction arrays:** For 4-directional: `dirs = [(0,1),(0,-1),(1,0),(-1,0)]`. For 8-directional: all combinations of `{-1,0,1} × {-1,0,1}` except `(0,0)`.

**Diagonal traversal:** Cells on the same diagonal satisfy `r + c = constant` (main diagonal) or `r - c = constant` (anti-diagonal).

**Layer peeling:** Many spiral/ring problems work best by tracking `top, bottom, left, right` boundaries and shrinking them, rather than computing complex index formulas.

Matrix problems reward systematic thinking and careful boundary handling. The underlying graph is always there — once you see the matrix as a grid graph, the right traversal algorithm follows naturally.
