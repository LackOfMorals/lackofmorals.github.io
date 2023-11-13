---
layout: post
title: "Doing more with less"
description: ""
tags: Neo4j Python REST 
---


# Episode 3: Like what you're done with that rabbit hole



Previously I wrote about the architectural pattern I was intending use for this adventure and I did make a start; honest.

I took initial steps to move communications into two functions, one for tfl and the other for Neo4j but...

Along came a squirrel.

![Gosh it's cute](/img/tflTube/squirrel_snow.jpg)

 Not a real one like that in the picture and really not this [one ](https://www.independent.co.uk/life-style/food-and-drink/brewdog-worlds-strongest-beer-squirrel-bottle-the-end-of-history-a7436201.html) [^1] but a virtual one wearing a large badge of distraction that read  _'I wonder if I could get all the information needed from tfl API in fewer calls?'_

Whilst quickly backfilling the justification with a dab of being efficient, I fired up PostMan[^2] and dived into the responses from tfl API endpoints. 

## Curiouser and curiouser

To recap, we had identified three tfl API endpoints for this little endeavour.  One to retrieve all of the tube lines, another to give stations on a tube line and the third would provide the information to sequence stations in the correct order.  

Could we reduce this to only two tfl API calls and be a bit more efficient?

Is there a tfl endpoint that can give us all of the stationss a tube line and the order in which they occur in a single response?

Looking at the response from https://api.tfl.gov.uk/Line/TUBE_LINE/Route/Sequence/inbound , we can see a glint of hope 

```json

 "stations": [
        {
            "$type": "Tfl.Api.Presentation.Entities.MatchedStop, Tfl.Api.Presentation.Entities",
            "stationId": "940GZZLUBKE",
            "icsId": "1000016",
            "topMostParentId": "940GZZLUBKE",
            "modes": [
                "bus",
                "tube"
            ],
            "stopType": "NaptanMetroStation",
            "zone": "4",

``` 
<p style="text-align: center;">tfl response with station information</p>


There's an array that contains station details! With the route sequences that follow later in the response, shown below, it looks like ( maybe ) we have what we need.

```json
    "orderedLineRoutes": [
        {
            "$type": "Tfl.Api.Presentation.Entities.OrderedRoute, Tfl.Api.Presentation.Entities",
            "name": "Ealing Broadway  &harr;  Epping ",
            "naptanIds": [
                "940GZZLUEBY",
                "940GZZLUWTA",
                "940GZZLUNAN",
                "940GZZLUEAN",
                "940GZZLUWCY",
                "940GZZLUSBC",
                "940GZZLUHPK",
                "940GZZLUNHG",
                "940GZZLUQWY",
                "940GZZLULGT",
                "940GZZLUMBA",
                "940GZZLUBND",
```
<p style="text-align: center;"> Station sequences</p>


## Why, sometimes I've believed as many as six impossible things before breakfast

After experimenting with this, I noticed that several stations were missing.  It felt like getting close to the top of Everest only to discover that someone had nicked the summit.  Honestly, some people will steal anything. 

Not to be put off, I carried on scrolling my way through the entire response, which felt very much like doom scrolling or whatever the cool kids do, something else made its presence felt. Thankfully not the rather spicy food I had consumed the previous evening on a night out [^3] but this 

```json
    "stopPointSequences": [
        {
            "$type": "Tfl.Api.Presentation.Entities.StopPointSequence, Tfl.Api.Presentation.Entities",
            "lineId": "central",
            "lineName": "Central",
            "direction": "inbound",
            "branchId": 0,
            "nextBranchIds": [
                5
            ],
            "prevBranchIds": [],
            "stopPoint": [
                {
                    "$type": "Tfl.Api.Presentation.Entities.MatchedStop, Tfl.Api.Presentation.Entities",
                    "stationId": "940GZZLUEPG",
                    "icsId": "1000076",
                    "topMostParentId": "940GZZLUEPG",
                    "modes": [
                        "tube"
                    ],
                    "stopType": "NaptanMetroStation",
                    "zone": "6",
```
<p style="text-align: center;"> stopPoints are stations</p>

Much checking and then some more checking, I found all of the stations for the tube line are here.

This means with one call , we can get all of the stations, their details and the sequence.

My goal of using fewer tfl calls was complete.


## The best way to explain it is to do it

Nothing is that straight foward though and this new approach required a re-write of our Python code to wrangle the response to get the information we need. The Psuedo code looks like this 

```Python

Get the list of tube lines from tfl api endpoint

For each tube line
    Make a request to  https://api.tfl.gov.uk/Line/TUBE_LINE/Route/Sequence/inbound 

    With the response
        For each set of stop points in stopPointSequence
            For each station in the set of stop points
                Build up a list of station data 
            Send the station data for the stop point to Neo4j
        
        For each route
            For each station in the route
                Build a list that links the stations together
            
            Use the list to establish relationships between the stations in Neo4j

```

You can download the entire Python code that useds one less call and has the two functions for comms with tfl and Neo4j here [Episode 3](/code/2023-10-13_code.py)

There's some basic error handling included when making network calls with tfl and Neo4j.   More to do there in the future.

### No, no! Sentence first—verdict afterwards.”
If you run the code you should have the entire London Tube network in Neo4j.  There's more code work to move further towards the pattern I want to use but the basics are there. 

Thanks for joining me on this journey - it's looking increasingly like it's not going to be the fastest trip but we are dealing with the U.K public transport system and nothing happens quickly in that domain.

Until the next time, laters



[^1]: Brewdog have run some headline grabbing marketing activities.  This particular one involved rewarding people who had contributed more than £16,000 in one of their crowdfunding series with a beer package in a [dead squirrel.](https://www.independent.co.uk/life-style/food-and-drink/brewdog-worlds-strongest-beer-squirrel-bottle-the-end-of-history-a7436201.html)

[^2]: [PostMan](https://www.postman.com) is a great tool for working with APIs and I'm selling it short using those words as an elivator pitch.  [Insomnia](https://insomnia.rest) does very similar tasks if you want an alternative.

[^3]: I didn't go out out, just out.  See [Are you out or out out ?](https://youtu.be/Q5k8Su_ek2k?si=wnlduzmi55bMejjL)