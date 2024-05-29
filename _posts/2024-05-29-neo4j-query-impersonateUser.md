---
layout: post
title: "Exploring impersonating with the Neo4j Query API"
description: ""
tags: Neo4j PM DevEx QueryAPI
---

# Pretending to be someone else

I recently watched a TV broadcast where someone self-identified as the U.k Prime Minster and claimed to have a plan to solve all of countries challenges.  But there were doubts in my mind as to his credibilty. Anyone who has visited the Unitied Kingdom and those of us who live here are well aware of the high probabilty for rain and yet this individual had not considered this possibility and got drenced whilst shouting into the void.  This makes me doubt his capability for forward planning and his claim to be the Prime Minister seems very far fetched indeed.  Was this a prank and it was an impersonator out in the rain that day?  We may never know.

There are times when impersonation can actually be useuful.  Let me give an exmaple in this post.

Since Neo4j 4.4, it has been possible to execute a Cypher statement as someone different from the person who has authenticated.  This is referred to as impersonation.  You may wonder why have such a capability and there are two very good reasons for it's existence.  

• Testing or debugging security controls is almost impossible unless you can mimic other users

• Enterprise systems with middle tier components or microservices often need to act on the behalf of other logins. Disconnecting/Reconnecting at every user change is error prone and carries excessive overhead 


The Query API supports this feature and here's two ways ( there's likely to be more ) that it can be used.


## 1. Impersonating users for testing / debugging

This will require us to have the user that is used with Query API auth to be able to impersonate others. 

For the purposes of this post, I'll create a user called queryAPIUser that has Read / Write to the Neo4j database where our graph is stored.

```TEXT
CREATE USER queryAPIUser SET PASSWORD 'secretpassword' CHANGE NOT REQUIRED;
```
This user will not have any other permissions - the only way it can do anything is to assume the identity of another user that has privledges.

To allow this user to do that, a new role will be needed as that permission cannot be directly granted to users. The permission is granted to the role and then the role is granted to the new user queryAPIUser

```TEXT
CREATE ROLE impersonateUsers; 
GRANT IMPERSONATE (*) ON DBMS TO impersonateUsers;
GRANT ROLE impersonateUsers to queryAPIUser;
```

Notice that IMPERSONATE (*) is using a wildcard which menans any user can be impersonated.  It is also possible to selectively assign users rather than the blanket approach used here. Be careful!

To use this feature with the Query API you will need to add another key:value pair to the message body,  impersonatedUser:_Username_  

For example, if we need to impersonate the user Bob 

```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryAPIUser:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "MATCH (n) RETURN n LIMIT 5", "impersonatedUser":"regularReader"}'
```


## 2. External access controls

Consider an architecture where users login to a front end with a backend that then determines what those users can do.  This is all performed outside of Neo4j.  The backend resolves access down to various roles which need to be used when accessing Neo4j data.  

Using impersonation is a mechanism we can deploy to meet that need.  There will be another option open to us in the very near future that take advantage of JWT claims and I'll write another post on that when it appears. 

We'll look at a simple scenario to show how this can be used where the backend assigns users one of two roles - dataReader and dataWriter.  From a CRUD point of view, these allow for

| Role | Create | Read | Update | Delete |
| -------- | ------- | ------- | ------- | ------- |
| dataReader  | N | Y | N | N |
| dataWriter  | Y | Y | Y | Y |


To do this, we will
- Create the dataReader user and role that allows read
- Create the dataWriter user and role that allows full CRUD
- Create a new role that allows impersonation of dataReader and dataWriter users only
- Create a user for the Query APi and grant it the impersonation role

Then we'll everyones favourite thing and do a bunch of tests to make sure everything works as we expect.


### Create the dataReader user and role that allow reads

First, the user account.

```TEXT
CREATE USER dataReader SET PASSWORD 'secretpassword' CHANGE NOT REQUIRED;
```

Then we will create a role that gives its members read access to data

```TEXT
CREATE ROLE dataReaders;
GRANT TRAVERSE ON GRAPH neo4j ELEMENTS * TO dataReaders;
GRANT READ {*} ON GRAPH neo4j ELEMENTS * TO dataReaders;
```

Grant the dataReader this role

```TEXT
GRANT ROLE dataReaders TO dataReader;
```

### Create dataWrite and a role that allows full CRUD

Like the previous step , we start with the user account. 

```TEXT
CREATE USER dataWriter SET PASSWORD 'secretpassword' CHANGE NOT REQUIRED;
```

Then we will create a role that gives its members read and write access to our data

```TEXT
CREATE ROLE dataWriters;
GRANT TRAVERSE ON GRAPH neo4j ELEMENTS * TO dataWriters;
GRANT READ {*} ON GRAPH neo4j ELEMENTS * TO dataWriters;
GRANT WRITE ON GRAPH neo4j TO dataWriters;
```

Then put our user into this role

```TEXT
GRANT ROLE dataWriters TO dataWriter;
```


### Create a role that allows impersonation of the two users

Naming is not one of my key strengths.  It's why both of my daugthers forenames both start with the letter A because those are at the start of the alphabetical list of possibilities.  It's a good a reason as any. I'm going for a descriptive name of the role here. 

```TEXT
CREATE ROLE impersonateDataUsers; 
GRANT IMPERSONATE (dataReader, dataWriter) ON DBMS TO impersonateDataUsers;
```


### Create an account for use by the Query API and grant it our impersonate role

This account will not have any access to our data unless impersonation is used. Using every ounce of my naming ability ( I did have a spell in Marketing - thankfully I never was called on to name products ) we will call this user queryNoData as that reflects its purpose.

```TEXT
CREATE USER queryNoData SET PASSWORD 'secretpassword' CHANGE NOT REQUIRED;
GRANT ROLE impersonateDataUsers to queryNoData;
```

### Lets go try this out

That's a lot of typing or copy / paste that we've done.  Lets check that it's working as we expect.

Lets start with a reminder of what we expect data access to be for our various users

| Role | Create | Read | Update | Delete |
| -------- | ------- | ------- | ------- | ------- |
| queryNoData  | N | N | N | N |
| dataReader  | N | Y | N | N |
| dataWriter  | Y | Y | Y | Y |

Rather than spam this post with all of the test results, I'll put the curl statements for each CRUD operation at the bottom of this post so you can try them out.  You will need to modify the various values to adjust for each test.  Suffice to say that everything did work as expected


## The end
We've seen how impersonation can be used with the Query API in a couple of scenarios and dropped a huge hint about an upcoming feature.  

Next post on the Query API will look at how we can use the various roles of each member of a cluster to help load balance and use of bookmarks to read our writes. 

Until then, laters


______

## Curl statements used in testing

### queryNoData 
This user account can not access our data in anyway.

**Create**
Expected result: No data created
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "CREATE (RyanReynolds:Person {name:'\''Ryan Reynolds'\'',born:1976})"} ' \
| jq
```

**Read**
Expected result: No data returned
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "MATCH (n) RETURN n LIMIT 5" } ' \
| jq 
```

**Update**
Expected result:  Data is not updated
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "MATCH (p:Person {name:'\''Ryan Reynolds'\''}) SET p.name='\''Bob Reynolds'\'' RETURN p.name"} ' \
| jq
```


**Delete**
Expected result: Data is not deleted
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
-data '{ "statement": "MATCH (p:Person) WHERE p.name='\''Jack Nicholson'\'' DELETE p" }' \
| jq
```



### dataReader
This user account can read our data but not make any changes to it.

**Create**
Expected result: No data created
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "CREATE (RyanReynolds:Person {name:'\''Ryan Reynolds'\'',born:1976})", "impersonatedUser":"dataReader"} ' \
| jq
```

**Read**
Expected result: Data returned
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "MATCH (n) RETURN n LIMIT 5", "impersonatedUser":"dataReader" } ' \
| jq 
```

**Update**
Expected result:  Data is not updated
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "MATCH (p:Person {name:'\''Ryan Reynolds'\''}) SET p.name='\''Bob Reynolds'\'' RETURN p.name", "impersonatedUser":"dataReader"} ' \
| jq
```


**Delete**
Expected result: Data is not deleted
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "MATCH (p:Person) WHERE p.name='\''Jack Nicholson'\'' DELETE p", "impersonatedUser":"dataReader" } ' \
| jq
```


### dataWriter
This user account can read our data and make changes to it.

**Create**
Expected result: Data created
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "CREATE (p:Person {name:'\''Ryan Reynolds'\'',born:1976}) RETURN p ", "impersonatedUser":"dataWriter"} ' \
| jq
```

**Read**
Expected result: Data returned
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "MATCH (n) RETURN n LIMIT 5", "impersonatedUser":"dataWriter" } ' \
| jq 
```

**Update**
Expected result:  Data is updated
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "MATCH (p:Person {name:'\''Ryan Reynolds'\''}) SET p.name='\''Bob Reynolds'\'' RETURN p.name", "impersonatedUser":"dataWriter"} ' \
| jq
```


**Delete**
Expected result: Data is deleted
```TEXT
curl --location 'http://localhost:7474/db/neo4j/query/v2' \
--user 'queryNoData:secretpassword' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--data '{ "statement": "MATCH (p:Person) WHERE p.name='\''Bob Reynolds'\'' DELETE p", "impersonatedUser":"dataWriter" } ' \
| jq
```