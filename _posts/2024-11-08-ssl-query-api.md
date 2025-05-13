---
layout: posts
title: "SSL for Neo4j so the Query API can use it "
description: "How to configure Neo4j for SSL using Lets Encrypt"
tags: Neo4j PM DevPM QueryAPI  Aura SSL
---

# A guide to using SSL with Neo4j Query API

To save my fingers hammering out letters to form the words that describe why, lets just accecpt that using SSL is a good thing.

If you're using Aura then you can skip reading my prose and do something more interesting instead as Aura only uses SSL.  For everyone else you will need to configure SSL.  

The following is a guide to doing this with LetsEncrypt, a free source of certificates, and an AWS EC2 running docker with Neo4j.  I run that combination on a frequent basis - it's my goto for trying stuff out.  

Neo4j supports SSL across these communication channels.

- bolt (port - 7687)
- https (port - 7473)
- cluster (ports - 5000, 6000, 7000, and 7688)
- backups (port - 6362)

It's entirely possible to selectively turn on SSL - you don't have to do everything.

I'm going to look at Bolt + HTTPS.  Why both?  For reasons that I've not yet discovered, to use HTTPS you also must have Bolt using SSL.

Enabling HTTPS covers everything that uses HTTP operations including the Query API

For this, I'll be using

- AWS
- GoDaddy for DNS
- Docker
- Lets Encrypt

and a fair bit of typing at the command shell

Lets get started

# Provision and configure an EC2 image with elastic IP address

You will need to provision an EC2 machine for running Neo4j.  Ideally this would be circa 4gb with a couple of vCPU or better.  Give it 250Gb of storage.

An elastic IP address is being used to avoid IP address changes on restarts etc.. as this gets messy with then having to adjust the public DNS entries.  

I'm using AWS Linux 2 for the image.

__Note__: Do not use aws linux 2023 as it does not fully support snapd which is used to install certbot for certificate generation with Lets Encrypt

## Adjust security group

Once the EC2 machine is provisioned, adjust the security group to allow all inbound TCP from your IP address to the EC2 machine

Then connect using SSH to the EC2 Machine

## Install any updates

Type at the command prompt on the EC2 machine

```Bash
sudo yum update -y
```

## Install Docker

Type at the command prompt on the EC2 machine

```Bash
sudo yum install docker -y
```

## Enable docker service at AMI boot time

Type at the command prompt on the EC2 machine

```Bash
sudo chkconfig docker on
```

## Start the docker service

```Bash
sudo service docker start
```

## Add the ec2-user to the dockergroup

This allows ec2-user to execute Docker commands without using sudo.

```Bash
sudo usermod -a -G docker ec2-user
```

## Log out, log back in

Confirm  docker commands can be run without sudo - this will throw an error if the user was not added or not logged out and back in

```Bash
docker info
```

You should see a data set that contains information about the version of Docker that has been installed

# Update DNS

I'm assuming that you've already got DNS configured somewhere.  To that configuration you need to add an 'A' record using the elastic IP address of your EC2 host and give it a hostname.  When creating a certificate for our EC2 machine, Certbot will lookup our entry and will fail if DNS resolution fails.   If you do not have a DNS provider, you can use the free DuckDNS service.  I'd avoid doing this for any production as DuckDNS system contains many entries that are used for malware. Be careful.

# Lets Encrypt

Let’s Encrypt is a free, automated, and open certificate authority (CA), run for the public’s benefit. It is a service provided by the Internet Security Research Group (ISRG).  You can read more about Let's Encrypt on their website [Lets Encrypt](https://letsencrypt.org/about/) website.

Lets Encrpt offers a CLI, Certbot , that takes care of getting a certificate for us and also can be used for renewals, something I discuss at the end.

Go ahead and SSH to the EC2 machine

## Pre-installation requirement

Certbot uses the snap system for installation.  There are other methods but this is what we are using here.  We'll need to install snap first.

On the EC2 machine, perform the following at the command prompt

```Bash
sudo yum update 
sudo wget -O /etc/yum.repos.d/snapd.repo \
    https://bboozzoo.github.io/snapd-amazon-linux/amzn2/snapd.repo
sudo yum install snapd -y
sudo systemctl enable --now snapd.socket
sudo systemctl start snapd
```

## Install Certbot

On the EC2 machine, perform the following at the command prompt

```Bash
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

## Allow all traffic from anywhere

For the moment adjust inbound security group rules to allow HTTP from anywhere.  Certbot will fail if this step is not done.

## Obtain a certificate

This is simply a matter of running Certbot from the command line with a few parameters and then answering a few basic prompts.

You can leave out -v as this is just to provide verbose output so you can see what's going on in detail.

__Note:__  Make sure you include --key-type rsa in the Certbot command line as this is the certificate format expected by Neo4j

On the EC2 machine, perform the following at the command prompt

```Bash
sudo certbot certonly --key-type rsa --standalone -d neo4j.giffard.xyz -v
```

If everything works ok, you will see something like this

```Text
Saving debug log to /var/log/letsencrypt/letsencrypt.log
Plugins selected: Authenticator standalone, Installer None
Requesting a certificate for neo4j.giffard.xyz
Performing the following challenges:
http-01 challenge for neo4j.giffard.xyz
Waiting for verification...
Cleaning up challenges

Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/neo4j.giffard.xyz/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/neo4j.giffard.xyz/privkey.pem
This certificate expires on 2025-02-05.
These files will be updated when the certificate renews.
Certbot has set up a scheduled task to automatically renew this certificate in the background.

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
If you like Certbot, please consider supporting our work by:
 * Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
 * Donating to EFF:                    https://eff.org/donate-le
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
```

Keys from CertBot are stored at

- /etc/letsencrypt/live/neo4j.giffard.xyz/fullchain.pem
- /etc/letsencrypt/live/neo4j.giffard.xyz/privkey.pem

## Adjust inbound security group rules

Now Cerbot has run, you can put the inbound security rules back to allow only traffic from your IP address

## Adjust certificates file permissions

We're going to use symlinks from our folders to the actual certs.  If we don't use symlinks, then we would need to copy the certs to the folders where Neo4j expects them to be. Symlinks avoids this.

The permission change - Make sure all directories and files are 'others' readable for letsencrpt folders & files

On the EC2 machine, perform the following at the command prompt

```Bash
sudo chmod -R o+rx /etc/letsencrypt/ *
```

## Install Neo4j Docker image

__Note:__  If you are not comfortable with the values used for the username & password , change NEO4J_AUTH=neo4j/password to  something that works for you.

On the EC2 machine, perform the following at the command prompt

```Bash
docker run -dt \
    --name=neo4jDb \
    --publish=7474:7474 \
    --publish=7687:7687 \
    --publish=5001:5000 \
    --publish=80:80 \
    --publish=443:443 \
    --volume=$HOME/neo4j/data:/data \
    --volume=$HOME/neo4j/conf:/conf \
    --volume=$HOME/neo4j/logs:/logs \
    --volume=$HOME/neo4j/certificates:/ssl \
    --volume=/etc/letsencrypt:/etc/letsencrypt \
    --env=NEO4J_ACCEPT_LICENSE_AGREEMENT=yes \
    --env=NEO4J_AUTH=neo4j/password \
   neo4j:enterprise
```

 __Note:__  For a container to follow a symlink it must have access to the destination.  Here it means that we need to attach /etc/letsencrypt on the host to the container. This is why we have  --volume=/etc/letsencrypt:/etc/letsencrypt so the container can reach the certs.

## Check Neo4j is up

Use your browser to connect to the IP address of the EC machine like so

http://EC2_DNS:7474

This should show you the Browser console for Neo4j.  Check you can login with neo4j / password

# Switch Neo4j to use SSL certs

## Folder structure

Neo4j requires a certain folder structure to be configured for SSL certificates.  As mentioned at the beginning, Neo4j allows for SSL to enabled independently for various networking components and they can use different certificates.  The structure is

| Path | Purpose
| -------- | ------- |
| /certificates/COMPONENT | The base directory under which cryptographic objects are searched for by default. |
|/certificates/COMPONENT/trusted | A directory populated with certificates of trusted parties. |
| /certificates/COMPONENT/revoked | A directory populated with certificate revocation lists (CRLs).|

Where COMPONENT is one from bolt, https, cluster or backup

On the EC2 machine, perform the following at the command prompt to create the folder structure for bolt and https

```Bash
sudo mkdir -p ~/neo4j/certificates/https/trusted; sudo mkdir -p ~/neo4j/certificates/https/revoked
sudo mkdir -p ~/neo4j/certificates/bolt/trusted; sudo mkdir -p ~/neo4j/certificates/bolt/revoked
```

## Create Symlinks

The nice part about our symlink structure  is that our links are always pointing to the certs in the “live” directory, which themselves are symlinks to whatever the latest certbot has created.  For that reason, we are able to automate keeping certificates fresh with a cron job and certbot ( See end of this blog ).

On the EC2 machine, perform the following at the command prompt

```Bash
   sudo ln -s /etc/letsencrypt/live/neo4j.giffard.xyz/fullchain.pem  ~/neo4j/certificates/bolt/neo4j.cert
   sudo ln -s /etc/letsencrypt/live/neo4j.giffard.xyz/privkey.pem ~/neo4j/certificates/bolt/neo4j.key
   sudo ln -s /etc/letsencrypt/live/neo4j.giffard.xyz/fullchain.pem ~/neo4j/certificates/bolt/trusted/neo4j.cert 
   sudo ln -s /etc/letsencrypt/live/neo4j.giffard.xyz/fullchain.pem  ~/neo4j/certificates/https/neo4j.cert
   sudo ln -s /etc/letsencrypt/live/neo4j.giffard.xyz/privkey.pem ~/neo4j/certificates/https/neo4j.key
   sudo ln -s /etc/letsencrypt/live/neo4j.giffard.xyz/fullchain.pem ~/neo4j/certificates/https/trusted/neo4j.cert
```

# Confirm synmlinks can be followed

The symlinks need to be followed from within the container.   We can do this by getting an interactive shell in the container and trying to read the certs

On the EC2 machine, perform the following at the command prompt

```Bash
docker exec -it neo4jDb /bin/bash
cat /var/lib/neo4j/certificates/bolt/trusted/neo4j.cert
cat /var/lib/neo4j/certificates/https/trusted/neo4j.cert
```

Enter ```exit``` to leave the container interactive shell

After each cat you should see a wall of text that represents the certificate.   If you do not

- Check that the container has  --volume=/etc/letsencrypt:/etc/letsencrypt  
- Check the file permissions.  Did you grant 'other' to fhe file?

## Update neo4j.conf file to use certificates

Using your favourite text editor, change the neo4j.conf file located in $HOME/neo4j/conf:/conf on the EC2 machine

```Text
# Bolt SSL configuration
dbms.ssl.policy.bolt.enabled=true
dbms.ssl.policy.bolt.base_directory=certificates/bolt
dbms.ssl.policy.bolt.private_key=neo4j.key
dbms.ssl.policy.bolt.public_certificate=neo4j.cert
dbms.ssl.policy.bolt.client_auth=NONE
dbms.ssl.policy.bolt.trusted_dir=trusted
dbms.ssl.policy.bolt.revoked_dir=revoked

# Https SSL configuration
dbms.ssl.policy.https.enabled=true
dbms.ssl.policy.https.base_directory=certificates/https
dbms.ssl.policy.https.private_key=neo4j.key
dbms.ssl.policy.https.public_certificate=neo4j.cert
dbms.ssl.policy.https.client_auth=NONE
dbms.ssl.policy.https.trusted_dir=trusted
dbms.ssl.policy.https.revoked_dir=revoked
```

Change network connector settings  to use  SSL for bolt and https with https being accessed on port 443. The use of port 80 for http will be disabled.

```Text
#*****************************************************************
# Network connector configuration
#*****************************************************************


# Bolt connector
server.bolt.enabled=true
server.bolt.tls_level=REQUIRED
server.bolt.listen_address=:7687
server.bolt.advertised_address=:7687

# HTTP Connector. There can be zero or one HTTP connectors.
server.http.enabled=false
#server.http.listen_address=:80
#server.http.advertised_address=:80

# HTTPS Connector. There can be zero or one HTTPS connectors.
server.https.enabled=true
server.https.listen_address=:443
server.https.advertised_address=:443
```

## Restart neo4j docker container

For the changes made in neo4j.conf to take effect, the Neo4j container needs to be restarted

On the EC2 machine, type this at a command prompt

```Bash
docker restart neo4jDb
```

We now should have a neo4j system running in AWS using SSL

## Confirm use of SSL

Use your browser to connect using HTTPS

HTTPS://EC2_DNS/browser

# Query API with SSL

This just requires use of HTTPS rather than HTTP in the URL.  Using curl on our local machine to connect to the EC2 we can confirm this

Swap out EC2_DNS, YOUR_NEO4j_USERNAME, and YOUR_NEO4j_PASSWORD for your values

```Bash
curl --location 'https://EC2_DNS/db/neo4j/query/v2' \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
-u YOUR_NEO4j_USERNAME: YOUR_NEO4j_PASSWORD\
--data '{ "statement": "MATCH (n) RETURN n LIMIT 1" }'
```

This should return a single entry from your graph across a HTTPS connection

# Renewing LetsEncrypt certificates on a schedule

The nice part about our symlink structure above is that our links are always pointing to the certs in the “live” directory, which themselves are symlinks to whatever the latest certbot has created.  For that reason, we are able to automate keeping certificates fresh with a cron job and certbot.

By running certbot with a renew flag, you can update certificates to push out the expiry date. Certbot will only do this if the certificate is expired.  

You can check that this will work by running on the EC2 machine

```Bash
sudo certbot renew --dry-run
```

And check that the output has no errors.

For a new cert to work, you will need to restart Neo4j.  certbot does allow for this by using --deploy-hook option that enables certbot to run a command.  With our example that uses a docker container to run Neo4j , we would create a cron job that runs fairly frequently to check if the certs need renewing that runs certbot like this

```Text
sudo certbot renew --deploy-hook "docker restart neo4jDb"
```
