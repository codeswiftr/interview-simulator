---
title: "Ruby on Rails Interview Prep: ActiveRecord, Metaprogramming, and the Questions That Separate Juniors from Seniors"
description: "A comprehensive guide to Ruby on Rails interviews — covering ActiveRecord internals, Rails conventions, metaprogramming patterns, testing strategies, and the performance pitfalls every interviewer expects you to know."
date: "2026-03-20"
category: "Programming Languages"
---

Ruby on Rails interviews have a distinct flavor. The framework's "convention over configuration" philosophy means interviewers spend less time on setup boilerplate and more time probing whether you understand *why* the conventions exist. Knowing how to scaffold a CRUD app is table stakes. Understanding N+1 queries, polymorphic associations, and the method_missing hook is where the conversation gets interesting.

## Ruby Language Fundamentals

Before Rails-specific questions, expect pure Ruby questions that reveal whether you think in Ruby idioms.

**Blocks, procs, and lambdas** — Interviewers distinguish candidates by whether they understand the differences: lambdas check arity and return from the lambda; procs don't check arity and return from the enclosing method. `yield` inside a method calls the implicit block. `&` converts a proc to a block. This matters in practice when you're writing enumerable methods or DSL-style code.

**Symbols vs. strings** — Symbols are immutable and deduplicated in the object space (one object per unique name). Strings are mutable and each string literal creates a new object. In Rails, hash keys and method names use symbols heavily. The distinction matters for memory in hot paths.

**Comparable and Enumerable modules** — Ruby's mixin-based inheritance model shows up in real code. If you include `Comparable`, you implement `<=>` and get `<`, `>`, `between?`, etc. for free. If you include `Enumerable`, you implement `each` and get `map`, `select`, `reduce`, and 50+ methods for free. Understanding this pattern demonstrates Ruby fluency.

**Frozen string literals** — The `# frozen_string_literal: true` pragma makes all string literals immutable, which reduces object allocation and GC pressure. Senior interviews may ask why this matters at scale.

## ActiveRecord: The Deep End

ActiveRecord is the part of Rails interviews where most candidates struggle. Surface-level knowledge — `belongs_to`, `has_many`, basic scopes — is expected. The real questions are about what happens under the hood.

**N+1 queries** — The classic Rails performance problem. You have a `Post` model that `has_many :comments`. If you do `Post.all.each { |p| p.comments.count }`, you fire one query to load posts and N additional queries to count each post's comments. The fix is eager loading: `Post.includes(:comments).all` fires two queries regardless of how many posts exist. Always mention `bullet` gem as an N+1 detection tool.

**`includes` vs. `joins` vs. `preload` vs. `eager_load`** — These are not interchangeable. `includes` lets Rails decide (usually two queries). `preload` always uses separate queries. `eager_load` always uses LEFT OUTER JOIN. `joins` loads associated records for filtering but does NOT prevent N+1 on access. Interviewers love this question.

**Scopes and query composition** — ActiveRecord scopes return `ActiveRecord::Relation` objects, making them chainable. `Post.published.recent.limit(10)` builds a single SQL query lazily. A common trap: a scope that returns `nil` instead of an empty relation breaks chaining. Always return `all` as a no-op default: `scope :published, -> { where(published: true) || all }`.

**Callbacks and their pitfalls** — `before_save`, `after_create`, etc. seem convenient but create tight coupling between business logic and persistence. Heavy use of callbacks makes models hard to test in isolation and creates surprising action-at-a-distance bugs. Strong candidates know when to extract logic to service objects instead.

**Database transactions** — `ActiveRecord::Base.transaction` wraps operations in a database transaction. If an exception is raised, the transaction rolls back. Importantly, `ActiveRecord` callbacks do NOT automatically roll back on validation failures — only on exceptions. Know the difference between `save` (returns false on failure) and `save!` (raises on failure).

## Polymorphic Associations

Polymorphic associations let a model belong to multiple other models through a single association:

```ruby
class Comment < ApplicationRecord
  belongs_to :commentable, polymorphic: true
end

class Post < ApplicationRecord
  has_many :comments, as: :commentable
end
```

The `comments` table stores `commentable_type` (the class name as a string) and `commentable_id`. This is flexible but has implications: you cannot use foreign key constraints across types, and queries that join on the polymorphic key are harder to optimize. Senior candidates know these tradeoffs and can discuss when STI (Single Table Inheritance) is a better alternative.

## Metaprogramming Patterns

Rails itself is built on Ruby metaprogramming. Understanding these patterns demonstrates deep Ruby knowledge.

**`method_missing` and `respond_to_missing?`** — When you call a method that doesn't exist, Ruby calls `method_missing`. ActiveRecord's dynamic finders (`find_by_email`) used `method_missing` historically. The pattern: intercept the call, detect the intent from the method name, and execute it. Always override `respond_to_missing?` alongside `method_missing` to keep duck typing correct.

**`define_method`** — Programmatically define methods at class definition time. Rails uses this extensively: `has_many :posts` calls `define_method(:posts)` under the hood to create the association accessor. When you see repetitive method definitions, refactor with `define_method` in a loop.

**`class_eval` and `instance_eval`** — `class_eval` executes a block in the context of a class (as if you were inside the class definition). `instance_eval` executes in the context of a specific object. These power DSLs like `has_many`, `validates`, and `scope`.

**`attr_accessor` internals** — It's just a macro that calls `define_method` twice: once for the getter and once for the setter. Understanding this demystifies most of Rails' "magic."

## Testing in Rails

Rails applications are tested at three levels, and interviewers probe all three.

**Unit tests** — Test models in isolation. Mock database calls where possible. Factory Bot is the standard fixture replacement: `FactoryBot.create(:user, email: "test@example.com")`.

**Controller/request specs** — Test that endpoints return correct status codes, headers, and body shapes. Prefer request specs over controller specs in modern Rails.

**System/feature specs** — End-to-end tests that drive a browser (via Capybara + Selenium). Slow but critical for testing user flows. Candidates should know when NOT to write system specs (too slow for unit-level behavior).

**Common interview question:** "How do you test a method that sends emails?" — Use `ActionMailer::Base.deliveries` in test mode, which captures emails without sending them, and assert on the queue.

## Performance Pitfalls to Know

Beyond N+1, Rails applications hit predictable performance walls:

**Eager loading too much** — Loading records you don't use (`includes` pulling in 10,000 associated records when you only need counts). Counter caches (`counter_cache: true`) solve the count problem without loading the records.

**Background jobs not being used** — Sending emails, processing images, or calling external APIs synchronously in a web request. Any operation over ~100ms belongs in Sidekiq or a similar background job system.

**Missing database indexes** — ActiveRecord makes it trivially easy to forget indexes on foreign keys and columns used in `where` clauses. `explain` your slow queries; a sequential scan on a large table is a red flag.

**Unbounded queries** — `User.all` in a context where the users table has 2M rows. Always add `.limit()` or use pagination (Kaminari, Pagy).

## The Hiring Bar in Practice

Rails interviews at strong engineering teams expect you to demonstrate taste — knowing when to use the framework's magic and when to fight it. "Skinny controllers, fat models" is old wisdom. Modern Rails best practice: skinny controllers, skinny models, rich service objects and query objects. If your model has more than three callbacks and five scopes, it's probably doing too much.

The candidates who stand out are those who can explain not just what Rails does, but why the convention exists, what it costs, and when you'd deviate from it.
