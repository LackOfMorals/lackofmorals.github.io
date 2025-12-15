---
layout: post
title: "PM tries to write MCP to control Aura infrastructure"
description: "Journal of writing a MCP server for Neo4j Aura platform"
tags: Neo4j PM DevEx Go
---

## Jumping on the MCP bandwagon

I've been learning Go over the last few months ( Its not a career change, just a desire to learn something new ). I'm now able do a pretty decent "Hello World"

I've also had the honour of working with some of Neo4j engineers to create and release MCP for Neo4j - which is written in Go - and proven to be popular.

It's that now would be a good moment to sup from the trough of MCP success and see if my Go is suffiicent to allow me to fork MCP for Neo4j and modify it to provide a LLM tools to manage Aura infrastructure.

## MCP for Aura API

The Aura API is another area that falls under my PM role at Neo4j. It allows for programmatic management of Aura infrastructure by use of RESTful like API endpoints. You can see this in action in our recent Neo4j Labs project, a [Terrform provider](https://github.com/neo4j-labs/terraform-provider-neo4jaura) for Aura.

A quick look at the Aura API specification shows there's around 50 actions available. Now that feels like that is a _lot_ to give to a LLM as individual tools and there are some actions - deleting Aura instance - that you may not want to place into the hands of a LLM without a safeguard or two.

I'm going to approach this from the perspective of jobs to be done that will look at the desired outcomes to be achieved. This will create the list of tools a LLM can use. I'll also tag each tool so that it can be toggled off / on which will allow me to let users decided if they want the safeguards or not.

Lets start with the first job to be done

- Show me the state of all of my Aura instances

And then we'll build out from there

## How many tools ?

Take a closer look at the MCP server for Neo4j and you'll notice that there is a single tool for GDS which, when called, provides the LLM with a list of available Graph Data Science functions - what each does and how to use them. The LLM then uses this information to create and execute a Cypher statement to get the results. This was a deliberate decision to avoid having to write 40 plus tools with the associated maintainance cost but it was mostly driven by avoiding overloading the LLM context window.

For those who may not be aware of what the context window is, it's the maximum amount of text ( measured in tokens, roughly words/parts of words ) a LLM can process as input and remember for a single response, crucial for understanding long documents, maintaining coherent conversations, and complex tasks, with sizes growing from thousands to over a million tokens, though performance can degrade with excessive length referred to as _context rot_. Included in that text are tools and their definitions. If you give a LLM a lot of tools, then you run the risk of LLM encountering context rot which shows itself as an error message, slow decision making, making no decisions or just plain wrong ones. You'll also notice that I mentioned tokens, something that is throttled depending on the plan you're using with your LLM or demands on the LLM itself.

In short, having lots of tools is not a good thing.

This means for my MCP for Aura server, I should avoid having lots of tools. Instead I'm going to follow a pattern that we ( briefly ) looked into for MCP for Neo4j but didn't have time to implement for the first releases:

- A tool that provides a summary of possible outcomes that the LLM can achieve
- A tool that provides the details for an outcome i.e what is needed
- A tool that allows the outcome to execute

This is similar to what is described by SpeakEasy in their article [Reducing MCP token usage by 100x](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2)

## Aura API

After avoiding writing a MCP server from scratch by forking MCP for Neo4j and only needing to write three tools ( yes, I know that will more functions needed ) I can turn my attention to how Aura API will be accessed.

As it turns out, the first Go package I put together is a client for the Aura API. For example, to list instances

```Go
package main

import (
    "log"
    aura "github.com/LackOfMorals/aura-client"
)

func main() {
    // Create client with credentials
    client, err := aura.NewClient(
        aura.WithCredentials("your-client-id", "your-client-secret"),
    )
    if err != nil {
        log.Fatalf("Failed to create client: %v", err)
    }

    // List all instances
    instances, err := client.Instances.List()
    if err != nil {
        log.Fatalf("Failed to list instances: %v", err)
    }

    for _, instance := range instances.Data {
        log.Printf("Instance: %s (ID: %s)\n", instance.Name, instance.Id)
    }
}
```

This was inspired by the Neo4j Labs Terraform project access the Aura API as I thought it would the Aura API easier to work with if it came as a Go package.

## lets code

I think I have all I need to make a start although it will be Claude helping whenever I encounter a road block or gap in my knowledge.

Until then

Laters
