---
layout: post
title: "Enabling introspection on the GraphQL for Aura"
description: "Enabling introspection on the GraphQL for Aura"
tags: Neo4j Aura GraphQL
---

# Enabling introspection on the GraphQL for Aura
Enabling introspection for a GraphQL API in Aura is coming shortly but you can do it today using the Aura API.  If you need this, and there's a number of steps to follow, then do this. 

Although we will use CURL to enable / disable introspection, we will need to use the Aura CLI to get the Instance ID and ID of the associated GraphQL API 

Get the Aura CLI installed and configured by following the steps given in the [GraphQL Beta Prerequisites](https://neo4j.com/docs/graphql/current/aura-graphql/prerequisites/)

Onto finding the Instance ID.  List all of your Aura instances using the table output which makes it easier to locate the ID

```Text
aura-cli instance list --output table
```

Make a note of the instance ID.

Now get the ID of the GraphQL API for that instance, changing YOUR_INSTANCE_ID for your value


```Text
aura-cli data-api graphql list --instance-id YOUR_INSTANCE_ID
```

Write down the ID of the GraphQL Data Api

Finally, we need a token to auth to the Aura API.  The Aura CLI caches these locally as the tokens last for 1 hour and there is no point in getting another one until it expires.  This also avoids spamming the token endpoint. 

You can see the token by asking the Aura CLI for it's configuration settings.  Do this with

```Text
aura-cli config list
```

This returns a JSON document that contains the current token as the value for the key ```access-token```


Make a note of that as well

At this point you should have three items

- ID of the GraphQL API
- ID of the associated Aura Instance
- A token for the Aura API

Here's the CURL command to set Instrospection on using those values


```Text
curl --location --request PATCH 'https://api.neo4j.io/v1beta5/instances/YOUR_AURA_INSTANCE_ID/data-apis/graphql/YOUR_GRAPHQL_API_ID' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--header 'Authorization: Bearer YOUR_AURA_API_TOKEN ' \
--data '{
 "security": {
            "introspection_enabled": true
        }
  }
}'

```

To disable introspection, set the value to false