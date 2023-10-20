# It all about the REST

![My sleeping cat](/img/mySleepingCat.png)

Neo4j DB as a Service ( DBaaS ) , Aura, now has a RESTful like API for provisioning.   The full details of the API in long form are in the  [documentation](https://neo4j.com/docs/aura/platform/api/specification/); in short it's a set of endpoints that provide for CRUD operations. You can try the Aura API from the documentation.  Here we're going to dig in and write code to do the needful.

At the time of writing ( Friday 20th October ) the API is for Aura Enterprise customers and I'm reliably informed that the audience will be expanded in the next couple of months.

To show how the Aura API can be used, we'll create a basic Python application that creates a new Aura instance. 

We'll walk through the various bits of Python code before putting it together.  If you just want the code, jump to the bottom of this post where you can download it. 

This is not a short read and you would be advised to have a bio break, get a hot beverage and settle in for some rough and ready coding. 


## To the Aura Console
To get started with the Aura API you'll need to obtain a client id and client secret.  BTW - I'm assuming that you already have an Aura Enterprise account.

After you have logged in , drive the mouse pointer to the top right of the Aura of the console and click on your account name

![Aura Account](/img/aura/auraConsoleAcccount.png)

Then choose _Account Details_ and then _Create_.  This will bring up the dialog for a new client id and client secret.  Make sure you copy these down and store them securely.

Armed with these two pieces of information we can now move onto the Aura API.


## Let me see some ID
Aura API is protected against people with flexbile morals by a time limited OAuth token which is obtained by using the client id and client secret.  OAuth is a well documented mechanism to use for this and covering that is beyond the confines of this blog post.  Go Google it if you're interested. 

Once we have an OAuth token, and it's only valid for a limited time, we can go ahead and use the Aura API.  

**Important** You must send the OAuth token with _every_ request that you make.

```
def get_oauth_token(aura_client_id,aura_client_secret):
    """
    Returns oauth token for use with Aura API

    params:
    client_id , required, string client id obtained from Aura console
    client_secret, required, string client secret obtained from Aura console

    """

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}
    url = "https://api.neo4j.io/oauth/token"

    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=data,
        auth=HTTPBasicAuth(aura_client_id,aura_client_secret),
        timeout=10
    )
    try:
        response.raise_for_status()
    except Exception as e:
        print("Authentication request was not succesful.")
        raise e

    return response.json()["access_token"]
```

Now we can get the OAuth token, what's next?


## Endpoints , oh the endpoints
 If you did take a look at the Aura documentation, you'll notice that there's several endpoints that available for various operations. For our purposes, we'll need to use just two:-

 -  /tenants
 -  /instances

As we have two endpoints to use, it will be helpful to have a function that takes care of network communication otherwise we'll be duplicating code.  Also you can use this yourself , although you may want to make some improvements.
 
 We'll write a function that takes the Aura endpoint URL we want to talk to, the HTTP method, our oauth token and then return the response as a Python dictionary. 

```
def call_endpoint(aura_endpoint, method, aura_token):
    base_url = "https://api.neo4j.io/v1"
    full_url = f"{base_url}{aura_endpoint}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {aura_token}"
    }

    response = requests.request(method, full_url, headers=headers, timeout=10)

    try:
        response.raise_for_status()
    except Exception as e:
        print("Request was not succesful.")
        raise e

    return response.json()
```

## You can't park there
Creating an instance requires a number of items to be given , one of which is the ID of the tenant for the instance. This makes sure we create the Aura instance in the right place. Could be awkward if they started turning up in random tenants within our Aura organisation;  the explaining would be needed. 

We'll use the /tenants endpoint which returns all tenants with ID.  With that we can look up the tenant ID based on the tenant name that we want to use. To find the tenant name , just look in the Aura console at top.  Using the screenshot in this post, this would be 'MyTenant' 

Lets write a function to get the tenant list and return the id based on the tenant name.

```
def get_tenant_id(tenant_name,token):
    """
    For a given tenant name, return it's id

    params:
    tenant_name, required, string, the name of the tenant to retrieve the id for
    """
    aura_tenants = call_endpoint('/tenants', 'GET', token)

    for entry in aura_tenants['data']:
        if entry['name'] == tenant_name:
            tenant_id = entry['id']
        else:
            tenant_id = 'Not found'

    return tenant_id
```
Notice that we're passing the token , something that we'll need to do for every endpoint that we use

With the ID, we can now create the Aura instance. 

You can guess what's coming next

## Yet another function
This will create an Aura instance to a pre-determined specification.  We'll  need to pass the tenant name, oauth token and the name we want for our new instance. 

To use the endpoint for creating an instance, we will need

- Instance name
- The cloud provider
- Cloud provider reqion to use
- Memory
- Tenant ID
- Type of Aura instance
- Neo4j version

Tenant ID will be obtained from get_tenant_id.  Everything else will come from the supplied parameters or be set directly within the function.

```
def create_instance(aura_token, aura_tenant, aura_instance_name):
    """
    Creates an Aura instance in the given tenant.
    Aura instance will have 2Gb memory, 1 CPU and 4Gb of storage using Google Cloud in europe-west1

    params:
    aura_token, string , required, a valid oauth token for Aura
    aura_tenant, string, the name of the tenant to create the instance in
    """

    # Get the tenant_id
    tenant_id = get_tenant_id(aura_tenant, aura_token)

    if tenant_id != 'Not found':
        spec = {
            "version": "5",
            "region": "europe-west1",
            "memory": "2GB",
            "name": aura_instance_name,
            "type": "enterprise-db",
            "tenant_id": tenant_id,
            "cloud_provider": "gcp"
        }

        create_response = call_endpoint('/instances','POST',aura_token,data=json.dumps(spec))

        return create_response

    return
```

If everthing works, and why would it not, then the endpoint returns a JSON document with the details for our new instance.  Our Python code translates this into a Python dictionary. 

About time we put this together

## Main event
Here's the main function that calls the functions and prints out the result from creating a new instance

```
def main():
    # Get an oauth token
    aura_api_token = get_oauth_token('YOUR CLIENT ID', 'YOUR CLIENT SECRET')
    # create the new instance
    new_instance_response = create_instance(aura_api_token,'YOUR TENANT NAME','YOUR INSTANCE NAME')

    #Print out the results
    if 'data' in new_instance_response:
        print(f"Instance ID {new_instance_response['data']['id']}")
        print(f"Username {new_instance_response['data']['username']}")
        print(f"Password {new_instance_response['data']['password']}")
        print(f"Connection URI {new_instance_response['data']['connection_url']}")
    else:
        print('Bad things happened')
```

## That's it folks
The only thing left to do is to put all of this inside a Python application

You can copy and paste the functions after the imports but before the call to main().  Hint: There's a big gap - put them there !

If you can't be bothered then the entire Python code can be download : [Create an new instance](/code/2023-10-20_code.py)

```
from requests.auth import HTTPBasicAuth
import requests
import json

# Paste the functions from this point





# But before here
main()
```

If you've kept going to the end, I hope this has been useful to you

To demonstrate what can be done with the Aura API, we've built a CLI tool for Aura on top of it. You can download the Aura CLI from [Neo4j Labs](https://neo4j.com/labs/aura-cli/)