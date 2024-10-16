---
layout: post
title: "Dipping into the code from the trinity of SSO, Neo4j and a web application "
description: "looking at the code"
tags: Neo4j PM DevEx QueryAPI SSO Token
---

# Dipping into the code from the trinity of SSO, Neo4j and a web application

As a follow on from my previous blog post, the trinity of SSO, Neo4j and a web application, this entry will look at the code used for the web application to see how it all fits together

 Given my JS / React knowledge is basic ( and I'm flattering myself there ) you'll be relieved to know that this is not a PR review or a step by step journey.

 I'm just looking at the important bits in small snippetts at a time.

 The web application is based on the example React application from Okta combined with code I had hanging around that obtained data from Neo4j and displayed it in a table.

### srv/pages/Home.jsx

If the user is not authenticated, ```!authState.isAuthenticated```      ,then some descriptive text is shown and the user is invited to click on the Login button

```Javascript
 {!authState.isAuthenticated && (
          <Grid columns={1}>
            <Header textAlign='left' as='h1'>One set of credentials</Header>
            <GridRow>
              <Container textAlign='left'>
              <p>
                This web application shows how a single set of credentials can be used to control access to the web application itself and obtain information from Neo4j to populate table.

                Click on the Login button to continue
              </p>
              </Container>
            </GridRow>
            <GridRow>
              <Button onClick={login}>Login</Button>
            </GridRow>
          </Grid>
```

When they do select login, this happens

```Javascript
const login = async () => {
    await oktaAuth.signInWithRedirect();
  };
```

Which causes the browser to load the okta sigin page.

If authentication was successful, then we now have this check to see if we should call the Movies component with a property that holds the value of the id token from the JWT Okta returned to us.

```
 {authState.isAuthenticated && (
          <Movies userToken={authState.idToken["idToken"]} ></Movies>
        )}

```

At this point, Movies has what it needs to go get data from Neo4j , populate a table and return that back to page.

### /srv/components/Movies.jsx

Lets start with calling the Neo4j Query API.

```Javascript
        const response = await fetch( "http://localhost:7474/db/neo4j/query/v2" ,
            {
              method : "POST",
              headers : {
                "Content-Type" : "application/json",
                'Authorization': 'Bearer ' + userIDToken["userToken"],
                },
              body: JSON.stringify({statement:"MATCH (p:Person)-[a:ACTED_IN]->(m:Movie) RETURN m.title, m.released, COLLECT(p.name) LIMIT 10"})
            }
          )
```

In the header, we set Authorization to use the value from the property we received.  Note the space used in 'Bearer ' - it must be there or things break.

We taken advantage of JSON.stringify ( what a great name ) to ccorreclty onvert the Cypher statement to JSON.  

The data contract for responses can be found in the Query API documentation but how you actually deal will be shaped by how you asked Cypher to return it.

Here's a sample of what's returned from the Cypher statement we're using

```JSON
{
    "data": {
        "fields": [
            "m.title",
            "m.released",
            "COLLECT(p.name)"
        ],
        "values": [
            [
                "The Matrix",
                1999,
                [
                    "Emil Eifrem",
                    "Hugo Weaving",
                    "Laurence Fishburne",
                    "Carrie-Anne Moss",
                    "Keanu Reeves",
                    "Emil Eifrem",
                    "Laurence Fishburne",
                    "Carrie-Anne Moss",
                    "Hugo Weaving",
                    "Keanu Reeves"
                ]
            ],
            .
            .
            .
            .
        ]
    },
    "bookmarks": [
        "FB:kcwQdRwP93oaRI2dmP/EtHZ/78kAmZA="
    ]
}

```

We'll do an initial tidy up using JS favourite method of dealing with arrays - Map.

```
const moviesMap = json.data["values"].map( movieEntries => { return movieEntries });
```

The result of this operation will be easier to deal with when we build out the table.

```JSON
[
    [
        "The Matrix",
        1999,
        [
            "Emil Eifrem",
            "Hugo Weaving",
            "Laurence Fishburne",
            "Carrie-Anne Moss",
            "Keanu Reeves",
            "Emil Eifrem",
            "Laurence Fishburne",
            "Carrie-Anne Moss",
            "Hugo Weaving",
            "Keanu Reeves"
        ]
    ],
    .
    .
    .
    .

]
```

The table is built up here

```Javascript
<div className='movies-table-wrapper'>
                  <table className='movies-table'>
                    <tbody>
                    <tr className='movie-header-row'>
                            <th className='movie-header'>title</th>
                            <th className='movie-header'>released</th>
                            <th className='movie-header'>starring</th>
                    </tr>
                    {listMovies.map((val, key) => {
                            return (
                                <tr key={key} className='movie-row'>
                                    <td className='movie-row-cell'>{val[0]}</td>
                                    <td className='movie-row-cell'>{val[1]}</td>
                                    <td className='movie-row-cell'>{val[2]+""}</td>
                                </tr>
                                )
                              }
                            )
                          }
                      </tbody>
                    </table>
                </div>
```

You can see .map being used again to build up the table rows.

```Javascript
<td className='movie-row-cell'>{val[0]}</td>
<td className='movie-row-cell'>{val[1]}</td>
<td className='movie-row-cell'>{val[2]+""}</td>
```

This where knowledge of the shape of response from the Query API comes in handy - you can see that title is the first entry in the array which corresponds to it's position immediately after ``` RETURN ``` in the Cypher statement
