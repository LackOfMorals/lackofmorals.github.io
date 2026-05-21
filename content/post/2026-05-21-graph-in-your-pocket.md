+++
title = "Graph in our pocket"
description = "graphlite lets you carry a fully queryable property graph, work with it offline then merge changes back to Neo4j when you reconnect."
date = "2026-05-21"
tags = ["Claude", "PM","Go","graphlite"]
draft = false
+++


# Graph in your pocket

My day job is being a Product Manager. I spend time thinking about products and on the odd occasion I get to write code that helps explore those thoughts.  It was during one of those moments that I got annoyed.

I've been learning about Go Interfaces and wanted to write code to land my understanding before carrying on with the book. The Go Programming Language, if you're curious — worth it

Now as it happens I'm on a train at this point.  I've got 90 minutes - if the train arrives on time - to fill.  If you've ever been on a train, then you'll understand that internet access is patchy at best. This rules out using Neo4j cloud service , Aura, and using Docker to grab the container variant.

Now I'm perturbed trending towards annoyance - not in the direction of the train company with their sub-optimal connectivity - but at ceremony you need undertake just to try something.

I was left with reading more of The Go Programming Language book. It's good but not as satisfying as seeing it work in code. 

What if you could have an embedded version of Neo4j ( for those history buffs, that's how Neo4j first got released ) ? Something lightweight with a surface that looks like the Neo4j Go Driver? Give it local storage - SQLite to keep with the lightweight approach.  Allow me to import data from Neo4j so I can try out Cypher.

Claude joined the chat and off we went. 

That conversation turned into [graphlite](https://github.com/LackOfMorals/graphlite).

The README covers the dev and test use case well — the one that started all this. Now I can pull the package into my Go whenever its needed. No setup required. But once graphlite was working, I closed the laptop and went for run to decompress. As I'm increasingly middle aged, you, dear reader, will be relieved to know that my running wardrobe is free of lycra. Whilst doing my best to avoid a heart attack, my mind wandered as it often does ( See earlier middle aged statement ) and embarked on other potential applications for graphlite; where else could this be useful? 

Afterall, Graphs are good at relationships. Relationships don't pause when the network drops.

I can't believe I wrote that. Please accept my apologies. 

---

## The use cases worth building

The applications which could benefit from graphlite share a shape: the underlying data is a graph, and the person using it needs to query across relationships, not just look up a record. Being able to access the relevant part of the graph 'offline' avoids blocking real work.  This is the sweet spot for graphlite.

### Fraud and financial crime investigation

Fraud is the most graph-native problem in enterprise software. Financial crime lives in the connections: who owns which company, which director appeared in three dissolved entities, which addresses are used to register large numbers of companies   Relationship data is a strong signal to indicate the presence of bad actors.

An investigator working a case carries that entire relationship network into the field. They visit subjects, interview associates, and discover connections that aren't in the central graph yet. The existing approach (paper notes, disconnected CRM fields, a VPN-dependent laptop) loses that context the moment the interview ends.

With graphlite, the investigator pulls the relevant subgraph before heading out. On the device, they run path queries across local data exactly as they would against Neo4j:

```go
// Find high-risk entities within 3 hops of the subject — no network required
result, err := neo4j.ExecuteQuery(ctx, localDriver,
    `MATCH (s:Subject {id: $id})-[:ASSOCIATED_WITH|DIRECTS*1..3]-(e:Entity)
     WHERE e.riskScore > 0.7
     RETURN e.name, e.type, e.riskScore
     ORDER BY e.riskScore DESC`,
    map[string]any{"id": "SUB-4419"},
    neo4j.EagerResultTransformer,
)
```

New connections discovered during the interview get written into the local graph immediately:

```go
_, err = session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (any, error) {
    return tx.Run(ctx,
        `MATCH (s:Subject {id: $subjectID}), (c:Company {regNumber: $companyReg})
         MERGE (s)-[r:LINKED_TO]->(c)
         ON CREATE SET r.discoveredAt = $now, r.source = "field_interview"`,
        map[string]any{
            "subjectID":  "SUB-4419",
            "companyReg": "12345678",
            "now":        time.Now().Unix(),
        },
    )
})
```

Back at base, those edges merge into the central investigation graph. The whole team sees the updated picture.

### Field service: infrastructure inspection

An engineer inspects substations across a rural network. The asset data is a graph: equipment nodes, their maintenance histories, and relationships to connected downstream assets. A fault on one transformer affects three distribution points, but that dependency is only visible if you can traverse the graph.

Out in the field, the engineer pulls the subgraph for today's sites, records inspection outcomes, flags faults, and queries which connected assets to prioritise for follow-up. All of that runs locally without a data connection.

The graph structure lets a fault on one asset automatically propagate a "flag for review" across connected neighbours. On paper, that's three separate steps.

---

## The code behind the pattern

### One line separates online from offline

The thing that made graphlite worth building — and this is what I kept coming back to when working with Claude on it — is that your application code doesn't need to know which driver it's talking to. You write a constructor that returns either a live Neo4j driver or a local graphlite driver depending on the environment:

```go
func newDriver(ctx context.Context, localPath string) (neo4j.DriverWithContext, error) {
    if uri := os.Getenv("NEO4J_URI"); uri != "" {
        auth := neo4j.BasicAuth(os.Getenv("NEO4J_USER"), os.Getenv("NEO4J_PASS"), "")
        return neo4j.NewDriverWithContext(uri, auth)
    }
    return graphlite.NewDriver(localPath, nil) // offline — SQLite-backed graph
}
```

Set `NEO4J_URI` in production. Leave it unset on the device. Nothing else moves.

### Seeding the local store

Before a field worker leaves connectivity, `CopyFrom` pulls the current state from Neo4j into a local graphlite file. When you need a subset rather than the full database, seed from a targeted Cypher query and import the result:

```go
remote, _ := neo4j.NewDriverWithContext("neo4j+s://xxx.databases.neo4j.io", auth)
local, _  := graphlite.Open("/secure/case-1042.db")

// Seed the full remote graph into the local store
if err := local.CopyFrom(ctx, remote); err != nil {
    log.Fatal(err)
}

// Take a consistent checkpoint before heading out
if err := local.Snapshot("/secure/case-1042-checkpoint.db"); err != nil {
    log.Fatal(err)
}
```

`Snapshot` uses SQLite's `VACUUM INTO`: an atomic copy of the database at that moment. It's a safety checkpoint before field work begins, and a rollback point if the merge-back needs to be re-run.

### Merging changes back

When connectivity returns, `CopyTo` pushes the local graph to the remote store. If the same node was modified in both places, write the sync with MERGE directly. That's where conflict resolution lives:

```go
_, err = session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (any, error) {
    return tx.Run(ctx,
        `UNWIND $links AS link
         MERGE (s:Subject {id: link.subjectID})
         MERGE (c:Company {regNumber: link.companyReg})
         MERGE (s)-[r:LINKED_TO]->(c)
         ON MATCH SET r += link.props
         ON CREATE SET r = link.props`,
        map[string]any{"links": newLinks},
    )
})
```

`ON MATCH SET` updates an existing relationship if it's already there. `ON CREATE SET` sets properties only on new ones. When multiple investigators sync back on the same day, this is what keeps the central graph consistent.

---

## When the graph earns its place

graphlite earns its place when the field data has relationship structure worth querying. If the question is "what does this entity connect to, three hops out?", that's a graph query. If it's "show me this record's properties", a flat table does the job.

For a delivery receipt or a meter reading, flat SQLite is the right tool. The graph earns its place when a fraud investigator runs a path query three hops deep or when an engineer needs to propagate a fault flag across connected assets.

Carry the shape of your data into the field. Relationships and all.

---

## Get started

graphlite requires Go 1.24+, no CGO, and runs on Linux, macOS, and Windows.

```bash
go get github.com/LackOfMorals/graphlite
```

The [README](https://github.com/LackOfMorals/graphlite) covers the full API including `CopyFrom`, `CopyTo`, `Snapshot`, and the `DriverCompat` interface. graphlite passes 235/235 openCypher TCK scenarios — any Cypher that works in Neo4j works offline.

If you build something with it, I'd like to hear what you built it for. Bugs and feature ideas welcome too.
