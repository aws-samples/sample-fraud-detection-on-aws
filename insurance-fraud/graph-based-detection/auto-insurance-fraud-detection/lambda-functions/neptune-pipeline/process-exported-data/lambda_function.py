import boto3
import os
import json
from datetime import datetime
from botocore.config import Config
from aws_lambda_powertools import Logger

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(event, context):
    logger.info("Processing Neptune export data", extra={"event_keys": list(event.keys())})

    neptune_endpoint = os.environ['NEPTUNE_ENDPOINT']
    s3_bucket = os.environ.get('S3_BUCKET')

    # Also check event for s3Bucket
    if not s3_bucket:
        s3_bucket = event.get('s3Bucket')

    if not s3_bucket:
        raise ValueError("S3_BUCKET not found in environment or event")

    role_arn = os.environ['NEPTUNE_ML_ROLE_ARN']

    # Get target property from event
    target_property = event.get('targetProperty', 'fraudScore')
    logger.info(f"Target property: {target_property}")
    logger.info(f"Using S3 bucket: {s3_bucket}")

    # Find the latest export folder in S3
    s3_client = boto3.client('s3')

    # List all export folders
    response = s3_client.list_objects_v2(
        Bucket=s3_bucket,
        Prefix='neptune-export/',
        Delimiter='/'
    )

    if 'CommonPrefixes' not in response:
        raise Exception("No export folders found in S3")

    # Get the latest folder (they're sorted by timestamp), excluding "failed" folder
    valid_folders = [prefix for prefix in response['CommonPrefixes'] if not prefix['Prefix'].endswith('failed/')]
    if not valid_folders:
        raise Exception("No valid export folders found in S3")

    latest_folder = sorted(valid_folders, key=lambda x: x['Prefix'])[-1]['Prefix']
    input_s3_path = f's3://{s3_bucket}/{latest_folder}'
    logger.info(f"Using export folder: {latest_folder}")
    logger.info(f"Input S3 path: {input_s3_path}")

    # Use the existing training-data-configuration.json file from the export
    config_filename = 'training-data-configuration.json'
    logger.info(f"Using existing config file: {config_filename}")

    # Configure boto3 with longer timeouts
    config = Config(
        read_timeout=900,
        connect_timeout=60,
        retries={'max_attempts': 3}
    )

    neptune_client = boto3.client(
        'neptunedata',
        endpoint_url=f'https://{neptune_endpoint}:8182',
        config=config
    )

    processing_id = f"processing-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    logger.info(f"Starting processing job: {processing_id}")

    # Get instance type from event (set by CheckQuotaStatus) or use default
    processing_instance_type = event.get('processingInstanceType', 'ml.m5.xlarge')
    logger.info(f"Using processing instance type: {processing_instance_type}")

    try:
        # Start ML data processing job
        response = neptune_client.start_ml_data_processing_job(
            id=processing_id,
            inputDataS3Location=input_s3_path,
            processedDataS3Location=f's3://{s3_bucket}/neptune-processed/',
            sagemakerIamRoleArn=os.environ['SAGEMAKER_ML_ROLE_ARN'],
            neptuneIamRoleArn=role_arn,
            configFileName=config_filename,
            modelType='heterogeneous',
            processingInstanceType=processing_instance_type,
            processingInstanceVolumeSizeInGB=20
        )

        logger.info(f"Processing job started successfully: {json.dumps(response, default=str)}")

        return {
            'statusCode': 200,
            'processingJobId': response['id'],
            'configFile': config_filename,
            'targetProperty': target_property,
            's3Bucket': s3_bucket,
            'trainingInstanceType': event.get('trainingInstanceType', 'ml.m5.xlarge')
        }
    except Exception as e:
        logger.info(f"Error starting processing job: {str(e)}")
        raise e
