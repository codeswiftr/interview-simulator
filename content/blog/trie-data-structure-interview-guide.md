---
title: "Trie Data Structure: A Complete Guide for Coding Interviews"
description: "Learn how to implement a Trie from scratch in Python, when to use it over a hash map, time and space complexity, and how to solve classic interview problems including autocomplete and word search."
date: "2025-10-11"
category: "Interview Preparation"
---
# Trie Data Structure: A Complete Guide for Coding Interviews

The Trie (pronounced "try," short for retrieval) is one of those data structures that feels exotic at first glance but becomes immediately intuitive the moment you realize it is just a tree of characters. It shows up in autocomplete systems, spell checkers, IP routing tables, and — most importantly for your career — coding interviews at top companies. If you have never implemented one, this guide will take you from zero to confident in a single sitting.

## What a Trie Is and How It Works

A Trie is a tree where each node represents a single character, and paths from root to marked nodes represent complete words. Every node has up to 26 children (for lowercase English letters) and a boolean flag indicating whether that node completes a valid word.

Consider inserting the words "apple," "app," and "apt" into a Trie. The root node has a child 'a'. That 'a' node has a child 'p'. The 'p' node has children 'p' and 't'. From the second 'p', we have a child 'l', then 'e'. Both "app" and "apple" share the same path for their first three characters — this shared prefix storage is the Trie's superpower.

A Trie is fundamentally different from storing words in a hash set. When you need prefix-based operations — "does any word start with 'pre'?" — a hash set forces you to iterate every stored word. A Trie answers that query in O(m) time where m is the length of the prefix, regardless of how many words are stored.

## Python Implementation from Scratch

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True

    def search(self, word: str) -> bool:
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def starts_with(self, prefix: str) -> bool:
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
```

All three operations — insert, search, startsWith — run in O(m) time where m is the word or prefix length. Space complexity is O(total characters across all inserted words) in the worst case.

In an interview, you can use a dictionary for `children` (flexible, Pythonic) or a fixed-size array of 26 elements (`[None] * 26`) for slightly faster constant-time lookups. The dictionary approach is almost always preferred for clarity.

## When to Use Trie vs Hash Map

This is the question interviewers love to probe. Use a hash map when you need exact word lookups and never need prefix information. Use a Trie when:

- You need to find all words with a given prefix (autocomplete)
- You need to check if any stored word is a prefix of a given string
- You are doing wildcard matching (the '.' character matching any letter)
- You need to find the longest prefix of a given string that is a valid word

The hash map is O(1) average for exact lookups but O(n * m) for prefix queries. The Trie is O(m) for both exact and prefix queries, where m is the query length. If prefix operations dominate your use case, Trie wins decisively.

Space is the tradeoff: a Trie can use significantly more memory than a hash set for sparse word sets with few shared prefixes. For dense sets with many common prefixes (like a dictionary of English words), the Trie's prefix compression makes it competitive.

## Classic Interview Problems

**LeetCode 208 — Implement Trie:** This is a direct implementation problem. The solution above is exactly what you need. Practice until you can write it from memory in under five minutes.

**LeetCode 212 — Word Search II:** Given a board of characters and a list of words, find all words present in the board. The naive approach searches the board separately for each word — O(words * board cells * 4^length). With a Trie, you insert all words, then DFS across the board once, pruning entire branches when the current path is no longer a valid prefix.

```python
def find_words(board, words):
    trie = Trie()
    for word in words:
        trie.insert(word)
    
    rows, cols = len(board), len(board[0])
    result = set()
    
    def dfs(node, r, c, path):
        if node.is_end:
            result.add(path)
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return
        char = board[r][c]
        if char not in node.children:
            return
        board[r][c] = '#'  # mark visited
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            dfs(node.children[char], r+dr, c+dc, path+char)
        board[r][c] = char  # restore
    
    for r in range(rows):
        for c in range(cols):
            dfs(trie.root, r, c, "")
    return list(result)
```

**Autocomplete System (LeetCode 642):** Users type characters one at a time, and you return the top 3 hot sentences matching the current prefix. Insert sentences into a Trie where each end node stores the frequency. When a prefix is typed, traverse to the prefix node, then DFS to collect all complete words under that subtree, returning the top 3 by frequency.

**Longest Common Prefix (LeetCode 14):** Insert all strings into a Trie. The longest common prefix is the longest path from the root where every node has exactly one child and is not an end node.

## Interview Tips for Trie Problems

Always clarify the character set before coding. "Lowercase English letters only" means 26 children max — you can use a list. If the input can contain digits, uppercase, or Unicode, a dictionary is safer.

When you spot a word or prefix problem, explicitly mention Trie as a candidate even if you ultimately choose a simpler solution. This signals pattern recognition to the interviewer.

One common mistake is forgetting to check `is_end` in the `search` method — returning True when you have only matched a prefix, not a complete word. The distinction between "app" existing and "apple" existing when both are stored is exactly this flag.

Finally, if the problem involves deleting words from a Trie, track a `word_count` at each node instead of a boolean. Decrement on delete; count > 0 means the word exists.

Tries appear in roughly 5% of top-company interviews but are disproportionately common at companies that build search or autocomplete systems. Knowing them cold distinguishes the prepared candidate from the one who half-remembers the pattern.
