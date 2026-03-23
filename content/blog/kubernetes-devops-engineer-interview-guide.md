# Kubernetes Engineer Interview Guide 2024: Container Orchestration at Production Scale

Kubernetes engineering roles — whether titled DevOps Engineer, Platform Engineer, or SRE — have converged on a core set of expectations: deep knowledge of cluster internals, the ability to debug live production issues under pressure, and the judgment to make architectural trade-offs at scale. This guide covers what those interviews actually test and how to prepare.

## What "Kubernetes Engineer" Actually Means

Job descriptions are inconsistent. Before preparing, identify which role you're actually interviewing for:

**Platform Engineer / Infrastructure Engineer:** Builds the platform that product teams run on. Heavy Terraform/IaC, cluster provisioning, multi-cluster architecture, developer experience tooling. Kubernetes is the runtime, not the focus.

**DevOps / Site Reliability Engineer with K8s focus:** Operates and improves Kubernetes-based production systems. Incident response, capacity planning, observability, deployment pipelines. Deep operational knowledge expected.

**Kubernetes Specialist / Container Platform Engineer:** Kubernetes as the primary domain. Custom controllers, operators, admission webhooks, cluster API, multi-tenancy. Expects expert-level architecture knowledge.

Read the job description for: operator pattern, custom controllers, cluster API, multi-cluster, or mesh — these signal the third category and require deeper preparation.

## Interview Format

**Large tech companies (Google, Meta, Stripe):**
- 1-2 coding rounds (medium DSA + scripting/automation)
- 1-2 system design rounds (reliability-focused)
- 1 live debugging or troubleshooting scenario
- 1 behavioral round

**Platform-focused companies and scaleups:**
- 1 practical exercise (debug a broken cluster, write a Helm chart, implement a controller)
- 1 architecture/system design round
- 1 culture/behavioral round

**Startups:**
- Often a take-home (build a Kubernetes operator, write a deployment pipeline)
- 1 technical deep-dive on your take-home
- 1 behavioral

## Control Plane Deep Dive

Interviewers expect you to trace exactly what happens when you run `kubectl apply -f deployment.yaml`. Know each component's role.

### API Server

The API server is the single entry point for all cluster operations. Every component (kubelet, scheduler, controller manager, clients) talks to the API server — never directly to each other.

Key responsibilities:
- **Authentication**: validates who is making the request (x509 certs, bearer tokens, OIDC)
- **Authorization**: checks RBAC policies to determine if the authenticated identity can perform the requested action on the resource
- **Admission control**: runs mutating admission webhooks (modify the object) then validating admission webhooks (accept/reject) before persisting
- **Validation**: ensures the object conforms to the schema
- **Persistence**: writes to etcd

What interviewers ask: "What happens between `kubectl apply` and the pod starting?" Walk this path in full — API server validates and persists the Deployment object, the Deployment controller creates a ReplicaSet, the ReplicaSet controller creates Pods, the scheduler assigns nodes to pods, kubelets on those nodes pull the image and start containers.

### etcd

The distributed key-value store that holds all cluster state. Everything else is derived state — if you lose etcd without a backup, your cluster state is gone.

Critical facts:
- **Raft consensus**: requires quorum (n/2 + 1 nodes) to accept writes. A 3-node etcd cluster tolerates 1 failure. A 5-node cluster tolerates 2 failures.
- **Performance sensitivity**: etcd is I/O-sensitive. Slow disks (or co-located noisy neighbors) degrade the entire control plane. Always run etcd on dedicated fast storage (NVMe SSD, dedicated IOPS on cloud).
- **Defragmentation**: etcd does not reclaim space automatically after deletes. Production clusters need periodic `etcdctl defrag` or they hit the storage quota and stop accepting writes.
- **Backup**: Kubernetes clusters have no built-in backup. You must snapshot etcd periodically (e.g., Velero for both etcd and persistent volume snapshots).

### Scheduler

The scheduler watches for pods with no `.spec.nodeName` set, selects a node for them, and updates the pod object with the node assignment. It does not start containers — that's the kubelet's job.

The scheduling algorithm runs in two phases:

**Filtering**: eliminate nodes that cannot run the pod
- Node has sufficient CPU/memory for the pod's requests
- Pod's `nodeSelector` matches node labels
- Node tolerates all the pod's taints
- Node affinity rules are satisfied
- Resource quotas allow additional pods in this namespace

**Scoring**: rank the remaining nodes
- Spread pods evenly (inter-pod anti-affinity)
- Bin-pack to free up nodes for autoscaling
- Prefer nodes with the pod's required images already pulled
- `topologySpreadConstraints` to balance across zones

After filtering and scoring, the scheduler selects the highest-scoring node and writes `.spec.nodeName` to the pod object.

### Controller Manager

Runs multiple controllers as goroutines in one process. Each controller watches specific resource types and reconciles actual state toward desired state:

- **Deployment controller**: watches Deployments, creates/updates ReplicaSets
- **ReplicaSet controller**: watches ReplicaSets, creates/deletes Pods to match `spec.replicas`
- **Node controller**: watches node heartbeats, marks nodes `NotReady` when heartbeats stop, evicts pods from unreachable nodes after `node-monitor-grace-period`
- **Service controller**: creates cloud load balancers for `LoadBalancer` type Services
- **Job controller**: watches Jobs, creates Pods, marks Jobs complete when enough Pods succeed

The pattern used by all controllers — watch, compare, reconcile — is the same pattern you'll implement when writing operators.

## Data Plane: Nodes and Networking

### Kubelet

The node agent. Watches the API server for pods assigned to its node and manages their lifecycle:

1. Pulls the container image (via the container runtime — containerd or CRI-O, not Docker in modern clusters)
2. Sets up the network namespace (by calling the CNI plugin)
3. Starts containers in the pod
4. Runs liveness and readiness probes
5. Reports pod status back to the API server
6. Manages volume mounts, including calling CSI drivers for persistent volumes

The kubelet does **not** schedule pods — it only manages pods already assigned to its node by the scheduler.

### Kube-proxy

Implements `Service` networking on each node. Watches the API server for Service and Endpoint changes, then programs the node's network rules accordingly.

Modes:
- **iptables mode** (default): writes iptables rules to DNAT traffic from a ClusterIP to a random pod endpoint. Linear rule lookup — degrades at ~10,000+ services.
- **IPVS mode**: uses kernel-level IPVS for O(1) lookup at any scale. Enable with `--proxy-mode=ipvs`. Preferred for large clusters.

Note: kube-proxy handles east-west service traffic within the cluster. It does not handle external traffic — that's handled by cloud load balancers or Ingress controllers.

### CNI Plugins

The Container Network Interface defines how pod networking is set up. The kubelet calls the CNI plugin to configure the network namespace when a pod starts.

Common plugins:

**Calico**: Implements NetworkPolicy enforcement with high performance. Uses BGP for routing in on-premise deployments; can use overlay (VXLAN/IP-in-IP) mode for cloud. eBPF dataplane available as alternative to iptables. Best choice for environments where NetworkPolicy enforcement is a hard requirement.

**Cilium**: eBPF-native, replaces kube-proxy entirely with eBPF programs. Offers L7 policy (filter by HTTP path, gRPC method), identity-based security (not just IP-based), and Hubble for deep observability. Performance advantage over iptables-based plugins at scale. Increasingly the default at companies running Kubernetes at scale.

**AWS VPC CNI / Azure CNI / GKE native**: Cloud-native plugins that assign actual VPC IP addresses to pods. Pods are first-class VPC citizens — no overlay. Simpler architecture but pod density limited by VPC IP allocation per node.

**Flannel**: Simple overlay network (VXLAN). Does not implement NetworkPolicy. Appropriate only for simple clusters where NetworkPolicy is not required.

## Pod Lifecycle and Scheduling

### QoS Classes

When node memory is exhausted, Kubernetes evicts pods based on their QoS class:

**Guaranteed** — evicted last. Requires `resources.requests == resources.limits` for ALL containers in the pod (both CPU and memory).

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

**Burstable** — evicted second. Has at least one container with requests or limits set, but not equal.

**BestEffort** — evicted first. No resource requests or limits set at all.

Production rule: critical system components (API gateway, databases) should be Guaranteed. Batch or background workloads can be Burstable or BestEffort.

### Node Affinity vs. Node Selector vs. Taints/Tolerations

These are three separate but overlapping mechanisms. Interviewers frequently ask you to distinguish them.

**nodeSelector**: Simple label matching. The pod runs only on nodes with these labels.

```yaml
spec:
  nodeSelector:
    disk: ssd
```

**Node Affinity**: More expressive version of nodeSelector. Supports `requiredDuringSchedulingIgnoredDuringExecution` (hard requirement) and `preferredDuringSchedulingIgnoredDuringExecution` (soft preference with weights).

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: topology.kubernetes.io/zone
            operator: In
            values:
            - us-east-1a
            - us-east-1b
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        preference:
          matchExpressions:
          - key: disk
            operator: In
            values:
            - ssd
```

**Taints and Tolerations**: Taints repel pods from nodes unless the pod has a matching toleration. Used to reserve nodes for specific workloads.

```yaml
# Taint the node (on the node spec or via kubectl):
kubectl taint nodes gpu-node-1 gpu=true:NoSchedule

# Pod must tolerate this taint to be scheduled on that node:
spec:
  tolerations:
  - key: "gpu"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
```

Effect options:
- `NoSchedule`: new pods without toleration are not scheduled here; existing pods unaffected
- `PreferNoSchedule`: soft version of NoSchedule
- `NoExecute`: both prevents scheduling and evicts existing pods without toleration

### Topology Spread Constraints

Ensures pods are spread across failure domains (zones, nodes). Replaces the deprecated `podAntiAffinity` patterns for zone spreading.

```yaml
spec:
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: my-service
```

`maxSkew: 1` means the difference in pod count between any two zones cannot exceed 1.

## Networking: Services and Ingress

### Service Types

**ClusterIP** (default): A stable virtual IP accessible only within the cluster. The IP is programmed into kube-proxy's iptables/IPVS rules on every node.

**NodePort**: Exposes the service on a port (30000-32767 by default) on every node. External traffic hits `<any-node-IP>:<node-port>` and gets NAT'd to a pod. Not suitable for production — exposes a port on every node.

**LoadBalancer**: Creates a cloud provider load balancer that routes external traffic to the NodePort and then to pods. The standard production pattern for externally-exposed services. The cloud controller manager provisions the LB.

**ExternalName**: Maps a Service to a DNS name. The cluster DNS returns a CNAME. Useful for accessing external services by a cluster-internal DNS name.

### Ingress and Ingress Controllers

`Ingress` is a Kubernetes resource that defines HTTP/HTTPS routing rules (host-based and path-based routing, TLS termination). The Ingress resource itself does nothing — you need an Ingress controller to process it.

Common Ingress controllers:
- **nginx-ingress**: The most widely deployed. Configures an nginx process based on Ingress resources.
- **Traefik**: Automatic Let's Encrypt certificates, dynamic configuration, good for smaller clusters.
- **AWS ALB Ingress Controller**: Provisions an AWS Application Load Balancer per Ingress resource. Better for AWS-native deployments.
- **Istio Gateway**: When you're already running a service mesh, prefer the Gateway API over Ingress.

The modern replacement for Ingress is the **Gateway API** (now GA). It provides cleaner role separation (infrastructure admin defines GatewayClass and Gateway; application dev defines HTTPRoute), more expressive routing, and protocol support beyond HTTP.

### Network Policies

Network Policies are firewall rules for pods. Without any NetworkPolicy, all pods in a cluster can reach all other pods — a security risk in multi-tenant clusters.

```yaml
# Deny all ingress to pods with app=payment, then allow only from app=checkout
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: payment-isolation
spec:
  podSelector:
    matchLabels:
      app: payment
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: checkout
    ports:
    - protocol: TCP
      port: 8080
```

Critical gotcha: NetworkPolicy is additive. Multiple policies selecting the same pod are ORed together — a pod with two NetworkPolicies allowing different ingress sources allows traffic from both. There's no "deny rule" that overrides allows.

NetworkPolicy enforcement requires your CNI to support it. Flannel does not. Calico and Cilium do.

## Storage: PVs, PVCs, and CSI

### The PV/PVC Model

**PersistentVolume (PV)**: A piece of cluster storage provisioned by an admin or dynamically by a StorageClass. Independent lifecycle from any pod.

**PersistentVolumeClaim (PVC)**: A request for storage by a pod. Specifies size, access mode, and optionally StorageClass.

**StorageClass**: Defines the provisioner (e.g., `ebs.csi.aws.com`) and parameters (volume type, IOPS, encryption). When a PVC references a StorageClass, the provisioner dynamically creates the PV.

Access modes:
- `ReadWriteOnce` (RWO): one node can mount read/write. Standard for block storage (EBS, GCE PD).
- `ReadOnlyMany` (ROX): multiple nodes can mount read-only.
- `ReadWriteMany` (RWX): multiple nodes can mount read/write. Requires a network filesystem (NFS, EFS, CephFS).

### CSI Drivers

Container Storage Interface is the standard plugin interface replacing the in-tree storage drivers. CSI drivers run as pods within the cluster and implement the Create/Delete/Attach/Detach/Mount/Unmount operations.

Examples: `ebs.csi.aws.com` (AWS EBS), `efs.csi.aws.com` (AWS EFS), `pd.csi.storage.gke.io` (GKE persistent disk), `rook-ceph.rbd.csi.ceph.com` (Rook/Ceph).

Interview question: "A pod is stuck in Pending state with `persistentvolumeclaim 'my-pvc' not found`. Walk me through debugging." Check: does the PVC exist and is it in `Bound` state? Does the StorageClass exist? Is the CSI driver running (`kubectl get pods -n kube-system`)? Are there events on the PVC (`kubectl describe pvc my-pvc`)?

## Operator Pattern and Custom Controllers

This is the section that separates mid-level from senior K8s candidates.

### The Reconcile Loop

An operator is a Kubernetes controller that extends the API with custom resources (CRDs) and manages their lifecycle. The core pattern:

```
Watch (API server events) → Compare (actual vs. desired state) → Act (create/update/delete resources) → Update status
```

The reconcile function must be **idempotent** — it can be called multiple times for the same event and must produce the same result. It must also handle errors gracefully (return error to trigger retry, not panic).

```go
func (r *MyAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    // 1. Fetch the custom resource
    app := &myv1.MyApp{}
    if err := r.Get(ctx, req.NamespacedName, app); err != nil {
        if errors.IsNotFound(err) {
            return ctrl.Result{}, nil // Deleted — nothing to do
        }
        return ctrl.Result{}, err
    }

    // 2. Check if the resource is being deleted
    if !app.DeletionTimestamp.IsZero() {
        return r.handleDeletion(ctx, app)
    }

    // 3. Ensure finalizer is registered
    if !controllerutil.ContainsFinalizer(app, myFinalizer) {
        controllerutil.AddFinalizer(app, myFinalizer)
        return ctrl.Result{}, r.Update(ctx, app)
    }

    // 4. Reconcile: ensure the Deployment exists with correct spec
    desired := r.buildDeployment(app)
    existing := &appsv1.Deployment{}
    if err := r.Get(ctx, types.NamespacedName{Name: app.Name, Namespace: app.Namespace}, existing); err != nil {
        if errors.IsNotFound(err) {
            return ctrl.Result{}, r.Create(ctx, desired)
        }
        return ctrl.Result{}, err
    }

    // 5. Update if needed
    if !reflect.DeepEqual(existing.Spec, desired.Spec) {
        existing.Spec = desired.Spec
        return ctrl.Result{}, r.Update(ctx, existing)
    }

    // 6. Update status
    app.Status.ReadyReplicas = existing.Status.ReadyReplicas
    return ctrl.Result{}, r.Status().Update(ctx, app)
}
```

### Informers and the Watch Mechanism

Operators don't poll the API server. They use informers — a cache backed by a long-running Watch connection. When the Watch receives events, informers update the local cache and enqueue reconcile requests.

The informer cache means `r.Get()` inside a reconcile function reads from the local cache, not the API server — this is why you might read stale state briefly after an update. This is fine because reconciles are eventually consistent.

**Owner references**: When a controller creates child resources (a Deployment for a MyApp CR), it sets an owner reference on the child pointing to the parent. When the parent is deleted, Kubernetes garbage-collects the children via the cascade deletion mechanism — the controller doesn't need to clean them up manually (unless it needs to perform external cleanup, in which case it uses finalizers).

## Security: RBAC, Pod Security, and Policy Enforcement

### RBAC Model

Four resources: Role, ClusterRole, RoleBinding, ClusterRoleBinding.

- **Role / RoleBinding**: namespace-scoped. A Role grants permissions within a namespace; a RoleBinding grants a Role to a subject within that namespace.
- **ClusterRole / ClusterRoleBinding**: cluster-scoped. Can grant access to cluster-scoped resources (nodes, PVs) or namespace-scoped resources across all namespaces.

```yaml
# Grant a service account read access to pods in one namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
- kind: ServiceAccount
  name: my-service
  namespace: production
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

Common interview question: "A pod is failing with 403 Forbidden when calling the Kubernetes API. How do you debug?" Check: what ServiceAccount is the pod using? `kubectl auth can-i list pods --as=system:serviceaccount:production:my-service`. If denied, check what Roles/ClusterRoles are bound to that ServiceAccount.

### Pod Security Standards

Pod Security Standards replaced PodSecurityPolicy (deprecated in 1.21, removed in 1.25). Three built-in profiles:

- **Privileged**: Unrestricted. No controls applied.
- **Baseline**: Prevents known privilege escalations. No privileged containers, no hostPath volumes, no hostNetwork.
- **Restricted**: Heavily restricted. Requires non-root user, drops all capabilities, requires seccompProfile.

Applied at the namespace level via labels:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### OPA/Gatekeeper for Policy as Code

When Pod Security Standards aren't expressive enough, OPA Gatekeeper provides a general-purpose policy framework using Rego.

A Gatekeeper constraint enforces that all containers have resource limits:

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sContainerLimits
metadata:
  name: container-must-have-limits
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  parameters:
    cpu: "2"
    memory: "4Gi"
```

Admission webhooks (which Gatekeeper uses) add latency to every API server write. Keep constraint evaluation fast and ensure the webhook has `failurePolicy: Fail` only for security-critical policies — otherwise a Gatekeeper outage blocks all cluster operations.

## Scaling: HPA, VPA, and KEDA

### Horizontal Pod Autoscaler (HPA)

Scales replica count based on metrics. Default: CPU utilization. Can use custom metrics via the metrics-server or external metrics adapters.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

The `stabilizationWindowSeconds` for scale-down prevents flapping when load oscillates around the threshold.

### Vertical Pod Autoscaler (VPA)

Adjusts CPU and memory requests/limits for containers based on historical usage. Works in three modes:
- `Off`: Only recommends; makes no changes.
- `Initial`: Sets resources only on pod creation; doesn't restart running pods.
- `Auto`: Updates running pods (requires restart).

VPA and HPA on the same Deployment using CPU is not supported — they conflict. Use VPA in `Off` mode to get recommendations, then apply them manually, or use VPA for vertical scaling and HPA with custom metrics (not CPU) for horizontal scaling.

### KEDA: Event-Driven Autoscaling

KEDA extends HPA to scale based on external event sources: Kafka consumer lag, SQS queue depth, Prometheus queries, Redis list length, HTTP request rate, and 60+ others.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: kafka-consumer-scaler
spec:
  scaleTargetRef:
    name: kafka-consumer-deployment
  minReplicaCount: 1
  maxReplicaCount: 100
  triggers:
  - type: kafka
    metadata:
      bootstrapServers: kafka.production:9092
      consumerGroup: my-consumer-group
      topic: user-events
      lagThreshold: "100"      # Scale up when lag per partition > 100
```

KEDA can also scale to zero — no consumers running when no messages exist, which HPA cannot do (minReplicas must be at least 1).

## Multi-Cluster Patterns

Senior K8s interviews increasingly include multi-cluster questions.

**Why multiple clusters:**
- Failure isolation: a cluster-level incident (etcd failure, control plane bug) doesn't affect all environments
- Regulatory: separate clusters for different data sovereignty requirements (EU data stays in EU cluster)
- Tenant isolation: separate clusters per large enterprise tenant
- Scale limits: a single cluster has practical limits (~5,000 nodes per cluster per upstream limits)

**Traffic distribution patterns:**
- **Active-active**: Traffic split across clusters behind a global load balancer (Cloudflare Load Balancing, AWS Route 53, or a service mesh with multi-cluster support like Istio)
- **Active-passive with failover**: Primary cluster handles all traffic; secondary is kept in sync and promoted during failures
- **Read replicas**: Write cluster in one region; read-only clusters in other regions with data replication

**Fleet management:**
- **ArgoCD ApplicationSets**: Deploy the same application across many clusters from a single definition
- **Cluster API**: Provision and lifecycle-manage clusters declaratively (the "Kubernetes to manage Kubernetes" pattern)
- **Fleet (Rancher)**: Multi-cluster GitOps at scale
- **Google Anthos / Azure Arc**: Managed fleet control planes for hybrid environments

## Common Interview Questions and How to Answer Them

### "Design a zero-downtime deployment strategy for a stateful service."

Walk through each concern:

**Rolling deploys**: `maxUnavailable: 0`, `maxSurge: 1`. New pods start before old pods terminate. Works for stateless services; for stateful services you must also handle:

**Database migrations**: Use the expand-contract pattern. Never rename a column — add the new column, copy data, migrate app code, drop old column over multiple deploys. The running app version must be able to work with both the pre-migration and post-migration schema simultaneously during the rollout window.

**Session affinity**: If users have sessions tied to specific pod instances, use session draining — remove the pod from the Service (readiness probe fails) and wait for in-flight requests to complete before terminating. Set `terminationGracePeriodSeconds` to cover maximum request duration plus connection draining time.

**Canary validation**: Route 5% of traffic to new pods using weighted traffic splitting (Argo Rollouts or Istio). Monitor error rate and latency. Automate rollback if error budget burns faster than threshold.

### "Explain how a pod gets scheduled."

Trace the complete path: user applies manifest → API server authenticates, authorizes, runs admission control, writes to etcd → Deployment controller sees new Deployment, creates ReplicaSet → ReplicaSet controller creates Pod objects with no node assignment → scheduler watches for unscheduled Pods, runs filter phase (resource fit, affinity, taints), runs scoring phase (spread, bin-pack), writes chosen node to pod's `.spec.nodeName` → kubelet on that node watches for pods assigned to it, calls CNI to set up networking, calls container runtime to pull image and start containers, runs probes → pod reports Ready → Endpoint controller adds pod IP to Service Endpoints → kube-proxy programs iptables/IPVS rules → traffic can reach the pod.

### "Debug a CrashLoopBackOff."

Structured approach:
1. `kubectl describe pod <name>` — look at Last State, Exit Code, and Events
2. `kubectl logs <pod> --previous` — logs from the most recent crashed container
3. Exit code meanings: 0 = clean exit, 1 = application error, 137 = OOMKilled (SIGKILL from OOM), 143 = graceful SIGTERM, 255 = commonly entrypoint not found

Common causes:
- Exit code 137: increase memory limits or fix memory leak
- Application crash on startup: missing environment variable, can't connect to database (check network policy, Service DNS, secret mounting)
- Entrypoint error: wrong CMD/ENTRYPOINT in Dockerfile or pod spec
- `kubectl exec -it <pod> -- /bin/sh` then manually run the entrypoint to see the error output directly

## Gotchas Candidates Miss

**Probes are not checked during rolling deploys until the pod is Running.** A readiness probe that takes 30 seconds to become healthy means your rolling deploy will appear stuck during that window. Set `initialDelaySeconds` appropriately and monitor `kubectl rollout status`.

**Resource limits on CPU don't kill containers — they throttle them.** A container exceeding `limits.cpu` gets CPU cycles taken away (throttling), not terminated. Only `limits.memory` exceeding causes OOMKill. Many teams mistakenly think CPU limits protect against runaway processes.

**Secrets are base64-encoded, not encrypted, at rest by default.** Without enabling etcd encryption at rest and a secret management solution (External Secrets Operator with AWS Secrets Manager/Vault), Kubernetes Secrets provide no meaningful security over ConfigMaps.

**NodePort services expose a port on EVERY node, including control plane nodes.** In hardened clusters, control plane nodes should not accept traffic on application ports. Use LoadBalancer type or Ingress for production traffic.

**Topology spread constraints only affect scheduling, not rescheduling.** If a node in zone A fails and its pods are rescheduled onto zone B nodes, the spread constraint won't rebalance pods back to zone A when the node recovers. You need to re-deploy (or force pod eviction) to rebalance.

**`kubectl apply` vs. `kubectl replace` vs. `kubectl patch`.** `apply` merges your manifest with the existing object (safe for GitOps). `replace` deletes and recreates (loses annotations, labels not in your manifest). `patch` applies a partial update. Server-side apply (SSA) in newer Kubernetes versions provides conflict detection and proper field management — prefer it for operators and CI/CD pipelines.

**Services route to ALL ready pods, including those in different namespaces — if the selector matches.** Service pod selection is namespace-scoped but label selectors don't prevent a misconfigured service in one namespace from selecting pods labeled identically in... actually services are namespace-scoped and only route to pods in the same namespace. This is a common trick question — the gotcha is that candidates often say cross-namespace routing is possible via Services when it's not.

## Preparation Timeline

**Week 1: Cluster internals and debugging**
- Set up a local cluster with k3d or minikube
- Break things intentionally: apply a deployment with wrong image, misconfigured probes, insufficient resource limits
- Practice the full `kubectl` debugging toolkit: describe, logs, exec, port-forward, events
- Study the scheduling algorithm: deploy pods with affinity rules and watch the scheduler's decisions

**Week 2: Networking, storage, and security**
- Deploy Calico or Cilium locally, write and test NetworkPolicies
- Create PVCs with different StorageClasses, observe dynamic provisioning
- Implement RBAC: create service accounts with minimal permissions, verify with `kubectl auth can-i`
- Configure HPA and load-test to watch it scale

**Week 3: Operators, multi-cluster, and system design**
- Write a simple operator using kubebuilder or controller-runtime
- Study at least one multi-cluster architecture (ArgoCD ApplicationSets or Cluster API)
- Practice the zero-downtime deployment design question out loud
- Review three production incident post-mortems from public SRE blogs

## The Interview Differentiator

The Kubernetes engineers who consistently land senior offers share one habit: they talk about Kubernetes in terms of what it enables, not just what it does. They don't say "HPA scales pods based on CPU" — they say "HPA let us reduce overprovisioning by 40% while maintaining SLO compliance during traffic spikes." Every design decision connects back to a production outcome.

When you debug a CrashLoopBackOff in an interview, narrate your reasoning — what you're looking for and why. Interviewers are evaluating your mental model, not just whether you know the right `kubectl` flags. Show that you've operated these systems under pressure, not just read documentation about them.

The gap between a candidate who passes and one who impresses is always the same: depth of operational experience translated into clear, opinionated answers. Kubernetes is opinionated; the engineers who work well with it are too.
