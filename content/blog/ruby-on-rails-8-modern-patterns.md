---
title: "Ruby on Rails 8: Modern Patterns Guide"
description: "Modern Ruby on Rails 8 patterns for production applications—Hotwire, Turbo, Stimulus, Solid Queue, solid_cache, import maps, and the return to simplicity that Rails 8 represents."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Ruby on Rails 8: Modern Patterns Guide

Rails 8 (released late 2024) doubles down on the "you may not need a separate JavaScript frontend" philosophy with significant improvements to Hotwire, built-in caching and queuing with SQLite3, and no-build JavaScript by default. For full-stack developers, Rails 8 is faster to ship with than ever before.

## What's New in Rails 8

**No-build by default**: Import maps replace Node.js + bundlers for most Rails apps. No webpack, no esbuild unless you specifically need them.

**Solid Queue**: Rails' new database-backed job queue, built into the framework. No Sidekiq/Redis required for job processing.

**Solid Cache**: Database-backed cache using SQLite or your existing database. No Redis required for caching common use cases.

**Authentication generator**: `rails generate authentication` creates a complete JWT-less session-based auth system.

**Better Hotwire**: Improved Turbo Streams, Turbo Frames, and Stimulus patterns.

## Authentication with Rails 8 Generator

```bash
rails generate authentication
```

This generates:
- `SessionsController` with login/logout
- `app/models/user.rb` with password hashing (bcrypt)
- `app/models/session.rb` for session management
- Password reset flow
- Authentication concern for controllers

```ruby
class ApplicationController < ActionController::Base
  include Authentication

  before_action :require_authentication
end

class PostsController < ApplicationController
  def index
    @posts = Current.user.posts
  end
end
```

Full, production-grade authentication in 2 minutes.

## Hotwire: Turbo Frames

Turbo Frames make partial page updates declarative:

```html
<!-- posts/index.html.erb -->
<turbo-frame id="new-post-form">
  <%= link_to "New Post", new_post_path %>
</turbo-frame>

<%= render @posts %>
```

```html
<!-- posts/new.html.erb -->
<turbo-frame id="new-post-form">
  <%= form_with(model: @post) do |form| %>
    <!-- form content -->
    <%= form.submit "Create Post" %>
  <% end %>
</turbo-frame>
```

Clicking "New Post" replaces the frame content with the form—no JavaScript written.

## Turbo Streams for Real-Time Updates

Turbo Streams broadcast real-time updates over WebSocket (via ActionCable):

```ruby
# In your model
class Post < ApplicationRecord
  after_create_commit -> {
    broadcast_append_to "posts",
      target: "posts-list",
      partial: "posts/post"
  }
end
```

```html
<!-- In your view -->
<%= turbo_stream_from "posts" %>

<div id="posts-list">
  <%= render @posts %>
</div>
```

Any new post created anywhere in the system (including background jobs) is pushed to all subscribed clients. Zero client-side code.

## Solid Queue for Background Jobs

```ruby
# config/queue.yml
default: &default
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    - queues: "*"
      threads: 3
      processes: 1

production:
  <<: *default
  workers:
    - queues: "critical"
      threads: 10
    - queues: "default"
      threads: 5
```

```ruby
# app/jobs/welcome_email_job.rb
class WelcomeEmailJob < ApplicationJob
  queue_as :default

  def perform(user_id)
    user = User.find(user_id)
    UserMailer.welcome(user).deliver_now
  end
end

# Enqueue from controller
WelcomeEmailJob.perform_later(user.id)
```

Solid Queue uses your existing database (PostgreSQL, MySQL, or SQLite) — no Redis/Sidekiq configuration.

## Import Maps (No-Build JavaScript)

```bash
./bin/importmap pin @hotwired/turbo
./bin/importmap pin @hotwired/stimulus
./bin/importmap pin lodash
```

This adds packages from jspm.io via CDN. No npm, no bundler. Works for most Rails applications.

For custom JavaScript with Stimulus:

```javascript
// app/javascript/controllers/hello_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["name"]

  greet() {
    console.log(`Hello, ${this.nameTarget.value}!`)
  }
}
```

## The Speed of Rails 8

A complete full-stack Rails 8 app with:
- User authentication (sessions, password reset)
- Real-time updates (Turbo Streams)
- Background jobs (Solid Queue)
- Caching (Solid Cache)
- Deployable to a $5/month VPS

...takes roughly 4-8 hours from scratch for an experienced developer. The philosophy is "boring technology that ships fast."

## Interview Tips

Rails 8 interview questions:

1. **Hotwire vs React** — when server-rendered HTML updates win; the CRUD application tradeoff
2. **Turbo Frames vs Turbo Streams** — Frames for replacing content, Streams for broadcasting
3. **Solid Queue** — database-backed jobs without Redis, when Redis is still better
4. **Import maps** — no-build JavaScript, when to add a bundler
5. **Rails conventions** — explain convention over configuration and its productivity benefits

The core Rails 8 interview insight: the "no-build, no separate frontend" approach is a genuine productivity advantage for full-stack developers building internal tools and CRUD applications. The question is when the trade-off (less SPA flexibility) is worth it — and increasingly often, it is.
