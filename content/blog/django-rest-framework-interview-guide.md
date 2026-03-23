---
title: "Django REST Framework Interview Guide: Serializers, Views, and API Design"
description: "A thorough guide to acing Django REST Framework interviews covering serializers, viewsets, authentication, permissions, and queryset optimization."
date: "2026-03-20"
category: "Technical Skills"
---

# Django REST Framework Interview Guide: Serializers, Views, and API Design

Django REST Framework (DRF) powers the APIs behind some of the largest Python web applications in production. Despite the rise of FastAPI, DRF remains the dominant choice for teams with existing Django codebases or those who value the batteries-included ecosystem. Senior Python interviews at companies running Django at scale will probe your depth with DRF's architecture and its sharp edges.

## DRF Architecture: The Request Lifecycle

A DRF request passes through: URL routing → view dispatch → authentication → permissions → throttling → content negotiation → serializer validation → queryset → response rendering.

Understanding where each concern lives lets you place logic correctly. Authentication failures return 401; permission failures return 403. Throttling occurs before business logic. Serializer validation errors return 400 with structured error bodies.

## Serializers: The Core Abstraction

Serializers handle both input validation and output representation. `ModelSerializer` auto-generates fields from your model:

```python
class ArticleSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'body', 'author_name', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_author_name(self, obj):
        return obj.author.get_full_name()
    
    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Title too short.")
        return value
```

Interview candidates often stumble on the difference between field-level validation (`validate_<field>`), object-level validation (`validate`), and `.create()`/`.update()` overrides. Be ready to implement a nested writable serializer — a common question that reveals whether you understand `validated_data` structure.

## ViewSets and Routers

`ViewSet` classes combine related actions. `ModelViewSet` provides `list`, `create`, `retrieve`, `update`, `partial_update`, and `destroy` out of the box.

```python
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related('author').all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.publish()
        return Response({'status': 'published'})
```

`DefaultRouter` auto-generates URL patterns including a browsable API root. Custom actions via `@action` are a favorite interview topic — explain when `detail=True` vs `detail=False` and how they affect URL generation.

## Authentication: Token, JWT, and OAuth

DRF ships with `BasicAuthentication`, `SessionAuthentication`, and `TokenAuthentication`. For stateless APIs, `TokenAuthentication` issues a per-user token stored in the database.

For production, most teams use `djangorestframework-simplejwt` for JWT:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

Interviewers ask about token refresh flows, JWT expiry handling, and the tradeoffs between stateless JWT (no server-side revocation without a blocklist) and database tokens (revocable but requires DB lookup on every request).

## Permissions and Throttling

Custom permissions are straightforward:

```python
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user
```

Throttling uses cache-backed rate limiting. `AnonRateThrottle` and `UserRateThrottle` are built in. Custom throttle scopes let you set different limits per endpoint:

```python
class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'

THROTTLE_RATES = {'burst': '60/min', 'sustained': '1000/day'}
```

## Queryset Optimization

N+1 queries are the most common performance issue in DRF apps. Use `select_related` for foreign keys and `only_fields`/`defer` for column projection. `prefetch_related` handles reverse FK and M2M relationships.

```python
queryset = Article.objects.select_related('author').prefetch_related('tags').only(
    'id', 'title', 'created_at', 'author__username'
)
```

Know how to use Django Debug Toolbar or query logging to catch N+1 in development. In interviews, explain why `SerializerMethodField` that hits the DB per row is an N+1 source and how to fix it with annotation or prefetch.

## DRF vs FastAPI: When to Use Each

| Concern | DRF | FastAPI |
|---|---|---|
| Existing Django app | Natural fit | Migration overhead |
| Async-first, high concurrency | Poor fit | Native support |
| Admin, ORM, migrations needed | Batteries included | Bring your own |
| Schema generation | drf-spectacular | Built-in OpenAPI |
| Team Python expertise | Mature, familiar | Newer patterns |

DRF wins when you need Django's ORM, admin, and ecosystem. FastAPI wins for greenfield high-throughput services, async I/O, and type-driven development.

## Sample Interview Questions with Answers

**Q: What's the difference between `to_representation` and `to_internal_value`?**
A: `to_representation` converts a model instance to Python primitives for output. `to_internal_value` converts incoming data to validated Python objects. Override both to customize serialization behavior fully.

**Q: How do you handle conditional field inclusion in a serializer?**
A: Override `__init__` to pop fields from `self.fields` based on context — passing `context={'request': request}` from the view gives you access to the current user and query params.

**Q: What happens if you don't call `serializer.is_valid(raise_exception=True)`?**
A: `validated_data` is unavailable and calling `.save()` raises an `AssertionError`. Always validate before saving.

**Q: How would you implement cursor-based pagination for a high-traffic feed endpoint?**
A: Use DRF's `CursorPagination` with an `ordering` field on a stable column (like `created_at` + `id`). Offset pagination degrades at large offsets because the DB must count skipped rows.

DRF mastery comes from understanding where to place logic, how to keep serializers thin, and how to protect your database from the N+1 problem. These are the questions that reveal experienced Django engineers.
