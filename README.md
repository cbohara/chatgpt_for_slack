
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

