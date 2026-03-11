from aws_lambda_powertools import Logger

logger = Logger()

import boto3
import os
import json


@logger.inject_lambda_context
def lambda_handler(event, context):
    neptune_endpoint = os.environ['NEPTUNE_ENDPOINT']
    role_arn = os.environ['NEPTUNE_ML_ROLE_ARN']

    if 'trainingJobId' in event:
        training_job_id = event['trainingJobId']
    elif 'trainingResult' in event:
        training_job_id = event['trainingResult']['trainingJobId']
    elif 'id' in event:
        training_job_id = event['id']
    else:
        raise ValueError(f"Cannot find trainingJobId in event: {event}")

    neptune_client = boto3.client(
        'neptunedata',
        endpoint_url=f'https://{neptune_endpoint}:8182'
    )

    response = neptune_client.get_ml_model_training_job(
        id=training_job_id,
        neptuneIamRoleArn=role_arn
    )

    status = response['status']
    logger.info(f"Training job {training_job_id} response: {json.dumps(response, default=str)}")

    result = {
        'trainingJobId': training_job_id,
        'status': status,
        'isComplete': status in ['Completed', 'Failed', 'Stopped']
    }

    if 'failureReason' in response:
        result['failureReason'] = response['failureReason']

    return result
