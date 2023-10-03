# Exploring London tube as a graph

When I set out to do this, I had two main goals
- Learn more about practical applications of graph databases 
- Improve my understanding of what it is like to work with graph databases from the perspective of a developer

I'll need a data source and I picked the London Tube Network to use as it as the people who run it, Transport For London - TFL , have a well documented API that provides deep insight into it.  Also, looking at a map of the Tube, it's looks like a graph. 

As to the developer experience side, I've played around with Python for some time.  I'm at  the point that I'm comfortable using it , still got lots to learn though. 

My immediate goal is use the data from TFL API to build a graph database that represents the Tube network.  Then I'm in a position to start asking questions like ' How do I get from Southwark to St. Pancreas whilsting avoiding busy stations? ' and similar route planning queries

## Receipe
Neo4j Desktop Edition ( Disclaimer:   I work there as a PM )
- Why Desktop ?  I've been jumping in and out on this on the train which makes using our cloud offering hard as the connection frequently drops out.  

Python
- I have a reasonable understanding.   I'd have used Rust for the hell of it but I'm at a very early stage with that language

TFL API
- https://api.tfl.gov.uk/  
- There's a free tier thats rate limited.  Needs registration to use after which you can create an API key 

Postman
- https://www.postman.com/home
- Great tool for working with APIs.  If it's not for you, try Insomnia https://insomnia.rest/


To begin, figure out TFL APIs

I used postman extensively for this as it made examing the response payloads much more straight forward. 

We'll need a list of all of the Tube lines and the stations on them in sequence.  This will allow us to create the graph. 

In general the TFL API returns a lot of information - and I mean a lot - most of which is not needed for our purposes.  There's a number of endpoints that look like they return what is needed; you can get all of the lines from https://api.tfl.gov.uk/line/mode/tube/status and then call https://api.tfl.gov.uk/line/{line id}/stoppoints for each line.  
This gets us all of the stations on a line but they are not in sequence :(

All is not lost

- We get a list of tube lines from https://api.tfl.gov.uk/line/mode/tube/status

- Then, for each line we can call https://api.tfl.gov.uk/{line id}/Route/Sequence/line_direction.  This returns a JSON document of which we find a list of stations, in sequence, in ["orderedLineRoutes"] for each route.  

Watch out for a line can contain more than one route and we'll need to take that into account. 


In the next update, we'll go write some code
