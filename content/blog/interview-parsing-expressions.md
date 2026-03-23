---
title: "Parsing and Expression Problems: Calculator, Tokenizer, and Recursive Descent"
description: "How to solve expression parsing problems in coding interviews — implement a calculator with parentheses, tokenize mathematical expressions, recursive descent parsing, and evaluate prefix/postfix expressions."
date: "2026-03-20"
category: "Algorithms"
---

# Parsing and Expression Problems: Calculator, Tokenizer, and Recursive Descent

Expression parsing problems appear in senior interviews because they require combining multiple techniques: string processing, stack-based evaluation, and sometimes recursive descent. They're also used in compiler design questions and interpreter implementation rounds. This guide covers the patterns from basic calculator to a mini expression evaluator.

## Basic Calculator II: +, -, *, /

"Implement a calculator that evaluates a string with +, -, *, / (integers, no parentheses)."

The key insight: * and / have higher precedence than + and -. Process + and - lazily (push to stack, merge at end) while processing * and / immediately with the previous term.

```python
def calculate(s):
    stack = []
    num = 0
    op = '+'  # Previous operator

    for i, c in enumerate(s + '+'):  # Sentinel to flush at end
        if c.isdigit():
            num = num * 10 + int(c)
        elif c in '+-*/':
            if op == '+':
                stack.append(num)
            elif op == '-':
                stack.append(-num)
            elif op == '*':
                stack.append(stack.pop() * num)
            elif op == '/':
                # Truncate toward zero (Python // truncates toward negative infinity)
                stack.append(int(stack.pop() / num))
            op = c
            num = 0

    return sum(stack)
```

The trick: process the current operator with the number we just finished parsing, not the number we're about to read.

## Basic Calculator I: +, -, Parentheses

"Evaluate a string with +, -, and parentheses."

Parentheses change the sign context. Use a stack to save the running total and sign when entering a parenthesis.

```python
def calculate(s):
    stack = []
    result = 0
    sign = 1
    num = 0

    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c == '+':
            result += sign * num
            num = 0
            sign = 1
        elif c == '-':
            result += sign * num
            num = 0
            sign = -1
        elif c == '(':
            # Save current state, start fresh inside parentheses
            stack.append(result)
            stack.append(sign)
            result = 0
            sign = 1
        elif c == ')':
            result += sign * num
            num = 0
            result *= stack.pop()  # Sign before the parenthesis
            result += stack.pop()  # Result before the parenthesis

    result += sign * num
    return result
```

## Expression Tokenizer

Before parsing, tokenize the expression into meaningful tokens (numbers, operators, parentheses):

```python
def tokenize(s):
    tokens = []
    i = 0
    while i < len(s):
        if s[i].isspace():
            i += 1
        elif s[i].isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            tokens.append(int(s[i:j]))
            i = j
        else:
            tokens.append(s[i])
            i += 1
    return tokens
```

## Evaluate Reverse Polish Notation (Postfix)

In postfix notation, operators come after operands: `3 4 + 2 *` = `(3+4)*2` = 14.

```python
def evalRPN(tokens):
    stack = []
    ops = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: int(a / b),  # Truncate toward zero
    }

    for token in tokens:
        if token in ops:
            b = stack.pop()
            a = stack.pop()
            stack.append(ops[token](a, b))
        else:
            stack.append(int(token))

    return stack[0]
```

## Recursive Descent Parser

For full expression parsing with variables and functions, recursive descent is the standard technique. Each grammar rule becomes a function:

```
expression → term (('+' | '-') term)*
term       → factor (('*' | '/') factor)*
factor     → number | '(' expression ')'
```

```python
def parse_expression(tokens, pos=0):
    def parse_expr():
        nonlocal pos
        result = parse_term()
        while pos < len(tokens) and tokens[pos] in ('+', '-'):
            op = tokens[pos]
            pos += 1
            term = parse_term()
            result = result + term if op == '+' else result - term
        return result

    def parse_term():
        nonlocal pos
        result = parse_factor()
        while pos < len(tokens) and tokens[pos] in ('*', '/'):
            op = tokens[pos]
            pos += 1
            factor = parse_factor()
            result = result * factor if op == '*' else int(result / factor)
        return result

    def parse_factor():
        nonlocal pos
        if tokens[pos] == '(':
            pos += 1  # consume '('
            result = parse_expr()
            pos += 1  # consume ')'
            return result
        else:
            num = tokens[pos]
            pos += 1
            return int(num)

    return parse_expr()
```

## Minimum Add to Make Parentheses Valid

Counting the minimum additions to make a parentheses string valid:

```python
def minAddToMakeValid(s):
    open_needed = 0   # Close parens needed
    close_needed = 0  # Open parens still unmatched

    for c in s:
        if c == '(':
            open_needed += 1
        elif open_needed > 0:
            open_needed -= 1  # Matched
        else:
            close_needed += 1  # Unmatched close

    return open_needed + close_needed
```

## Score of Parentheses

"Score a parentheses string: `()` = 1, `AB` = score(A) + score(B), `(A)` = 2 * score(A)."

```python
def scoreOfParentheses(s):
    stack = [0]  # Current score at each depth

    for c in s:
        if c == '(':
            stack.append(0)  # New scope
        else:
            v = stack.pop()
            score = max(2 * v, 1)  # Either 2*inner or base 1
            stack[-1] += score

    return stack[0]
```

## Interview Approach

When you see a parsing/calculator problem:
1. Identify what operators/operations are supported
2. Determine if precedence matters — if yes, use the "lazy +/- eager */" pattern
3. Determine if parentheses are involved — if yes, use a stack for context save/restore
4. For arbitrary expressions, build a tokenizer first, then recursive descent

The two-stack calculator (one for values, one for operators) is an alternative approach worth knowing. Recursive descent is cleaner for full expressions with function calls or more complex grammar.
