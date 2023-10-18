from requests.auth import HTTPBasicAuth
import requests
import json


def get_oauth_token(aura_client_id, aura_client_secret):
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
        auth=HTTPBasicAuth(aura_client_id, aura_client_secret),
        timeout=10
    )
    try:
        response.raise_for_status()
    except Exception as e:
        print("Authentication request was not succesful.")
        raise e

    return response.json()["access_token"]


def call_endpoint(aura_endpoint, method, aura_token, **kwargs):
    base_url = "https://api.neo4j.io/v1"
    full_url = f"{base_url}{aura_endpoint}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {aura_token}"
    }

    response = requests.request(method, full_url, headers=headers, timeout=10,  **kwargs)

    try:
        response.raise_for_status()
    except Exception as e:
        print("Request was not succesful.")
        raise e

    return response.json()


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

main()
