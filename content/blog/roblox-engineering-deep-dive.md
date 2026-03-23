# Roblox Engineering Deep Dive: Physics at Scale, Luau, and What They're Really Testing

Roblox has a problem that almost no other company faces. On any given day, 70 million users are not just playing games — they are playing millions of simultaneously-running, user-created game instances, each with its own physics simulation, its own networking stack, and its own untrusted code executing in a sandboxed environment. The company that built this infrastructure did not adapt an existing game engine or borrow someone else's networking model. They built most of it from scratch, and the engineering decisions they made along the way are exactly what you will be asked about in an interview.

This guide is for engineers who want to understand Roblox's systems at the level their interviewers operate at — not the API surface, but the architecture underneath.

---

## Real-Time Physics at Millions of Concurrent Instances

Roblox runs its own physics engine called the Roblox Physics Engine (RPE), which is a rigid-body simulation system built on top of a custom constraint solver. The core challenge is not simulating physics for one game — it is running physically accurate simulations for millions of game instances simultaneously, each potentially with hundreds of moving parts, joints, and collision meshes.

The physics pipeline runs at 240 Hz internally, with the visible update rate exposed to developers at 60 Hz. The reason for the higher internal rate is stability: constraint solvers for rigid-body dynamics are numerically stiff, and running iterations faster than the exposed frame rate reduces energy drift and prevents constraint explosions when objects stack.

The most difficult problem in multiplayer physics is determinism. If two clients simulate the same physics independently and arrive at different results, you get desync: a block lands in a different position on each client, and the two players are effectively in different physical realities. Roblox addresses this through a hybrid model. The server is authoritative for all physics state. Clients run a predictive simulation locally for immediate responsiveness, but the server's state is the ground truth. When client and server diverge beyond a threshold, the client snaps to the server state and resimulates.

True deterministic simulation — where clients produce bit-identical results given the same inputs — is extremely difficult across different hardware, operating systems, and floating-point implementations. Roblox does not attempt full determinism for client simulation. Instead, they use the server as the arbiter and reconciliation as the correction mechanism. This is a deliberate engineering trade-off: the cost of occasional visible corrections is lower than the cost of enforcing cross-platform determinism.

For complex mechanical builds — vehicles with many joints, constraint chains — the physics engine uses the Projected Gauss-Seidel (PGS) solver, which iteratively resolves constraint violations. The solver runs multiple substeps per frame and uses sleeping to avoid simulating objects at rest. When objects exceed a velocity threshold, they wake neighboring sleeping bodies, which is a common source of cascade performance problems in user-created games with unstable tower builds.

---

## The Networking Model: Custom UDP at Game Scale

Roblox uses a custom UDP-based networking protocol. TCP is not viable at game scale because its head-of-line blocking causes all data to stall when a single packet is lost — unacceptable for a real-time game with 60-tick physics. Roblox's protocol handles reliability, ordering, and priority at the application layer, above UDP.

The protocol separates data into channels with different delivery guarantees. Physics state updates are sent as unreliable ordered messages — if a packet is lost, the client uses the most recent received state rather than waiting for retransmission. Game events like player deaths or item pickups use reliable ordered delivery. This differentiation means a single lost packet does not halt the entire game state.

Game state synchronization uses a replication model based on the DataModel, which is Roblox's scene graph. Every object in a Roblox game — every part, script, model, and service — exists in this tree. The server holds the authoritative copy. Changes are propagated to clients as differential updates: only modified properties are sent, not the full state. The replication system uses a dirty-bit scheme where modified properties are marked, batched, and transmitted at the end of each network tick.

Client-side prediction works at the player character level. When a user presses a movement key, the client immediately moves the character locally without waiting for server confirmation. The server processes the same input and returns its authoritative result. The client then compares its predicted position to the server's and, if the error exceeds a threshold, smoothly interpolates or snaps to correct it. This reconciliation is the source of the "rubber-banding" effect players occasionally see when latency spikes.

The bandwidth budget per player is tightly managed. Roblox uses a priority queue for replication: objects that are closer to the player, moving faster, or recently interacted with are assigned higher replication priority. Objects outside the streaming radius may not be replicated at all, which is the basis of the Streaming Enabled feature that allows large worlds to load progressively.

---

## Voice Chat at Game Scale: From WebRTC to Server-Side Mixing

Roblox's spatial voice chat, launched in 2021, initially used WebRTC with peer-to-peer connections. The architecture worked at small player counts but had fundamental scalability problems. WebRTC peer-to-peer means each client maintains direct connections to every other client in voice range — an N² connection problem. For a 10-player session, that is manageable. For a 100-player concert or a populated game hub, it falls apart.

Roblox migrated to a server-side mixing architecture using Selective Forwarding Units (SFUs) and custom media servers. In this model, each client sends a single audio stream to a media server. The server handles mixing, spatialization calculations, and fan-out. The client no longer needs to know about every other player in range — it just sends its audio upstream and receives a mixed stream back.

Spatial audio at Roblox is calculated server-side based on the authoritative positions in the physics simulation. The server knows where every player's character is at any given tick. When mixing audio for a recipient, it applies distance attenuation and panning based on the 3D position of each speaker relative to the listener. The key insight is that spatial audio calculations are cheap compared to establishing and maintaining per-peer connections — centralizing the mix trades compute for connection overhead, and the trade-off favors centralization at scale.

The migration required solving lip sync alignment between the physics-authoritative character positions and the audio stream. Audio and game state travel on separate paths with different latency characteristics. Roblox compensates by introducing a configurable audio delay buffer that brings audio latency in line with game state latency, preventing the uncanny valley of a character's mouth moving out of sync with their voice.

---

## Luau: Why Roblox Forked Lua

Roblox has used Lua as its scripting language since the early days. Lua is lightweight, fast to embed, and easy to sandbox. But standard Lua had critical gaps for a platform running millions of user-submitted scripts: no static types, no performance guarantees, and a weak security model.

Luau is Roblox's fork, and it is not a superficial dialect change. The core additions are:

**Gradual typing.** Luau adds an optional static type system with inference. Developers can annotate variables and function signatures with types, and the Luau compiler will flag type errors. Code that omits annotations still runs — the type system is gradual, not mandatory — but typed code gets better error messages and enables tooling like autocomplete in Roblox Studio.

```luau
-- Typed Luau: the compiler can verify this function is called correctly
local function calculateDamage(baseDamage: number, multiplier: number): number
    return baseDamage * multiplier
end

-- Remote event handler with typed parameters
local function onPlayerHit(player: Player, hitPart: BasePart, damage: number)
    local character = player.Character
    if character then
        local humanoid = character:FindFirstChildOfClass("Humanoid")
        if humanoid then
            humanoid.Health -= calculateDamage(damage, 1.5)
        end
    end
end

RemoteEvents.PlayerHit.OnServerEvent:Connect(onPlayerHit)
```

**Performance optimizations.** Luau includes a register-based bytecode compiler, an incremental garbage collector with configurable step sizes, and a JIT-capable backend (Codegen) that compiles hot Luau functions to native machine code at runtime. The GC improvements are critical because Roblox scripts run in sandboxed environments — a script with a poorly tuned GC would cause frame spikes that other scripts and the physics engine would have to absorb.

**Security model.** Every Luau script in Roblox runs in one of three trust levels: the Roblox engine itself (full trust), developer scripts on the server (high trust), and user-facing LocalScripts (sandboxed). The sandbox prevents LocalScripts from accessing the file system, making HTTP requests, or interacting with the OS. The trust model is enforced at the bytecode level, not just at the API surface — sandboxed code cannot access trusted APIs even via reflection or metatable tricks.

The fork required Roblox to maintain their own toolchain: compiler, LSP server, test runner, and documentation. The investment is justified because the language is the primary interface through which millions of developers build on the platform — every friction point in the language directly affects platform adoption.

---

## What Roblox Interviews Actually Test

Roblox engineering interviews are distinct from most other large tech companies because the domain spans two worlds that rarely overlap: game engine systems and web-scale distributed infrastructure. An interviewer for a platform team role might ask you to design a game state synchronization system and then ask how you would scale it to a million concurrent sessions. Both halves of the question matter.

**System design questions at Roblox tend to have physics or game state as the domain.** Expect prompts like: "Design a system to synchronize player positions across a 100-player game instance," or "How would you architect the server-side physics simulation to handle a game with 500 dynamic objects?" The expected answer is not just a distributed systems pattern — it is a distributed systems pattern applied with awareness of game-specific constraints: low latency, ordered delivery, client prediction, and server authority.

The key trade-offs Roblox engineers think about are:
- **Consistency vs. latency.** For physics, eventual consistency with server authority is acceptable. For economy (item trades, purchases), strong consistency is required. Knowing which subsystem requires which model is a signal of genuine depth.
- **Client trust vs. server cost.** Trusting client-reported physics reduces server compute but opens cheating vectors. How much validation the server performs is an active design question at Roblox.
- **Replication fidelity vs. bandwidth.** Not every object needs to replicate at full fidelity to every client. Priority-based and proximity-based replication are techniques Roblox uses that you should be able to discuss and design from scratch.

**Coding interviews test whether you can reason about real-time systems.** You may be asked to implement a simple client prediction and reconciliation loop, or to find a bug in a physics integration step. Understanding how Euler integration and Verlet integration differ in stability will serve you well.

**Engineering values at Roblox.** The company cares deeply about safety — both platform safety (preventing abuse and exploitation) and code safety (the Luau security model reflects this). Engineers who can articulate the security implications of their design decisions alongside the performance implications will stand out. Roblox also has a strong culture of dogfooding: engineers are expected to have played games on the platform, to have used Roblox Studio, and to understand the developer experience they are building for.

The interview process will probe whether you understand that Roblox is not just a game company and not just a cloud infrastructure company. It is a platform that must be both simultaneously — and the unusual engineering decisions they have made are a direct result of navigating that dual identity.

---

## Preparing for the Roblox Interview

The most effective preparation combines three things: deep reading on game networking (Gabriel Gambetta's "Fast-Paced Multiplayer" series is foundational), hands-on time in Roblox Studio writing Luau scripts to understand the developer experience, and practice designing systems where latency and consistency are in direct tension.

Study how the DataModel replication system works. Understand why RemoteEvents and RemoteFunctions exist separately. Know what FilteringEnabled does and why it was made mandatory. These are not trivia questions — they are windows into Roblox's actual security and architecture philosophy, and interviewers who built these systems will ask about the reasoning, not the facts.

If you can explain why Roblox chose a custom UDP protocol over WebSocket, why they moved voice chat from WebRTC to server-side mixing, and what problem Luau's type system actually solves for the platform — you are thinking at the level Roblox interviewers want to see.
