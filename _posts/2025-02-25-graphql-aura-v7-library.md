---
layout: post
title: "Generate the schema for GraphQL for Neo4j AuraDB beta"
description: "Using introspector with v7 library"
tags: Neo4j Aura GraphQL
---

# Generate the schema for GraphQL for Neo4j AuraDB beta

In our roadmap [blog](https://neo4j.com/blog/developer/neo4j-graphql-library-roadmap/) we outlined what to expect in GraphQL releases across 2025. One of those items is v7 of the library that introduces several changes that will massively reduce schema size to improve server startup and query time.

This also means that the v7 Libary schema is different. For example, it is required to use the @node directive to any type they wish to be considered a "node" in their database for which we should generate graphql queries and mutations

Here's the schema that v7 library expects for the sample Movies Graph

```Text
type ActedInProperties @relationshipProperties {
 roles: [String]!
}

type Movie @node {
 peopleActedIn: [Person!]! @relationship(type: "ACTED_IN", direction: IN, properties: "ActedInProperties")
 peopleDirected: [Person!]! @relationship(type: "DIRECTED", direction: IN)
 peopleProduced: [Person!]! @relationship(type: "PRODUCED", direction: IN)
 peopleReviewed: [Person!]! @relationship(type: "REVIEWED", direction: IN, properties: "ReviewedProperties")
 peopleWrote: [Person!]! @relationship(type: "WROTE", direction: IN)
 released: BigInt!
 tagline: String
 title: String!
}

type Person @node {
 actedInMovies: [Movie!]! @relationship(type: "ACTED_IN", direction: OUT, properties: "ActedInProperties")
 born: BigInt
 directedMovies: [Movie!]! @relationship(type: "DIRECTED", direction: OUT)
 followsPeople: [Person!]! @relationship(type: "FOLLOWS", direction: OUT)
 name: String!
 peopleFollows: [Person!]! @relationship(type: "FOLLOWS", direction: IN)
 producedMovies: [Movie!]! @relationship(type: "PRODUCED", direction: OUT)
 reviewedMovies: [Movie!]! @relationship(type: "REVIEWED", direction: OUT, properties: "ReviewedProperties")
 wroteMovies: [Movie!]! @relationship(type: "WROTE", direction: OUT)
}

type ReviewedProperties @relationshipProperties {
 rating: BigInt!
 summary: String!
}
```

The GraphQL for Neo4j AuraDB will be launched using the v7 library ( the beta of that service is using an early release of v7 ) and it would be nice if there was a quick way to generate a v7 schema.

Which is possible by making a simple change to the GraphQL introspector tool

## GraphQL introspector

This is a separate npm package, @neo4j/introspector. To use it in the way intended here, you will need to create a new project

```Bash
npm create vite@latest my-graphql-introspector
```

When prompted for a framework, select Vanilla

For the Variant, select JavaScript

Then we will install all of the packages we need including the latest build of the v7 GraphQL library.

```Bash
cd my-graphql-introspector
npm install
npm install dotenv
npm install @neo4j/introspector
npm install @neo4j/graphql@7.0.0-alpha.3
```

Create a file called intro.cjs in the src folder under my-graphql-introspector with this content

```javascript
var neo4j = require("neo4j-driver");
const { toGraphQLTypeDefs } = require("@neo4j/introspector");
require("dotenv").config();

const fs = require("fs");
const NEO4J_URI = process.env.NEO4J_URI;
const NEO4J_USR = process.env.NEO4J_USR;
const NEO4J_PWD = process.env.NEO4J_PWD;

const driver = neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USR, NEO4J_PWD));

const sessionFactory = () =>
  driver.session({ defaultAccessMode: neo4j.session.READ });

// We create a async function here until "top level await" has landed
// so we can use async/await
async function main() {
  const typeDefs = await toGraphQLTypeDefs(sessionFactory);
  console.log(typeDefs);
  await driver.close();
}
main();
```

Connection details for Neo4j are held in a .env file. DO NOT SYNC THIS TO GITHUB !

In the folder my-graphql-introspector save .env with this content replacing the supplied values with those that match your environment

```Text
NEO4J_URI=neo4j://localhost:7687
NEO4J_USR=neo4j
NEO4J_PWD=password
```

Finally we run intro.cjs like this

```Bash
node ./src/intro.cjs
```

Output to the console will be a v7 library GraphQL schema file for your Neo4j database. You can adjust it as needed and then load into the GraphQL for Neo4j AuraDB using the Console or the Aura CLI.

## A few final words

Admitedly this can be improved ( a lot, I'm not kidding myself at all ) with items such as:-

- Output to a file
- Better error handling for things like issue with Neo4j connection

But it works.

If you're taking part in the Conway Game of Life competition, using the introspector in this way allows you to quickly generate the schema based off the Developer Blog for [Conway Game of Life in Cyper](https://neo4j.com/blog/developer/cypher-game-of-life/)

You can then use that with a GraphQL DataAPI

Later
