---
layout: post
title: "About that Conway Game Of Life"
description: "Figuring out the Graphql - Part One"
tags: Neo4j Aura GraphQL
---

# Lets figure out the GraphQL for Conway - Part One

Grab an adult beverage and read this [blog entry](https://medium.com/neo4j/a-cypher-game-of-life-53b5faf04caa/).

TL;DR In that blog post, Christoffer Bergman describes Conways Game of Life implemented in Cypher. I'm going to base my attempt at Conway Game Of Life using GraphQL on his work. To start with , I'm going to need a GraphQL schema and a GraphQL service. That will then allow me to experiment with GraphQL Queries / Mutations to figure out those needed to implement the game.

Lets get the GraphQL Data API deployed and then , in next post, we can try out that GraphQL.

You may guess from those words this a fairly long entry.

I'd go get another adult beverage from the fridge.

## Eyes open

Christoffer uses a Neo4j schema that has a Cell node using a boolean property, alive, to represent the cells state ( true = alive, false = dead ). Additionally, there is a Spatial coordinate used for Cells position in the grid. Finally, Cells are related to each other using NEIGHBOUR_OF.

I am going to represent this in GraphQL 'as is' apart from an adjustment for the co-ordinates so they use x and y properties as it makes GraphQL operations somewhat easier. I'll also add in an ID for good measure. My GraphQL schema looks like this

```Text
type Cell @node {
 cellsConnected: [Cell!]! @relationship(type: "NEIGHBOUR_OF", direction: IN)
 connectedCells: [Cell!]! @relationship(type: "NEIGHBOUR_OF", direction: OUT)
 alive: Boolean!
 id: String!
 x: BigInt!
 y: BigInt!
}
```

I would like to say I wrote this but I didn't. Instead I ran Cypher against an Aura instance to create Cells and relate them. Then I a modified version of the GraphQL Introspector to generate the schema from me. I will also use the same Neo4j Db for the GraphQL Data api.

## Look what you made me do

If you have an Aura Professional, Business Critical or Virtual Dedicated Cloud account, then you can skip this bit. If you don't have one of these, then sign up for an Aura Profressional Trial account as the GraphQL for Neo4j AuraDB Beta is not avaiable on Aura Free.

**Signing up for an Aura Pro Trial**

- Head over to [Signing up for AuraDB](https://login.neo4j.com/u/signup/) and complete that process.
- Create an instance but choose Aura Professional 'Try For Free'
  ![](/img/graphql-aura-beta/tryAuraProFree.png)
- Select your cloud provider , the 4Gb instance, suggested name and accept the terms
  ![](/img/graphql-aura-beta/AuraProInstance.png)
- Wait for the instance to be deployed and , **IMPORTANT BIT**, make sure you save the connection information.

## I knew you were trouble

Now to run Cypher against the deployed Aura database to create several Cells and connect them together using NEIGHBOUR_OF.

First create a few cells with the properties we want.

```Text
UNWIND range(1,2) as x
    UNWIND range (1,2) as y
    CREATE (c:Cell {id:x + '_' + y, x: x, y: y, alive: False})
RETURN COUNT(c)
```

Then join the cells together using the NEIGHBOUR_OF relationship but do not join a cell to itself.

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

## Shake it off

The GraphQL schema was genereted using the Introspect tool which I had adapted to use the GraphQL v7 library used by the GraphQL for Neo4j AuraDB.

I have created a GitHub repo which you can use by following these steps

- Clone the repo

```Text
git clone https://github.com/LackOfMorals/my-graphql-introspector.git
```

- Install

```Text
cd my-graphql-introspector
npm install
```

- Set connection to Neo4j / AuraDB by creating a .env file at the folder root. Replace values for NEO4J_URI, NEO4J_USR and NEO4J_PWD with the values that match your configuraiton

```Text
NEO4J_URI=neo4j://localhost:7687
NEO4J_USR=neo4j
NEO4J_PWD=password
```

- Run the Introspector

```Text
node ./src/intro.csj
```

If you want to see how to modify the Introspector and build your own, see this [blog post](https://www.pm50plus.com/2025/02/25/graphql-aura-v7-library.html).

We're now ready to deploy GraphQL for AuraDB Beta using the schema that was just provider by the Introspector.

##  Blank space

Jump back into the Aura Console.

Note: You will need the username and password for your Aura DB instance that we just used with Cypher and Instrospector.

- Select _Data APIs Beta_ and then _Create API_
  ![](/img/graphql-aura-beta/DataAPI.png)

- There's a number of boxes to fill out and it doens't fit nicely into a single screenshot. I've broken them out in multiple ones.

- _Details_
  - API Name , a friendly name
  - Instance. From the drop down, select the name of the Aura DB to use with GraphQL. Choose the one that was used with Cypher / Introspector
  - Instance username. The username for the Instance you selected
  - Instance password. The password for the Instance you selected

![](/img/graphql-aura-beta/DataAPIDetails.png)

- _Type Definitions_
  Copy and paste the GraphQL schema that came from the Introspection or just use the one at begining of this blog post. Do not select _Enable GraphQL subgraph_
  ![](/img/graphql-aura-beta/DataAPITypeDefs.png)

- _CORS policy_
  ![](/img/graphql-aura-beta/DataAPICors.png)

- By default, as part of security layers around a GraphQL Data API, a very restrictive CORS policy excludes all communications from a browser. This will be problematic for any browser based application that is going to be using it. For more on CORs, AWS has a good write up here: - [What is Cross-Origin Resource Sharing?](<https://aws.amazon.com/what-is/cross-origin-resource-sharing/#:~:text=Cross%2Dorigin%20resource%20sharing%20(CORS)%20is%20an%20extension%20of,that%20are%20public%20or%20authorized>)

- As all of my development is using the vite framework on node.js, <http://localhost:5173> will need adding to the CORS policy by selecting _Add allowed origin_.

![](/img/graphql-aura-beta/DataAPICORSlocalhost.png)

- _Authentication providers_
  ![](/img/graphql-aura-beta/DataAPIAuthProviders.png)

- API key and secure JWT are supported for authentication to the GraphQL Data API. Authentication is always required. I'm going to use an API key.

  - Select _Add authenticaton provider_
  - Choose _API key_ from the drop down
  - Enter a friendly name for the API key. The key itself will automatically be generated

- _Sizing_
  There will be a number of different sizes at different charging rates for GraphQL Data API when its fully released. The beta is free and uses a fixed size.

![](/img/graphql-aura-beta/DataAPISizing.png)

That's everything needed. Select _Create_

Note: There's a little defect that occasionally crops up that results in having to re-enter the Instance username and Instance password when creating or modifying when there is no need to do so. We'll fix that before release. Hopefully.

If everything has been entered and validated you will see a window with the URL and API Key for the GraphQL Data API. Make sure you save this in a safe place as there is no way to recover the API Key. If you do misplace the key, a new one will need to be furnished.

Deployment will take a few minutes. As this post is going on for way longer than I intended, now is would be a good time for a cup of tea. Or another adult beverage.

## Cruel Summer

In the new user experience you should now see the GraphQL Data API with a status of Ready. We'll run a GraphQL Query that returns the Cells we created earlier using Cypher. curl will be used for this.

Replace

- YOUR_GRAPHQL_DATA_API_URL with your URL for the GraphQL Data API
- YOUR_API_KEY with your API key

```text
curl --location  'YOUR_GRAPHQL_DATA_API_URL' \
--header 'Content-Type: application/json' \
--header 'x-api-key: YOUR_API_KEY' \
--data '{"query":"query getAllCells {\n    cells {\n      alive\n      id\n      x\n      y\n    }\n  }","variables":{}}'
```

You should see a JSON response with the data.

##  Is it over now?

For now, yes, that's it. We have a working GraphQL Data API which we can now use to figure out the various GraphQL Queries and Mutations with Conway Game Of Life.

Which we'll do in the next blog .

Until then

Laters
