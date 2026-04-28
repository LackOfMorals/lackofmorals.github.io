---
layout: post
title: "Getting ready"
description: "Journal entry number one "
tags: Neo4j PM DevEx Go
---

## MCP 4 Aura API - taking the first step

As mentioned in my previous post, I'm basing my MCP for Aura API on the existing MCP for Neo4j. This post is all about stripping that down to get ready to then start writing the code I actually want.

## Declutering

After forking [MCP for Neo4j](https://github.com/neo4j/mcp) and looking over the code, I now have this list of features that will not be needed and can be removed

- Sending back metrics
- Database connectivity
- Get schema, read & write cypher tools
- Associated configuration environmental variables

I've created a branch to preserve the original code and then another that will be stripped back.

Lets work our way through this list, starting at the top

## Sending back metrics

At various points in the code, metrics are sent back to record MCP startup and name of the tool that was executed. There's also a package to do sending.

Files to change

- cmd / neo4j-mcp / main.go
  Initialization of analytics, read config setting for metrics & enabled / disable

- internal / server / server.go
  Server startup event

- internal / config / config.go
  Remove code for handling of configuration setting for metrics

- internal / analytics
  Remove entire folder as this is where the analytics package resides

## Database connectivity

Everything related for access with a Neo4j database will be removed.

- cmd / neo4j-mcp / main.go
  Initialization of database server, database config settings

- internal / server / server.go
  Database is represented in several structs, creating a new MCP server instance and verifying requirements. All of this will need removing.

- internal / config / config.go
  Remove code for dealing with database settings

## Get schema, read & write cypher tools

This mostly removing the files under - internal / tools with edits to - internal / server / tools_register.go

I will keep - internal / tools / cypher / get_schema_handler.go and - internal / tools / cypher / get_schema_spec.go as examples to work from.

## Other stuff

Anything not immediately related to what I need is going to be removed e.g files used for building , docs, integration tests etc.. Speaking of tests, as I'm making a bunch of radical changes to the code base, I'll be removing the test files. I will put tests back in at a later date.

Rather importantly, once all of these changes are done, I'll need to update `go.mod` and then run `go mod tidy`

`go.mod` will contain the package name and point to the repo on my github.

## And we have a branch

[prepare-for-mcp-4-aura](https://github.com/LackOfMorals/mcp4AuraAPI/tree/prepare-for-mcp-4-aura) will be the branch that contains stripped down MCP server that I'm going to then build MCP for 4 Aura from.

Best get going with the delete key ;)

Laters
