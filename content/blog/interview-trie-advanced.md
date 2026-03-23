---
title: "Advanced Trie Problems for Coding Interviews: Word Search, XOR, and Autocomplete"
description: "Master advanced trie interview problems: Word Search II, stream of characters, design add and search words, replace words, maximum XOR with trie, and prefix autocomplete with frequency ranking."
date: "2026-03-20"
category: "Data Structures & Algorithms"
---

# Advanced Trie Problems for Coding Interviews: Word Search II, XOR, and Autocomplete

Tries (prefix trees) appear in FAANG interviews more often than their placement in most study guides suggests. The reason: trie problems test your ability to think about character-level structure, recursive descent, and space-time tradeoffs simultaneously. Once you understand the core data structure, the interesting challenge is knowing which variant to reach for — standard trie, compressed trie, bitwise XOR trie — and when to augment the nodes with additional metadata.

## Core Trie Implementation

Before the advanced problems, a clean foundation:

```python
class TrieNode:
    def __init__(self):
        self.children: dict[str, TrieNode] = {}
        self.is_end: bool = False
        self.word: str | None = None  # useful for backtracking problems

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.word = word

    def search(self, word: str) -> bool:
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end
```

## Word Search II (LeetCode 212)

This is the canonical "trie on a grid" problem. You're given a 2D character board and a list of words; find all words present in the grid (adjacent cells, no revisiting).

The naive approach — DFS from every cell for every word — is `O(M * N * 4^L * W)` where W is the number of words. The trie optimization prunes the search: instead of searching word by word, build a trie of all words and do a single DFS that advances through the trie simultaneously with the grid traversal.

```python
def findWords(board: list[list[str]], words: list[str]) -> list[str]:
    trie = Trie()
    for word in words:
        trie.insert(word)

    rows, cols = len(board), len(board[0])
    found = []

    def dfs(row: int, col: int, node: TrieNode) -> None:
        ch = board[row][col]
        if ch not in node.children:
            return
        next_node = node.children[ch]
        if next_node.word:
            found.append(next_node.word)
            next_node.word = None  # deduplicate

        board[row][col] = "#"  # mark visited
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != "#":
                dfs(nr, nc, next_node)
        board[row][col] = ch  # restore

        # Pruning: remove leaf nodes as words are found
        if not next_node.children and not next_node.word:
            del node.children[ch]

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, trie.root)

    return found
```

The pruning step (removing leaf nodes after a word is found) is the key optimization that makes this solution efficient enough for the largest test cases. Without it, the DFS revisits dead branches repeatedly.

## Design Add and Search Words (LeetCode 211)

This problem adds wildcard matching: the `.` character matches any letter. The standard trie doesn't handle this directly because `.` doesn't correspond to a specific child.

```python
class WordDictionary:
    def __init__(self):
        self.root = TrieNode()

    def addWord(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word: str) -> bool:
        def dfs(node: TrieNode, i: int) -> bool:
            if i == len(word):
                return node.is_end
            ch = word[i]
            if ch == ".":
                return any(dfs(child, i + 1) for child in node.children.values())
            if ch not in node.children:
                return False
            return dfs(node.children[ch], i + 1)

        return dfs(self.root, 0)
```

The wildcard forces a branching DFS over all children, giving worst-case `O(M * 26^N)` for a pattern of all dots — but in practice, non-dot characters prune the search space dramatically.

## Replace Words (LeetCode 648)

Given a dictionary of root words and a sentence, replace every word in the sentence with the shortest matching root (or leave it unchanged if no root matches).

```python
def replaceWords(dictionary: list[str], sentence: str) -> str:
    trie = Trie()
    for root in dictionary:
        trie.insert(root)

    def find_root(word: str) -> str:
        node = trie.root
        for i, ch in enumerate(word):
            if node.is_end:
                return word[:i]  # found a shorter root
            if ch not in node.children:
                return word
            node = node.children[ch]
        return word

    return " ".join(find_root(w) for w in sentence.split())
```

## Maximum XOR of Two Numbers (LeetCode 421)

This is the canonical **bitwise XOR trie** problem. To maximize XOR of two numbers from an array, you need to pair each number with the number whose bits are most complementary.

Build a trie of binary representations (MSB first), then for each number, greedily choose the opposite bit at each level:

```python
class BitTrie:
    def __init__(self):
        self.root = [None, None]  # children[0] = '0' bit, children[1] = '1' bit

    def insert(self, num: int) -> None:
        node = self.root
        for bit in range(31, -1, -1):
            b = (num >> bit) & 1
            if node[b] is None:
                node[b] = [None, None]
            node = node[b]

    def max_xor(self, num: int) -> int:
        node = self.root
        xor = 0
        for bit in range(31, -1, -1):
            b = (num >> bit) & 1
            want = 1 - b  # prefer opposite bit to maximize XOR
            if node[want] is not None:
                xor |= (1 << bit)
                node = node[want]
            else:
                node = node[b]
        return xor

def findMaximumXOR(nums: list[int]) -> int:
    trie = BitTrie()
    for n in nums:
        trie.insert(n)
    return max(trie.max_xor(n) for n in nums)
```

Time complexity: `O(N * 32)` = `O(N)`. Compare to the brute-force `O(N²)`.

## Prefix Autocomplete with Frequency Ranking (LeetCode 1268)

Given a list of products and a search word, return the top 3 lexicographically smallest products for each prefix of the search word. This is a trie augmented with sorted product lists at each node.

```python
import bisect

class AutocompleteNode:
    def __init__(self):
        self.children: dict[str, AutocompleteNode] = {}
        self.suggestions: list[str] = []  # top 3 sorted

def suggestedProducts(products: list[str], searchWord: str) -> list[list[str]]:
    root = AutocompleteNode()
    products.sort()

    for product in products:
        node = root
        for ch in product:
            if ch not in node.children:
                node.children[ch] = AutocompleteNode()
            node = node.children[ch]
            if len(node.suggestions) < 3:
                node.suggestions.append(product)

    result = []
    node = root
    for ch in searchWord:
        if node and ch in node.children:
            node = node.children[ch]
            result.append(node.suggestions)
        else:
            node = None
            result.append([])

    return result
```

The key insight: since products are inserted in sorted order, each node's `suggestions` list is automatically in lexicographic order — no additional sorting needed.

## Stream of Characters (LeetCode 1032)

Design a data structure that, given a stream of characters, answers "does any word from a given list end with the current suffix of the stream?"

The trick: build a **reverse trie** (insert words reversed), then for each incoming character, maintain active search positions in the trie.

```python
class StreamChecker:
    def __init__(self, words: list[str]):
        self.root = TrieNode()
        for word in words:
            node = self.root
            for ch in reversed(word):
                if ch not in node.children:
                    node.children[ch] = TrieNode()
                node = node.children[ch]
            node.is_end = True
        self.buffer: list[str] = []

    def query(self, letter: str) -> bool:
        self.buffer.append(letter)
        node = self.root
        for ch in reversed(self.buffer):
            if ch not in node.children:
                return False
            node = node.children[ch]
            if node.is_end:
                return True
        return False
```

## Interview Tips for Trie Problems

1. **Identify the structure first**: Is it a character trie, a bitwise trie, or a suffix/reverse trie? The problem's constraints usually make this clear.
2. **Node augmentation**: What extra information do you need at each node? `is_end`, `word`, `count`, `suggestions` — add only what the problem requires.
3. **Pruning**: In search problems (Word Search II), pruning dead branches is often the difference between TLE and acceptance.
4. **Space tradeoff**: A trie with 26-way branching uses more memory than a HashMap approach but enables prefix operations. State this tradeoff explicitly in interviews.

Tries reward systematic thinking over cleverness. Practice the standard patterns, and the variants become straightforward.
