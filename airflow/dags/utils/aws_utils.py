import requests
import json
import os
import boto3
import datetime
from dotenv import load_dotenv
from typing import Union

# Load Environment Variables
load_dotenv()

# Retrieve json file from S3 Bucket
def get_data(file_prefix: str) -> None:
    boto3_s3 = boto3.client('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    current_date = datetime.date.today().strftime('%Y%m%d')
    if file_prefix == 'locations.json':
        file = boto3_s3.get_object(Bucket=os.environ.get('S3_BUCKET_RAW'), Key=file_prefix)
    else:
        file = boto3_s3.get_object(Bucket=os.environ.get('S3_BUCKET_RAW'), Key=file_prefix + current_date)
    contents = file['Body'].read().decode('utf-8')
    return json.loads(contents)

# Put json file into S3 Bucket
def put_data(file_prefix: str, data: list, bucket_type: str) -> Union[None, Exception]:
    data_json = json.dumps(data)
    boto3_s3 = boto3.client('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))
    current_date = datetime.date.today().strftime('%Y%m%d')
    if bucket_type == 'raw':
        boto3_s3.put_object(Bucket=os.environ.get('S3_BUCKET_RAW'), Key=file_prefix + current_date, Body=data_json, 
        ContentType='application/json')
    elif bucket_type == 'transformed':
        boto3_s3.put_object(Bucket=os.environ.get('S3_BUCKET_TRANSFORMED'), Key=file_prefix + current_date, Body=data_json,
        ContentType='application/json')
    else:
        raise Exception('bucket_type must be either "raw" or "transformed"')
    
    
