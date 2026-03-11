import boto3
import os

def lambda_handler(event, context):
    ml_endpoint_name = event.get('mlEndpointName')
    if not ml_endpoint_name:
        raise Exception("No ML endpoint name found in event")
    
    lambda_client = boto3.client('lambda')
    
    # Update FraudDetectionFunction environment variables
    response = lambda_client.update_function_configuration(
        FunctionName='FraudDetectionFunction',
        Environment={
            'Variables': {
                'NEPTUNE_ENDPOINT': os.environ['NEPTUNE_ENDPOINT'],
                'NEPTUNE_PORT': '8182',
                'ML_ENDPOINT': ml_endpoint_name,
                'ML_ROLE_ARN': os.environ['NEPTUNE_ML_ROLE_ARN']
            }
        }
    )
    
    return {
        'statusCode': 200,
        'message': f'FraudDetectionFunction updated with ML endpoint: {ml_endpoint_name}',
        'mlEndpointName': ml_endpoint_name
    }
