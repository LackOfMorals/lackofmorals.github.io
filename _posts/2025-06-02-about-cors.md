---
layout: post
title: "A guide to not loosing your shit over CORS"
description: "CORS and GraphQL for AuraDB"
tags: Neo4j PM DevEx GraphQL
---

## CORs?

Dear Reader,

Take a moment and load web page in your browser. Then jump over into the browsers developer tools and look at all of the different domains that page is connecting to. This reflects the need of a web page to communicate across different domains to function properly ( although I'd bet a lot of what you can see right now is advertising or tracking ).

Allowing cross domain connects can be of concern when it comes to security. But there's something we can do about that. Enter **CORS**—Cross-Origin Resource Sharing, a browser feature, that controls how and when web pages can make requests to domains other than their own.

But CORS can also be a pain in the arse for Developers creating those web applications if CORs has not been configured correctly , or not at all, on the server your browser wants to talk to.

Like the GraphQL for AurDB API.

Before we jump into how to configure CORS for GraphQL for AurDB API, let first understand some more about CORS itself.

Or you can skip that and just get into it.

Let me hear you make decisions
Without your television
(c) Depeche Mode, Stripped

---

## What is CORS?

CORS is a security mechanism implemented by web browsers that restricts web pages from making requests to a domain different from the one that served the web page. This policy is called the **Same-Origin Policy (SOP)**, and CORS is a way to safely relax it.

Without CORS, your frontend JavaScript running on `https://www.myapp.com` would be blocked from making a request to `https://api.ineed.com`, even if the API was publicly available without requiring authentication of any kind. CORS allows `api.ineed.com` to explicitly declare which origins are allowed to access its resources.

This only applies to web browsers like Chrome, Firefox etc.. as CORS is enforced by the _browser_. CORS does not come into play when calling an API directly from a non-web application such as CURL

> Note: It's the **server** that informs the **browser** if access will be permitted from it's origin ( i.e the domain or host ) and not the other way around. CORS is therefore configure on the _server_.

---

## Why Is CORS Useful?

1. **Prevents Malicious Cross-Domain Requests**
   CORS helps mitigate **cross-site request forgery (CSRF)** by ensuring that only trusted domains can access sensitive APIs. Trusted domains are configured as part of the Same-Origin Policy

2. **Enables Safe API Sharing**
   Modern applications often use microservices, CDNs, or third-party APIs. CORS enables these services to be accessed securely and intentionally, without exposing users to unwanted risk.

3. **Encourages Explicit Permissions**
   Developers have to think about the individual domains have to be allowed in order to make their web app work. This makes CORS policies intentional as wildwards are not permitted.

---

## CORs and GraphQL for AuraDB

By default GraphQL for AuraDB APIs block all requests from any origin. This will need adjusting for any web application that needs to make a request to GraphQL endpoint. This includes development environments, e.g node.js, that serves content on <http://localhost> or similar or when using web based tooling for GraphQL APIs such as [Apollo Studio](https://studio.apollographql.com/)

> Note: The domain entered in the CORs policy must be an exact match. For example, <http://localhost> is not the same as <http://localhost:3000/>. Wildcards are not supported.

To set the CORS policy, When creating the GraphQL API or modifying an existing one, you need to go scroll down the configuration page until you reach the CORS policy section

![](/img/cors-graphql-for-auradb/create-cors-policy.png)

To add a CORS policy entry , enter the exact domain, inclusive of http / https and any port number, in the **Origin box**. If you need multiple entries, select **Add allowed origin**

## Best Practices

- **Be specific with allowed origins** rather than using wildcards.
- **Limit allowed methods and headers** to only what’s necessary.
- **Test CORS configurations** thoroughly in development and staging environments.

---

## Summary

When it comes to developing web applications there's no avoiding CORS; it has a role in protecting users from bad actors. Configuring GraphQL for AuraDB for CORS is straight forward so long as you enter _exactly_ allowed origins and remember - no wildcards !
