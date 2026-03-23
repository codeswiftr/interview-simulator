---
title: "Protocol Buffers and gRPC Interview Guide"
description: "Technical interview preparation for roles requiring Protocol Buffers and gRPC expertise: schema design, service definitions, streaming patterns, performance characteristics, and what infrastructure-heavy companies like Google, Uber, and microservices shops expect."
date: "2026-03-19"
category: "Technical Skills Guides"
---

# Protocol Buffers and gRPC Interview Guide

Protocol Buffers (protobuf) and gRPC are Google's open-source stack for efficient, schema-first API communication between services. While REST/JSON dominates external APIs, gRPC has become the dominant internal service communication mechanism at Google, Uber, Netflix, Dropbox, and other companies with large microservice architectures. The combination of binary serialization (smaller payloads, faster parsing), schema-first contract definition (API changes are versioned in `.proto` files), and generated client libraries in multiple languages makes gRPC compelling for internal APIs at scale.

## Protocol Buffers: Schema Definition and Serialization

**The .proto file**: Protobuf messages are defined in `.proto` files. A message is a collection of typed fields with field numbers: `message User { string name = 1; int32 age = 2; repeated string roles = 3; }`. Field numbers (not names) are encoded in the binary wire format — changing a field number is a breaking change; changing a field name is not.

**Wire format**: Protobuf uses a binary encoding that encodes each field as a tag (field number + wire type) followed by the value. Integers use variable-length encoding (varint) — small integers are encoded in fewer bytes. The binary format is significantly smaller than JSON for most payloads (30-70% smaller is typical) and much faster to parse (no string tokenization).

**Field numbering and backward compatibility**: Fields are identified by number, not name. Rules for backward-compatible changes: you can add new fields (old code ignores unknown fields), you can rename fields (wire format doesn't use names), you can mark fields as `reserved` to prevent reuse of old field numbers. You cannot change field types incompatibly, cannot remove fields without reserving the number, cannot change repeated/singular/oneof categorization without care.

**Oneof fields**: `oneof value { string string_val = 1; int32 int_val = 2; }` — only one field in the oneof is set at a time. Useful for discriminated union patterns. Only one variant can be set; setting one clears the others.

**Well-known types**: Protobuf includes standard types: `google.protobuf.Timestamp` (nanosecond precision UTC time), `google.protobuf.Duration`, `google.protobuf.Any` (arbitrary message, useful for generic containers), `google.protobuf.Struct` (JSON-like dynamic values), `google.protobuf.FieldMask` (specify which fields to update).

## gRPC: RPC Framework on HTTP/2

**Service definition**: gRPC services are defined in `.proto` files as `service` blocks: `service UserService { rpc GetUser (GetUserRequest) returns (User); rpc ListUsers (ListUsersRequest) returns (stream User); }`. The protobuf compiler generates server interfaces and client stubs.

**HTTP/2 multiplexing**: gRPC runs over HTTP/2, which enables multiple concurrent streams over a single TCP connection. This is crucial for performance — no head-of-line blocking, no connection establishment overhead per request, header compression. In contrast, HTTP/1.1 REST requires either connection pooling or sequential requests.

**Four communication patterns**: Unary RPC (single request, single response — like a regular function call). Server streaming (single request, multiple responses — the server streams results). Client streaming (client sends a stream of messages, server responds with one message). Bidirectional streaming (both sides stream independently).

**Status codes**: gRPC has a defined set of status codes (similar to HTTP but different): `OK`, `CANCELLED`, `UNKNOWN`, `INVALID_ARGUMENT`, `NOT_FOUND`, `ALREADY_EXISTS`, `PERMISSION_DENIED`, `RESOURCE_EXHAUSTED` (rate limiting), `FAILED_PRECONDITION`, `ABORTED`, `DEADLINE_EXCEEDED`, `UNAVAILABLE` (server down), `INTERNAL`. Using the right status code communicates intent to clients.

**Deadlines and cancellation**: gRPC supports client-specified deadlines propagated through the call chain. `ctx.WithDeadline(time.Now().Add(5 * time.Second))` sets a deadline on the context, and the RPC returns `DEADLINE_EXCEEDED` if not complete in time. Deadlines propagate through service calls — if service A calls service B with a 5-second deadline, B also inherits that deadline.

**Interceptors (middleware)**: gRPC interceptors are the equivalent of HTTP middleware. Unary interceptors wrap unary calls; stream interceptors wrap streaming calls. Common uses: authentication (extract token from metadata, validate), logging (record request/response, duration), tracing (extract/inject trace context), retry (retry on transient errors).

## Schema Design Best Practices

Interviews often include schema design exercises:

**Versioning strategies**: Proto3 has no field required/optional distinction (all fields are effectively optional). Common versioning: use field numbers strictly (never reuse), use `reserved` for deleted fields, add new fields with new numbers, create new message types for major breaking changes.

**Pagination**: Standard gRPC pagination pattern: `int32 page_size = 1; string page_token = 2;` in requests; `string next_page_token = 2;` in responses. Empty `next_page_token` signals no more pages.

**Field masks for partial updates**: Use `google.protobuf.FieldMask` to specify which fields to update in an update RPC. This avoids the "update everything" antipattern and enables atomic partial updates.

## Who Uses gRPC

**Google**: gRPC was created at Google; all internal services use protobuf/Stubby (the internal predecessor). Cloud APIs (Google Cloud Storage, BigQuery, etc.) are gRPC-first with transcoded REST.

**Uber**: Entire service mesh uses gRPC with protobuf. Uber's YARPC framework wraps gRPC.

**Netflix**: Replaced Thrift with gRPC for many services.

**Cloud-native ecosystems**: Kubernetes API server communicates with the kubelet over gRPC. Envoy proxy uses gRPC-based control plane (xDS APIs). Istio, Linkerd.

**Microservices at scale**: Any company with 50+ internal services benefits from the contract enforcement and generated clients that gRPC provides over ad-hoc REST/JSON.

gRPC expertise signals infrastructure sophistication — understanding HTTP/2, binary protocols, schema evolution, and service mesh integration differentiates candidates for distributed systems roles.
