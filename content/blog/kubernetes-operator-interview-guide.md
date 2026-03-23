---
title: "Kubernetes Operator Interview: Custom Resources, Controllers, and Operator Patterns"
description: "A technical guide to Kubernetes operator interviews: the CRD + controller pattern, reconciliation loops, kubebuilder vs operator-sdk, and what senior engineers need to demonstrate."
date: "2026-03-20"
category: "Technical Skills"
---

# Kubernetes Operator Interview: Custom Resources, Controllers, and Operator Patterns

Kubernetes operators have moved from novelty to standard infrastructure pattern. Companies running stateful workloads, internal platforms, or complex lifecycle automation expect senior engineers to understand operator architecture deeply. Here is what interviews in this space actually cover.

## The Operator Pattern: What It Actually Is

An operator is the combination of a **Custom Resource Definition (CRD)** and a **controller** that watches instances of that custom resource and drives the cluster toward the desired state. The power of the pattern is encoding operational knowledge — the kind of thing a human operator would do at 2am — into software.

The CRD defines a new API resource type in the cluster. After applying the CRD manifest, `kubectl get mydatabases` works just like `kubectl get deployments`. The schema is defined in OpenAPI v3 format within the CRD's spec.

The controller is a reconciliation loop. It watches for changes to the custom resource (and often related native resources like Pods and Services), compares current state to desired state, and takes actions to close the gap. The controller-runtime library provides the scaffolding.

## The Reconciliation Loop

The reconciliation loop is the core mental model. Interviewers will test whether you understand it at a design level, not just syntactically.

```go
func (r *MyDatabaseReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // 1. Fetch the custom resource
    var db myv1.MyDatabase
    if err := r.Get(ctx, req.NamespacedName, &db); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // 2. Examine desired vs actual state
    // 3. Take actions to close the gap
    // 4. Update status subresource
    // 5. Return result (requeue if needed)
}
```

Key properties of a correct reconciliation loop:

**Idempotency**: The reconciler must handle being called multiple times with the same input without producing incorrect side effects. Creating a resource should check whether it already exists first.

**Level-triggered, not edge-triggered**: The reconciler reacts to the current state of the world, not to the specific event that triggered it. This means missing an event is safe — the next reconciliation will observe the current state and act accordingly.

**Status subresource**: Conditions should be updated on the CR's status subresource, keeping spec (desired) and status (observed) separate. Use `meta.SetStatusCondition` to manage conditions correctly.

**Finalizers**: If your operator creates external resources (cloud infrastructure, DNS records, etc.), add a finalizer to the CR. The finalizer prevents deletion until your cleanup logic runs.

## kubebuilder vs operator-sdk

Both frameworks scaffold operator projects and share the underlying `controller-runtime` library. The practical differences are mostly in tooling.

**kubebuilder** (maintained by the Kubernetes SIG API Machinery team) generates CRD manifests, controller scaffolding, RBAC markers, and test boilerplate. Markers like `// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch` generate ClusterRole manifests during `make manifests`. It is the more minimal and Kubernetes-idiomatic choice.

**operator-sdk** (maintained by Red Hat/OperatorHub) wraps kubebuilder and adds Ansible and Helm-based operator scaffolding for teams not writing Go controllers. It also integrates with the Operator Lifecycle Manager (OLM) and OperatorHub publishing pipeline. If your operator needs to be distributed through OLM, operator-sdk is the practical choice.

For Go-based operators at companies running their own clusters, kubebuilder is typically preferred for its directness.

## Controller-Runtime Patterns

**Watches and Owns**: `ctrl.NewControllerManagedBy(mgr).For(&myv1.MyDatabase{}).Owns(&appsv1.StatefulSet{})` tells controller-runtime to enqueue a reconciliation request for a MyDatabase whenever a StatefulSet it owns changes. `Watches` is more flexible — you can watch arbitrary resources and map events to reconciliation requests.

**Predicates**: Filter events before they reach the queue. A common pattern: only enqueue on generation change (ignoring status updates) using `predicate.GenerationChangedPredicate{}`. Without predicates, updating status will retrigger reconciliation, creating unnecessary loops.

**RequeueAfter**: Return `ctrl.Result{RequeueAfter: 30 * time.Second}` to schedule a future reconciliation without an external event. Useful for polling external systems (cloud APIs, database status checks).

**Rate limiting and backoff**: controller-runtime uses a rate limiter on the workqueue. Returning an error triggers exponential backoff automatically. Do not implement your own retry loop inside `Reconcile`.

## Common Interview Questions

**"How do you handle creation of external resources in an operator?"**
Add a finalizer on first reconciliation. On deletion (when `DeletionTimestamp` is set), run cleanup, remove the finalizer. This ensures your cleanup logic runs before the CR is garbage collected.

**"What is the difference between an informer and a watch in Kubernetes?"**
A watch is a raw streaming HTTP connection to the API server. An informer wraps a watch with a local in-memory cache and event handlers — it handles reconnection, list-watch startup, and delivers events from the cache rather than directly from the API server. controller-runtime's client uses informers via the cache layer.

**"How do you test a controller without a real cluster?"**
`envtest` (from controller-runtime) starts a real API server and etcd binary locally. Tests use a real Kubernetes API surface. `envtest` is the standard approach for controller integration tests. Unit test individual helper functions; integration test the reconciler with `envtest`.

**"What are the operator maturity levels?"**
OperatorHub defines five levels: Basic Install, Seamless Upgrades, Full Lifecycle (backup/restore), Deep Insights (metrics/SLOs), and Auto Pilot (horizontal/vertical scaling, auto-remediation). Interviewers use these levels to assess how much operational knowledge your operator actually encodes.

---
