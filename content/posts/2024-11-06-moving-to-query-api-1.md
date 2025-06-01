+++
date = '2024-11-06T00:00:00+01:00'
draft = true
title = 'Migratiing to the Query API - part one'
+++

If you're interested in transitioning to the Query API, this post will provide an overview of the key areas to consider and plan for. A follow up post post will dive deeper with a worked example. While there's no immediate pressure to move from the HTTP API, it's important to note that updates will be limited to critical security and defect fixes. All future development effort will be focused on the Query API.

---

## Embracing differences

In an ideal world, there would not be any differences between the HTTP and Query APIs. When designing the Query API data contracts, our primary goal was to make Developer outcomes easier to achieve compared to what had gone before. As we iterated our way along the design and development process, it quickly became apparent that changes would be needed to realise the benefits we set out to achieve. Lets delve more into what those changes are and what they mean to you.

### URL

The most obvious change is with the URL. The path has changed to support Versioning ( covered in more detail next ) and introduces the name of API itself. The latter avoids a namespace collision to allow running of both API so you can gradually move over

- HTTP API: /db/{db name}
- Query API: /db/{db name}/query/v2

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

We like a challenge and commenced on a ground-up re-design for extending JSON with Neo4j type information. With the Query API you now `Accept: application/vnd.neo4j.query` to your request header and get back a JSON response that is decorated with Neo4j type information. More detail on this in in the [JSON with Type](https://neo4j.com/docs/query-api/current/result-formats/#_json_with_type_information) documentation

Feedback is encouraged.

### Response changes

It's morphed a bit from the response that you previously got from the HTTP API. The response has been organised into distinct areas within the JSON response with a top level that contains one or more these entries

```text

{
   "data":{},
   "counters":[],
   "profiledQueryPlan": {},
   "identifiers":[],
   "children":[],
   "notifications":[{}],
   "errors":[{}],
   "bookmarks": []
```

The top level entries change depending on the request, if an error occurred, information from the Neo4j server, and if the Cypher statement was to be profiled. Exact details for each of these can be found in the [documentation](https://neo4j.com/docs/query-api/current/)

---

## What's next?

There's three other points to consider when planning your migration

- Be curious
  Althought this blog has covered the main areas of difference between the HTTP API and the Query API, do not assume that these are the **only areas** that you need to pay attention to. These are general points and each application will have it's own quirks. Be curious - go read your applications source code to learn more about how they are using the HTTP API

- Remember that the Tortoise won
  "The Tortoise and the Hare" is one of Aesop's Fables where the Hare looses the race due to foolish over confidence. A slow and steady migration is better than a hasty swap over. For self-managed customers, the HTTP API will be supported for a long time yet as part of the 5.26 LTS version of Neo4j, recieving updates for critical bugs and security defects.

- Dual running
  Self-managed customers can run both the HTTP and Query API at the sametime. Take advantage of this for back to back testing where results, performance, and security can be compared between the two APIs. It also allows for a gradual transistion with the HTTP being switched off when eveything has been moved across.

- Read the docs
  Do not forget to read the Query API documentation so that you are informed of what the API does and it does it! [Query API Documentation](https://neo4j.com/docs/query-api/current/)

As mentioned at the start of this blog, a follow up post will look at code changes to move a Python application from the HTTP API to the Query API.
