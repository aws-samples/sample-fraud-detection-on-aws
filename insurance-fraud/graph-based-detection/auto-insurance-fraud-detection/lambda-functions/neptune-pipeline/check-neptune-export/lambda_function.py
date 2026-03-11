import boto3
import os

def lambda_handler(event, context):
    batch = boto3.client('batch')
    
    export_job_id = event['exportJobId']
    s3_bucket = os.environ['S3_BUCKET']
    
    response = batch.describe_jobs(jobs=[export_job_id])
    
    if not response['jobs']:
        return {
            'exportJobId': export_job_id,
            'status': 'NOT_FOUND',
            'isComplete': True
        }
    
    status = response['jobs'][0]['status']
    
    return {
        'exportJobId': export_job_id,
        'status': status,
        'isComplete': status == 'SUCCEEDED',
        'isFailed': status == 'FAILED',
        'outputS3Path': f's3://{s3_bucket}/neptune-export/'
    }
