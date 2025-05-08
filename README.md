# ChatGPT for Slack app

Local setup
```
python3.9 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Run unit tests
```
python -m pytest tests/test_lambda_slack.py
```

Deploy to AWS
```
python cdk_deploy.py --config .env.dev
```