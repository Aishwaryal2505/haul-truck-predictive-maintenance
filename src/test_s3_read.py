"""
Step 5: Test that we can read the dashboard files from S3.

Uses the read-only login saved on your computer under the name
"powerbi-reader" (in C:\\Users\\<you>\\.aws\\credentials).
No keys are written in this file.
"""

import io

import boto3
import pandas as pd
from botocore.exceptions import ClientError, ProfileNotFound

BUCKET = "haul-truck-maintenance-aish2026"
REGION = "ap-southeast-2"
PROFILE = "powerbi-reader"
FILES = ["dashboard_latest.csv", "dashboard_daily.csv"]

try:
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
    s3 = session.client("s3")

    for key in FILES:
        response = s3.get_object(Bucket=BUCKET, Key=key)
        df = pd.read_csv(io.BytesIO(response["Body"].read()))
        print(f"OK: read {key} from S3 -> {len(df)} rows, {len(df.columns)} columns")

    print("\nSuccess. Python can read your files from AWS.")

except ProfileNotFound:
    print(f"Could not find the login named '{PROFILE}'.")
    print("Check that C:\\Users\\<you>\\.aws\\credentials exists and the first line is [powerbi-reader].")

except ClientError as error:
    code = error.response["Error"]["Code"]
    print(f"AWS said no: {code}")
    print("Check the bucket name, the file names, and that the policy is attached to powerbi-reader.")
