---
title: "Software Design Patterns for Interviews: When and Why to Use Each"
description: "Design patterns in technical interviews — Singleton, Factory, Observer, Strategy, Decorator, Command, Builder patterns: when to use each, implementation examples, and how to discuss patterns in system design and OOD interviews."
date: "2026-03-20"
category: "System Design"
---

# Software Design Patterns for Interviews: When and Why to Use Each

Design patterns are recurring solutions to common software design problems. Interviewers expect senior engineers to recognize when a pattern fits and to explain the tradeoffs. This guide covers the most frequently asked patterns with the interview-relevant context.

## Why Design Patterns Matter in Interviews

The goal isn't pattern name-dropping. It's demonstrating that you've internalized solutions to common problems and can recognize when to apply them. When you say "I'd use a Strategy pattern here because we need to swap algorithms at runtime without changing the calling code," you're showing architectural thinking, not vocabulary.

Conversely: don't force patterns where they don't fit. An unnecessary Singleton or an over-engineered Factory is a red flag. The best engineers know when NOT to use a pattern.

## Singleton

**What it does:** Ensures a class has only one instance, providing a global access point.

**When to use:** Database connection pools, configuration managers, logging service, thread pools — resources that should only be initialized once.

**Implementation (thread-safe Java):**
```java
public class ConnectionPool {
    private static volatile ConnectionPool instance;
    private ConnectionPool() { /* initialize connections */ }
    
    public static ConnectionPool getInstance() {
        if (instance == null) {
            synchronized (ConnectionPool.class) {
                if (instance == null) instance = new ConnectionPool();
            }
        }
        return instance;
    }
}
```

**Tradeoffs:** Global state is hard to test (can't replace with a mock easily). Prefer dependency injection over singletons when testability matters.

## Factory and Abstract Factory

**What it does:** Creates objects without specifying the exact class to create. Factory method: subclasses decide which class to instantiate. Abstract Factory: creates families of related objects.

**When to use:** When the type of object to create is determined at runtime; when you want to encapsulate object creation logic; when creating an object is complex.

```python
class NotificationFactory:
    @staticmethod
    def create(channel: str) -> Notification:
        if channel == "email": return EmailNotification()
        if channel == "sms": return SMSNotification()
        if channel == "push": return PushNotification()
        raise ValueError(f"Unknown channel: {channel}")
```

**Interview use:** Whenever an OOD question involves creating objects of different types based on runtime conditions — reach for Factory.

## Observer

**What it does:** Defines a one-to-many dependency. When one object changes state, all its dependents are notified automatically.

**When to use:** Event systems, publish-subscribe patterns, UI data binding (React's state → re-render), anything where many components need to react to one source of change.

```python
class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
    
    def subscribe(self, event_type, handler):
        self._subscribers[event_type].append(handler)
    
    def publish(self, event_type, event_data):
        for handler in self._subscribers[event_type]:
            handler(event_data)
```

**Interview use:** Notification systems, user activity tracking, any system where "when X happens, do Y and Z."

## Strategy

**What it does:** Defines a family of algorithms, encapsulates each one, and makes them interchangeable. The algorithm can vary independently from the clients that use it.

**When to use:** When you want to switch algorithms at runtime; when multiple classes differ only in their behavior; to eliminate conditional statements that select behavior.

```python
class Sorter:
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy
    
    def sort(self, data):
        return self._strategy.sort(data)

class QuickSort(SortStrategy):
    def sort(self, data): ...

class MergeSort(SortStrategy):
    def sort(self, data): ...
```

**Interview use:** Parking lot payment strategies (cash/credit/validation), shipping cost calculators, different discount strategies in e-commerce.

## Decorator

**What it does:** Attaches additional responsibilities to an object dynamically. Decorators provide a flexible alternative to subclassing for extending functionality.

**When to use:** Adding features to objects without changing the class; when extension by subclassing would lead to an explosion of subclasses for every combination of features.

Classic example: Java I/O streams. `BufferedReader(new FileReader("file.txt"))` — the BufferedReader wraps and adds buffering to any Reader.

```python
class LoggingService:
    def __init__(self, service):
        self._service = service
    
    def process(self, request):
        print(f"Request: {request}")
        result = self._service.process(request)
        print(f"Response: {result}")
        return result
```

**Interview use:** Adding caching, logging, or authentication to services; middleware in web frameworks.

## Command

**What it does:** Encapsulates a request as an object, allowing parameterization, queuing, and undoable operations.

**When to use:** Undo/redo functionality, job queues, transaction systems, macro recording.

```python
class Command(ABC):
    @abstractmethod
    def execute(self): ...
    
    @abstractmethod
    def undo(self): ...

class MoveCommand(Command):
    def __init__(self, piece, to_position):
        self.piece = piece
        self.to_position = to_position
        self.from_position = piece.position
    
    def execute(self):
        self.piece.move_to(self.to_position)
    
    def undo(self):
        self.piece.move_to(self.from_position)
```

**Interview use:** Chess game undo, text editor undo/redo, transaction management, remote execution.

## Builder

**What it does:** Separates the construction of a complex object from its representation.

**When to use:** When constructing an object requires many steps; when the same construction process should create different representations; when an object has many optional parameters.

```python
class QueryBuilder:
    def __init__(self):
        self._table = None
        self._conditions = []
        self._limit = None
    
    def from_table(self, table):
        self._table = table
        return self
    
    def where(self, condition):
        self._conditions.append(condition)
        return self
    
    def limit(self, n):
        self._limit = n
        return self
    
    def build(self):
        # construct the SQL string
        ...
```

**Interview use:** SQL query builders, HTTP request builders, complex object initialization with many optional parameters.

## Pattern Selection in Interviews

When asked "how would you design X?":
1. Identify the variation: what changes? algorithms (Strategy), object creation (Factory), behavior addition (Decorator), event handling (Observer)?
2. Name the pattern only if it fits naturally — don't force it
3. Explain the tradeoffs: why this pattern over alternatives?

The interview is testing judgment, not vocabulary. "I'd use dependency injection here rather than a Singleton because it makes the code testable" shows better thinking than pattern name-dropping.

