+++
title = "A Python SDK for the Neo4j Aura API"
description = "A Python SDK for Neo4j Aura API"
date = "2026-09-30"
tags = ["Claude", "PM","Python","Aura API","Neo4j"]
draft = false
+++

Earlier this year I shipped a [SDK for Go](https://github.com/neo4j-contrib/aura-go-sdk) in Neo4js contributors repository.  It's proved popular and is currently the 3rd most used mechanism, the top two being Python based, for working with the Aura API.

I've now instructed Claude Code to create a Python SDk for the Aura API. The two top languages applications using our Aura API are written in is Python and Go so there are now SDKs for both.

But that's not the only reason for doing this.

AI has proven rather adapt at coding. We used it almost exclusively to build to [neo4j-cli](https://neo4j.sh).  I'm really interested if it can be used to build SDKs for the Aura API by

- Supply the definition of the surface. One thing I'd like to do is to maintain a consistent feel between the SDKs whilst confirming to best practices for each language.  So if you've used the Go SDK , it's not a huge step over to the Python SDK.
- Describe the endpoints that the SDK wraps.  This would be in the form of an OpenAPI specificaiton
- Define the architecture / design patterns to use along with any libraries to be used e.g slog for Go logging, httpx for Python http networking
- Iterate , refininig the SDK making sure it aligns with usage expected usage patterns, security reviews etc..

Once the SDK is ready, we can build tests that treat the SDK as a sealed box to ensure what ever the AI builds - and to a certain degree I don't care what is inside the sealed box - the surface is maintained.

If this holds, then we can get the AI to keep the SDK updated with minimal oversight.

## Python Aura SDK

THe process I just described has been used to build a Python SDK for Aura.  Once I'm comfortable with surface - I'll be diving back into Python after using Go for the last few months and exercising the SDK - then the final bit will be to build the surface conformity tests.  As mentioned, these will be used to ensure consistency as the SDK evolves with the Aura API.

With the SDK, you can use the capabilities found in V1 of the Aura API.  Want to see how many instances you have? 

Install the SDK
Requires Python 3.11 or later.

```bash
pip install aura-python-sdk
```

```python
import aura_python_sdk as aura

with aura.AuraClient(client_id="your-client-id", client_secret="your-client-secret") as client:
    for instance in client.instances.list():
        print(f"{instance.name} ({instance.id})")
```

Any feedback, open an Issue in Github 

Laters
