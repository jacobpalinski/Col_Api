import requests
import json
import os
import boto3
import datetime
from dotenv import load_dotenv

load_dotenv()

def get_data(file_prefix: str):
    boto3_s3 = boto3.client('s3', aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY'))
    current_date = datetime.date.today().strftime('%Y%m%d')
    file = boto3_s3.get_object(Bucket = os.environ.get('S3_BUCKET_RAW'), Key = file_prefix + current_date)
    contents = file['Body'].read().decode('utf-8')
    return json.loads(contents)

def put_data(file_prefix: str, data: list, bucket_type: str):
    data_json = json.dumps(data)
    boto3_s3 = boto3.client('s3', aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID'), aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY'))
    current_date = datetime.date.today().strftime('%Y%m%d')
    if bucket_type == 'raw':
        boto3_s3.put_object(Bucket = os.environ.get('S3_BUCKET_RAW'), Key = file_prefix + current_date, Body = data_json)
    elif bucket_type == 'transformed':
        boto3_s3.put_object(Bucket = os.environ.get('S3_BUCKET_TRANSFORMED'), Key = file_prefix + current_date, Body = data_json)
    else:
        raise Exception('bucket_type must be either "raw" or "transformed"')
    
    