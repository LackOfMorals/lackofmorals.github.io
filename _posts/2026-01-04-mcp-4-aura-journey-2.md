---
layout: post
title: "List instances"
description: "Journal entry number two"
tags: Neo4j PM DevEx Go
---

## List instances

The work from my [first step](https://www.pm50plus.com/2025/12/16/mcp-4-aura-journey-1.html) puts me in a positon to build the first tool - list instances. This MCP tool will

- Get a list of instances
- Obtain a summary set of data for each one
- Return the response as a JSON document to the LLM / Agent

All that is need is to write the tool handler and spec. Lets get into that

## The spec

This is the relativelty simple part. Decide on the tool name and the description. The description is rather important. It needs to tell the LLM / Agent what the tools does and how to use it in a concise manner.

Here's what I've come up with

```Go
package outcomes

import (
 "github.com/mark3labs/mcp-go/mcp"
)

func ListInstancesSpec() mcp.Tool {
 return mcp.NewTool("list-instances",
  mcp.WithDescription(`
  Retrieve a list of instances in Neo4j Aura cloud.  An empty list means there are no instances or the user does not have access.`),
  mcp.WithTitleAnnotation("List instances"),
  mcp.WithReadOnlyHintAnnotation(true),
  mcp.WithIdempotentHintAnnotation(true),
  mcp.WithDestructiveHintAnnotation(false),
  mcp.WithOpenWorldHintAnnotation(true),
 )
}
```

## The handler

Here's where we do the work to obtain the information from the Aura API using the Aura Client ( Aura Client being a Go wrapper around the Aura API , avoiding having the manage that ). A list of instances is obtained using `.Instances.List()`. The result is then looped around to use the Id of each entry to read the details with `.Instances.Get(Id)` with all of this being added to an array which is converted to JSON and sent back to the calling LLM / Agent. Here's what that looks like

```Go
package outcomes

import (
 "context"
 "encoding/json"
 "log/slog"

 "github.com/LackOfMorals/mcp4AuraAPI/internal/tools"
 "github.com/mark3labs/mcp-go/mcp"
)

// ListInstancesHandler returns a handler function for the list-instances tool
func ListInstancesHandler(deps *tools.ToolDependencies) func(context.Context, mcp.CallToolRequest) (*mcp.CallToolResult, error) {
 return func(ctx context.Context, _ mcp.CallToolRequest) (*mcp.CallToolResult, error) {
  return handleListInstances(ctx, deps)
 }
}

// handleListInstances retrieves a list of instances using Aura Client
func handleListInstances(ctx context.Context, deps *tools.ToolDependencies) (*mcp.CallToolResult, error) {

 type instanceDetail struct {
  Id            string
  Name          string
  CloudProvider string
  Memory        string
  Type          string
  URL           string
  Status        string
 }

 type instanceList []instanceDetail

 if deps.AClient == nil {
  errMessage := "Aura API Client is not initialized"
  slog.Error(errMessage)
  return mcp.NewToolResultError(errMessage), nil
 }

 slog.Info("retrieving instances from aura api")

 // Get the list of instances
 instances, err := deps.AClient.Instances.List()
 if err != nil {
  errMessage := "Failed to list instances"
  slog.Error(errMessage)
 }

 // Create an empty list
 records := instanceList{}

 // Now get the details for each instance
 // And add them to records list
 for _, inst := range instances.Data {
  instanceInfo, err := deps.AClient.Instances.Get(string(inst.Id))
  if err != nil {
   errMessage := "Failed to get instance details for " + string(inst.Name)
   slog.Error(errMessage)
  }

  records = append(records, instanceDetail{
   Name:          instanceInfo.Data.Name,
   Id:            instanceInfo.Data.Id,
   Status:        instanceInfo.Data.Status,
   CloudProvider: instanceInfo.Data.CloudProvider,
   Memory:        instanceInfo.Data.Memory,
   Type:          instanceInfo.Data.Type,
   URL:           instanceInfo.Data.ConnectionUrl,
  })

 }

 if len(records) == 0 {
  slog.Warn("No instances retrieved.")
  return mcp.NewToolResultText("The tool executed successfully; however, no instance information was returned."), nil
 }

 jsonData, err := json.Marshal(records)
 if err != nil {
  slog.Error("failed to serialize to JSON", "error", err)
  return mcp.NewToolResultError(err.Error()), nil

 }
 return mcp.NewToolResultText(string(jsonData)), nil
}

```

If you want to try this out, then jump over to the [GitHUb Repo](https://github.com/LackOfMorals/mcp4AuraAPI)

## What's next?

Writing a single tool didn't take that much effort as the vast bulk of the work had already been done. I'd already written a wrapper for Aura API and basing the MCP server itself on the official MCP Server for Neo4j has saved a lot of time. Listing Instances is very much a quick win.

I could write a bunch more tools to achieve various outcomes - the Aura API offers lot of flexibility. What I'm more interested in is seeing how only having three tools could work

- A tool to provide a summary of available outcomes
- A tool that gets the details for an outcome
- A tool that executes an outcome

Now I realise that I'll still have to code each outcome - there's no getting away from that.

Next step, go write those three tools and go from there.
