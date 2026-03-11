from aws_lambda_powertools import Logger

logger = Logger()

import boto3
import os
from datetime import datetime

@logger.inject_lambda_context
def lambda_handler(event, context):
    neptune_endpoint = os.environ['NEPTUNE_ENDPOINT']
    s3_bucket = os.environ.get('S3_BUCKET') or event.get('s3Bucket')
    
    if not s3_bucket:
        raise ValueError("S3_BUCKET not found in environment or event")
    
    neptune_role_arn = os.environ['NEPTUNE_ML_ROLE_ARN']
    sagemaker_role_arn = os.environ['SAGEMAKER_ML_ROLE_ARN']
    
    processing_job_id = event.get('processingJobId') or event.get('exportJobId')
    if not processing_job_id:
        raise Exception("No processing job ID found in event")
    
    neptune_client = boto3.client(
        'neptunedata',
        endpoint_url=f'https://{neptune_endpoint}:8182'
    )
    
    training_id = f"training-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Get instance type from event (set by CheckQuotaStatus) or use default
    training_instance_type = event.get('trainingInstanceType', 'ml.m5.xlarge')
    logger.info(f"Using training instance type: {training_instance_type}")
    
    response = neptune_client.start_ml_model_training_job(
        id=training_id,
        dataProcessingJobId=processing_job_id,
        trainModelS3Location=f's3://{s3_bucket}/models/',
        sagemakerIamRoleArn=sagemaker_role_arn,
        neptuneIamRoleArn=neptune_role_arn,
        trainingInstanceType=training_instance_type,
        maxHPONumberOfTrainingJobs=4,
        maxHPOParallelTrainingJobs=2
    )
    
    return {
        'statusCode': 200,
        'trainingJobId': response['id'],
        's3Bucket': s3_bucket
    }
