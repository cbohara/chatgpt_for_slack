# ChatGPT for Slack app

Deploy
```
$ python cdk_deploy.py --config .env.dev
```

Test
```
python -m pytest tests/test_lambda_listener.py
```


## Deploy to AWS
https://github.com/slackapi/bolt-python/blob/main/examples/aws_lambda/aws_lambda.py
https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda_python_alpha/README.html   

## [Lazy listener (FaaS)](https://slack.dev/bolt-python/concepts#lazy-listeners)
Typically must acknowledge the event within 3 seconds    
Use ack() to send 200 OK response to Slack   
Let's Slack know I'm handling the response then process 

However, FaaS don't work with threads/processes after returning HTTP response   
Which means we can't ack first, process later    

Instead we set process_before_response to True   
This holds off from sending HTTP response until all things in the listener function are done   
However, this means you need to complete within 3 seconds    
Otherwise it will timeout + retry    

To allow more time, added lazy listener function    
Doesn't work as a decorator    
Instead it accepts 2 keyword args - ack() and lazy = list of processes related to the request 

https://github.com/slackapi/bolt-python/issues/678
https://github.com/slackapi/bolt-python/issues/693
https://dev.to/aws-builders/slackapi-bolt-python-app-with-aws-lambda-and-aws-cdk-4h5d

https://github.com/vumdao/slackapi-aws-lambda-bolt-python/blob/master/src/lambda-handler/index.py

https://github.com/slackapi/bolt-js/issues/361

[Free tier](https://docs.aws.amazon.com/whitepapers/latest/how-aws-pricing-works/get-started-with-the-aws-free-tier.html)
Amazon DynamoDB: Up to 200 million requests per month (25 write capacity units (WCUs) and 25 read capacity units (RCUs)); 25 GB of storage.    
AWS Lambda: 1 million free requests per month; up to 3.2 million seconds of compute time per month.   

https://api.slack.com/apps/A04LFFL3URE/oauth?
prod link   
https://22cv6vylhfcady2rsmzeeru53e0jatwy.lambda-url.us-east-1.on.aws/

SLACK_BOT_TOKEN is found under the OAuth & Permissions tab      
The DMs are under the App Home tab with the message tab toggle    

CDK deploy will not update if changes in .env.dev or .env.prod   

---

Ok so I can get the user ID and team ID and email from slack when users visit the home page     
The user ID + team ID are unique across all slack workspaces so that works as a primary key    
Billing will be mapped to user's email in Stripe     
In the events itself we can access the user ID + team ID   

If the primary access pattern especially for user facing interaction is user ID + team ID, that should be the primary key   

I can have 2 dynamodb tables   
one that uses the user ID + team ID as the primary key 

one that uses the email as the primary key and has a list of user ID + team ID combos     
this table will be accessed by event driven stripe call to update billing info    
but then it would need to update the user ID + billing ID table ....    

userID + teamID + email as primary key    

ok so first time on the home page register a new user   
first table - set the user ID + team ID as a primary key and email will be a value along with other metadata    
slack app will query first table directly usin user ID + team ID to get info whether user should get service or not   

second table - set email as primary key and map to user ID + team ID list    
billing backend services will update the second table which it can access using the user ID + team ID list upon event driven stripe call    
it will then update the first table    

