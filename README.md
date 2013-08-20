Nimbostratus target
===================

This repository holds a target infrastructure you can use for testing [nimbostratus](https://github.com/andresriancho/nimbostratus).

This code deploys an Amazon AWS infrastructure which has various vulnerabilities and weak configuration settings which 
can be exploited using [nimbostratus](https://github.com/andresriancho/nimbostratus).

**If you're not sure what this is all about, you better avoid using any of the code that lives here.**

Usage
=====

```bash
git clone git@github.com:andresriancho/nimbostratus-target.git
cd nimbostratus-target
pip install -r requirements.txt
```

Make sure you have configured your "root" AWS credentials in `~/.boto` before you run the fabric script.


```bash
fab deploy
```

The console messages will show you the progress to understand what's deployed and where.
At the end you should end up with the following AWS components:

 * Front-end EC2 instance with:
   * HTTP server and vulnerable Web application
   * Celery configured to use SQS as broker
   * Deployed using user-data script
   * With an instance profile which allows acces to SQS
 * Backend worker:
   * Consumes SQS messages sent by front-end instance
   * Uses pickle as serialization method
   * No instance profile configured, hard-coded AWS credentials
   * AWS credentials can access `RDS:*` and `IAM:*`
   * Stores information in RDS database using low-privileged user
 * RDS database
 * IAM user for backend worker

Disclaimer
==========

 * This code wasn't developed for re-usability.
 * Running this code will create Amazon AWS charges!
