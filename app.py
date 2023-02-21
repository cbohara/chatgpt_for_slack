#!/usr/bin/env python3

from aws_cdk import App

from api_lambda.api_lambda_stack import ApiLambdaStack


app = App()
ApiLambdaStack(app, "ApiLambdaStack")

app.synth()
