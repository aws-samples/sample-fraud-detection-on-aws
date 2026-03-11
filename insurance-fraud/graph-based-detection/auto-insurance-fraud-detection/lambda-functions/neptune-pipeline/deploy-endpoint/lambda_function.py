from aws_lambda_powertools import Logger

logger = Logger()

import boto3
import os

@logger.inject_lambda_context
def lambda_handler(event, context):
    neptune_endpoint = os.environ['NEPTUNE_ENDPOINT']
    endpoint_name = os.environ.get('ENDPOINT_NAME', 'auto-insurance-fraud-endpoint')
    role_arn = os.environ.get('NEPTUNE_ML_ROLE_ARN')
    parameter_group_name = os.environ.get('PARAMETER_GROUP_NAME', 'neptunedbclusterparametergroup-hailxvqmsl4c')
    instance_identifier = os.environ.get('INSTANCE_IDENTIFIER', 'auto-insurance-fraud-instance')
    
    # Handle different event structures
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
    
    try:
        # Try to delete old endpoint if exists
        neptune_client.delete_ml_endpoint(
            id=endpoint_name,
            neptuneIamRoleArn=role_arn
        )
    except Exception:
        logger.info("No existing ML endpoint to delete, proceeding with creation")
    
    # Create new endpoint with trained model
    response = neptune_client.create_ml_endpoint(
        id=endpoint_name,
        mlModelTrainingJobId=training_job_id,
        instanceType='ml.m5.xlarge',
        instanceCount=1,
        neptuneIamRoleArn=role_arn
    )
    
    # Get the actual SageMaker endpoint name from the response
    sagemaker_endpoint_name = response['id']
    
    # Check if parameter group already has this endpoint configured
    neptune_rds_client = boto3.client('neptune')
    
    params = neptune_rds_client.describe_db_cluster_parameters(
        DBClusterParameterGroupName=parameter_group_name,
        Source='user'
    )

    current_endpoint = None
    for param in params['Parameters']:
        if param['ParameterName'] == 'neptune_ml_endpoint':
            current_endpoint = param['ParameterValue']
            break

    if current_endpoint == sagemaker_endpoint_name:
        logger.info(f"Endpoint {sagemaker_endpoint_name} already configured in parameter group")
        return {
            'statusCode': 200,
            'endpointId': response['id'],
            'mlEndpointName': sagemaker_endpoint_name,
            'message': 'Endpoint created, parameter group already up to date'
        }
    else:
        neptune_rds_client.modify_db_cluster_parameter_group(
            DBClusterParameterGroupName=parameter_group_name,
            Parameters=[
                {
                    'ParameterName': 'neptune_ml_endpoint',
                    'ParameterValue': sagemaker_endpoint_name,
                    'ApplyMethod': 'pending-reboot'
                }
            ]
        )

        # Reboot Neptune instance to apply parameter changes
        neptune_rds_client.reboot_db_instance(
            DBInstanceIdentifier=instance_identifier
        )

    return {
        'statusCode': 200,
        'endpointId': response['id'],
        'mlEndpointName': sagemaker_endpoint_name,
        'message': 'Endpoint created and Neptune parameter group updated'
    }
