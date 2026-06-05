+++
title = "A Go SDK for the Neo4j Query API"
description = "A Go SDK for Neo4j Query API"
date = "2026-06-05"
tags = ["Claude", "PM","Go","Query API","Neo4j"]
draft = false
+++

I've been rethinking how my MCP server talks to Neo4j for a new use case.

Until now I've been using the full Go driver — the complete, connection-pooling, retry-aware package that's great for working with graphs on a single Neo4j server or cluster. But I'm doing something different: an MCP server that needs to work across many graphs for many users. Think salespeople querying a customer 360 graph while production engineers explore a bill of materials graph, where you can't assume a single Neo4j server or cluster. The driver may not be a good fit here.

So I started looking at the Query API instead.

At a high level, the driver flow looks like this:

1. A request comes in.
2. Create a new driver. This establishes how to reach the database, but doesn't open a connection yet — that's deferred until the first query runs.
3. Use the driver to send the query. This is when the connection actually opens.
4. Process the response.
5. Close the driver.

The Query API over HTTP(S) is simpler:

1. A request comes in.
2. Shape the request into an HTTP body.
3. POST to the Query API.
4. Process the response.

No driver lifecycle. No connection management. Just HTTP (HTTPS if any of the security team are reading this).

One caveat worth being clear about: if all your graphs sit on the same Neo4j server, the Query API probably isn't the right tool. The driver handles that case well and gives you more control. But when each user might be hitting a completely different Neo4j instance — which is exactly my situation — the picture changes. No driver to spin up and tear down per connection, no shared state to manage across unrelated graphs. Just a POST to wherever you need to go.

That was enough to make it worth building something properly. And since I wanted to use the Query API in more than one Go project, it made more sense to build a shared SDK than copy-paste HTTP boilerplate everywhere. So that's what I did.

**Introducing query-go-sdk**

After a few iterations (Claude and I have developed a rhythm — my music teacher would be very surprised, given my catastrophic relationship with the triangle), we built [query-go-sdk](https://github.com/neo4j-contrib/query-go-sdk) — a Go client for the Neo4j Query API that runs Cypher over plain HTTP or HTTPS.

One design decision I'm glad I took: mirroring the transformer pattern from the Go driver. If you've used the driver before, the mental model transfers. And even if you haven't, transformers make working with results much friendlier than parsing raw responses — though you can still do that if you want.

Here's what it looks like. Say you have a struct:

```go
type Actor struct {
    Name  string
    Title string
    Roles []string
}
```

You populate it like this:

```go
actors, err := query.WithTransformer(client.Query, ctx, cypher, nil,
    query.Collect(func(rec *query.Record) (Actor, error) {
        name, _ := rec.GetString("p.name")
        title, _ := rec.GetString("m.title")
        rawRoles, _ := rec.GetList("a.roles")
        roles, _ := query.StringList(rawRoles)
        return Actor{
            Name:  name,
            Title: title,
            Roles: roles,
        }, nil
    }),
)
```

Clean, typed, and familiar if you've spent time with the driver.

The SDK is on [GitHub](https://github.com/neo4j-contrib/query-go-sdk) — have a look, try it out, and let me know if it's useful (or where it falls short).

Next stop: wiring it into the MCP server I'm putting together.
