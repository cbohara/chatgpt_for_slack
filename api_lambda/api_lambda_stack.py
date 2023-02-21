import os
from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_lambda_python_alpha as python,
    aws_lambda as _lambda,
    aws_sqs,
    Aws,
    Stack,
    Duration
)

class ApiLambdaStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        #Creating Lambda function that will be triggered by API gateway
        lambda_function = python.PythonFunction(
            self,
            'LambdaFunction',
            runtime=_lambda.Runtime.PYTHON_3_9,
            entry='lambda',
            index='lambda_handler.py',
            handler='handler',
            environment={
                'OPENAI_API_KEY': os.environ['OPENAI_API_KEY'],
                'SLACK_BOT_TOKEN': os.environ['SLACK_BOT_TOKEN'],
                'SLACK_SIGNING_SECRET': os.environ['SLACK_SIGNING_SECRET'],
            },
            timeout=Duration.seconds(120),
        )

        #Create the API GW service role with permissions to call SQS
        rest_api_role = iam.Role(
            self,
            "RestAPIRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess")]
        )

        #Create an API GW Rest API
        base_api = apigw.RestApi(
            self,
            'ApiGW',
            rest_api_name='slack',
        )

        #Create a resource named "email" on the base API
        api_resource = base_api.root.add_resource('events')
        method = api_resource.add_method("POST", apigw.LambdaIntegration(lambda_function))

        #Create dead letter queue for safekeeping
        dead_letter_queue = aws_sqs.Queue(
            self,
            'DeadLetterQueue',
            retention_period=Duration.days(14)
        )

        #Send messages to sqs for processing
        queue = aws_sqs.Queue(
            self,
            'Queue',
            retention_period=Duration.days(14),
            visibility_timeout=Duration.seconds(300),
            dead_letter_queue=aws_sqs.DeadLetterQueue(
                max_receive_count=4,
                queue=dead_letter_queue
            )
        )

        #Grant Lambda to send message to SQS
        queue.grant_send_messages(lambda_function)