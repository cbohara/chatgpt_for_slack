import argparse
import subprocess
from dotenv import load_dotenv


parser = argparse.ArgumentParser()
#parser.add_argument('--config', dest='config')
args = parser.parse_args()

load_dotenv(dotenv_path='.env')
#load_dotenv(dotenv_path=args.config)
subprocess.call(['cdk', 'deploy', '-v'], cwd='.')