---
layout: post
title: "Dipping into the code from the trinity of SSO, Neo4j and a web application "
description: "looking at the code"
tags: Neo4j PM DevEx QueryAPI SSO Token
---

# Commentary on the web application code used in SSO post

As a follow on from my previous blog post, the trinity of SSO, Neo4j and a web application, this entry takes a deeper look at the code used for the web application to see how it all fits together.

Given my JS / React knowledge is basic ( and I'm flattering myself there ) the more experienced of you are likely to be amused at my efforts.

The web application is based on code I had previously used for showing how graphql can be used to read data from Neo4j and displayed it in a table.  I've borrowed heavily from OKtas example React application - many thanks to them.

Lets start with the home page

### srv/pages/Home.jsx

If the user is not authenticated, ```!authState.isAuthenticated```      ,then we show a bit of descriptive text and invite the user to auth by selecting the login button.  

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

When they do select login, to do the acutal login, something that Okta handles for us, we do this

```Javascript
const login = async () => {
    await oktaAuth.signInWithRedirect();
  };
```

Which causes the browser to load the okta sigin page.

If authentication was successful, ``` authState.isAuthenticated ``` ,call the Movies component with a property that holds the value of the id token that Okta included to us as part of the received JWT.

```
 {authState.isAuthenticated && (
          <Movies userToken={authState.idToken["idToken"]} ></Movies>
        )}

```

Lets move to the Movies component.

### /srv/components/Movies.jsx

We start with calling the Neo4j Query API using the id token.  I'm using ```fetch``` for the HTTP reequest and there's likely something better than would deal with retries, responses codes etc.. in a more graceful manner

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

We'll do an initial tidy up using JS favourite method of dealing with arrays - .map

```
const moviesMap = json.data["values"].map( movieEntries => { return movieEntries });
```

This trims the response from Neo4j Query API to just the data.

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

The table is built up with this code.  You can see .map being used again for the table rows.

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

This where knowledge of the shape of response from the Query API comes in handy - you can see that title is the first entry in the array which corresponds to it's position immediately after ``` RETURN ``` in the Cypher statement

```Javascript
<td className='movie-row-cell'>{val[0]}</td>
<td className='movie-row-cell'>{val[1]}</td>
<td className='movie-row-cell'>{val[2]+""}</td>
```

+"" ensures that a comma seperates the names of various actors.

That's the main bits of the web application.  I'm sure that there's other ( and likely better ) ways of achieving the same outcome - I can understand what's going on here so I'll stick with this until I acquire more knowledge !.

Laters
