# Miro Engineering Deep Dive: Collaborative Whiteboard at Infinite Canvas Scale

Miro's infinite canvas sounds like a simple idea — a whiteboard with no edges. In practice, building a system where fifty people simultaneously drag sticky notes across a board with millions of objects, with sub-100ms latency and no conflicts, is one of the harder real-time engineering problems in the product space. If you're interviewing at Miro or preparing for a system design question about collaborative tools, understanding how this actually works is worth the investment.

## The Infinite Canvas Problem: Viewport Rendering

The first challenge is rendering. A Miro board can contain hundreds of thousands of objects — shapes, frames, images, connectors, sticky notes, mind map nodes. Rendering all of them simultaneously would saturate even a high-end GPU. The solution is viewport culling: only objects visible in the current viewport are rendered.

Miro's canvas is defined in a world coordinate system. Every object has a bounding box in world coordinates `(x, y, width, height)`. The viewport is a rectangle in world space defined by the current pan offset and zoom level. Before each render frame, a spatial query filters the object set:

```javascript
function getVisibleObjects(objects, viewport) {
  return objects.filter(obj => {
    return (
      obj.x < viewport.right &&
      obj.x + obj.width > viewport.left &&
      obj.y < viewport.bottom &&
      obj.y + obj.height > viewport.top
    );
  });
}
```

A brute-force linear scan over 100,000 objects before every animation frame is too slow. Miro uses a spatial index — typically an R-tree or a simpler quad-tree — to make viewport queries O(log n + k) where k is the number of returned objects.

**Level-of-detail (LOD) rendering** adds another layer. When zoomed out far enough, individual text labels on sticky notes are smaller than a pixel. Rendering the full font layout for invisible text wastes CPU cycles. Miro switches objects to simplified representations — a solid rectangle in their brand color — below a zoom threshold. This is the same technique used in geographic mapping tools like Google Maps, which swaps road labels for colored lines at lower zoom levels.

```javascript
const LOD_TEXT_THRESHOLD = 0.4; // zoom level below which text is hidden

function renderStickyNote(ctx, note, zoom) {
  ctx.fillStyle = note.color;
  ctx.fillRect(note.x, note.y, note.width, note.height);

  if (zoom > LOD_TEXT_THRESHOLD) {
    ctx.fillStyle = '#1a1a2e';
    ctx.font = `${14 * zoom}px Inter`;
    ctx.fillText(note.text, note.x + 8, note.y + 20);
  }
}
```

## Real-Time Collaboration: Operational Transforms for Cursor and Element Position

When fifty users are on the same board, every drag, resize, and text edit needs to propagate to all participants without conflicts. Miro uses a variant of Operational Transforms (OT) — the same family of algorithms that powers Google Docs — adapted for spatial operations rather than text.

The fundamental problem OT solves: two users apply operations concurrently. When both operations arrive at the server, they may conflict. OT defines a `transform` function that takes two concurrent operations and produces a transformed version of one that can be applied after the other while preserving intent.

For element position, the operation type is a move:

```typescript
interface MoveOperation {
  type: 'MOVE';
  widgetId: string;
  dx: number;  // delta x in world coordinates
  dy: number;  // delta y in world coordinates
  revision: number;  // board state revision this op was based on
}

function transformMove(op: MoveOperation, concurrent: MoveOperation): MoveOperation {
  // If both ops move the same widget, compose them
  if (op.widgetId === concurrent.widgetId) {
    return {
      ...op,
      dx: op.dx,  // last writer wins for position (or merge additively)
      dy: op.dy,
    };
  }
  // Different widgets: ops are independent, no transform needed
  return op;
}
```

Cursor positions are handled separately from widget state because they're ephemeral — you don't need cursor positions in the persistent board snapshot. Miro broadcasts cursor moves via a separate low-latency channel (typically WebSocket with a dedicated cursor channel) and applies them client-side without going through OT. This keeps cursor updates at 60fps without saturating the OT pipeline.

The server maintains a revision counter. Each operation includes the revision it was based on. If an operation arrives with revision N but the server is at revision M > N, the server transforms the operation through all operations from N to M before applying it. This is the classic OT server architecture.

## The Widget System: Modeling Heterogeneous Object Types

Miro's canvas contains fundamentally different object types — sticky notes, shapes, connectors (arrows with endpoints that can snap to other objects), frames, images, text blocks, and embed widgets. Each has different properties, different rendering logic, and different interaction models.

The widget system uses a polymorphic data model with a shared base:

```typescript
interface BaseWidget {
  id: string;
  type: WidgetType;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  createdAt: number;
  updatedAt: number;
}

interface StickyNote extends BaseWidget {
  type: 'STICKY_NOTE';
  text: string;
  color: StickyColor;
  textColor: string;
}

interface Connector extends BaseWidget {
  type: 'CONNECTOR';
  startWidgetId: string | null;   // null if floating endpoint
  endWidgetId: string | null;
  startPosition: { x: number; y: number };
  endPosition: { x: number; y: number };
  lineStyle: 'straight' | 'curved' | 'elbowed';
  startArrow: ArrowStyle;
  endArrow: ArrowStyle;
}
```

Connectors introduce a dependency problem: when a widget moves, all connectors attached to it must update their endpoint positions. Miro maintains an index from widget ID to a list of attached connector IDs. On every move operation, the server fans out position updates to dependent connectors. This is a local constraint propagation step that must be fast because it happens synchronously during OT application.

## Large Board Performance Optimization: Spatial Indexing

Boards in enterprise Miro accounts can contain millions of objects — entire product roadmaps, org charts, or research synthesis boards accumulated over years. The R-tree spatial index is the core data structure that makes queries performant.

An R-tree organizes spatial objects into a tree of bounding rectangles. Leaf nodes contain the actual objects; internal nodes contain minimum bounding rectangles (MBRs) of their children. A viewport query traverses the tree, pruning branches whose MBR doesn't intersect the query rectangle:

```python
class RTreeNode:
    def __init__(self):
        self.mbr = None          # minimum bounding rectangle
        self.children = []       # child nodes or leaf entries
        self.is_leaf = False

def query_viewport(node, viewport):
    """Return all objects overlapping the viewport."""
    if not intersects(node.mbr, viewport):
        return []
    if node.is_leaf:
        return [obj for obj in node.children if intersects(obj.bounds, viewport)]
    results = []
    for child in node.children:
        results.extend(query_viewport(child, viewport))
    return results
```

For large boards, Miro also uses progressive loading: the full board state is not downloaded on open. Instead, the client downloads only the objects in and near the current viewport, then prefetches adjacent regions as the user pans. The server partitions the board into spatial tiles and serves tile manifests. This is architecturally similar to how map tile servers work — the Miro engineering team has cited Google Maps as an explicit inspiration.

## Interview Implications

Miro-style questions frequently appear in design interviews at collaborative software companies. Three patterns are worth knowing deeply.

**Real-time conflict resolution** — understand OT versus CRDTs. OT requires a central server to sequence operations; CRDTs (Conflict-free Replicated Data Types) allow peer-to-peer merging with no coordination. Figma uses CRDTs for its collaborative model; Miro uses server-side OT. The tradeoff: CRDTs are more complex to implement correctly but tolerate network partitions better.

**Spatial indexing** — when asked "how would you support 1 million objects on a canvas," the answer involves spatial indexes (R-tree, quad-tree, k-d tree), viewport culling, and level-of-detail rendering. Be able to explain the query complexity of each.

**Dependency graphs** — connectors that snap to widgets create a directed dependency graph. When a widget moves, its connector endpoints must update. This is a topological propagation problem. In interviews, frame it as: "we maintain an adjacency list from each widget to its dependent connectors, and on any position update we propagate changes in O(d) where d is the out-degree."

The deeper lesson from Miro's architecture is that collaborative spatial applications converge on the same set of solutions as geospatial mapping: spatial indexes, viewport-based progressive loading, and LOD rendering. If you understand how a map tile server works, you understand most of Miro's rendering pipeline.
