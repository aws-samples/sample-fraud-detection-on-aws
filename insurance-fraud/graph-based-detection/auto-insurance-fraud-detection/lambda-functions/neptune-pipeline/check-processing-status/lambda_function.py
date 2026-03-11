from aws_lambda_powertools import Logger

logger = Logger()

import boto3
import os
import json


@logger.inject_lambda_context
def lambda_handler(event, context):
    neptune_endpoint = os.environ['NEPTUNE_ENDPOINT']
    role_arn = os.environ['NEPTUNE_ML_ROLE_ARN']

    # Handle different event structures
    if 'processingJobId' in event:
        processing_job_id = event['processingJobId']
    elif 'processingResult' in event:
        processing_job_id = event['processingResult']['processingJobId']
    elif 'id' in event:
        processing_job_id = event['id']
    else:
        raise ValueError(f"Cannot find processingJobId in event: {event}")

    logger.info(f"Checking processing job: {processing_job_id}")

    neptune_client = boto3.client(
        'neptunedata',
        endpoint_url=f'https://{neptune_endpoint}:8182'
    )

    response = neptune_client.get_ml_data_processing_job(
        id=processing_job_id,
        neptuneIamRoleArn=role_arn
    )

    logger.info(f"Neptune ML response: {json.dumps(response, default=str)}")

    status = response['status']

    if status == 'Failed':
        logger.info(f"Job failed. Full response: {json.dumps(response, default=str)}")
        failure_reason = response.get('failureReason', 'No failure reason provided')
        raise Exception(f"Data processing job {processing_job_id} failed: {failure_reason}")

    return {
        'processingJobId': processing_job_id,
        'status': status,
        'isComplete': status == 'Completed'
    }