import os
from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda_python_alpha as python,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    Stack,
    Duration,
    App
)


class SlackAppStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        aws_account = os.environ["CDK_DEFAULT_ACCOUNT"]
        env = os.environ["ENV"]
        name = os.environ["NAME"]

        # Creating IAM role for Lambda function
        lambda_role = iam.Role(
            self, 
            f'{env}-{name}-lambda-role',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            role_name=f'{env}-{name}-lambda-role'
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
        lambda_slack_function = python.PythonFunction(
            self,
            f'{env}-{name}-lambda-slack-function',
            runtime=_lambda.Runtime.PYTHON_3_9,
            entry='lambda_slack',
            index='lambda_handler.py',
            handler='handler',
            environment={
                'OPENAI_API_KEY': os.environ['OPENAI_API_KEY'],
                'OPENAI_MODEL': os.environ['OPENAI_MODEL'],
                'SLACK_SIGNING_SECRET': os.environ['SLACK_SIGNING_SECRET'],
                'SLACK_CLIENT_ID': os.environ['SLACK_CLIENT_ID'],
                'SLACK_CLIENT_SECRET': os.environ['SLACK_CLIENT_SECRET'],
                'SLACK_BOT_TOKEN': os.environ['SLACK_BOT_TOKEN'],
                'SLACK_SCOPES': os.environ['SLACK_SCOPES'],
                'SLACK_INSTALLATION_S3_BUCKET_NAME': os.environ['SLACK_INSTALLATION_S3_BUCKET_NAME'],
                'SLACK_STATE_S3_BUCKET_NAME': os.environ['SLACK_STATE_S3_BUCKET_NAME'],
                'DDB_USERS': os.environ['DDB_USERS'],
                'DDB_PUBLIC_CHATS': os.environ['DDB_PUBLIC_CHATS'],
                'DDB_PRIVATE_CHATS': os.environ['DDB_PRIVATE_CHATS'],
                'SLACK_EVENTS': os.environ['SLACK_EVENTS'],
                'MAX_CHAT_LENGTH': os.environ['MAX_CHAT_LENGTH'],
                'STRIPE_MONTHLY_LINK': os.environ['STRIPE_MONTHLY_LINK'],
                'STRIPE_ANNUAL_LINK': os.environ['STRIPE_ANNUAL_LINK'],
                'STRIPE_LIFETIME_LINK': os.environ['STRIPE_LIFETIME_LINK'],
            },
            timeout=Duration.seconds(300),
            role=lambda_role,
            log_retention=logs.RetentionDays.ONE_MONTH
        )

        # Create function URL
        function_url = lambda_slack_function.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
        )

#        # Create S3 bucket for installation credentials
#        slack_install_bucket = s3.Bucket(
#            self,
#            "SlackInstallationsBucket",
#            bucket_name=f"{env}-{name}-installations-{aws_account}"
#        )
#        
#        # Create S3 bucket for state variables during OAuth flow
#        slack_state_store_bucket = s3.Bucket(
#            self,
#            "SlackStateStoreBucket",
#            bucket_name=f"{env}-{name}-state-store-{aws_account}"
#        )

        # Import existing buckets
        slack_install_bucket = s3.Bucket.from_bucket_name(
            self,
            f"{env}-{name}-installations-{aws_account}",
            bucket_name=f"{env}-{name}-installations-{aws_account}"
        )

        slack_state_store_bucket = s3.Bucket.from_bucket_name(
            self,
            f"{env}-{name}-state-store-{aws_account}",
            bucket_name=f"{env}-{name}-state-store-{aws_account}"
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
            sid=f'{env}{name.replace("-","")}app',
        )

        # Attach the policy to the Lambda role so it can access S3
        lambda_role.add_to_policy(s3_policy)

        # Create DynamoDB table for storing users
        users_table = dynamodb.Table(
            self,
            f'{env}-{name}-users-table',
            table_name=f'{env}_{name.replace("-","_")}_users',
            partition_key=dynamodb.Attribute(
                name='slack_id',
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name='email',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # Create DynamoDB table for storing public chats 
        public_chats_table = dynamodb.Table(
            self,
            f'{env}-{name}-public-chats-table',
            table_name=f'{env}_{name.replace("-","_")}_public_chats',
            partition_key=dynamodb.Attribute(
                name='public_chat_id',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # Create DynamoDB table for storing private chats
        private_chats_table = dynamodb.Table(
            self,
            f'{env}-{name}-private-chats-table',
            table_name=f'{env}_{name.replace("-","_")}_private_chats',
            partition_key=dynamodb.Attribute(
                name='private_chat_id',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # Update lambda function to read and write to dynamodb tables
        users_table.grant_read_write_data(lambda_slack_function)
        public_chats_table.grant_read_write_data(lambda_slack_function)
        private_chats_table.grant_read_write_data(lambda_slack_function)


app = App()
SlackAppStack(
    app, 
    f'{os.environ["ENV"]}-{os.environ["NAME"]}'
)
app.synth()
