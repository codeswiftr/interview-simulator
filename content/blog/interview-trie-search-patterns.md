---
title: "Trie Patterns Beyond the Basics: Auto-Complete, XOR Trie, and Prefix Problems"
description: "Go beyond basic trie implementation — learn auto-complete with ranking, Word Search II with pruning, prefix sum trees, and XOR trie for maximum XOR problems."
date: "2026-03-20"
category: "Algorithms"
---

Most candidates can implement a basic trie: insert a word, search for a word, starts-with prefix. The interviews that separate strong candidates ask you to combine tries with other data structures, use tries for non-string problems (like XOR on integers), or apply tries with pruning in DFS. This post covers the patterns that matter at the senior level.

## Trie Foundations (Done Right)

Before building on the foundation, make sure it's solid:

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.count = 0  # Words passing through this node

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
            node.count += 1
        node.is_end = True

    def search(self, word: str) -> bool:
        node = self._find(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        return self._find(prefix) is not None

    def _find(self, prefix: str):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node
```

The `count` field is often needed for ranking in auto-complete — it tells you how many words pass through each node.

## Auto-Complete with Ranked Results

LeetCode 1268 (Search Suggestions System) asks for the top 3 lexicographically smallest words per prefix. A trie with DFS handles this efficiently:

```python
def suggested_products(products: list[str], search_word: str) -> list[list[str]]:
    trie = Trie()
    for p in products:
        trie.insert(p)

    def dfs(node, prefix, results):
        if len(results) == 3:
            return
        if node.is_end:
            results.append(prefix)
        for ch in sorted(node.children.keys()):
            dfs(node.children[ch], prefix + ch, results)

    result = []
    node = trie.root
    current_prefix = ""
    for ch in search_word:
        if node is None or ch not in node.children:
            node = None
            result.append([])
        else:
            node = node.children[ch]
            current_prefix += ch
            suggestions = []
            dfs(node, current_prefix, suggestions)
            result.append(suggestions)

    return result
```

**Optimization:** Pre-sort the `products` list before inserting. Then DFS naturally encounters words in lexicographic order, so you don't need `sorted()` in the inner loop.

## Word Search II: Trie + DFS with Pruning

This is the canonical hard trie problem. Given a board and a list of words, find all words that exist as paths in the board. The naive approach — run word search for each word — is O(words × board). The trie approach is dramatically faster:

```python
def find_words(board: list[list[str]], words: list[str]) -> list[str]:
    trie = TrieNode()
    for word in words:
        node = trie
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = word  # Store word at end node

    rows, cols = len(board), len(board[0])
    result = []

    def dfs(r, c, node):
        ch = board[r][c]
        if ch not in node.children:
            return
        next_node = node.children[ch]

        if next_node.is_end:
            result.append(next_node.is_end)
            next_node.is_end = False  # Avoid duplicates

        # Prune: remove leaf nodes as we backtrack
        board[r][c] = '#'  # Mark visited
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != '#':
                dfs(nr, nc, next_node)
        board[r][c] = ch  # Restore

        # Prune trie: remove childless nodes
        if not next_node.children:
            del node.children[ch]

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, trie)

    return result
```

The critical optimization: **delete childless trie nodes after backtracking**. This progressively prunes the trie as words are found, dramatically reducing redundant DFS exploration.

## Prefix Sum + Trie: Minimum XOR Sum

The XOR trie maps integers to their binary representation and finds pairs minimizing XOR. But a related pattern is counting prefix XOR sums — combining a standard prefix sum array with a trie for range XOR queries.

**Maximum XOR of Two Numbers (XOR Trie):**

```python
class XORTrie:
    def __init__(self):
        self.root = {}

    def insert(self, num: int) -> None:
        node = self.root
        for i in range(31, -1, -1):
            bit = (num >> i) & 1
            if bit not in node:
                node[bit] = {}
            node = node[bit]

    def max_xor(self, num: int) -> int:
        node = self.root
        xor = 0
        for i in range(31, -1, -1):
            bit = (num >> i) & 1
            want = 1 - bit  # Flip to maximize XOR
            if want in node:
                xor |= (1 << i)
                node = node[want]
            else:
                node = node[bit]
        return xor

def find_maximum_xor(nums: list[int]) -> int:
    trie = XORTrie()
    for n in nums:
        trie.insert(n)
    return max(trie.max_xor(n) for n in nums)
```

**Maximum XOR of a subarray:** Combine prefix XOR with XOR trie. For each index j, compute `prefix_xor[j]` and query the trie for the maximum XOR with any previous prefix. Insert `prefix_xor[j]` into the trie after querying.

## Compressed Trie (Patricia Trie)

When the input consists of sparse, long strings, a standard trie wastes memory on single-child chains. A compressed trie merges single-child paths into edge labels.

In interviews, you rarely implement a compressed trie from scratch — but knowing the concept matters when asked about memory optimization:

- Standard trie: O(total characters) nodes
- Compressed trie: O(words) nodes, with O(total characters) total edge label length

Suffix arrays achieve similar goals for suffix-based search and are preferred in production string matching.

## Trie for IP Routing (Longest Prefix Match)

IP routing tables use tries where keys are IP address prefixes. The **longest prefix match** rule finds the most specific route for a destination:

```python
def longest_prefix_match(routes, destination):
    # Routes: list of (prefix_bits, prefix_length, next_hop)
    node = trie_root
    best_match = None
    for bit in ip_to_bits(destination):
        if bit not in node.children:
            break
        node = node.children[bit]
        if node.is_route:
            best_match = node.next_hop
    return best_match
```

This is O(32) for IPv4, O(128) for IPv6 — constant time regardless of routing table size. CIDR-based longest prefix match is one of the original motivations for tries.

## When to Use a Trie vs HashMap

| Scenario | Prefer |
|----------|--------|
| Exact string lookup | HashMap (simpler, faster) |
| Prefix search | Trie |
| All strings sharing prefix | Trie |
| Lexicographic ordering | Trie |
| XOR/bitwise prefix problems | XOR Trie |
| Memory-constrained exact search | HashMap |

## Interview Tips

**Don't over-engineer the node.** Start with `children: dict` and `is_end: bool`. Add fields only when the problem requires them.

**Pruning is the differentiator.** For Word Search II and similar DFS + trie problems, mention the pruning optimization even if you implement the basic version first. It shows you understand the performance bottleneck.

**Complexity analysis.** Trie operations are O(L) where L is the word length — often better stated as O(L) than O(log n) for sorted alternatives. Interviewers appreciate the correct characterization.

Tries reward candidates who see the connection between prefix operations and tree structure. Once you internalize that connection — and pair it with DFS pruning — the hardest trie problems become manageable.
