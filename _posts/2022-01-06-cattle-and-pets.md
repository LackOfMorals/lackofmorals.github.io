---
layout: post
title: "Cattle and Pets"
description: "Thoughts on how to compute resources"
tags: ComputeResources
---


## Cattle and Pets 

Cattle and Pets is a way to help think about compute resources that are involved in providing a service.  The resources could be anything from a kubernetes pod to a S3 bucket.  Determining which classification you assign determines how you can treat it.  With most cloud service providers allowing you to tag a resource, you can use these as filters to see which resources are critical requiring care and attention and those that can be left ( almost ) alone.


* Can be destroyed and replaced at any time without the service failing => Cattle


* Indispensable; destroying and replacing will cause the overall service to fail => Pet


