+++
date = '2025-01-31T00:00:00+01:00'
draft = true
title = 'Tutorial for GraphQL for Neo4j AuraDB - The Preamble'
+++

With the launch of GraphQL for AuraDB, its seems an auspicious time to put together a tutorial. All tutorials have an outcome - seems sensible - so we're going to show how you can build Conway Game Of Life.

_Conway?_ Wait, what?

---

### From the 1970s to Neo4j: A Journey Through Conway’s Game of Life

Cast your mind back to the 1970s (or Google it if you must)—an era of disco fever, bell-bottoms, and, in the UK, the [Winter of Discontent](https://en.wikipedia.org/wiki/Winter_of_Discontent). But while the world danced and protested, a youngish John Conway was tucked away in the world of academia, blissfully unaware of it all. Instead of embracing the chaos of the decade, he was pondering something far more abstract: a cellular automaton that could generate endlessly growing patterns while making it devilishly difficult to prove whether any given pattern would do so. (Because, really, what else would a brilliant young mathematician do with his time?)

Mathematicians, as you might have gathered, are a lively bunch—so much so that they were often called upon to ensure guests left parties promptly by dazzling them with their sparkling wit and even more dazzling equations.

Following one such dazzling conversation (possibly involving an exceptional cup of tea and a fresh fairy cake \* ), Conway’s creation first appeared in the October 1970 issue of _Scientific American_, within Martin Gardner’s legendary “Mathematical Games” column.

### The Game Itself

The rules of Conway’s Game of Life are deceptively simple:

1. Start with a grid—let’s say 10x10.
2. Randomly mark each cell as either "alive" or "dead" to form the first generation.
3. Apply the following rules to determine the next generation:

   - Any live cell with fewer than two live neighbors dies (loneliness).
   - Any live cell with two or three live neighbors survives.
   - Any live cell with more than three live neighbors dies (overcrowding).
   - Any dead cell with exactly three live neighbors becomes a live cell (reproduction).

Each new generation is a pure function of the previous one, and these rules continue indefinitely, leading to a fascinating variety of patterns.

This, of course, explains why mathematicians had no time for ’70s entertainment—they were already teetering on the edge of excitement, and any more might have been fatal.

### Bringing It to the Present

Fast-forward to today, and we can recognize something intriguing: the grid of Conway’s Game of Life is essentially a **graph**—a structure of **nodes** and **relationships**. And if there’s one technology that excels at working with graphs, it’s **Neo4j**.

So, in this tutorial series, we’ll build a sleek browser-based front end that communicates with **Neo4j Aura** using **GraphQL**. Along the way, we’ll explore:

- Setting up GraphQL for AuraDB
- Writing GraphQL queries for our cellular automaton
- Extending GraphQL with custom Cypher queries
- Designing an attractive user experience

Until next time!

\* Some details here may be _alternative facts_—but wouldn’t it be nice if they were true?
