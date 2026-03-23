---
title: "Django 5: Advanced Patterns Guide"
description: "Advanced Django 5 patterns for production applications—async views, database optimization, custom managers, signals, Class-Based Views, and the architectural patterns that scale Django applications."
date: "2026-03-21"
category: "Language Deep Dives"
---

# Django 5: Advanced Patterns Guide

Django 5 continues the framework's evolution toward async support while maintaining its famously productive synchronous patterns. This guide covers the advanced patterns that distinguish senior Django developers from beginners.

## Async Views in Django 5

Django 5 fully supports async views when using async-capable servers (Uvicorn, Daphne):

```python
from django.http import JsonResponse
import asyncio

async def get_user_dashboard(request):
    # Run multiple async operations concurrently
    user_data, notifications, activity = await asyncio.gather(
        get_user_data(request.user.id),
        get_notifications(request.user.id),
        get_recent_activity(request.user.id),
    )
    return JsonResponse({
        'user': user_data,
        'notifications': notifications,
        'activity': activity
    })
```

Use `sync_to_async` for ORM operations within async views (the Django ORM itself remains synchronous):

```python
from asgiref.sync import sync_to_async

async def get_user_data(user_id):
    user = await sync_to_async(User.objects.get)(id=user_id)
    return {'id': user.id, 'name': user.username}
```

## Database Optimization Patterns

**select_related for ForeignKey** (SQL JOIN):
```python
# BAD: N+1 query problem
posts = Post.objects.all()
for post in posts:
    print(post.author.username)  # Extra query per post

# GOOD: Single JOIN query
posts = Post.objects.select_related('author').all()
for post in posts:
    print(post.author.username)  # No extra queries
```

**prefetch_related for ManyToMany** (separate query, Python-side join):
```python
# Fetch posts with all their tags in 2 queries total
posts = Post.objects.prefetch_related('tags').all()
for post in posts:
    print([tag.name for tag in post.tags.all()])
```

**annotations for aggregations**:
```python
from django.db.models import Count, Avg, Q

posts = Post.objects.annotate(
    comment_count=Count('comments'),
    avg_rating=Avg('ratings__value'),
    approved_comments=Count('comments', filter=Q(comments__approved=True))
).filter(comment_count__gt=5)
```

## Custom Managers and QuerySets

Encapsulate query logic in the model layer:

```python
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='published')

class PostQuerySet(models.QuerySet):
    def by_author(self, user):
        return self.filter(author=user)

    def with_stats(self):
        return self.annotate(
            comment_count=Count('comments'),
            view_count=Sum('page_views')
        )

    def popular(self):
        return self.filter(view_count__gt=1000).order_by('-view_count')

class Post(models.Model):
    status = models.CharField(max_length=20, default='draft')
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = PostQuerySet.as_manager()
    published = PublishedManager()

# Usage
popular_posts = Post.published.by_author(request.user).popular().with_stats()
```

## Class-Based Views for RESTful APIs

```python
from django.views import View
from django.core.paginator import Paginator
from django.http import JsonResponse

class UserListView(View):
    def get(self, request):
        users = User.objects.select_related('profile').order_by('username')
        paginator = Paginator(users, 25)
        page = paginator.get_page(request.GET.get('page', 1))

        data = [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'joined': u.date_joined.isoformat()
        } for u in page]

        return JsonResponse({
            'users': data,
            'total': paginator.count,
            'pages': paginator.num_pages
        })

    def post(self, request):
        import json
        body = json.loads(request.body)
        user = User.objects.create_user(
            username=body['username'],
            email=body['email'],
            password=body['password']
        )
        return JsonResponse({'id': user.id}, status=201)
```

## Signals for Decoupled Operations

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        send_welcome_email.delay(instance.id)  # Celery task
```

Signals keep models clean by moving side effects to receivers.

## Database Transactions

```python
from django.db import transaction

def transfer_funds(from_account, to_account, amount):
    with transaction.atomic():
        # Both operations succeed or both fail
        from_account.balance -= amount
        from_account.save()

        to_account.balance += amount
        to_account.save()

        TransferLog.objects.create(
            from_account=from_account,
            to_account=to_account,
            amount=amount
        )
```

## Caching Strategies

```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# Per-view caching
@cache_page(60 * 15)  # 15 minutes
def public_post_list(request):
    posts = Post.published.with_stats()[:50]
    return render(request, 'posts/list.html', {'posts': posts})

# Programmatic caching
def get_user_feed(user_id):
    cache_key = f'user_feed_{user_id}'
    feed = cache.get(cache_key)

    if feed is None:
        feed = compute_feed(user_id)  # Expensive operation
        cache.set(cache_key, feed, timeout=300)  # 5 minutes

    return feed
```

## Interview Tips

Django interview questions for senior roles:

1. **N+1 query prevention** — select_related vs prefetch_related use cases
2. **Custom managers and QuerySets** — encapsulating query logic in the model layer
3. **database transactions** — when and how to use transaction.atomic()
4. **Async Django** — sync_to_async for ORM in async views
5. **Signals** — decoupling side effects from model logic

The most impressive Django knowledge: understanding when the ORM's convenience creates performance problems, and knowing how to use `explain()` and `connection.queries` to diagnose and fix them.
