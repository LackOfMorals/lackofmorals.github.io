---
layout: post
title: "Using token with GraphQL for AuraDB "
description: "Part one of a guide to using token with GraphQL for AuraDB"
tags: Neo4j PM DevEx QueryAPI SSO Token
---

# Tokens - nice

In a previous blog post I discussed a web application obtaining and using a token with Neo4j Query API as a result of a user successfully authenticating. This entry looks at what would be involved for an application to obtain a token and use it with Neo4j Query API.

**Plot spoiler** - it's very similar.

Many organisations prefer a token based approach, one reason for this is the limited lifespan and scope of token which helps to reduce risk if it is intercepted. Lets look at how this can be achieved.

We will need

- A free Okta developer account

- AuraDB Professional, AuraDB Professional Trial or AuraDB Business Critical

- GraphQL for AuraDB deployed

- A local copy of curl

- Text editor

## Okta

Okta has a free offering for development purposes. We'll take advantage of this and use Okta for our identity provider.

In Okta,we will need to :-

- Create and configure a new Application
- Create and configure a new Security Authorisation Server

Go ahead and sign into your Okta Developer account

### Application

Once signed in, select **Applications** -> **Create App Integration** -> **API Services**

- Provide a name e.g tokenForFGraphQLAPI

The configuration for the new Application will be shown. Make changes as described below

**General**

Client credentials

- Client ID: Copy the client id as this will be needed later

- Client authentication: Client secret

CLIENT SECRETS

- Client secret:   Copy this as it also will be needed later

General Setting

- Proof of possession :  Make sure Require Demonstrating Proof of Possession (DPoP) header in token requests is not selected

### Security

Select **Security** -> **API** -> **Add Authorization Server**

Now make these changes to the configuration

- Name:  Give this a meaningful name e.g neo4j query api

- Audience: This will form part of the generated token.  Suggest using that is short and descriptive e.g neo4j-query-api.  This will be needed for Neo4j configuration

- Description: Enter some words that describe what this is for

The newly created authorization server is now displayed. Changes are need to the Scope and Rules

The next step is to create a Scope which will be used in the Neo4j configuration to map to a Neo4j role.  This determines the access level that will be granted.

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

A token to use with the Query API is obtained from **https://YOUR_DEVELOPER_ACCOUNT_DOMAIN/oauth2/default/v1/token**  as illustrated with this example using CURL

Replace the following with your values from Okta with the curl command

- ISSUER_URI

- SCOPE

- CLIENT_ID

- CLIENT_SECRET_ID

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

```JSON
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
