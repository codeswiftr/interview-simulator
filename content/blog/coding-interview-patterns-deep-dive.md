# Coding Interview Patterns Deep Dive: Master the 15 Essential Patterns

Most engineers approach coding interviews by grinding through hundreds of LeetCode problems in random order, hoping that pattern recognition will emerge through sheer volume. It rarely does. The engineers who consistently clear FAANG-level screens do something different: they study patterns first, then map problems onto those patterns. When you see a new problem, the question is not "have I solved this before?" but "which pattern does this fit?"

This guide covers the 15 patterns that underlie the vast majority of algorithm interview questions. For each pattern, you will learn how to recognize it from problem cues, see a reusable Python template, and see concrete example problems. Use this as your mental index — once a problem triggers a pattern, the solution structure falls into place.

---

## 1. Sliding Window

**When to use it**

Look for these cues in the problem statement:
- "contiguous subarray" or "contiguous substring"
- "maximum/minimum length subarray with property X"
- "all substrings of size K"
- Input is a linear sequence (array or string) and you need to process a fixed or variable-size window

The key insight: instead of recomputing the entire window from scratch on each step, you expand one edge and contract the other, maintaining running state in O(1).

**Python template**

```python
def sliding_window(arr, k):
    left = 0
    window_sum = 0
    result = float('-inf')

    for right in range(len(arr)):
        window_sum += arr[right]           # expand window

        if right - left + 1 == k:         # window is full
            result = max(result, window_sum)
            window_sum -= arr[left]        # shrink window
            left += 1

    return result

# Variable-size window (shrink when condition violated)
def variable_window(arr, target):
    left = 0
    window_sum = 0
    min_len = float('inf')

    for right in range(len(arr)):
        window_sum += arr[right]

        while window_sum >= target:
            min_len = min(min_len, right - left + 1)
            window_sum -= arr[left]
            left += 1

    return min_len if min_len != float('inf') else 0
```

**Example problems**
- Maximum sum subarray of size K
- Longest substring with K distinct characters (variable window)
- Minimum size subarray sum (variable window, shrink while valid)

---

## 2. Two Pointers

**When to use it**

- Sorted array, and you need pairs or triplets that satisfy a condition
- "Two sum" variants where you need to find elements that sum to a target
- Palindrome checks, merging two sorted arrays, removing duplicates in-place
- Any problem where you can eliminate possibilities by moving pointers toward each other

Two pointers eliminates the nested loop, reducing O(n²) to O(n) when the array is sorted or when the structure allows one pointer to only ever move in one direction.

**Python template**

```python
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1

    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1     # need larger value
        else:
            right -= 1    # need smaller value

    return []

# Three sum variant
def three_sum(arr):
    arr.sort()
    result = []

    for i in range(len(arr) - 2):
        if i > 0 and arr[i] == arr[i - 1]:
            continue   # skip duplicates
        left, right = i + 1, len(arr) - 1

        while left < right:
            total = arr[i] + arr[left] + arr[right]
            if total == 0:
                result.append([arr[i], arr[left], arr[right]])
                while left < right and arr[left] == arr[left + 1]:
                    left += 1
                while left < right and arr[right] == arr[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1

    return result
```

**Example problems**
- Two Sum II (sorted array)
- Three Sum (all unique triplets summing to zero)
- Container With Most Water (maximize area between two lines)

---

## 3. Fast and Slow Pointers (Floyd's Cycle Detection)

**When to use it**

- Detect a cycle in a linked list or sequence
- Find the middle of a linked list in one pass
- "Happy number" problems (detect if a sequence loops)
- Find the start of a cycle, or determine cycle length

The mathematical guarantee: if a cycle exists, the fast pointer (moving 2 steps) will eventually meet the slow pointer (moving 1 step). If they never meet before fast reaches null, there is no cycle.

**Python template**

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def has_cycle(head):
    slow = fast = head

    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True

    return False

def find_cycle_start(head):
    slow = fast = head

    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            break
    else:
        return None   # no cycle

    # Reset one pointer to head; move both at speed 1
    slow = head
    while slow != fast:
        slow = slow.next
        fast = fast.next

    return slow   # cycle start node

def find_middle(head):
    slow = fast = head

    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next

    return slow   # middle node
```

**Example problems**
- Linked List Cycle (detect cycle)
- Linked List Cycle II (find cycle start)
- Happy Number (detect infinite loop in number sequence)

---

## 4. Merge Intervals

**When to use it**

- Input contains intervals (pairs of start/end times or ranges)
- "Merge overlapping intervals," "insert interval," "find free time slots"
- Scheduling problems, calendar overlap detection
- Any time you need to combine ranges that share overlap

The standard approach: sort by start time, then scan linearly and merge when the current interval overlaps the last merged interval.

**Python template**

```python
def merge_intervals(intervals):
    if not intervals:
        return []

    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for start, end in intervals[1:]:
        last_end = merged[-1][1]

        if start <= last_end:            # overlap
            merged[-1][1] = max(last_end, end)
        else:                            # no overlap
            merged.append([start, end])

    return merged

def insert_interval(intervals, new_interval):
    result = []
    i = 0
    n = len(intervals)

    # Add all intervals that end before new_interval starts
    while i < n and intervals[i][1] < new_interval[0]:
        result.append(intervals[i])
        i += 1

    # Merge overlapping intervals with new_interval
    while i < n and intervals[i][0] <= new_interval[1]:
        new_interval[0] = min(new_interval[0], intervals[i][0])
        new_interval[1] = max(new_interval[1], intervals[i][1])
        i += 1

    result.append(new_interval)
    result.extend(intervals[i:])
    return result
```

**Example problems**
- Merge Intervals (merge all overlapping)
- Insert Interval (insert and merge into sorted list)
- Meeting Rooms II (minimum conference rooms needed — use a min-heap of end times)

---

## 5. Cyclic Sort

**When to use it**

- Array contains numbers in range [1, n] or [0, n]
- "Find the missing number," "find all duplicates," "find the corrupt pair"
- In-place sorting required; numbers can serve as their own indices

Cyclic sort exploits the fact that number `i` belongs at index `i-1` (for 1-indexed) or index `i` (for 0-indexed). Swap each number to its correct position in one pass, then scan for violations.

**Python template**

```python
def cyclic_sort(nums):
    i = 0
    while i < len(nums):
        correct = nums[i] - 1   # where nums[i] should go (1-indexed)
        if nums[i] != nums[correct]:
            nums[i], nums[correct] = nums[correct], nums[i]
        else:
            i += 1
    return nums

def find_missing_number(nums):
    # Range [0, n], one number missing
    i = 0
    n = len(nums)
    while i < n:
        j = nums[i]
        if j < n and nums[i] != nums[j]:
            nums[i], nums[j] = nums[j], nums[i]
        else:
            i += 1

    for i in range(n):
        if nums[i] != i:
            return i
    return n

def find_all_duplicates(nums):
    i = 0
    while i < len(nums):
        correct = nums[i] - 1
        if nums[i] != nums[correct]:
            nums[i], nums[correct] = nums[correct], nums[i]
        else:
            i += 1

    return [nums[i] for i in range(len(nums)) if nums[i] != i + 1]
```

**Example problems**
- Missing Number (find the one missing from [0, n])
- Find All Duplicates in an Array
- Find the Corrupt Pair (one duplicate, one missing)

---

## 6. In-place Linked List Reversal

**When to use it**

- "Reverse a linked list" or "reverse a sublist"
- "Rotate linked list by K positions"
- Any transformation requiring pointer redirection without extra space

The core operation is always the same: track previous, current, and next, then repoint `current.next` to `previous` before advancing.

**Python template**

```python
def reverse_linked_list(head):
    prev = None
    current = head

    while current:
        next_node = current.next
        current.next = prev
        prev = current
        current = next_node

    return prev   # new head

def reverse_sublist(head, left, right):
    if not head or left == right:
        return head

    dummy = ListNode(0)
    dummy.next = head
    prev = dummy

    # Advance to node before 'left'
    for _ in range(left - 1):
        prev = prev.next

    current = prev.next
    for _ in range(right - left):
        next_node = current.next
        current.next = next_node.next
        next_node.next = prev.next
        prev.next = next_node

    return dummy.next
```

**Example problems**
- Reverse Linked List (full reversal)
- Reverse Linked List II (reverse from position left to right)
- Reverse Nodes in K-Group (reverse in chunks of K)

---

## 7. Tree BFS (Level-Order Traversal)

**When to use it**

- "Level by level" output
- "Minimum depth," "zigzag traversal," "right side view"
- Shortest path in an unweighted graph
- Any problem where you need to process nodes layer by layer

BFS uses a queue. At each level, you drain all nodes currently in the queue (that is one complete level) before enqueuing their children.

**Python template**

```python
from collections import deque

def level_order(root):
    if not root:
        return []

    result = []
    queue = deque([root])

    while queue:
        level_size = len(queue)
        current_level = []

        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node.val)

            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)

        result.append(current_level)

    return result

def minimum_depth(root):
    if not root:
        return 0

    queue = deque([(root, 1)])

    while queue:
        node, depth = queue.popleft()

        if not node.left and not node.right:
            return depth

        if node.left:
            queue.append((node.left, depth + 1))
        if node.right:
            queue.append((node.right, depth + 1))
```

**Example problems**
- Binary Tree Level Order Traversal
- Binary Tree Right Side View (last node at each level)
- Minimum Depth of Binary Tree

---

## 8. Tree DFS

**When to use it**

- Path sum problems ("does a root-to-leaf path sum to target?")
- "All paths," "maximum path sum," "diameter of tree"
- Serialize/deserialize a tree
- Any problem that involves exploring a complete path before backtracking

DFS is naturally recursive. For trees, pre-order visits the node before its children, in-order visits left subtree, node, then right subtree (gives sorted order for BSTs), and post-order visits children before the node.

**Python template**

```python
def has_path_sum(root, target_sum):
    if not root:
        return False
    if not root.left and not root.right:
        return root.val == target_sum
    remaining = target_sum - root.val
    return has_path_sum(root.left, remaining) or has_path_sum(root.right, remaining)

def all_paths(root, target_sum):
    result = []

    def dfs(node, current_path, remaining):
        if not node:
            return
        current_path.append(node.val)

        if not node.left and not node.right and remaining == node.val:
            result.append(list(current_path))
        else:
            dfs(node.left, current_path, remaining - node.val)
            dfs(node.right, current_path, remaining - node.val)

        current_path.pop()   # backtrack

    dfs(root, [], target_sum)
    return result

def diameter_of_tree(root):
    max_diameter = [0]

    def height(node):
        if not node:
            return 0
        left_h = height(node.left)
        right_h = height(node.right)
        max_diameter[0] = max(max_diameter[0], left_h + right_h)
        return 1 + max(left_h, right_h)

    height(root)
    return max_diameter[0]
```

**Example problems**
- Path Sum (root-to-leaf, does it equal target?)
- All Paths for a Sum (return all such paths)
- Diameter of Binary Tree (longest path between any two nodes)

---

## 9. Two Heaps

**When to use it**

- "Median of a data stream"
- Problems requiring you to track the lower half and upper half of a dataset simultaneously
- Scheduling where you need both the minimum and maximum efficiently
- Any problem where you need the middle element dynamically

Maintain a max-heap for the lower half and a min-heap for the upper half. Balance them so their sizes differ by at most one. The median is either the top of the larger heap or the average of both tops.

**Python template**

```python
import heapq

class MedianFinder:
    def __init__(self):
        self.small = []   # max-heap (negate values for Python's min-heap)
        self.large = []   # min-heap

    def add_num(self, num):
        # Always push to max-heap first
        heapq.heappush(self.small, -num)

        # Balance: ensure all of small <= all of large
        if self.small and self.large and (-self.small[0]) > self.large[0]:
            heapq.heappush(self.large, -heapq.heappop(self.small))

        # Balance sizes (small can be at most 1 larger than large)
        if len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        elif len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def find_median(self):
        if len(self.small) > len(self.large):
            return -self.small[0]
        return (-self.small[0] + self.large[0]) / 2
```

**Example problems**
- Find Median from Data Stream (add numbers, query median at any point)
- Sliding Window Median (median of each window of size K)
- IPO (maximize capital by selecting projects — max-heap on profits)

---

## 10. Subsets and Backtracking

**When to use it**

- "All subsets," "all permutations," "all combinations"
- "Generate all valid parentheses," "letter combinations of a phone number"
- Constraint satisfaction: N-Queens, Sudoku solver
- Any problem asking for every possible arrangement or selection

Backtracking builds the solution incrementally. At each step, you choose an element, recurse, then undo the choice (backtrack) before trying the next option.

**Python template**

```python
def subsets(nums):
    result = []

    def backtrack(start, current):
        result.append(list(current))   # every state is a valid subset

        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1, current)
            current.pop()              # backtrack

    backtrack(0, [])
    return result

def permutations(nums):
    result = []

    def backtrack(current, remaining):
        if not remaining:
            result.append(list(current))
            return
        for i in range(len(remaining)):
            current.append(remaining[i])
            backtrack(current, remaining[:i] + remaining[i+1:])
            current.pop()

    backtrack([], nums)
    return result

def combination_sum(candidates, target):
    result = []

    def backtrack(start, current, remaining):
        if remaining == 0:
            result.append(list(current))
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break
            current.append(candidates[i])
            backtrack(i, current, remaining - candidates[i])   # i, not i+1 (reuse allowed)
            current.pop()

    candidates.sort()
    backtrack(0, [], target)
    return result
```

**Example problems**
- Subsets (all subsets including empty set)
- Permutations (all orderings)
- Combination Sum (combinations that sum to target, reuse allowed)

---

## 11. Modified Binary Search

**When to use it**

- Sorted array (or rotated sorted array)
- "Search in rotated sorted array," "find first/last position," "search in nearly sorted"
- Monotonic functions: "find minimum in rotated sorted array," "peak element"
- Any time you can eliminate half the search space per step based on a condition

The key is correctly identifying which half to eliminate. For rotated arrays, determine which half is sorted first, then check if the target falls within that sorted half.

**Python template**

```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = left + (right - left) // 2   # avoids integer overflow

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1

def search_rotated(nums, target):
    left, right = 0, len(nums) - 1

    while left <= right:
        mid = left + (right - left) // 2

        if nums[mid] == target:
            return mid

        # Left half is sorted
        if nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        # Right half is sorted
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1

    return -1

def find_first_position(nums, target):
    left, right = 0, len(nums) - 1
    result = -1

    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            result = mid
            right = mid - 1   # keep searching left
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return result
```

**Example problems**
- Binary Search (standard)
- Search in Rotated Sorted Array
- Find First and Last Position of Element in Sorted Array

---

## 12. Top K Elements (Heap)

**When to use it**

- "K largest," "K smallest," "K most frequent"
- "Kth largest element in stream"
- Sorting is O(n log n) but you only need K elements — heap gives O(n log K)

For K largest elements, maintain a min-heap of size K. When the heap exceeds size K, pop the smallest. Whatever remains is the top K largest.

**Python template**

```python
import heapq
from collections import Counter

def top_k_frequent(nums, k):
    count = Counter(nums)
    # Min-heap of (frequency, element)
    heap = []

    for num, freq in count.items():
        heapq.heappush(heap, (freq, num))
        if len(heap) > k:
            heapq.heappop(heap)

    return [item[1] for item in heap]

def kth_largest(nums, k):
    heap = []

    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)

    return heap[0]   # root of min-heap is the Kth largest

def k_closest_points(points, k):
    # Max-heap (negate distance to simulate with min-heap)
    heap = []

    for x, y in points:
        dist = -(x**2 + y**2)
        heapq.heappush(heap, (dist, x, y))
        if len(heap) > k:
            heapq.heappop(heap)

    return [[x, y] for (_, x, y) in heap]
```

**Example problems**
- Top K Frequent Elements
- Kth Largest Element in an Array
- K Closest Points to Origin

---

## 13. K-way Merge

**When to use it**

- "Merge K sorted lists/arrays"
- "Find the smallest range covering elements from K lists"
- Input consists of K individually sorted sequences
- You need a globally sorted output or global minimum/maximum across K sources

Use a min-heap initialized with the first element from each list. Each pop gives you the globally smallest element; push the next element from the same list.

**Python template**

```python
import heapq

def merge_k_sorted_lists(lists):
    result = []
    heap = []

    # Initialize with first element from each list
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0].val, i, lst[0]))

    while heap:
        val, i, node = heapq.heappop(heap)
        result.append(node)
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))

    # Link nodes
    for i in range(len(result) - 1):
        result[i].next = result[i + 1]
    if result:
        result[-1].next = None

    return result[0] if result else None

def kth_smallest_in_sorted_matrix(matrix, k):
    n = len(matrix)
    heap = [(matrix[0][0], 0, 0)]
    visited = {(0, 0)}
    count = 0

    while heap:
        val, row, col = heapq.heappop(heap)
        count += 1

        if count == k:
            return val

        for dr, dc in [(0, 1), (1, 0)]:
            nr, nc = row + dr, col + dc
            if nr < n and nc < n and (nr, nc) not in visited:
                visited.add((nr, nc))
                heapq.heappush(heap, (matrix[nr][nc], nr, nc))
```

**Example problems**
- Merge K Sorted Lists
- Kth Smallest Element in a Sorted Matrix
- Smallest Range Covering Elements from K Lists

---

## 14. Dynamic Programming

**When to use it**

- "Number of ways to reach X," "minimum cost to reach X"
- Optimal substructure: the best solution to the whole problem depends on best solutions to subproblems
- Overlapping subproblems: the same subproblem is solved multiple times in a naive recursion
- Keywords: "minimum," "maximum," "longest," "shortest," "count," "how many ways"

DP comes in two forms. Memoization (top-down) adds a cache to a recursive solution. Tabulation (bottom-up) fills a table iteratively. Tabulation is usually faster in practice; memoization is easier to derive.

**Python template**

```python
# Memoization (top-down) — example: coin change
def coin_change_memo(coins, amount):
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def dp(remaining):
        if remaining == 0:
            return 0
        if remaining < 0:
            return float('inf')
        return 1 + min(dp(remaining - c) for c in coins)

    result = dp(amount)
    return result if result != float('inf') else -1

# Tabulation (bottom-up) — same problem
def coin_change_tab(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0

    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i:
                dp[i] = min(dp[i], dp[i - coin] + 1)

    return dp[amount] if dp[amount] != float('inf') else -1

# Longest Common Subsequence — classic 2D DP
def lcs(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    return dp[m][n]
```

**Example problems**
- Coin Change (minimum coins to make amount)
- Longest Common Subsequence (LCS)
- 0/1 Knapsack (include or exclude each item)

---

## 15. Topological Sort

**When to use it**

- Directed acyclic graph (DAG) with ordering constraints
- "Course schedule" (prerequisites), "task scheduling," "build order"
- "Find all possible orderings," "detect cycle in directed graph"
- Any problem with dependencies where A must come before B

Kahn's algorithm uses in-degree counts and a queue. Start with all nodes that have no incoming edges, process them, and reduce the in-degree of their neighbors. If not all nodes are processed, a cycle exists.

**Python template**

```python
from collections import defaultdict, deque

def topological_sort(vertices, edges):
    in_degree = {i: 0 for i in range(vertices)}
    adjacency = defaultdict(list)

    for src, dst in edges:
        adjacency[src].append(dst)
        in_degree[dst] += 1

    # Start with nodes that have no prerequisites
    queue = deque([v for v in range(vertices) if in_degree[v] == 0])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)

        for neighbor in adjacency[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return order if len(order) == vertices else []   # empty = cycle detected

def can_finish_courses(num_courses, prerequisites):
    in_degree = [0] * num_courses
    adjacency = defaultdict(list)

    for course, prereq in prerequisites:
        adjacency[prereq].append(course)
        in_degree[course] += 1

    queue = deque([i for i in range(num_courses) if in_degree[i] == 0])
    count = 0

    while queue:
        node = queue.popleft()
        count += 1
        for neighbor in adjacency[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return count == num_courses   # False means cycle exists
```

**Example problems**
- Course Schedule (can you finish all courses given prerequisites?)
- Course Schedule II (return one valid ordering)
- Alien Dictionary (infer character ordering from sorted word list)

---

## Pattern Recognition Cheat Sheet

Use this table during problem analysis. Read the problem statement, extract the cues, and map to the correct pattern before writing a single line of code.

| Pattern | Trigger Keywords | Data Structure | Complexity |
|---|---|---|---|
| Sliding Window | contiguous subarray/substring, size K window, longest/shortest with property | Array/string, two indices | O(n) time, O(1) space |
| Two Pointers | sorted array, pairs/triplets, palindrome, in-place, remove duplicates | Sorted array, two indices | O(n) time, O(1) space |
| Fast & Slow Pointers | linked list cycle, middle of list, happy number | Linked list, two pointers | O(n) time, O(1) space |
| Merge Intervals | overlapping intervals, schedule conflicts, insert interval | Sorted intervals, array | O(n log n) time |
| Cyclic Sort | range [1,n], missing number, duplicates, in-place | Array used as index | O(n) time, O(1) space |
| In-place Reversal | reverse linked list, rotate list, reverse sublist | Linked list, prev/curr pointers | O(n) time, O(1) space |
| Tree BFS | level order, minimum depth, right side view, zigzag | Tree/graph, queue | O(n) time, O(n) space |
| Tree DFS | path sum, all paths, diameter, serialize/deserialize | Tree, recursion stack | O(n) time, O(h) space |
| Two Heaps | median of stream, sliding window median, balance two halves | Two heaps (max + min) | O(log n) per operation |
| Subsets/Backtracking | all subsets, all permutations, combinations, generate all | Recursion + backtrack, result list | O(2^n) or O(n!) |
| Modified Binary Search | sorted/rotated array, search variant, monotonic condition | Sorted array, two indices | O(log n) time |
| Top K Elements | K largest/smallest/frequent, Kth element | Min-heap of size K | O(n log K) time |
| K-way Merge | merge K sorted lists/arrays, Kth smallest across K lists | Min-heap with K entries | O(n log K) time |
| Dynamic Programming | min/max ways, count paths, optimal substructure, overlapping subproblems | DP table or memo cache | O(n²) or O(n·W) typically |
| Topological Sort | prerequisites, dependencies, build order, detect directed cycle | DAG, in-degree array, queue | O(V + E) time |

### Quick Decision Tree

Start here when you see a new problem:

1. Is the input a **sorted array or string** with a contiguous constraint? → Sliding Window or Two Pointers
2. Is the input a **linked list** with cycle or middle questions? → Fast and Slow Pointers
3. Is the input a **list of intervals**? → Merge Intervals
4. Does the input contain numbers in **range [1, n]** with missing/duplicate questions? → Cyclic Sort
5. Is the input a **tree** and you need levels or shortest path? → Tree BFS
6. Is the input a **tree** and you need paths or subtree properties? → Tree DFS
7. Do you need a **dynamic median** or balancing two halves? → Two Heaps
8. Do you need **all possible combinations or arrangements**? → Backtracking
9. Is the input **sorted** and you need to search efficiently? → Modified Binary Search
10. Do you need **K largest/smallest/frequent** elements? → Top K (Heap)
11. Do you need to **merge K sorted sequences**? → K-way Merge
12. Does the problem have **overlapping subproblems** and **optimal substructure**? → Dynamic Programming
13. Is the input a **directed graph with ordering constraints**? → Topological Sort

### Complexity Anchors

Memorize these benchmarks. If your solution exceeds them for a given pattern, you are likely missing the pattern's core insight:

- O(1) space with O(n) time: Sliding Window, Two Pointers, Cyclic Sort, In-place Reversal, Fast & Slow
- O(log n) time: Modified Binary Search
- O(n log K) time: Top K Elements, K-way Merge
- O(n log n) time: Merge Intervals (sort step dominates)
- O(2^n) or O(n!): Backtracking (unavoidable for exhaustive enumeration)
- O(V + E): Graph traversal (BFS, DFS, Topological Sort)

---

## Applying the Framework

Pattern recognition is a skill, not a lookup table. The goal is to internalize the structure well enough that when you see "contiguous subarray with maximum sum," your first thought is "sliding window" before you consciously articulate why.

Practice one pattern at a time. Solve five to ten problems that are clearly in one category, identify the structural elements that triggered the pattern, then move to the next. After covering all 15, mix problems across categories and practice the triage step: which pattern fits here, and why does it fit rather than the alternatives?

The cheat sheet above is a diagnostic tool during preparation, not a crutch during the interview. When you walk into a live session, the patterns should surface from memory. The interview question is your input; the pattern is your output; the template is your starting scaffold.

The 15 patterns in this guide cover the structural anatomy of the overwhelming majority of algorithm interview questions at any tier. Master them and you will stop solving individual problems and start recognizing categories — which is exactly how experienced engineers approach unfamiliar problems in both interviews and production code.
