---
layout: post
title: "Aura API Go client"
description: "v1 of a Go client for Aura API "
tags: Neo4j PM DevEx Go
---

## A Go client for Aura API

Over the last few weeks I've worked on creating a wrapper around the Aura API for use with Go. This is not wholly my own work; I've lifted the concept of using structs to model API request / responses from our Neo4j Labs Terraform Provider and embraced assistance from Claude to explore potential ideas, write tests and direct me when I got stuck.

The Aura CLient ( I'm not that great with naming ) is ready for use - mostly. Did I mention that I'm a hobby coder ?

## Installation

```bash
go get github.com/LackOfMorals/aura-client
```

## Quick Start

### Basic Setup

```go
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

[Report Issues](https://github.com/LackOfMorals/aura-client/issues)

Hopefully you'll find this of use
