---
title: "Object-Oriented Design Interviews: Parking Lot, Chess, Library System"
description: "How to ace object-oriented design interviews — identifying classes and relationships, encapsulation, inheritance vs composition, SOLID principles, and walkthroughs of the most common OOD interview questions."
date: "2026-03-20"
category: "System Design"
---

# Object-Oriented Design Interviews: Parking Lot, Chess, Library System

Object-oriented design (OOD) interviews ask you to model a real-world system using classes and relationships. Unlike system design which focuses on scale and distributed systems, OOD focuses on clean abstraction, correct class relationships, and application of OO principles.

## The OOD Interview Process

You'll be given a problem like "Design a parking lot" or "Design a chess game." The interviewer expects:

1. **Requirements clarification:** What features? What constraints?
2. **Core classes identification:** What are the nouns? They often become classes.
3. **Relationships:** Inheritance? Composition? Association?
4. **Key methods:** What operations does each class expose?
5. **Design pattern application:** Where are patterns (Strategy, Observer, Factory) applicable?

Don't rush to write code. Spend 5 minutes discussing requirements and identifying classes before any implementation.

## Design a Parking Lot

Requirements: multiple floors, different vehicle sizes (motorcycle, car, truck), different spot sizes (small, medium, large), vehicle can park in its size or larger, track availability, payment system.

**Core classes:**
- `ParkingLot` — manages floors, entry/exit
- `ParkingFloor` — contains spots, tracks availability
- `ParkingSpot` — has type (SMALL/MEDIUM/LARGE), occupied/free, current vehicle
- `Vehicle` (abstract) — has license plate, `getType()`
- `Motorcycle(Vehicle)`, `Car(Vehicle)`, `Truck(Vehicle)`
- `ParkingTicket` — entry time, spot, vehicle
- `PaymentCalculator` — computes fee based on time and vehicle type

**Key design decisions:**
- Use `enum SpotType` and `enum VehicleType` — cleaner than string comparisons
- `ParkingSpot.canFit(Vehicle)` encapsulates the size compatibility logic
- `ParkingFloor.findAvailableSpot(VehicleType)` searches for the best spot
- Payment uses Strategy pattern — different rate strategies for weekday/weekend/valet

**Inheritance vs composition here:** Vehicle types use inheritance (`Motorcycle extends Vehicle`) because they genuinely share behavior (all vehicles have license plates, entry/exit). Different payment strategies use composition — a `PaymentCalculator` delegates to a `RateStrategy` rather than subclassing.

## Design a Chess Game

Requirements: two players, all piece types, movement rules, check/checkmate detection, game history.

**Core classes:**
- `ChessGame` — manages game state, turn taking, win detection
- `Board` — 8×8 grid of squares, knows piece positions
- `Square` — has position (row, col), holds optional piece
- `Piece` (abstract) — has color, position; abstract `getValidMoves(Board)`
- `King`, `Queen`, `Rook`, `Bishop`, `Knight`, `Pawn` — each implements `getValidMoves()`
- `Player` — has color, set of pieces
- `Move` — from square, to square, optional captured piece (for history/undo)

**Key design decisions:**
- `Piece.getValidMoves(Board)` returns list of valid moves — each piece type knows its own movement rules. This is the core polymorphism.
- Check detection: after any move, call `isKingInCheck(color)` — determines if any opponent piece can capture the king
- Checkmate: the king is in check AND has no valid moves that escape check
- `GameHistory` stores all `Move` objects — enables undo, replay, PGN export
- Observer pattern: `GameObserver` interface; ChessGame notifies observers (UI, logger) on each event

## Design a Library System

Requirements: search books by title/author/ISBN, check out and return, reservations for checked-out books, multiple copies, members, overdue fines.

**Core classes:**
- `Library` — central coordinator, manages catalog and members
- `BookItem` — a physical copy of a book (has barcode, status: AVAILABLE/CHECKED_OUT/RESERVED)
- `Book` — a book title (has ISBN, title, authors, category, shelf location)
- `Catalog` — search index; maps title/author/ISBN to Book objects
- `Member` — has ID, name, checkout history, fine balance
- `Checkout` — links BookItem to Member, has due date
- `Reservation` — queue per BookItem for when it's returned
- `FineCalculator` — computes overdue fine per day

**Relationships:**
- `Library` has a `Catalog` (composition) and many `Member`s (association)
- `Book` has many `BookItem`s (one-to-many)
- `Member` has many `Checkout`s (one-to-many)

**Search optimization:** The `Catalog` maintains inverted indexes — HashMap from normalized title tokens → Set of Books. Multiple HashMaps for title, author, ISBN. This gives O(1) lookup vs O(N) linear scan.

## SOLID Principles in OOD Interviews

Interviewers sometimes explicitly ask you to apply SOLID. Know what each means:

**Single Responsibility:** Each class has one reason to change. `ParkingLot` manages lots; `PaymentCalculator` handles fees — they're separate because billing logic can change independently of parking management.

**Open/Closed:** Open for extension, closed for modification. Adding a new vehicle type (e.g., Bus) shouldn't require modifying existing code — just add a new subclass.

**Liskov Substitution:** Subclasses must be substitutable for their parent class. A `Pawn` must behave like a valid `Piece` everywhere a `Piece` is expected.

**Interface Segregation:** Don't force clients to depend on interfaces they don't use. Instead of one fat `VehicleInterface`, have `Parkable`, `Payable`, `Trackable` interfaces.

**Dependency Inversion:** High-level modules depend on abstractions. `ParkingLot` depends on `PaymentStrategy` interface, not on `CreditCardProcessor` directly. New payment methods plug in without changing `ParkingLot`.

## Common OOD Interview Mistakes

**Modeling everything as attributes instead of classes:** If "VehicleType" appears in multiple places and has behavior, make it a class or enum, not a string.

**Using inheritance when you need composition:** "Has-a" relationships should use composition. A `Car` doesn't "is-a" `Engine` — it has an engine. Overusing inheritance creates fragile hierarchies.

**Not thinking about extension:** OOD interviews often have follow-up "now add X feature" questions. Designs that require modifying existing classes for each new feature violate open/closed. Use Strategy, Observer, and Factory patterns to enable extension.

**Ignoring the interface between classes:** How does `ParkingFloor` tell `ParkingLot` a spot is available? What parameters does `findAvailableSpot` take? These method signatures are part of your design.

