+++
date = '2024-05-03T00:00:00+01:00'
draft = true
title = 'Using the forthcoming Aura GraphQL API'
+++

Much later this year you'll be able to us GraphQL API with our Aura platform - yep, you read that correctly, we've got the builders in to add an extension.  

We've done this as it removes the requirement for customers to provision, configure, and then maintain a graphql server for the purposes of hosting a graphQL API - we're taking care of all of that in the Aura platform.  Additionally, it also ensures the GraphQL API is next door, figratively speaking, to the Aura instance avoiding the transist of information across the occasionally choppy waters of the internet which improves responsiveness and security. 

In short, it's going to be much easier to take advantage of the benefits of GraphQL with Aura based DBs

We are running an invitation only early access program for this at the moment and will be opening it up later this Summer before the *estimated* full release towards the end of the year.  

Let me know if you want in by filling out this [Google form](https://forms.gle/3WSWtwjuj44k5LZR6)

## A web app with Aura GraphQL API

Lets see how this upcoming feature can be used for which we'll need some code.

I've recently embarked on learning more about React so lets take that route.  First thought we'll need the GraphQL API.

### Provisioning the GraphQL API for Aura

This is performed by using of the Aura CLI, something I have written about [before](https://www.pm50plus.com/2023/11/30/cli.html).  We've extended the Aura CLI for this purpose with a new command group ( BTW it's not visible unless you're in the EAP). The command group is 'data-apis' which could be suggestive of more API types,  say REST or gRPC, as a possibility in the future but I couldn't possibly comment on that.  

Using the Aura CLI, we provision the GraphQL API like so

```Bash
aura data-apis create --name <friendly-name> --instance-id <aura-instance-id> \ 
--instance-username <aura-instance-user>  --instance-password <aura-instance-password> \
--type-definitions <path-to-type-defs> --wait
``` 

I've used Type Definitions generated from introspection of the sample Movie graph database using our [GraphQL Toolbox](https://graphql-toolbox.neo4j.io/). 

### Using GraphQL API with React
Ther eare a number of ways to hook up a web app to a GraphQL API.  I'm using React with Javascript for which there are many pre-built modules available for this, such as :-

- [urql](https://commerce.nearform.com/open-source/urql/)
- [Apollo Client](https://www.apollographql.com/docs/react/api/core/ApolloClient/)
- [relay](https://relay.dev/docs/tutorial/graphql/)

I've used ```fetch``` which is built in.  I'm taking that path as I can better illustrate what's required for using the Aura GraphQL API.  For anything more serious, I'd suggest you use one of the others I just mentioned.

Here's the code that talks to the GraphQL API which is part of a function ```useGraphQLAPI```.  It takes a parameter, ```query```, which has the GraphQL query that will be used.

```JavaScript
useEffect(() => {
    const fetchData = async() => {
      const response = await fetch( "<YOUR URL TO THE AURA GRAPHQL API>" ,
          {
            method : "POST",
            headers : {
              "Content-Type" : "application/json",
              "x-api-key" : "<YOUR GRAPHQL API KEY>"
              },
            body: JSON.stringify({query})
            }
        )
      const json = await response.json();
      if (response.status === 200) {
        setListMovies(json);
        setReadyForRender(true);
        }  
    };
    
    fetchData();

  }, [query]);
```
Note the x-api-key key value in the header.  This is used to allow access to GraphQL API and must be used in every request.

The GraphQL query itself is defined like so

```JavaScript
const MOVIES_QUERY = `query {
          movies( options: { limit: 10 }, where: {title_CONTAINS: "` + movieSearchName +  `" } ) {
            movieId
            released
            title
          }
        }
    `;
```


```movieSearchName``` is the variable that holds the name of the Movie that we're looking for.  You'll note that the GraphQL query gets 10 movies whose title contains whatever the value of ```movieSearchName``` is set to. 

I've used ```setReadyForRender``` as a flag that informs React what to render on the screeen.  Initially this will be "Loading...." , where ```setReadyForRender``` is False,  to indicate data is being retrieved .  When data has been obtained, ```setReadyForRender``` becomes True and we display a table filled with the said data.

If you're wanting to try this yourself, and franky why wouldn't you, you can download the [application](../code/2024-05-03-using-aura-graphql-api_code.zip) , unzip it and then nstall using ```npm install```.  Make sure you change the values in MovieTable.js to be the ones used by your Aura GraphQL API which is also where you'll find the code snippets above.  

When you're ready, do a ```npm start``` and be stunned by the brilliance of the UX. 

It's all amaze balls I know and will surely set me on the road to billionaire status with one or more super yatchs and perhaps an island somewhere warm.


Laters

JG
