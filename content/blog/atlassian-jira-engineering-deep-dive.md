# Atlassian Jira Engineering Deep Dive: Issue Tracking at Enterprise Scale

Jira is the unglamorous backbone of software engineering at scale. Over 300,000 organizations use it, many with millions of issues accumulated over a decade of project history. Behind the familiar kanban boards and sprint views is a data model and query engine that has to reconcile extreme flexibility with the performance demands of enterprise teams running JQL queries across tens of millions of rows. Understanding this architecture is directly applicable to interviews at Atlassian and to any system design question involving flexible data models and full-text query engines.

## The Data Model: Flexibility at a Cost

Jira's core abstraction is the **issue** — a unit of work with a type (bug, story, task, epic), a status, an assignee, and a set of fields. The design challenge is that different organizations, teams, and even individual projects need radically different fields. A software team needs a "story points" field; a legal team needs a "contract expiry date" field; an HR team needs a "candidate level" field. Jira's response was a generic custom field system.

The classic implementation of this pattern is the **Entity-Attribute-Value (EAV)** model. Rather than storing each field as a column on the issues table, field values are stored as rows in a separate table:

```sql
-- Core issue table (sparse, only universal fields)
CREATE TABLE issues (
  id          BIGINT PRIMARY KEY,
  project_id  BIGINT NOT NULL,
  issue_type  VARCHAR(64) NOT NULL,
  status      VARCHAR(64) NOT NULL,
  summary     TEXT NOT NULL,
  created_at  TIMESTAMP NOT NULL,
  updated_at  TIMESTAMP NOT NULL
);

-- EAV table for custom field values
CREATE TABLE custom_field_values (
  issue_id    BIGINT NOT NULL REFERENCES issues(id),
  field_id    BIGINT NOT NULL,
  text_value  TEXT,
  number_value DOUBLE PRECISION,
  date_value  DATE,
  PRIMARY KEY (issue_id, field_id)
);
```

This model is extremely flexible — adding a new custom field requires no schema migration, just inserting new rows. But it makes multi-field queries pathologically expensive. A query like "find all bugs with story points > 5 AND assignee = 'alice' AND sprint = 'Sprint 42'" requires joining the `custom_field_values` table multiple times, once per custom field:

```sql
SELECT i.id, i.summary
FROM issues i
JOIN custom_field_values cfv_sp   ON cfv_sp.issue_id = i.id   AND cfv_sp.field_id = 100  -- story points
JOIN custom_field_values cfv_sp2  ON cfv_sp2.issue_id = i.id  AND cfv_sp2.field_id = 101 -- sprint
WHERE i.issue_type = 'Bug'
  AND cfv_sp.number_value > 5
  AND cfv_sp2.text_value = 'Sprint 42';
```

Each join is a full scan of the EAV table filtered by field ID. With millions of issues and hundreds of custom fields, this becomes slow. Atlassian's mitigation strategies include denormalized read models (materialized per-project index tables populated asynchronously), per-field indexes on the EAV table, and eventually a move toward document-oriented storage for issue snapshots in their cloud architecture.

## JQL: Jira Query Language

JQL is Jira's SQL-like query language for issue search. A typical JQL query looks like:

```
project = MYPROJ AND issuetype = Bug AND status != Done
AND created >= -14d ORDER BY priority DESC
```

Executing this against millions of issues requires a proper query compiler, not just string interpolation into SQL. The JQL engine operates in three phases: lexing and parsing, AST construction, and SQL translation with query planning.

**Lexing and parsing** tokenizes the input and builds a parse tree. JQL has a relatively small grammar — identifiers (field names), operators (`=`, `!=`, `>`, `>=`, `in`, `not in`, `is`, `is not`, `~` for text search), literals (strings, numbers, dates), date math expressions like `-14d`, and boolean connectors (`AND`, `OR`, `NOT`).

**AST construction** turns the parse tree into a typed abstract syntax tree where each node knows the field type of its left-hand side:

```python
@dataclass
class FieldCondition:
    field_name: str
    field_type: FieldType  # TEXT, NUMBER, DATE, USER, OPTION, etc.
    operator: Operator
    value: Any

@dataclass
class BooleanNode:
    connector: Literal['AND', 'OR', 'NOT']
    children: list  # FieldCondition or BooleanNode

def parse_jql(tokens) -> BooleanNode:
    # Recursive descent parser
    # Returns typed AST with field metadata resolved
    ...
```

**SQL translation** walks the AST and generates the appropriate SQL joins and WHERE clauses. The key insight is that each field maps to a different join strategy depending on where its data lives:

```python
def translate_condition(cond: FieldCondition, alias_counter) -> tuple[str, list[str]]:
    """Returns (WHERE clause fragment, list of JOIN clauses needed)."""

    if cond.field_name in BUILTIN_FIELDS:
        # Built-in fields map directly to issues table columns
        col = BUILTIN_FIELD_MAP[cond.field_name]
        return f"i.{col} {sql_operator(cond.operator)} %s", []

    # Custom field: requires EAV join
    alias = f"cfv_{alias_counter}"
    field_id = lookup_field_id(cond.field_name)
    value_col = value_column_for_type(cond.field_type)

    join = f"""
        JOIN custom_field_values {alias}
          ON {alias}.issue_id = i.id
         AND {alias}.field_id = {field_id}
    """
    where = f"{alias}.{value_col} {sql_operator(cond.operator)} %s"
    return where, [join]

def jql_to_sql(ast: BooleanNode) -> str:
    joins = []
    where_parts = []
    counter = 0

    for condition in flatten_conditions(ast):
        where_frag, join_frags = translate_condition(condition, counter)
        counter += 1
        joins.extend(join_frags)
        where_parts.append(where_frag)

    boolean_where = reconstruct_boolean(ast, where_parts)

    return f"""
        SELECT DISTINCT i.id, i.summary
        FROM issues i
        {' '.join(joins)}
        WHERE {boolean_where}
        ORDER BY {translate_order_by(ast.order_by)}
    """
```

The text search operator (`~`) routes to a full-text index — in Jira Data Center this is Lucene via Elasticsearch; in Jira Cloud it's a managed search service. Text conditions are evaluated as a pre-filter that returns matching issue IDs, which are then used as an `IN` clause in the main SQL query.

## Next-Gen Board Rendering

Jira's classic board was a server-rendered HTML table. The next-generation board (introduced alongside "next-gen projects," now called "team-managed projects") is a fully client-side React application with a virtualized list renderer.

Virtualization is the key technique for rendering a sprint board with 200 issues without DOM performance degradation. Only the cards visible in the viewport are rendered as actual DOM nodes. Cards scrolled out of view are unmounted; their positions are preserved using placeholder divs with explicit heights:

```tsx
function VirtualizedColumn({ issues, columnHeight }: Props) {
  const [scrollTop, setScrollTop] = useState(0);
  const itemHeight = 88; // px per card

  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(
    startIndex + Math.ceil(columnHeight / itemHeight) + 1,
    issues.length
  );

  const visibleIssues = issues.slice(startIndex, endIndex);
  const topPadding = startIndex * itemHeight;
  const bottomPadding = (issues.length - endIndex) * itemHeight;

  return (
    <div onScroll={e => setScrollTop(e.currentTarget.scrollTop)}>
      <div style={{ height: topPadding }} />
      {visibleIssues.map(issue => <IssueCard key={issue.id} issue={issue} />)}
      <div style={{ height: bottomPadding }} />
    </div>
  );
}
```

Drag-and-drop across columns uses an optimistic update model: the card moves immediately in the local state, and the status change is persisted asynchronously. If the API call fails, the card snaps back with an error notification.

## Cloud Migration: From Data Center to Atlassian Cloud

Jira was originally a self-hosted Java application (Data Center). The cloud migration involved more than just moving the binary to AWS — it required re-architecting for multi-tenancy, horizontal scalability, and the operational model of a SaaS product.

The most significant architectural change was tenant isolation. In Data Center, each customer runs their own database schema. In Atlassian Cloud, multiple customers share infrastructure. Atlassian solved this by adopting a per-tenant logical isolation model: every row in every table carries a `tenant_id` column, enforced at the application layer through a tenant context that's set at request ingress and propagated through the request-scoped data access layer. This prevents cross-tenant data leakage while enabling shared infrastructure.

The JQL engine was re-implemented to route queries through a dedicated search service (based on Elasticsearch) for cloud, bypassing the multi-join SQL approach for large result sets. The search service maintains a near-real-time index of all issue fields, updated via an event stream whenever issues are created or modified. JQL queries are translated to Elasticsearch DSL rather than SQL:

```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "project_key": "MYPROJ" } },
        { "term": { "issue_type": "Bug" } },
        { "range": { "created": { "gte": "now-14d" } } }
      ],
      "must_not": [
        { "term": { "status": "Done" } }
      ]
    }
  },
  "sort": [{ "priority_rank": "desc" }]
}
```

## Interview Implications

Jira's architecture surfaces three canonical interview themes.

**Flexible schema design** — the EAV pattern and its tradeoffs come up in any "design a project management tool" question. Know that EAV buys schema flexibility at the cost of query performance, and that the mitigation is denormalized read models or document storage for query paths that need to filter across many fields simultaneously.

**Query language compilation** — if asked to "add a search feature to Jira," the answer involves a lexer/parser (or using a parser combinator library), an AST with type information, and a translator to the underlying storage query language. The JQL-to-SQL pseudocode above is a concrete starting point.

**Multi-tenant SaaS design** — Atlassian's migration from single-tenant Data Center to multi-tenant Cloud is a textbook case. Row-level tenant isolation, tenant context propagation, and the operational tradeoffs (shared infrastructure cost savings vs. noisy-neighbor risks) are standard system design interview territory.

The broader lesson from Jira's architecture is that enterprise B2B software lives and dies on flexibility — the willingness to store almost anything — and the engineering effort is in building the indexing and query layer on top of that flexibility without sacrificing the performance that enterprise users expect.
