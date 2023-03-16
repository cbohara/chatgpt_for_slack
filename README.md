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