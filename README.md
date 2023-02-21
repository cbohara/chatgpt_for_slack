
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
curl -H 'Content-Type: application/json' -d 'email=local@gmail.com' -X POST https://lo9whtzd96.execute-api.us-east-1.amazonaws.com/prod/email
```