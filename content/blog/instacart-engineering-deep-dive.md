# Instacart Engineering Deep Dive: On-Demand Grocery at Logistics Scale

Instacart operates at the intersection of real-time inventory, dynamic routing, demand prediction, and last-mile logistics — all within a two-hour delivery window that most customers have come to treat as a baseline expectation. The engineering problems Instacart solves are fundamentally different from typical e-commerce. Every order must match available inventory at a specific physical store, be picked by a shopper who is physically present or nearby, and be delivered while items are still fresh. If you are interviewing at Instacart, the interviewers will be evaluating whether you think like a logistics engineer, not just a web developer.

## The Real-Time Inventory Problem No One Fully Solves

Every grocery store changes its inventory continuously. Items sell out, arrive on trucks, get misplaced, go on sale. Instacart does not have direct access to store inventory systems for most of its retail partners. The approach is probabilistic: Instacart estimates item availability based on historical purchase data, shopper feedback from previous orders, and signals from store systems when available.

When a shopper cannot find an item, they mark it as "out of stock" and trigger Instacart's substitution engine. The substitution engine must, in real time, propose alternatives that are available, match the original item's intent, and that the customer is likely to approve. This is a ranking problem with hard constraints:

```python
def rank_substitutions(unavailable_item, catalog, customer_preferences):
    candidates = catalog.find_similar(
        category=unavailable_item.category,
        brand_affinity=customer_preferences.brand_affinity,
        dietary_restrictions=customer_preferences.restrictions
    )

    scored = []
    for candidate in candidates:
        score = (
            0.4 * brand_match_score(unavailable_item, candidate) +
            0.3 * attribute_similarity(unavailable_item, candidate) +
            0.2 * customer_purchase_history_score(candidate, customer_preferences) +
            0.1 * availability_confidence(candidate)
        )
        scored.append((candidate, score))

    return sorted(scored, key=lambda x: x[1], reverse=True)[:5]
```

The substitution approval rate is a key metric Instacart optimizes. A low approval rate means customers rejecting substitutions in the app, which delays the shopper and reduces customer satisfaction. Getting substitution ranking right requires understanding why items are similar beyond simple category matching — a gluten-free shopper wants gluten-free substitutions even if the brand differs.

## Shopper Matching: Real-Time Assignment with Moving Parts

When an order is placed, Instacart's assignment system must identify the best available shopper to fulfill it. "Best" means fastest expected delivery, but the problem is combinatorially complex. Shoppers are at different points in existing orders, at different physical locations, and have different vehicle types that affect what they can carry.

Instacart's batch algorithm is one of their most technically interesting systems. Rather than assigning one order to one shopper, the algorithm allows a shopper to batch multiple orders from nearby stores in a single trip. The value to customers is lower delivery costs; the value to shoppers is higher earnings per hour. The constraint is that batching increases pick time and risks delayed delivery.

The assignment system operates on a continuous horizon. As new orders arrive, the optimizer re-evaluates existing assignments and may re-route shoppers. This is a variant of the vehicle routing problem (VRP), one of the classic NP-hard problems in combinatorial optimization. Instacart does not solve it to optimality — the time budget is measured in hundreds of milliseconds. Instead, they use heuristic approaches: greedy initialization followed by local search with move operators (swapping orders between shoppers, inserting new orders into existing routes).

## Demand Forecasting: Knowing What to Expect Before Customers Order

Instacart's logistics economics depend on predicting when and where orders will arrive. If orders cluster in a small geographic area during a Sunday afternoon, Instacart needs shoppers pre-positioned near those stores. Over-positioning wastes shopper time; under-positioning causes long wait times for customers.

Demand forecasting uses a hierarchical model: national demand patterns, regional variations, store-level patterns, and SKU-level predictions. The features include time of day, day of week, weather, local events (sports games increase beer and snack orders predictably), and proximity to holidays.

The forecasting system outputs a probability distribution over order volumes for each time window and geography. Operations teams use these forecasts to tune incentives that attract more shoppers to high-demand areas before demand spikes. This creates a feedback loop that Instacart must be careful to avoid amplifying: if the model predicts high demand, incentives attract shoppers, which changes the supply picture, which affects fulfillment speed, which affects future demand.

## Search and Discovery: Grocery Has Unique Challenges

Grocery search is harder than most e-commerce search. Users do not always know the exact product they want. A search for "pasta sauce" has thousands of valid results that differ meaningfully on dimensions that matter to specific users: organic, low-sodium, specific brands, jar size. Personalization matters more than in most domains because grocery shopping is highly habitual.

Instacart's search system combines keyword matching with ML ranking. The ranking model uses collaborative filtering signals (what items are frequently purchased together), personal purchase history, and real-time availability at the specific store the customer is shopping from. Showing an unavailable item ranks low not because of relevance but because it will require substitution.

The catalog problem is significant: Instacart must maintain a unified product catalog across thousands of retailers, each with their own item identifiers, descriptions, and images. Natural language processing and computer vision both play roles in deduplication and catalog normalization — matching a Trader Joe's "Organic Whole Milk" to the same product sold differently at Safeway.

## Interview Implications

Instacart interviewers are evaluating your ability to think about operational systems, not just transactional systems. The difference matters: an operational system must make decisions under uncertainty, optimize over time horizons, and degrade gracefully when conditions change.

**System design questions** Instacart asks: design a real-time shopper assignment system, design a grocery search engine with inventory filtering, design a demand forecasting system for delivery logistics. These questions reward candidates who think about edge cases (what happens when a shopper goes offline mid-order?), data freshness (how stale can inventory data be?), and failure modes (what happens when the assignment service is down?).

**ML depth**: Instacart is a heavy ML company. Expect questions about recommender systems, demand forecasting, and operational ML (how do you update a model that affects real-time logistics?). Understanding the difference between batch and online learning matters here.

**Product sense**: Instacart interviews often include product-sense questions for engineering roles. Why does Instacart's two-hour delivery model create different constraints than Amazon Prime Now's one-hour model? What metrics would you use to evaluate substitution quality? Thinking through the business implications of engineering decisions is valued.

Instacart's engineering culture rewards pragmatism. The right answer to many of their problems is "good enough fast" rather than "optimal but slow." If your instinct is to build a perfect optimizer before shipping, Instacart's interview bar will expose that as a liability.
