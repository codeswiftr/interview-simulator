# Epic Games Engineering Deep Dive: Unreal Engine, Fortnite at Scale, and What It Takes to Join the Team

Epic Games sits at one of the most technically demanding intersections in software engineering: real-time 3D rendering, distributed systems at massive scale, and a cross-platform SDK serving hundreds of millions of users. Interviewing here means demonstrating fluency not just in algorithms, but in systems that push hardware to its physical limits. This guide breaks down the architecture decisions that define Epic's engineering culture.

## Unreal Engine Architecture: Actors, Components, and the Game Loop

Unreal Engine's object model is built around the **Actor/Component** pattern, which is conceptually similar to an Entity-Component System (ECS) but diverges in important ways. In Unreal, an `AActor` is a base C++ class that can exist in the world — a player character, a weapon, a trigger volume. Actors are composed from `UActorComponent` subclasses, which encapsulate discrete behaviors. A `USkeletalMeshComponent` renders an animated character mesh; a `UCharacterMovementComponent` handles physics-based locomotion; a `UCameraComponent` defines the player's viewpoint.

This is not a pure data-oriented ECS. Actors have identity, ownership, and network replication semantics built in. The distinction matters architecturally: Unreal's model trades some cache-locality for richer object relationships and a deep integration with the engine's replication system.

The engine's execution is driven by the **tick system**. Every frame, Unreal calls `UWorld::Tick()`, which dispatches ticks to registered actors and components in dependency order. Components can specify tick prerequisites — for example, a foot inverse-kinematics component must tick after the skeletal mesh has been posed for that frame. The tick groups (`TG_PrePhysics`, `TG_DuringPhysics`, `TG_PostPhysics`, `TG_PostUpdateWork`) define execution phases around the physics simulation step.

```cpp
// Simplified actor/component lifecycle showing tick registration
AMyCharacter::AMyCharacter()
{
    // Components declared here are registered automatically
    MeshComponent = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
    MovementComponent = CreateDefaultSubobject<UCharacterMovementComponent>(TEXT("Movement"));

    // Enable tick for this actor
    PrimaryActorTick.bCanEverTick = true;

    // This component must tick after physics resolves
    MeshComponent->PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void AMyCharacter::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    // Per-frame game logic here — runs every world tick
    UpdateAbilityState(DeltaTime);
}

// GameMode controls session rules; GameState replicates session state to all clients
void AMyGameMode::PostLogin(APlayerController* NewPlayer)
{
    Super::PostLogin(NewPlayer);
    // GameMode runs server-only; GameState is replicated
    Cast<AMyGameState>(GameState)->RegisterPlayer(NewPlayer);
}
```

**GameMode** and **GameState** are architectural cornerstones for multiplayer. `AGameMode` is server-authoritative and never replicated — it holds the rules of the match (win conditions, player spawn logic). `AGameState` is replicated to all clients and holds observable match state (current score, time remaining, player list). This clean separation between authority and visibility is a pattern that comes up directly in system design interviews.

## Rendering: Nanite and Lumen

Unreal Engine 5 introduced two rendering systems that represent genuine architectural breakthroughs.

**Nanite** is a virtualized geometry system. Traditional 3D rendering requires artists to manually author multiple levels of detail (LODs) and the engine selects among them based on screen-space coverage. Nanite eliminates this: meshes are stored as hierarchical clusters of triangles, and at render time, Nanite rasterizes only the clusters that correspond to the visible screen pixels — a process called cluster culling. This means a scene can contain billions of source triangles, yet the GPU only processes the subset that contributes to the final frame. The system uses a software rasterizer for small triangles (which are inefficient in hardware rasterization) and hardware rasterization for larger ones, switching dynamically per cluster. For engineers: Nanite is a compute-heavy, indirect-draw pipeline that relies heavily on GPU-driven rendering — the CPU submits a single indirect draw call and the GPU determines what actually gets rendered.

**Lumen** is a fully dynamic global illumination system. Rather than precomputing light bounces (as lightmaps do), Lumen traces rays in screen space and world space using a multi-level scene representation: surface cache, mesh distance fields, and screen-space radiance caches. Hardware ray tracing is used where available (via DXR/Vulkan RT); on hardware without RT support, Lumen falls back to software ray marching against signed distance fields. The architectural insight is that Lumen decomposes the GI problem into a hierarchy of approximations — fast and low-quality for nearby geometry, slower and cached for distant indirect lighting — and blends between them seamlessly.

## Fortnite at Scale: Battle Royale Server Architecture

Fortnite has exceeded 350 million registered accounts with peak concurrent player counts in the tens of millions. Battle royale is a particularly demanding server workload: a single match server must track the state of 100 players simultaneously and broadcast authoritative world state at approximately 60Hz. Every player's position, velocity, rotation, health, inventory, and zone damage must be computed and distributed within a 16ms window.

Epic runs Fortnite's dedicated servers on their own cloud infrastructure (built on top of cloud providers with custom orchestration). The matchmaking flow for a battle royale session involves several layers:

1. **Session service**: players request a match, the matchmaking service groups them by skill rating, region, and ping profile into a lobby of ~100 players.
2. **Server allocation**: a game server is allocated from a warm pool (servers pre-loaded with the map, waiting for assignment). Cold-start time for a Fortnite server is too slow to be on the critical path.
3. **Session handoff**: the matchmaking service hands off the 100 players' session tokens to the dedicated server; clients connect directly via UDP.
4. **Replication**: inside the server, Unreal's network relevancy system determines which actors are relevant to which clients. Actors outside a player's network relevancy radius are not replicated to that client, which is essential at 100 players — you cannot send every player's state to every other player without saturating bandwidth.

The replication system uses property-level delta compression and prioritization. High-priority actors (your own character, nearby enemies) get replicated every tick; low-priority actors (distant players, background AI) are replicated less frequently. The server tracks which properties have changed per actor and only sends deltas — an RPC-over-UDP model with reliability selectively applied per message type.

## Epic Online Services: Platform SDK at 700M Accounts

Epic Online Services (EOS) is Epic's cross-platform gaming services SDK — a direct competitor to Steam, PlayStation Network, and Xbox Live. It provides friends lists, achievements, entitlements, matchmaking, anti-cheat (Easy Anti-Cheat), analytics, and voice communication, all accessible through a single C SDK that wraps platform-specific backends.

The technical architecture centers on a **callback-based async model**: all EOS API calls are non-blocking. You call `EOS_Friends_QueryFriendsList()`, pass a callback function pointer and a user data pointer, and the SDK dispatches the result asynchronously on a background thread. This pattern is consistent across the entire surface area of the SDK and reflects the constraint that any of these operations may involve multiple backend round-trips across datacenters.

The account system (Epic Account Services vs. EOS Game Services) is a studied separation of concerns: Epic Account Services requires an Epic Games account and provides cross-game social features; EOS Game Services requires only a product user ID and provides in-game features without a full account. Designing a system that cleanly separates platform identity from game identity — while still allowing them to link — is a non-trivial distributed systems problem.

## Chaos Physics: Building a First-Party Physics Engine

Epic replaced NVIDIA's PhysX with their own **Chaos** physics engine starting in Unreal Engine 5. The reasons were multifaceted: PhysX licensing uncertainty following NVIDIA's acquisition of Mellanox, performance ceilings for large-scale destruction, and deep integration requirements (PhysX ran as a black box; Chaos runs on Unreal's task graph and shares memory management with the engine).

Chaos uses a **Position Based Dynamics / XPBD (Extended Position Based Dynamics)** approach for soft bodies and cloth, and a constraint-based rigid body solver for collisions and joints. Constraint-based solvers express interactions as constraints that must be satisfied — contact constraints prevent interpenetration, joint constraints limit relative motion of connected bodies — and solve them iteratively per-frame. This is more stable than impulse-based methods at low iteration counts, which matters when you have thousands of physics bodies active simultaneously.

**Chaos Fracture** (formerly Chaos Destruction) handles real-time geometry breaking. Meshes are pre-fractured into a hierarchical cluster tree at authoring time. At runtime, when sufficient force is applied to a cluster, it breaks apart into its children — which can themselves break recursively. Each leaf fragment becomes an active rigid body. The challenge is managing the combinatorial explosion of active bodies during large destruction events; Chaos uses sleeping, level-of-detail physics, and field-based effects (radial force fields, strain fields) to drive destruction without simulating every fragment individually.

## Interview Implications: What Epic Is Actually Looking For

Epic's engineering culture is deeply specialized. Teams do not generalize across the company the way they might at a cloud provider — Unreal Engine, Fortnite, and EOS are each their own deeply expert domains. In interviews, demonstrating genuine understanding of one of these domains carries more weight than broad knowledge.

**System design questions at Epic tend to focus on:**
- Design a matchmaking system for a battle royale game with 100-player sessions (consider: latency, fairness, server allocation, connection handoff)
- Design the replication layer for a multiplayer game server (consider: delta compression, relevancy, bandwidth budgets, clock synchronization)
- Design a real-time physics simulation that supports destruction of thousands of objects (consider: sleeping bodies, LOD physics, broad phase collision detection)

**What distinguishes strong candidates:**
- C++ fluency at a level beyond syntax — move semantics, memory layout, cache performance, template metaprogramming patterns common in game engine code
- Understanding of real-time constraints: hard frame budgets (16ms at 60fps), the cost of context switches, why lock-free data structures matter in game engine tick loops
- Familiarity with GPU programming concepts — even if not a graphics engineer, understanding why Nanite uses indirect draws or why Lumen uses a hierarchical representation signals genuine engine-level thinking
- Live service awareness: Fortnite ships updates to 350M accounts with no downtime; understanding hot patch mechanisms, feature flags, and server-side rollout strategies is expected on the platform side

Epic rarely hires generalists into technical roles. The expectation is deep competency in at least one of their three major domains, paired with the systems-level thinking to reason about the interactions between them.
