---
layout: posts
title: "Exploring London tube as a graph"
description: "Introducing Graphs using London Tube as an example"
tags: Neo4j Tfl
---

# Exploring London tube as a graph

![London Tube from graph database](/img/tflTube/tfl.png)

When I set out to do this, I had two main goals

- Learn more about practical applications of graph databases 
- Improve my understanding of what it is like to work with graph databases from the perspective of a developer

I'll need a data source to build the graph from. I picked the London Tube Network to use as it as the people who run it, Transport For London - TFL , have a well documented API that provides a wealth of information.  And it's free for basic use.  Also, looking at a map of the Tube, it's looks like a graph. 

As to the developer experience side I'll be using Python as I've played around with it for some time.  I'm now comfortable with using it , still got lots to learn though. 

Finally the graph database.  I'm extremely fortunate to work as a Product Manager at Neo4j , who it could be argued, invented graph databases.   I'll use that. 


## Receipe
Neo4j Desktop Edition

- Why Desktop ?  I work on this activity when able and frequently this is happens on a train whilst heading to / from Neo4j London office.  Connectivity on a train is not great and suffers from frequent drop outs.  The Desktop edition makes it easy to move this to our Neo4j AuraDB cloud SaaS offering in the future. 

Python 3

- I have a reasonable understanding. I would have attempted this in Rust for the hell of it but I'm at a very early stage with that language

TFL API

- [https://api.tfl.gov.uk/]()
- There's a free tier thats rate limited but will work for what I need.  

Postman

- [https://www.postman.com/home]()
- Great tool for working with APIs.  If it's not for you, try Insomnia [https://insomnia.rest/]()


## To begin, figure out TFL APIs

I used postman extensively for this as it made examining the response payloads much more straightforward. 

There's a number of TFL endpoints that look like they return what is needed e.g you can get all of the lines from [https://api.tfl.gov.uk/line/mode/tube/status]() and then call [https://api.tfl.gov.uk/line/line_id/stoppoints]() for each line.  

In general, the TFL API returns a lot of information - and I mean a lot - most of which is not needed for our purposes.  There are a number of endpoints that look like they return what is needed; you can get all of the lines from [https://api.tfl.gov.uk/line/mode/tube/status] and then call [https://api.tfl.gov.uk/line/{line id}/stoppoints] for each line.  

This gets us all of the stations on a line but they are not in sequence :(

All is not lost as we can use other endpoints.

- We get a list of tube lines from [https://api.tfl.gov.uk/line/mode/tube/status]()

- Then, for each line we can call [https://api.tfl.gov.uk/{line id}/Route/Sequence/line_direction]() .  This returns a JSON document in which we find a list of stations, in sequence, in ["orderedLineRoutes"] for each route.  

Watch out for lines that can contain more than one route; we'll need to take that into account. 


In the next update, we'll go write some code. 


