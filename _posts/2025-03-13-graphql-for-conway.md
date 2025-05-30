---
layout: post
title: "Lets figure out the GraphQL for Conway Game Of Life"
description: "GraphQL for Conway with a bit of Cypher"
tags: Neo4j Aura GraphQL Conway
---

## GraphQL for Conway Game Of Life

In my [last post](https://www.pm50plus.com/2025/03/01/conway-part-une.html) I covered setting up GraphQL for AuraDB with this Schema / Type Definition

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

and checked it was all working with a very simple GraphQL Query

```Text
curl --location  'YOUR_GRAPHQL_DATA_API_URL' \
--header 'Content-Type: application/json' \
--header 'x-api-key: YOUR_API_KEY' \
--data '{"query":"query getAllCells {\n    cells {\n      alive\n      id\n      x\n      y\n    }\n  }","variables":{}}'

```

Which means we have arrived at the point to start thinking about the GraphQL queries and mutations that will be needed as part of the implementation of Conway Game Of Life.

Like most new adventures, the first step is the hardest.

I find starting with the User Experience helps with this so lets answer this question. What will a Player need to do to setup and then play the game?

A quickly drawn basic UI is a great quide in helping answering that question.

Here's my attempt - go ahead and judge me if you like.

![Shite UX by a PM](/img/conway-graphql/ConwayGameOfLife.drawio.png)

Back to our question. What will a Player need to do to setup and then play the game? Refering back to my drawing, I can suggest the following:-

- Enter the width and height of the grid.
- Select Draw will cause the grid to appear in line with the dimensions they entered.
- If the Player chooses Reset, then the grid is removed and they can choose new parameters
- Start does what it says - starts the simulation
- Stop, well that's apparant as to its function

Our storage for all of this is a Neo4j AuraDB that we are accessing using GraphQL. We can take our requirements above and slice them into the various operations of Create, Read, Update, and Delete , otherwise known as CRUD.

## Create

After the Player has supplied the size of the grid, we will need to create the nodes and relationships in Neo4j. This will be a two part operation - create nodes and then associate them with a relationship.

### Create individual nodes

A mutation is required to create the nodes, or rather cells as the game refers to them. Thoughout the various GraphQL operations we will be using variables. These are JSON documents that get sent along with the GraphQL operation and allow for efficient operation and flexibility. You can read more about the use of variables on the [GraphQL website](https://graphql.org/learn/queries/)

As for our create cells mutation

```Text
mutation createCells($input: [CellCreateInput!]!) {
  createCells(input: $input) {
    cells {
      id
    }
  }
}
`;
```

And the associated variables JSON document

```JSON
{
  "input": [
    {
        "alive": boolean, true if the cell is alive, false if dead
        "x": int , X position on the Grid.
        "y": int, Y position on the Grid
        "id": string, unique identifier for the cell made from x & y seperated by an underscore e.g "1_1"
    }
   ]
 }
```

You may wonder where the input type `CellCreateInput` comes from. The answer to that is, along with several other input types, it is automatically generated by the GraphQL library that is helping to power the GraphQL API.

The variables JSON document will be assembled by our code ( more on that in the next blog entry ) and sent along with the mutation. This allows us to create all of the cells in a single requuest in the database.

We now have all of the cells and need to join them together into a grid.

### Making a grid

A cell is joined together with its immediate neighbour. Recall that each cell has X & Y values that represent it's co-ordinates. We can therefore calculate a neighbour like this

> C1 is a cell. C2 is another cell. C1 and C2 are neighbours if C2(X-1) <= C1(X) <= C2(X+1) and C2(Y-1) <= C1(Y) <= C2(Y+1).

We can then connect them together in Neo4j by using the NEIGHBOUR_OF relationship.

In GraphQL that is achieved with a mutation.

```Text
mutation connectCellWithNeighbours($where: CellWhere, $update: CellUpdateInput) {
  updateCells(where: $where, update: $update) {
    info {
      relationshipsCreated
      nodesCreated

    }
  }
}
```

The variable JSON document looks like this

```JSON
{
  "where": {
    "id": {
      "eq": string, the Unique ID of the Cell we will make connections for
    }
  },
  "update": {
    "connectedCells": [
      {
        "connect": [
          {
            "where": {
              "node": {
                "id": {
                  "in": [ string ] , a list of IDs for Cells that will be connected
                }
              }
            }
          }
        ]
      }
    ]
  }
}
```

But there's a drawback. This will require looping around all of the cells, sending a mutation to link each of them with it's immediate neighbours. For a 10x10 grid, that is 100 requests and with our max grid of 100x100, well that is a _lot_ of network action.

What if there was a way to do this in a more efficient way? Well there is - get Neo4j to do it.

Neo4j GraphQL has a number of directives, one of which allows the execution of Cypher that has been defined in a query or mutation the GraphQL schema / Type Definitions. Read more about directives and what they can offer at [Directives with Neo4j GraphQL](https://neo4j.com/docs/graphql/current/directives/)

We will need to modify the GraphQL for Aura Data API and add this mutation to the Type Definitions

```TEXT
type Mutation {
    joinCellsTogetherIntoGrid: String @cypher(statement: """
        MATCH(ac:Cell)
        UNWIND ac AS c
        CALL (c) {
            MATCH (c2:Cell)
            WHERE c2.x-1<=c.x<=c2.x+1
            AND c2.y-1<=c.y<=c2.y+1
            AND c.id <> c2.id
            MERGE (c)-[:NEIGHBOUR_OF]->(c2)
        }
        RETURN "Done" AS status
    """, columnName: "status")
}
```

You can see that the @CYPHER directive is used to define Cypher statement that connects all of the cells together to form a grid.

> Why do this? Recall the Game Of Life use rules that flip an individual cell between life and death based on how many of it's neighbours are alive. This is where using a Neo4j graph database comes into it own as this is really easy to model as the rules are describing a _graph!_

We use this mutation by calling it with a mutation GraphQL request

```TEXT
mutation MyMutation {
    joinCellsTogetherIntoGrid
  }
```

As all of the work is performed on the Neo4j server, this is way quicker than making all of those individual GraphQL requests.

That's everything required to build the Grid. What about reading it so it can be displayed?

## Read

### The Grid

There's an additional element to factor in when obtaining the information needed to display the grid; the visualisation library to be used. I've chosen [ForceGraph2D](https://github.com/vasturiano/react-force-graph) for this and it expects a list of nodes and a list of links between them. Node list is made from Cells and their properties. Links are used to join the Nodes together which looks like `[{ source: Cell ID, target: Cell ID}]`

We will need a query that returns a Cell with all of its properties and the ID of any connected Cell. This provides everything needed to use ForceGraph2D to display the grid

```TEXT
query getEntireGrid {
    cells {
      alive
      id
      x
      y
      connectedCells {
        id
      }
    }
```

### How many neighbours are alive

The rules for Conway Game Of Live are remarkably simple. If a living cell has two or three living neighbors, it stays alive, otherwise it dies. If a dead cell has three living neighbors, it is born (or reborn).

Which means we need a query that tells us how many alive neighbours a cell has. This information will then determine the cells fate.

We do this with this query

```Text
query aliveCellsWithAliveNeighours($where: CellWhere) {
    cells {
      id
      alive
      connectedCells(where: $where) {
        id
      }
    }
  }
```

The variables JSON document will be

```JSON
{
  "where": {
    "alive": {
      "eq": true
    }
  }
}
```

The response will return a cells ID, alive ( true or false ) and then the IDs of any alive neighbours. Here's a snippet of a typical response to this query.

```JSON
{
    "data": {
        "cells": [
            {
                "id": "1_1",
                "connectedCells": [
                    {
                        "id": "1_2"
                    }
                ]
            },
            {
                "id": "1_5",
                "connectedCells": []
            },

```

You can see cell 1_1 has one alive neighbour where as cell 1_5 has none. As connectCells is an array, we can use JS `.length` to return an int representing how many alive neighbours there are.

We now have a query to give the values needed to process the simulation rules.

## Update

There are two areas for consideration when it comes to updates

- Enable a Player to choose which Cells start the simulation Alive or Dead
- Setting a Cell status as the simulation is running

### Alive or Dead Cells

Before the simulation can start, the Player will need to select a number of Cells to be alive as they all start out as dead. This requires setting the Alive property of a cell to either True ( Alive ) or False ( Dead ) in case the Player changes their mind and wishes to kill off a cell they previously set to alive.

This is a relatively straight forward mutation

```TEXT
 mutation changeCellAlive($where: CellWhere, $update: CellUpdateInput) {
  updateCells(where: $where, update: $update) {
    cells {
      alive
    }
  }
}
```

The variable JSON document will be

```JSON
{
  "where": [
    {
      "id": {
        "eq": string, unique ID of the Cell whose Alive value we are going to change
      }
    }
   ],
   "update": [
    {
      "alive": {
        "set": true or false as determined by the Players action
      }
    }
    ]
}
```

### Changing the status of a Cell during the simulation

Running Conway Game Of Life requires evaluating each cell in the grid to see how many of its neighbours are alive and then applying the rules to determine if the cell stays alive, becomes alive or is marked as dead.

You may noticed in the variable JSON that the mutation, to change a single cell from alive to dead and vice a versa, uses a list which appears odd as there is only one entry for that particular operation. But it's useful for the bulk changes that will be needed when the simulation is running. Here our code will execute the _Find how many Neighbours are alive query_ and then loop around the list of cells building up two lists of cells; those to mark alive and those who will be dead. The lists can be then used with mutation _Alive or Dead Cells_ with a different variable JSON document to what we used before.

```JSON
{
    where: {
        id: {
            in: [ string, a list of Cell IDs ]
            }
        },
    update: {
        alive: {
            set: boolen,  true or false depending on rule outcome
            }
        }
}
```

This allows for bulk updates rather than doing them on a cell by cell basis.

## Delete

The outcome I'm looking for is to wipe everything so that the Player can start again. The simplest way of doing this is a delete using a mutation.

```Text
mutation deleteEntireGrid {
    deleteCells {
      relationshipsDeleted
      nodesDeleted
    }
  }
```

deleteCells, relationshipsDeleted and nodesDeleted all come from the GraphQL library with the latter two returning totals for each of those categories. As I want to remove everything, a where filter is not used. Which brings me to a word of caution; this will delete **everything** in Neo4j , all of the Cells and all of the NEIGHBOUR_OF relationships will be gone. Use this type of operation with care

## And breathe with me

That's the GraphQL ready. Now for the hard part, well at least for me, coding all of this in JS & React.

Mm. I wonder how good ChatGPT actually is ....

Laters
