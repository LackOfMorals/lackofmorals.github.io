---
layout: post
title: "Token for auth with GraphQL for AuraDB "
description: "Part two of a guide to using token with GraphQL for AuraDB"
tags: Neo4j PM DevEx Token GraphQL
---

# An introdcution to using JWTs with GraphQL for AuraDB - Part Two

In [part one](https://www.pm50plus.com/2025/05/16/graphql-jwks-part-1.html) I covered how to set up GraphQL for AuraDB to use JWTs and the identity provider, okta, that generates them.

This blog will look at using properties of a token to control access to the API and the data within.

But I'm overreaching a bit as I'm assuming knowledge ( a trap so easier to stumble into when trying to convey information ) on the topic of JSON Web Token (JWT ).

Lets quickly fix that.

## A primer on JSON Web Token (JWT )

A JSON Web Token (JWT) is an open standard (RFC 7519) that defines a compact and self-contained way for securely transmitting information between parties as a JSON object. This information can be verified and trusted because it is digitally signed. So any attempt to change a JWT in order to gain access will fail as the JWT will not pass verification.

A JWT consists of three elements, a Header, Payload and Signature and it's the 2nd part we're interested in as this contains _claims_. Keeping with the 3 theme, there are three types of claims: registered, public, and private claims.

> Note: Claim names are only three characters long to keep the JWT as small as possible.

### Registered claims

These are a set of predefined claims which are not mandatory but recommended, to provide a set of useful, interoperable claims.

### Public claims

These can be defined at will by those using JWTs ( e.g adding scopes in Okta ). Ideally they should be defined in the IANA JSON Web Token Registry to avoid collison but most don't bother.

### Private claims

These are the custom claims created to share information between parties that agree on using them and are neither registered or public claims.

Here's an example of a decoded payload from Okta that was configured as described in the Part One blog.

```JSON
{
    "ver": 1,
    "jti": "AT.3qOFwHd-YW0gOUACNT2th5-1r7YQ3DDnug3UGOvaDcI",
    "iss": "https://dev-85257838.okta.com/oauth2/ausoqtatu2kOwMgbe5d7",
    "aud": "graphqAPIUsers",
    "iat": 1747844937,
    "exp": 1747848537,
    "cid": "0oaoqt9j7yYo1ytbs5d7",
    "scp": [
        "graphqlAPIRO"
    ],
    "sub": "0oaoqt9j7yYo1ytbs5d7"
}
```

Public claims that you will often see include

- iss: The issuer of the JWT, usually a URI of some sort.
- aud: The audience for the JWY.
- iat: Issued At. The Date time when the token was created
- exp: Expiry. When the token expires

This quick JWT introduction arms us with suffiicient detail for what we need to do. If you want to find out more, the [official specification](https://datatracker.ietf.org/doc/html/rfc7519) is a good place to start.

> Note: JWT payload can be read by _anyone_ who has it unless it has been encrypted. Be careful what you include.

## Using JWT with GraphQL for AuraDB

At the end of part one of this blog series, we had a GraphQL data api that can only be access with a valid JWT. Your use case may determine that this is sufficient - possesion of a verifiable JWT is a sufficient level of protection for being able to query / mutate your data using GraphQL operations. If you need nothing more than this, you now have the chance to do something else instead of moving your eyes over the rest of these fine words.

But what if you need more control?

For reference, here's what is possible with JWTs along with links to the relevant documentation page

[Authentication](https://neo4j.com/docs/graphql/current/security/authentication/)
You could judge that this is fairly useless as the GraphQL API itself has already checked the JWT and allowed access if it was verified. However, that process does not look at any private claims that have been added to the JWT payload which you may want to use to further refine who is permitted to use the GraphQL API, set specific or default rules as to what they can do by controlling what operations are pemitted.

[Authorization](https://neo4j.com/docs/graphql/current/security/authorization/)
Authorization rules cover what specific data a generated Cypher query is allowed to access and hence can control the outcomes of GraphQL queries and mutations. There are two types of rules that can be used; _Filtering rules_ that filter out data which users do not have access to, without throwing any errors and _Validating rules_ that throw an error if a query is executed against data which users do not have access to.

We'll use examples to show these being used in a number of scenarios.

Introducing ACME Corporation.

### Scenario One - Controlling access to a group of ACME's users

ACME Corporation use Single Sign On for all of their applications. They wish to use the same system to provide access to GraphQL Data API for a subset of their users.

Configuring the GraphQL to support JWT will allow anyone using SSO in ACME Corp to gain access but we only want some of them to do so. To enforce additional controls, we can use the `@authentication` directive to check the JWT to see if it contains a certain claim that indicates authentication should be allowed. Using the Okta web console, ACME Corp adds an additional entry in the JWT scope claim for this purpose - "acmeGraphQLUser"

Lets modify the Type Definitions to use this

```JSON
type JWTPayload @jwt {
            roles: [String!]! @jwtClaim(path: "scp")
            }

extend @authentication( jwt: { roles: { includes: "acmeGraphQLUser" } })
```

Lets dig into what's going on here.

We define a type, JWTPayload that's decorated with @jwt. You can use any type name so long as you add @jwt. Within the type we have an array of strings, roles and we use @jwtClaim to copy over values from the JWT payload claim 'scp' into it. So the net result is we now have access to the values defined in the scp claim of our JWT. We have to do this as scp is a private claim from Okta and not a publically registered one. If we were only using [public claim names](https://www.rfc-editor.org/rfc/rfc7519#section-4.1) from the JWT specification, e.g iss, then we don't need to do this as those claims are automatically available to us.

Now we have the values, we can check them to see if access shoud be granted with use of the `@authentication` directive. You can see that we check roles to see if contains the value "acmeGraphQLUser"; If it does the request will be accepted, if not it will be rejected.

ACME Corporation now has secured its GraphQL API so that only people who have been given the "acmeGraphQLUser" as part of the token issued to them will be able to have access.

Great success.

### Scenario Two - Protecting sensitive data

ACME Corporation is so stoked with the outcomes it's getting from using GraphQL with AuraDB that they want to do more. But some of the data they wish to expose is sensitive and not all users should be able to access it.

Here's where we can make use of `@authorization` directive combined with either validation or verification rules or a combination thereof.

Rather than rush in, ACME Corp decides to try a few things using the Movies example graph. Here's the Type Definitions for Movies graph.

```JSON
type JWT @jwt {
    roles: [String!]! @jwtClaim(path: "scp")
}

extend schema @authentication( jwt: { roles: { includes: "acmeGraphQLUser" } } )


type ActedInProperties @relationshipProperties {
  roles: [String!]!
}

type Movie @node  {
  peopleActedIn: [Person!]!
    @relationship(
      type: "ACTED_IN"
      direction: IN
      properties: "ActedInProperties"
    )
  peopleDirected: [Person!]! @relationship(type: "DIRECTED", direction: IN)
  peopleProduced: [Person!]! @relationship(type: "PRODUCED", direction: IN)
  peopleReviewed: [Person!]!
    @relationship(
      type: "REVIEWED"
      direction: IN
      properties: "ReviewedProperties"
    )
  peopleWrote: [Person!]! @relationship(type: "WROTE", direction: IN)
  released: BigInt!
  tagline: String
  title: String!
}


type Person @node {
  actedInMovies: [Movie!]!
    @relationship(
      type: "ACTED_IN"
      direction: OUT
      properties: "ActedInProperties"
    )
  born: BigInt
  directedMovies: [Movie!]! @relationship(type: "DIRECTED", direction: OUT)
  followsPeople: [Person!]! @relationship(type: "FOLLOWS", direction: OUT)
  name: String!
  peopleFollows: [Person!]! @relationship(type: "FOLLOWS", direction: IN)
  producedMovies: [Movie!]! @relationship(type: "PRODUCED", direction: OUT)
  reviewedMovies: [Movie!]!
    @relationship(
      type: "REVIEWED"
      direction: OUT
      properties: "ReviewedProperties"
    )
  wroteMovies: [Movie!]! @relationship(type: "WROTE", direction: OUT)
}

type ReviewedProperties @relationshipProperties {
  rating: BigInt!
  summary: String!
}
```

ACME Corp has the changes from Scenario One that control access to the GraphQL API to those with the "acmeGraphQLUser" claim in their token. This token will always be present but there will be an additional token, "acmeGraphQLSensitive" that allows access to sensitive data.

There are two rules ACME can use with `@authorization` filtering and validuation. Recall from our earlier explanation, filtering will remove data according to defined rules where as validation returns an error. Let sees what's these look like when protecting sensitive data.

The Person type contains sensitive data that we want to protect. Lets do that by restricting it to only those users with "acmeGraphQLSensitive" in their token.

```JSON
type Person @node @authorization(filter: [ { where: { jwt: { roles: { includes: "acmeGraphQLSensitive" } } } } ])
{
  actedInMovies: [Movie!]!
    @relationship(
      type: "ACTED_IN"
      direction: OUT
      properties: "ActedInProperties"
    )
  born: BigInt
  directedMovies: [Movie!]! @relationship(type: "DIRECTED", direction: OUT)
  followsPeople: [Person!]! @relationship(type: "FOLLOWS", direction: OUT)
  name: String!
  peopleFollows: [Person!]! @relationship(type: "FOLLOWS", direction: IN)
  producedMovies: [Movie!]! @relationship(type: "PRODUCED", direction: OUT)
  reviewedMovies: [Movie!]!
    @relationship(
      type: "REVIEWED"
      direction: OUT
      properties: "ReviewedProperties"
    )
  wroteMovies: [Movie!]! @relationship(type: "WROTE", direction: OUT)
}
```

If you now run a graphQL query with the "acmeGraphQLSensitive" claim in your token the query will return what's being asked for. Without the token you just see this

```JSON
{
    "data": {
        "people": []
    }
}
```

But what if there are only a subset of fields that need to protected ? Well you can apply `@authorization` to individual fields. If a query contains any of those field and the received JWT lacks the required claim, an emplty JSON document is returned like the one above. But if the query does not have any of protected fields and the JWT lacks the need claim, you will still get the asked for data back.

To do this, ACME changes its Type Def as follows

```JSON
type Person @node
{
  actedInMovies: [Movie!]!
    @relationship(
      type: "ACTED_IN"
      direction: OUT
      properties: "ActedInProperties"
    )
  born: BigInt @authorization(filter: [ { where: { jwt: { roles: { includes: "acmeGraphQLSensitive" } } } } ])
  directedMovies: [Movie!]! @relationship(type: "DIRECTED", direction: OUT)
  followsPeople: [Person!]! @relationship(type: "FOLLOWS", direction: OUT)
  name: String!
  peopleFollows: [Person!]! @relationship(type: "FOLLOWS", direction: IN)
  producedMovies: [Movie!]! @relationship(type: "PRODUCED", direction: OUT)
  reviewedMovies: [Movie!]!
    @relationship(
      type: "REVIEWED"
      direction: OUT
      properties: "ReviewedProperties"
    )
  wroteMovies: [Movie!]! @relationship(type: "WROTE", direction: OUT)
}
```

When a query is issued that does not include _born_ and the JWT does not have "acmeGraphQLSensitive" in its claims, then we still get them requested results

```JSON
{
    "data": {
        "people": [
            {
                "name": "Keanu Reeves"
            }
        ]
    }
}
```

Instead of empty JSON documents, ACME could have an error returned by using **validation** instead of **filter**. The structure is similar

```JSON
born: BigInt @authorization(validate: [ { where: { jwt: { roles: { includes: "acmeGraphQLSensitive" } } } } ])
```

When requesting **born** without the required JWT claim, you now get an error like this.

```JSON
{
    "errors": [
        {
            "message": "Forbidden",
            "locations": [
                {
                    "line": 2,
                    "column": 3
                }
            ],
            "path": [
                "people"
            ]
        }
    ],
    "data": null
}
```

More on **filter** and **validate** can be found in the GraphQL API [documentation](https://neo4j.com/docs/graphql/current/security/authorization/)

### Scenario Three - control writes

With protection for sensitive data, ACME Corporation turns it attention to controlling who can change the data. ACME Corps adds another claim to the JWT to control this:- "acmeGraphQLReadWrite".

Staying with the Type Defs already present, we add `@authentication`, with a check for "acmeGraphQLReadWrite" in the JWT, to each node that requires protection against change like this:-

```JSON
@authentication(operations: [CREATE, DELETE, UPDATE], jwt: { roles: { includes: "acmeGraphQLReadWrite" } } )
```

See the [list of operations](https://neo4j.com/docs/graphql/current/security/authentication/#_operations) in the documentation to see what is possible

ACME Corps type defintions now look like this

```JSON
type JWT @jwt {
    roles: [String!]! @jwtClaim(path: "scp")
}

extend schema @authentication(  jwt: { roles: { includes: "acmeGraphQLUser" } } )


type ActedInProperties @relationshipProperties {
  roles: [String!]!
}


type Movie @authentication(operations: [CREATE, DELETE, UPDATE], jwt: { roles: { includes: "acmeGraphQLReadWrite" } } )  @node   {
  peopleActedIn: [Person!]!
    @relationship(
      type: "ACTED_IN"
      direction: IN
      properties: "ActedInProperties"
    )
  peopleDirected: [Person!]! @relationship(type: "DIRECTED", direction: IN)
  peopleProduced: [Person!]! @relationship(type: "PRODUCED", direction: IN)
  peopleReviewed: [Person!]!
    @relationship(
      type: "REVIEWED"
      direction: IN
      properties: "ReviewedProperties"
    )
  peopleWrote: [Person!]! @relationship(type: "WROTE", direction: IN)
  released: BigInt!
  tagline: String
  title: String!
}


type Person @authentication(operations: [CREATE, DELETE, UPDATE], jwt: { roles: { includes: "acmeGraphQLReadWrite" } } )  @node   {
  actedInMovies: [Movie!]!
    @relationship(
      type: "ACTED_IN"
      direction: OUT
      properties: "ActedInProperties"
    )
  born: BigInt @authorization(validate: [ { where: { jwt: { roles: { includes: "acmeGraphQLSensitive" } } } } ])
  directedMovies: [Movie!]! @relationship(type: "DIRECTED", direction: OUT)
  followsPeople: [Person!]! @relationship(type: "FOLLOWS", direction: OUT)
  name: String!
  peopleFollows: [Person!]! @relationship(type: "FOLLOWS", direction: IN)
  producedMovies: [Movie!]! @relationship(type: "PRODUCED", direction: OUT)
  reviewedMovies: [Movie!]!
    @relationship(
      type: "REVIEWED"
      direction: OUT
      properties: "ReviewedProperties"
    )
  wroteMovies: [Movie!]! @relationship(type: "WROTE", direction: OUT)
}

type ReviewedProperties @relationshipProperties {
  rating: BigInt!
  summary: String!
}
```

If someone at ACME Corp tries to make a change and lacks the necessary claim in their JWT, they get this response

```JSON
{
    "errors": [
        {
            "message": "Unauthenticated",
            "locations": [
                {
                    "line": 2,
                    "column": 5
                }
            ],
            "path": [
                "createPeople"
            ]
        }
    ],
    "data": null
}
```

## Summary

ACME Corparation now has all of the three outcomes it was looking for. GraphQL API fits into it's SSO system whilst restricting access to those who have the "acmeGraphQLUser" claim in their JWT. Their senstive data requires an additional claim, "acmeGraphQLSensitive", and any change to the People data needs "acmeGraphQLReadWrite"

This is a gentle introduction controlling data access using claims found in JWT. There's more flexibilty available by using logical operations such as OR , AND and this is covered in the [documentation](https://neo4j.com/docs/graphql)

A pragmatic approach is recommended when it comes to applying this in a production environment. You need to carefully balance operational overhead and security or you can end up diving down this rabiit hole and end up a guest at the Mad Hatters Tea party.

Next time I'll be covering using this approach with a using a client initiated JWT from a web browser app.
