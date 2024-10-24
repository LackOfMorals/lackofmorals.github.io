---
layout: post
title: "Applications, Tokens and Neo4j Query API "
description: "A gude to using tokens with application and Neo4j Query API"
tags: Neo4j PM DevEx QueryAPI SSO Token
---

# Applications, Tokens and Neo4j Query API

Using tokens with Applications and Neo4j Query API for auth
================================================

In a previous blog post I discussed a web application obtaining and using a token with Neo4j Query API as a result of a user successfully authenticating.  This entry looks at what would be involved for an application to obtain a token and use it with Neo4j Query API.  

**Plot spoiler** - it's very similar.

Many organisations prefer a token based approach, one reason for this is the limited lifespan and scope of token which helps to reduce risk if it is intercepted.  Lets look at how this can be achieved.

We will need

* A free Okta developer account

* Neo4j Enterprise running in Docker locally

* Docker installed

* A local copy of curl

* Text editor

## Neo4j Docker image

### Install & Run the Neo4j Docker image

**Note**:  If you are not comfortable with the values used for the username & password , change NEO4J_AUTH=neo4j/password to  something that works for you.

The neo4j docker image will use folders in the home directory.  Create those first

```Bash
mkdir -p ~/neo4j/conf
mkdir -p ~/neo4j/data
mkdir -p ~/neo4j/logs
```
  
Tell Docker to download and run Neo4j

```Bash
docker run -dt \
--name=neo4jDb \
--publish=7474:7474 \
--publish=7687:7687 \
--volume=$HOME/neo4j/data:/data \
--volume=$HOME/neo4j/conf:/conf \
--volume=$HOME/neo4j/logs:/logs \
--env=NEO4J_ACCEPT_LICENSE_AGREEMENT=yes \
--env=NEO4J_AUTH=neo4j/password \
neo4j:enterprise
```

### Test

Check Neo4j is up and running by going to this local URL [http://localhost:7474/browser](http://localhost:7474/browser)

This should show you the Browser console for Neo4j.  Auth using neo4j for the user and password for the password.

* * *

Okta configuration
==================

This requires configuration work in two areas of the Okta console; Applications and  Security and also obtaining the developer account Okta Domain.  

Okta developer account domain
------------

Before starting any work , we need the developer account okta domain.  Locate this by going to the top right and selecting your account.  From the drop down menu , you will see your email address and immediately underneath the domain for your developer account.  Make a note of this.

Applications
------------

**Applications** -> **Create App Integration** -> **API Services**

* Provide a name e.g neo4j m2m query api for API Service

When the new API Service is shown :-

### General

Client credentials

* Client ID: Copy the client id as this will be needed later

* Client authentication: Client secret

CLIENT SECRETS

* Client secret:   Copy this as it also will be needed later

General Setting

* Proof of possession :  Make sure Require Demonstrating Proof of Possession (DPoP) header in token requests is not selected

Security
--------

**Security** -> **API** -> **Add Authorization Server**

* Name:  Give this a meaningful name e.g neo4j query api

* Audience: This will form part of the generated token.  Suggest using that is short and descriptive e.g neo4j-query-api.  This will be needed for Neo4j configuration

* Description: Enter some words that describe what this is for

The newly created authorization server is now displayed.

The next step is to create a Scope which will be used in the Neo4j configuration to map to a Neo4j role.  This determines the access level that will be granted.

Select **Scopes**

### Add Scope

* Name: Provide a name for the scope e.g Neo4jDba

* Display phrase:  Enter what this is for e.g DBA access

* Description: Longer description e.g DBA level access for Neo4j

* User consent:  Implicit

* Block services :  Not checked

* Default scope:  If checked, this will be given to any token request that does not explicitly ask for a scope.  Advise that this is not checked.

* Metadata:  The scope will be included in the response from the well known API and hence visible.  Advise that this is not checked.

Select **Create**

The newly created scope will now be shown in the table.  Make a note of the **Issuer URI**

Takeways from Okta confiuration work
--------

Once Okta is configured, we will have

* Developer account domain

* Client ID

* Client Secret

* Issuer URI

* Audience

* Scope

* * *

Neo4j configuration
-------------------

It's entirely possible for Neo4j to have more than one configured ODIC provider.  It's also possible to hide an entry from users of the Neo4j web Browser console, something that we will need to do as the configuration for an application to use token is not going to work for a user.

This is line that we'll need to use with our OIDC configuration entry
```dbms.ecurity.oidc.YOUR_OIDC_ENTYR_NAME.visible=false```

Edit neo4j.conf and add this in the OIDC section swapping out these values for yours from Okta.

* YOUR_AUDIENCE_ID_FROM_OKTA

* YOUR_CLIENT_ID_FROM_OKTA

* YOUR_CLIENT_SECRET_ID_FROM_OKTA

* YOUR_ISSUER_URI_FROM_OKTA

* YOUR_SCOPE_FROM_OKTA

```Text
# Okta m2m settings
dbms.ecurity.oidc.m2m.visible=false
dbms.security.oidc.m2m.display_name=m2m
dbms.security.oidc.m2m.auth_flow=pkce
dbms.security.oidc.m2m.well_known_discovery_uri=YOUR_ISSUER_URI_FROM_OKTA/.well-known/openid-configuration
dbms.security.oidc.m2m.audience=YOUR_AUDIENCE_ID_FROM_OKTA
dbms.security.oidc.m2m.client_id=YOUR_CLIENT_ID_FROM_OKTA
dbms.security.oidc.m2m.claims.groups=scp
dbms.security.oidc.m2m.claims.username=sub
dbms.security.oidc.m2m.params=client_id=YOUR_CLIENT_ID_FROM_OKTA;response_type=code;scope=openid profile scp
dbms.security.oidc.m2m.authorization.group_to_role_mapping=YOUR_SCOPE_FROM_OKTA=admin
```

Save the file and then restart Neo4j.

```Bash
docker restart neo4jDb
```

* * *

Getting a token from Okta to use with Neo4j Query API
-----------------------------------------

A token to use with the Query API is obtained from **https://YOUR_DEVELOPER_ACCOUNT_DOMAIN/oauth2/default/v1/token**  as illustrated with this example using CURL

Replace

* YOUR_DEVELOPER_ACCOUNT_DOMAIN

* YOUR_SCOPE_FROM_OKTA

* YOUR_CLIENT_ID_FROM_OKTA

* YOUR_CLIENT_SECRET_ID_FROM_OKTA

with values from the Okta configuration

```Bash
curl --request POST \

--url https://YOUR_DEVELOPER_ACCOUNT_DOMAIN/oauth2/default/v1/token \
--header 'accept: application/json' \
--header 'cache-control: no-cache' \
--header 'content-type: application/x-www-form-urlencoded' \
--data 'grant_type=client_credentials&scope=YOUR_SCOPE_FROM_OKTA' \
-u CLIENT_ID:CLIENT_SECRET
```

This should result in a response that looks similar to this

```JSON
{
"token_type": "Bearer",
"expires_in": 3600,
"access_token": "eyJraWQiOiJfM0lPdk9tUEJGN3hKN2FPbHNmYzVKWmlGWXdua1Q4WHY5ZG9hYk9JOEhFIiwiYWxnIjoiUlMyNTYifQ.eyJ2ZXIiOjEsImp0aSI6IkFULmZkYjJ3eGZPMFJaSmFiUDNIUkxGLVl6VFpHczhkTVFYUnJLWU02aUFlemsiLCJpc3MiOiJodHRwczovL2Rldi04NTI1NzgzOC5va3RhLmNvbS9vYXV0aDIvZGVmYXVsdCIsImF1ZCI6Im5lbzRqLWF1ZCIsImlhdCI6MTcyOTYzMzA2MiwiZXhwIjoxNzI5NjM2NjYyLCJjaWQiOiIwb2FrZ2R4eHJyM3FiVkhFRDVkNyIsInNjcCI6WyJuZW80akRiYSJdLCJzdWIiOiIwb2FrZ2R4eHJyM3FiVkhFRDVkNyJ9.CGHx-dnhKd1d_i_hEroNHOCPUYROh0wqz2EuKCDYuieiIkqx9sG1Z8f1hnb96FL2uyyTL2bpAILiG3-85urVeG-6R5Dazf87opM5IyLhYTxboM5VjF3xsKsUiSjIQBP7jsCqHFxCsBpOB2nUSxzmk3NZpVhV2oZJK5-WBl1wCj7ttyAeuZ7sbm44SdrdIz9pmf6RmTQ30nBexZ6ccNx7YxxZZyo2jJeRvNDOn-yRpydkOOOqe7kR1qk7qhG14cKLQBgmx2RL5DAxG9ZJOHh1dUcOE87duhT3uD476JmcmS8DG589CCO3bMcmORYLkArf_5QFWW-bG8FJy5UGJVffFA",
"scope": "neo4jDba"
}
```
  
From this we use the value of the access_token key to use with the Query API.

* * *

Using a token with the Query API
--------------------------------

Replace

* YOUR_ACCESS_TOKEN

with the value obtained from Okta

```Bash

curl -X POST <http://localhost:7474/db/neo4j/query/v2> \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{"statement": "MATCH (n) RETURN n LIMIT 1"}'
```

A response with a single entry from your Neo4j graph will be returned

* * *

## An example Python application

```Python
"""
 * Copyright (c) 2024-Present, Neo4j. and/or its affiliates. All rights reserved.
 *
 * You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *
 * See the License for the specific language governing permissions and limitations under the License.
"""

# -*- coding: utf-8 -*-
# Generic/Built-in
import json
from typing import Dict

# Other Libs
from requests import Request, Session
from requests.auth import HTTPBasicAuth, AuthBase

# Owned

# Configuration values
class MyConfiguration():
    CLIENT_ID = "YOUR_CLIENT_ID_FROM_OKTA"
    CLIENT_SECRET = "YOUR_CLIENT_SECRET_FROM_OKTA"
    OKTA_TOKEN_URI = "https://YOUR_DEVELOPER_ACCOUNT_DOMAIN/oauth2/default/v1/token"
    OKTA_SCOPE = "YOUR_SCOPE_FROM_OKTA"
    NEO4J_QUERY_URI = "YOUR_NEO4j_QUERY_API_URL"

# Returns Auth object for use with Python requests 
# that uses our token from Okta
class BearerAuth(AuthBase):
   """
   Returns a request header that uses Bearer token for auth
    
   :return: Header that uses Bearer token
   """
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


def make_request(request_url: str, request_operation: str, request_headers: dict, request_body,
                 request_auth: AuthBase) -> Dict:
    """
   Makes a request to Aura API and returns the JSON from the response
   :param request_url The path to the endpoint to make a request to
   :param request_operation The HTTP operation to perform for the request
   :param request_headers  A dictionary containing headers for the request
   :param request_body  The body of the request
   :param request_auth  Auth to use with the request
   :return: The JSON response back as a Python Dict
   """

    # A session will be used to avoid having to make a new connection with each request
    request_session = Session()

    # Prepare our request
    prepared_request = Request(request_operation, request_url, headers=request_headers, auth=request_auth,
                               data=request_body).prepare()

    try:
        # Send the request
        response = request_session.send(prepared_request)

    except Exception as e:
        print("%s raised an error: \n%s", aura_api_request, e)
        raise

    else:
        return response.json()


def get_token_from_okta(url: str, client_id: str, client_secret: str, token_scope: str):
    """
   Gets a token from Okta
   :param url: URL for Okta token
   :param client_id: Okta client id
   :param client_secret: Okta client secret
   :param token_scope: Okta scope

   """
    # Ask for a bearer token using the client id and client secret from Okta

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    body = {"grant_type": "client_credentials", "scope": token_scope}

    okta_response = make_request(url, 'POST', headers, body, HTTPBasicAuth(client_id, client_secret))

    if 'access_token' in okta_response:
        return okta_response['access_token']
    else:
        return None


def get_data_from_neo4j(cypher_statement: str, query_api_url: str, token_from_okta: str) -> Dict:
    """
    Gets a data from Neo4j Query API using a bearer token for auth
    :param cypher_statement: Cypher statement in the form of a dictionary
    :param query_api_url:URL for Neo4j Query API
    :param token_from_okta: token from Okta
    :return A dictionary containing the data from Neo4j
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    neo4j_response = make_request(query_api_url, 'POST', headers, cypher_statement, BearerAuth(token_from_okta))

    if 'data' in neo4j_response:
        return neo4j_response['data']
    else:
        return {}

    pass


def showcase_token_with_queryapi(config):

    okta_token = get_token_from_okta(config.OKTA_TOKEN_URI, config.CLIENT_ID, config.CLIENT_SECRET, config.OKTA_SCOPE)

    neo4j_query = {"statement": "MATCH (n) RETURN n LIMIT 1"}

    neo4j_data = get_data_from_neo4j(json.dumps(neo4j_query), config.NEO4J_QUERY_URI, okta_token)

    print(f"Data from Neo4j: {neo4j_data['values'][0]}")


if __name__ == '__main__':
    showcase_token_with_queryapi(MyConfiguration)


```
