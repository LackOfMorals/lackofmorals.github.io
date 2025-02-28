---
layout: post
title: "About that Conway Game Of Life"
description: "Figurnig out the graphql"
tags: Neo4j Aura GraphQL
---

# Lets figure out the graphql for Conway

Grab an adult beverage and read this [blog entry](https://medium.com/neo4j/a-cypher-game-of-life-53b5faf04caa/) as I'm going to make reference to it. In that blog post, Christoffer Bergman describes Conways Game of Life and shows how to implement it using Cypher. I'm going to base the schema for my attempt at Conway Game Of Life on his work.

## And you're back in the room

Christoffer uses a Neo4j schema that has a Cell node using a boolean property, alive, to represent the cells state ( true = alive, false = dead ). Additionally, there is a Spatial coordinate used for Cells position in the grid. Finally, Cells are related to each other using NEIGHBOUR_OF. I am going to represent this in GraphQL as is apart from an adjustment so that a Cells co-ordinates use x and y properties - it makes GraphQL operations somewhat easier. I'll also add in an ID. My draft GraphQL schema looks like this

```java
type Cell @node {
 cellsConnected: [Cell!]! @relationship(type: "NEIGHBOUR_OF", direction: IN)
 connectedCells: [Cell!]! @relationship(type: "NEIGHBOUR_OF", direction: OUT)
 alive: Boolean!
 id: String!
 x: BigInt!
 y: BigInt!
}
```

Rather than write the GraphQL schema directly, you can create a few Cells using Cypher, link them together and then use the Introspector tool. To this, execute these Cypher statements

Create a few cells

```Text
UNWIND range(1,2) as x
    UNWIND range (1,2) as y
    CREATE (c:Cell {id:x + '_' + y, x: x, y: y, alive: False})
RETURN COUNT(c)
```

Join the cells together

```Text
MATCH(ac:Cell)
UNWIND ac AS c
CALL (c) {
    MATCH (c2:Cell)
    WHERE c2.x-1<=c.x<=c2.x+1
    AND c2.y-1<=c.y<=c2.y+1
    AND c.id <> c2.id
    MERGE (c)-[:NEIGHBOUR_OF]->(c2)
}
```

Then run the Introspect tool, following the instructions here - Using In
