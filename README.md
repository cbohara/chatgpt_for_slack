
# API Gateway + Lambda

Creates an API Gateway API with a POST Method and a Lambda function. Requests to the API triggers the Lambda function.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

Synthesize to generate CloudFormation template 

```
$ cdk synth
```

One time bootstrap per account and region
```
$ cdk bootstrap 
```

Deploy app by submitting Cloudformation template to AWS
```
$ cdk deploy
```

## Testing the app

```
curl -H 'Content-Type: application/json' -d 'test' -X POST https://849wdyw4k3.execute-api.us-east-1.amazonaws.com/prod/events
```


## Deploy to AWS
https://github.com/slackapi/bolt-python/blob/main/examples/aws_lambda/aws_lambda.py
https://medium.com/glasswall-engineering/how-to-create-a-slack-bot-using-aws-lambda-in-1-hour-1dbc1b6f021c
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

Update API Gateway to respond success if lambda is going to time out   
https://github.com/slackapi/bolt-python/issues/155

https://github.com/seratch/slack_learning_app_ja/blob/9552489b1d5d3adc61a7c73645a1ae09abc9d933/lambda_app.py

This is the link I'll share wtih folks with the landing page with a button to install the app   
https://ybavldcu6tonw3tcwxjww2ffdi0jfanq.lambda-url.us-east-1.on.aws


[Free tier](https://docs.aws.amazon.com/whitepapers/latest/how-aws-pricing-works/get-started-with-the-aws-free-tier.html)
Amazon DynamoDB: Up to 200 million requests per month (25 write capacity units (WCUs) and 25 read capacity units (RCUs)); 25 GB of storage.    
AWS Lambda: 1 million free requests per month; up to 3.2 million seconds of compute time per month.   