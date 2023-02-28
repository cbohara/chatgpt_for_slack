import os
from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_lambda_python_alpha as python,
    aws_lambda as _lambda,
    aws_sqs,
    Stack,
    Duration,
    App
)


class SlackAppStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        aws_account = os.environ["CDK_DEFAULT_ACCOUNT"]
        env = os.environ["ENV"]

        # Creating IAM role for Lambda function
        lambda_role = iam.Role(
            self, 
            f'{env}-slack-app-lambda-role',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            role_name=f'{env}-slack-app-lambda-role'
        )

        # Attach policies to the IAM role
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                'AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
        )
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                'AWSLambdaExecute',
                'arn:aws:iam::aws:policy/AWSLambdaExecute'
            )
        )
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(
                self,
                'AWSLambdaRole',
                'arn:aws:iam::aws:policy/service-role/AWSLambdaRole'
            )
        )

        # Creating Lambda function that will be triggered by Lambda function URL
        lambda_listener_function = python.PythonFunction(
            self,
            f'{env}-lambda-listener-function',
            runtime=_lambda.Runtime.PYTHON_3_9,
            entry='lambda_listener',
            index='lambda_handler.py',
            handler='handler',
            environment={
                'OPENAI_API_KEY': os.environ['OPENAI_API_KEY'],
                'SLACK_SIGNING_SECRET': os.environ['SLACK_SIGNING_SECRET'],
                'SLACK_CLIENT_ID': os.environ['SLACK_CLIENT_ID'],
                'SLACK_CLIENT_SECRET': os.environ['SLACK_CLIENT_SECRET'],
                'SLACK_INSTALLATION_S3_BUCKET_NAME': os.environ['SLACK_INSTALLATION_S3_BUCKET_NAME'],
                'SLACK_STATE_S3_BUCKET_NAME': os.environ['SLACK_STATE_S3_BUCKET_NAME'],
                'SLACK_BOT_TOKEN': os.environ['SLACK_BOT_TOKEN'],
                'SLACK_SCOPES': os.environ['SLACK_SCOPES'],
            },
            timeout=Duration.seconds(300),
            role=lambda_role
        )

        # Create function URL
        function_url = lambda_listener_function.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
        )

        # Create dead letter queue for safekeeping
        dead_letter_queue = aws_sqs.Queue(
            self,
            f'{env}-lambda-listener-dead-letter-queue',
            retention_period=Duration.days(14)
        )

        # Send messages to sqs for processing
        queue = aws_sqs.Queue(
            self,
            f'{env}-lambda-listener-queue',
            retention_period=Duration.days(14),
            visibility_timeout=Duration.seconds(300),
            dead_letter_queue=aws_sqs.DeadLetterQueue(
                max_receive_count=4,
                queue=dead_letter_queue
            )
        )

        # Grant Lambda to send message to SQS
        queue.grant_send_messages(lambda_listener_function)

#        # Create S3 bucket for installation credentials
#        slack_install_bucket = s3.Bucket(
#            self,
#            "SlackInstallationsBucket",
#            bucket_name=f"{env}-slack-installations-s3-{aws_account}",
#        )
#        
#        # Create S3 bucket for state variables during OAuth flow
#        slack_state_store_bucket = s3.Bucket(
#            self,
#            "SlackStateStoreBucket",
#            bucket_name=f"{env}-slack-state-store-s3-{aws_account}",
#        )

        # Import existing buckets
        slack_install_bucket = s3.Bucket.from_bucket_name(
            self,
            f"{env}-slack-installations-s3-{aws_account}",
            bucket_name=f"{env}-slack-installations-s3-{aws_account}",
        )

        slack_state_store_bucket = s3.Bucket.from_bucket_name(
            self,
            f"{env}-slack-state-store-s3-{aws_account}",
            bucket_name=f"{env}-slack-state-store-s3-{aws_account}",
        )

        # Define the IAM policy statement
        s3_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:*",
                "s3-object-lambda:*"
            ],
            resources=[
                slack_install_bucket.bucket_arn,
                f'{slack_install_bucket.bucket_arn}/*',
                slack_state_store_bucket.bucket_arn,
                f'{slack_state_store_bucket.bucket_arn}/*'
            ],
            sid=f'{env}-slack-app-s3-access',
        )

        # Attach the policy to the Lambda role so it can access S3
        lambda_role.add_to_policy(s3_policy)


app = App()
SlackAppStack(
    app, 
    f'{os.environ["ENV"]}-{os.environ["NAME"]}'
)
app.synth()
