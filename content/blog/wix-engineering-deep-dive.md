# Wix Engineering Deep Dive: Website Creation at 250 Million Users

Wix has built one of the most technically underestimated platforms in web development. Two hundred and fifty million registered users, the majority of them non-technical business owners and creators, use Wix to build production websites. The engineering challenge behind that simplicity is immense: a WYSIWYG editor that produces professional-grade websites, a rendering engine that delivers those sites at CDN speed globally, and a platform that supports everything from a local restaurant's landing page to a full e-commerce operation with inventory management and payments. If you think of Wix as a visual drag-and-drop toy, the engineering team will correct that impression in the first round of your interview.

## The Editor: Rendering Engine and DOM Management at Scale

The Wix Editor is one of the most complex web applications ever built. It renders a live preview of a website while simultaneously managing the state of a WYSIWYG editing session. Every drag, resize, style change, and content update must be reflected instantly without a page refresh. The editor maintains a document model — a structured representation of all components, their layouts, their properties — and translates that model into rendered HTML in real time.

Wix built a custom component rendering framework called Thunderbolt, which replaced their earlier React-based rendering approach. Thunderbolt uses a headless rendering model: the server renders the initial HTML (SSR), and the client hydrates only the interactive parts. For published sites, Thunderbolt pre-generates HTML at deploy time, resulting in fast initial paint without waiting for JavaScript execution.

The editor itself manages a virtual document that can have thousands of components. Wix invested heavily in structural sharing and immutable data structures to handle editor state changes efficiently:

```typescript
interface ComponentModel {
  id: string;
  type: string;
  layout: LayoutProperties;
  style: StyleProperties;
  data: Record<string, unknown>;
  children: string[]; // IDs of child components
}

interface DocumentModel {
  components: Map<string, ComponentModel>;
  pageOrder: string[];
  version: number;
}

function updateComponent(
  doc: DocumentModel,
  componentId: string,
  updates: Partial<ComponentModel>
): DocumentModel {
  // Structural sharing: only create new objects for changed nodes
  return {
    ...doc,
    components: new Map(doc.components).set(componentId, {
      ...doc.components.get(componentId)!,
      ...updates,
    }),
    version: doc.version + 1,
  };
}
```

Every update produces a new document version. This enables undo/redo as a stack of document snapshots, collaborative editing as a series of document patches, and auto-save as periodic snapshots sent to the server.

## Wix's Micro-Frontend Architecture: 200+ Teams, One Editor

Wix has over 200 engineering teams. The editor is not a monolithic application — it is a platform that hosts dozens of first-party and third-party applications (panels, tools, widgets) that integrate into the editor surface. The technical challenge is identical to what companies like Shopify face with their app stores: how do you let external code run inside your application without allowing it to break the host?

Wix's answer is a micro-frontend architecture built on top of their Workers Platform (similar in concept to Cloudflare Workers). Each editor app runs in an isolated context with a structured API surface. The editor exposes a platform SDK; apps interact with the document model only through this SDK, never through direct DOM manipulation.

This isolation model has performance implications. Cross-frame communication is slower than in-process calls. Wix built a batching layer that queues SDK calls and executes them in bulk to minimize the overhead of the isolation boundary.

## Velo: Bringing Code to a Visual Platform

Velo is Wix's developer platform: a JavaScript runtime that allows developers to add custom backend logic and dynamic data to Wix sites without leaving the Wix environment. A user can write a Node.js function in the browser-based IDE, connect it to a Wix-hosted database, and deploy it — without ever touching a terminal.

The underlying infrastructure is serverless. Velo backend functions run as isolated function instances on Wix's cloud infrastructure. The cold start problem is significant here: when a site receives its first visitor after a period of inactivity, the backend function must boot before it can respond. Wix optimizes cold starts through function pre-warming based on traffic prediction — sites with consistent traffic patterns have their function instances kept warm.

Wix's database platform (Wix Data) provides a document store accessible both from Velo backend code and from front-end code via a permissions model. The permissions model is critical for security: a malicious front-end script cannot read data that the backend has designated as server-only.

## Global Site Delivery: CDN Architecture at Scale

Published Wix sites must load fast globally. A restaurant in São Paulo, a photographer in Tokyo, a lawyer in Toronto — all expect their Wix site to load in under two seconds anywhere in the world.

Wix operates a global CDN with edge nodes that serve static assets (images, scripts, CSS) from the nearest point of presence. For HTML, Wix uses a split strategy: the HTML shell is served from the CDN edge, while dynamic data (database queries, personalization) is fetched from origin servers and merged on the client.

Image optimization is a major part of their CDN strategy. Wix automatically converts uploaded images to WebP or AVIF depending on browser support, resizes images to the exact dimensions needed for each display context, and serves them over HTTP/2. Their image processing pipeline handles billions of image transformations per day.

## Interview Implications

Wix interviews are product-engineering-heavy. The company cares about building things users actually use, which means interviewers will probe your product judgment alongside your technical depth.

**System design questions** Wix asks: design a collaborative document editor (directly relevant to their core product), design a global CDN for user-generated websites, design a serverless function platform with cold-start optimization. These questions reward candidates who understand rendering pipelines, caching strategies, and isolation models.

**Frontend depth**: Wix is one of the few companies where deep browser API knowledge is genuinely valued. Understanding the DOM, the event loop, requestAnimationFrame, Web Workers, and browser rendering pipelines matters for the editor and Thunderbolt work.

**Micro-frontend architecture**: If you are interviewing for platform teams, expect questions about module federation, cross-origin isolation, and performance trade-offs of different micro-frontend approaches.

Wix's engineering culture is product-driven and pragmatic. They ship features used by hundreds of millions of people. If your instinct is to build the most elegant solution rather than the most useful one, that tension will come up.
