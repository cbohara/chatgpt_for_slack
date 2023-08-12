import os
from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda,
    aws_lambda_python_alpha as lambda_python,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
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
        lambda_slack_function_name=f'{env}-{name}-lambda-slack-function'
        lambda_slack_function = lambda_python.PythonFunction(
            self,
            lambda_slack_function_name,
            function_name=lambda_slack_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_9,
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
                'SLACK_APP_URL': os.environ['SLACK_APP_URL'],
                'DDB_USERS_ID': os.environ['DDB_USERS_ID'],
                'DDB_USERS_EMAIL': os.environ['DDB_USERS_EMAIL'],
                'DDB_PUBLIC_CHATS': os.environ['DDB_PUBLIC_CHATS'],
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
        )

        lambda_slack_function_log_group = logs.LogGroup(
            self,
            f'{lambda_slack_function_name}-logs',
            log_group_name=f"/aws/lambda/{lambda_slack_function_name}",
            retention=logs.RetentionDays.ONE_MONTH
        )

        # Create function URL
        function_url = lambda_slack_function.add_function_url(
            auth_type=aws_lambda.FunctionUrlAuthType.NONE,
        )

        # Creating Lambda function that runs on a daily schedule to disable free trials when completed
        lambda_cron_function_name=f'{env}-{name}-lambda-cron-function'
        lambda_cron_function = lambda_python.PythonFunction(
            self,
            lambda_cron_function_name,
            function_name=lambda_cron_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            entry='lambda_cron',
            index='lambda_handler.py',
            handler='handler',
            environment={
                'DDB_USERS_ID': os.environ['DDB_USERS_ID'],
                'FREE_TRIAL_DAYS': os.environ['FREE_TRIAL_DAYS'],
            },
            timeout=Duration.seconds(300),
            role=lambda_role,
        )

        lambda_cron_function_log_group = logs.LogGroup(
            self,
            f'{lambda_cron_function_name}-logs',
            log_group_name=f"/aws/lambda/{lambda_cron_function_name}",
            retention=logs.RetentionDays.ONE_MONTH
        )

        # Create the CloudWatch Events rule with a cron schedule
        rule = events.Rule(
            self,
            'DailyLambdaSchedule',
            schedule=events.Schedule.cron(minute='0', hour='0'),
        )

        # Add the Lambda function as a target for the CloudWatch Events rule
        rule.add_target(targets.LambdaFunction(lambda_cron_function))

        # Creating Lambda function that will be triggered by Stripe events
        lambda_stripe_function_name=f'{env}-{name}-lambda-stripe-function'
        lambda_stripe_function = lambda_python.PythonFunction(
            self,
            lambda_stripe_function_name,
            function_name=lambda_stripe_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            entry='lambda_stripe',
            index='lambda_handler.py',
            handler='handler',
            environment={
                'STRIPE_SECRET': os.environ['STRIPE_SECRET'],
                'DDB_USERS_ID': os.environ['DDB_USERS_ID'],
                'DDB_USERS_EMAIL': os.environ['DDB_USERS_EMAIL'],
            },
            timeout=Duration.seconds(300),
            role=lambda_role,
        )

        lambda_stripe_function_log_group = logs.LogGroup(
            self,
            f'{lambda_stripe_function_name}-logs',
            log_group_name=f"/aws/lambda/{lambda_stripe_function_name}",
            retention=logs.RetentionDays.ONE_MONTH
        )

        # Create function URL
        function_url = lambda_stripe_function.add_function_url(
            auth_type=aws_lambda.FunctionUrlAuthType.NONE,
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

        # Create DynamoDB table for storing users - primary access pattern is stripe events
        users_email_table = dynamodb.Table(
            self,
            f'{env}-{name}-users-email-table',
            table_name=f'{env}_{name.replace("-","_")}_users_email',
            partition_key=dynamodb.Attribute(
                name='email',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # Create DynamoDB table for storing users - primary access pattern is slack app
        users_id_table = dynamodb.Table(
            self,
            f'{env}-{name}-users-id-table',
            table_name=f'{env}_{name.replace("-","_")}_users_id',
            partition_key=dynamodb.Attribute(
                name='slack_id',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # Create DynamoDB secondary index to access via plan_type - primary access pattern is cron lambda to deactive trials
        users_id_table.add_global_secondary_index(
            index_name='plan_type_index',
            partition_key=dynamodb.Attribute(
                name='plan_type',
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name='slack_id',
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
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
        users_email_table.grant_read_write_data(lambda_slack_function)
        users_id_table.grant_read_write_data(lambda_slack_function)
        users_id_table.grant_read_write_data(lambda_cron_function)
        public_chats_table.grant_read_write_data(lambda_slack_function)
        private_chats_table.grant_read_write_data(lambda_slack_function)


app = App()
SlackAppStack(
    app, 
    f'{os.environ["ENV"]}-{os.environ["NAME"]}'
)
app.synth()
