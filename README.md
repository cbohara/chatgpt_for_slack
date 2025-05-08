# ChatGPT for Slack app

## Local

Local python setup
```
python3.9 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Run unit tests
```
python -m pytest tests/test_lambda_slack.py
```

## AWS

Install [Docker](docker.com)   

Install AWS CDK 
```
brew install node
npm install -g aws-cdk@2.65.0
```

Use CDK to deploy to AWS
```
python cdk_deploy.py --config .env.dev
```