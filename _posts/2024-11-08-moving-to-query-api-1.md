---
layout: post
title: "Moving to Neo4j Query API - Partie Un "
description: "Say goodbye, wave hello"
tags: Neo4j PM DevEx QueryAPI  Aura
---


# Moving forwards

If you're interested in transitioning to the Query API, this is the place to start. This post will provide an overview of the key areas to consider and plan for. A follow up post post, will dive deeper with a worked example.  

While there's no immediate pressure to move from the HTTP API, it's important to note that its updates will be limited to critical security and defect fixes. All future development and improvements will be focused on the Query API.

---

## Embracing differences
In an ideal world, there would not be any differences between the HTTP and Query APIs. When designing the Query API data contracts, our primary goal was to make Developer outcomes easier to achieve compared to what had gone before. As we iterated our way along the design and development process, it quickly became apparent that changes would be needed to realise the benefits we set out to achieve.  Lets delve more into what those changes are and what they mean to you.

### Versioning
The Query API will support the current version ( n ) and the immediately prior one ( n-1 ). This allows the introduction of new features that require breaking changes while ensuring applications continue without interruption. It also clearly identifies which Query API variant is being used. Following best practices, the version number is now in the URL
/db/{db name}/query/v{major version number}

### Using implicit or explicit transactions
Like the HTTP API, the Query API offers both implicit and explicit transactions. For the former, you supply a Cypher statement and the transaction is managed for you. With the latter you're in control of the transaction from start to finish.

The HTTP API path for these operations is somewhat shy when it comes to showing intent. From the paths below, which does what?

- URL path : /db/{db name}/query/v{major version number}/tx
- URL path : /db/{db name}/query/v{major version number}/tx/commit

You would use the top one for explicit and the bottom for implicit, something that is not immediately obvious.

We took this approach with the Query API to improve clarity by taking advantage of most peoples use of tx for transactions

- implicit URL path : /db/{db name}/query/v{major version number}
- explicit URL path : /db/{db name}/query/v{major version number}/tx

### A single Cypher statement per request
On the face of it, having multiple Cypher statements in a single request has advantages; you get a lot done in one go and only take the hit from establishing a TCP connection once. The reality is that it was not used this way - it was harder to track down which Cypher statement had a syntax error or was otherwise not working as intended when there were many of them in a single request. With the vast majority of programming platforms allowing re-use of an existing TCP session which eliminated the time overhead of connection establishment, the advantages of many Cypher statements in a single request have faded away.

It became clear that the simplicity offered from a single Cypher statement per request was the direction of travel to pursue. This also created the opportunity to improve information for errors and make better use of HTTP status codes.

### Response Notifications has a category
This is an addition to the Notification section of a response and is there for classification purposes e.g performance. This is primarily intended for logging and subsequent analysis.

### JSON with Type information
JSON allows for values a type from string, number, JSON object, array , boolean or null. The Neo4j type list is much more extensive covering many more types. The HTTP API has a content type that adds JSON type information to the returned JSON response - JOLT. Jolt, short for JSON Bolt, is a JSON-based format which encloses the response value's type together with the value inside a singleton object ( Bolt being the packet stream based protocol use by Neo4j server and platform drivers ).

In all honesty, the feedback from Developers for JOLT can best be summarised as _'Would not recommend'_ but there remained a desire for types.  

We like a challenge and commenced on a ground-up re-design for extending JSON with Neo4j type information. With the Query API you now ```Accept: application/vnd.neo4j.query``` to your request header and get back a JSON response that is decorated with Neo4j type information.

Feedback is encouraged.

### Response format change
It's morphed a bit from the response that you'd get from making HTTP API requests.  This is what you will now be receiving

```
{
  "data": {
    "fields": [ field1, field2, ... ],
    "values": [ entity1, entity2, ... ]
  }
  "bookmarks": [ bookmark1, bookmark2, ...     ]
}
```

If the Neo4j DB server decides that you could do better with your Cypher, than this will be included in the response

```
  "notifications": [
    {
      "code": string,
      "description": string,
      "severity": string,
      "title": string,
      "position": {
          "offset": int
          "line": int,
          "column": int
      },
      "category": string,
    }
  ]
```

And if something has gone wrong, then you'll get this to explain what's gone wrong

```
  "errors":[
    { 
      "code": string,
      "message": string
     },
    ]
}

```
