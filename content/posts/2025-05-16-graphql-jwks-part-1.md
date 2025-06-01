+++
date = '2025-05-16T00:00:00+01:00'
draft = true
title = 'An introduction to using JWTs with GraphQL for AuraDB - Part One'
+++

There are two options ( we're looking at another token based approach for the future ) to control access to a GraphQL for AuraDB endpoint

- API Key
- JWT

Using APIs keys are asimple, straight forward approach to control access to a GraphQL API and work really well for development environments. For production environments we recommend the use of a 3rd party indentity provider that manages tokens in the form of JWTs as these provide more flexibility when securing access to your GraphQL. Additionally, JWTs enable the use of rules within your type definitions for authentication and authorisation.

In this blog post I walk through an example covering the setup of the GraphQL API itself and the indentity provider. A follow on post will look at providing granula control using type defintion directives, @authentication and @authorization. That example is using machine to machine token as it's relatively straight forward. The last, and final post in this series will show how user initiated token flow - Single Sign On in a browser - can be used.

Lets get started

---

## Pre-reqs

- A Okta developer account. These are currently free!

- AuraDB Professional, AuraDB Professional Trial or AuraDB Business Critical with Movies example graph

- GraphQL for AuraDB deployed

- A local copy of curl

## Okta

In Okta, we need to :-

- Create and configure a new Application
- Create and configure a new Security Authorisation Server

Go ahead and sign into your Okta Developer account

### Okta -> Application

Once signed in to Okta, select **Applications** -> **Create App Integration**

- Select **API Services**
- Click **Next**

When you're at the **New API Services App Integration** display

- Provide a name e.g tokenForFGraphQLAPI
- Select **Save**

The configuration screen for the new Application will be shown. Make changes as described below

**General section**
Client credentials

- Client ID: Copy the client id as this will be needed later

- Client authentication: Client secret

Client Secret

- Client secret:   Copy this as it also will be needed later

General Setting

- Proof of possession :  Make sure Require Demonstrating Proof of Possession (DPoP) header in token requests is not selected

Make sure you select **Save** when done.

### Oktas -> Security

Select **Security** -> **API** -> **Add Authorization Server**

Now make these changes to the configuration

- Name:  Give this a meaningful name e.g neo4j query api

- Audience: This will form part of the generated token.  Suggest using that is short and descriptive e.g neo4j-query-api.  This will be needed for Neo4j configuration

- Description: Enter some words that describe what this is for

The newly created authorization server is now displayed. Changes are need to the Scope and Rules

The next step is to create a Scope which will be used later on in the next blog to determine access.

**Scopes**
Select **Scopes** -> **Add Scope**

- Name: Provide a name for the scope e.g graphQLUser

- Display phrase:  Enter what this is for e.g DBA access

- Description: Longer description e.g DBA level access for Neo4j

- User consent:  Implicit

- Block services :  Not checked

- Default scope:  If checked, this will be given to any token request that does not explicitly ask for a scope.  Advise that this is not checked.

- Metadata:  The scope will be included in the response from the well known API and hence visible.  Advise that this is not checked.

Select **Create**

The newly created scope will now be shown in the table.  Make a note of the **Issuer URI**

**Access Polices**
Select **Add New Access Policy** and complete as follows

- Name: short name
- Description: description what this does ( mandatory )
- Assign to: All Clients

A new, blank policy is created. A rule is needed to permit access.

Select **Add rule**

- Name: short name

Leave everything else as defaults. Select **Create rule** to finish this step.

Then go back to list the of API Authorization Servers. Make a note of the Issuer URI for the auth server that you just created.

### Takeways from Okta configuration work

Now Okta is configured, we will have

- Client ID

- Client Secret

- Issuer URI

- Scopes

### Test Okta by getting a token

A token to use with the Query API is obtained from **ISSUER_URI/v1/token**  as illustrated with this example using CURL

Replace the following with your values from Okta with the curl command

- ISSUER_URI
- SCOPE
- CLIENT_ID
- CLIENT_SECRET_ID

curl command to request a token

```Bash
curl --request POST \

--url ISSUER_URI/v1/token \
--header 'accept: application/json' \
--header 'cache-control: no-cache' \
--header 'content-type: application/x-www-form-urlencoded' \
--data 'grant_type=client_credentials&scope=SCOPE' \
-u CLIENT_ID:CLIENT_SECRET
```

This should result in a response that looks similar to this

```text
{
"token_type": "Bearer",
"expires_in": 3600,
"access_token": "eyJraWQiOiJfM0lPdk9tUEJGN3hKN2FPbHNmYzVKWmlGWXdua1Q4WHY5ZG9hYk9JOEhFIiwiYWxnIjoiUlMyNTYifQ.eyJ2ZXIiOjEsImp0aSI6IkFULmZkYjJ3eGZPMFJaSmFiUDNIUkxGLVl6VFpHczhkTVFYUnJLWU02aUFlemsiLCJpc3MiOiJodHRwczovL2Rldi04NTI1NzgzOC5va3RhLmNvbS9vYXV0aDIvZGVmYXVsdCIsImF1ZCI6Im5lbzRqLWF1ZCIsImlhdCI6MTcyOTYzMzA2MiwiZXhwIjoxNzI5NjM2NjYyLCJjaWQiOiIwb2FrZ2R4eHJyM3FiVkhFRDVkNyIsInNjcCI6WyJuZW80akRiYSJdLCJzdWIiOiIwb2FrZ2R4eHJyM3FiVkhFRDVkNyJ9.CGHx-dnhKd1d_i_hEroNHOCPUYROh0wqz2EuKCDYuieiIkqx9sG1Z8f1hnb96FL2uyyTL2bpAILiG3-85urVeG-6R5Dazf87opM5IyLhYTxboM5VjF3xsKsUiSjIQBP7jsCqHFxCsBpOB2nUSxzmk3NZpVhV2oZJK5-WBl1wCj7ttyAeuZ7sbm44SdrdIz9pmf6RmTQ30nBexZ6ccNx7YxxZZyo2jJeRvNDOn-yRpydkOOOqe7kR1qk7qhG14cKLQBgmx2RL5DAxG9ZJOHh1dUcOE87duhT3uD476JmcmS8DG589CCO3bMcmORYLkArf_5QFWW-bG8FJy5UGJVffFA",
"scope": "graphQLUser"
}
```

From this we will use the value of the access_token key to use with the graphQL

---

## GraphQL for AuraDB

When creating a GraphQL API for an AuraDB, you will need type definitions.

The type definitions given here are those for the Movies example graph.

```Text
type ActedInProperties @relationshipProperties {
  roles: [String!]!
}

type Movie @node {
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

As we are using JWT, we will need to supply the Okta endpoint that is used to validate the incoming JWT. This is often referred to as a JWKS endpoint.

With Okta, this is your ISSUER_URI appended with /v1/keys

Lets create the GraphQL API

### Creating the Graph QL

> Note: Assumes you have an AuraDB provisioned with the Movies example graph. If you haven't done this, do it now before proceeding.

Log into Aura.

Select **Data API**

Then choose **Create API**

You are shown the create API screen. There's a lot to complete so we will go section by section

**Details**

- API Name: Provide a short name
- Instance: Select the AuraDB to use with your GraphQL API
- Instance Username: Provide the username to access the AuraDB. Normally this is Neo4j
- Instance Password: Provide the associated password for the username

**Type Definitions**
Copy the Type Definitions from earlier and paste them in

**Cross origin policy**
Nothing to see here for now as a browser is not being used to access our GraphQL API

**Authentication providers**

- Type: JWKS
- Name: Provide a descriptive name
- URL: The JWKS endpoint. This is your ISSUER_URI appended with /v1/keys

> Note: The JWKS endpoint could be different if you're not using Okta. Check this for your identity provider if that is the case

**Sizing**
Only 256Mb is availabel at time of writing

When you've done all of this, select **Save**

Make sure you note the URL for the GraphQL API.

It will take a few moments to provision the GraphQL API

Select **Data API** to see the current status. Whent the status becomes 'ready' we're ready to test

## Testing

Use curl to get the token. Replace ISSUER_URI, SCOPE, CLIENT_ID, CLIENT_SECRET_ID with your values

```Bash
curl --request POST \

--url ISSUER_URI/v1/token \
--header 'accept: application/json' \
--header 'cache-control: no-cache' \
--header 'content-type: application/x-www-form-urlencoded' \
--data 'grant_type=client_credentials&scope=SCOPE' \
-u CLIENT_ID:CLIENT_SECRET
```

From the response, copy the value for access_token

Lets run a simple graphql query with the token

```Bash
curl --location 'GRAPHQL_API_URI' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer TOKEN_FROM_OKTA \
--data '{"query":"query MoviesAndDirectors{\n  movies(limit: 5 )\n{\n    released\n    title\n    peopleDirected { name }\n    peopleActedIn { name }\n  }\n}","variables":{}}'
```

This should return 5 movies and their directors
