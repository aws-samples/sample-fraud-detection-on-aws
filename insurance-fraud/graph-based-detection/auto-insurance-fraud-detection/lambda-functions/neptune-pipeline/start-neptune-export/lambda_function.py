import json
import os
import boto3
import logging
from datetime import datetime, timezone

client = boto3.client('batch')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    neptune_endpoint = os.environ['NEPTUNE_ENDPOINT']
    s3_bucket = os.environ['S3_BUCKET']
    job_queue = os.environ['JOB_QUEUE']
    job_definition = os.environ['JOB_DEFINITION']
    neptune_export_jar_s3_uri = os.environ['NEPTUNE_EXPORT_JAR_S3_URI']
    region = os.environ['AWS_REGION']
    max_file_descriptor_count = os.environ.get('MAX_FILE_DESCRIPTOR_COUNT', '10000')
    vcpus = os.environ.get('JOB_VCPUS', '8')
    memory_gb = int(os.environ.get('JOB_MEMORY_GB', '8'))
    
    json_payload = {
        'command': 'export-pg',
        'outputS3Path': f's3://{s3_bucket}/neptune-export/',
        'params': {
            'endpoint': f'{neptune_endpoint}:8182',
            'profile': 'neptune_ml',
            'useIamAuth': True
        },
        'additionalParams': {
            'neptune_ml': {
                'version': 'v2.0',
                'targets': [
                    {'node': 'fraudEntity', 'property': 'fraudScore', 'type': 'regression'}
                ],
                'features': [
                    {'node': 'claim', 'property': 'amount', 'type': 'numerical'},
                    {'node': 'claim', 'property': 'isFraud', 'type': 'category'},
                    {'node': 'accident', 'property': 'accidentType', 'type': 'category'},
                    {'node': 'accident', 'property': 'maneuverType', 'type': 'category'},
                    {'node': 'accident', 'property': 'policeVerified', 'type': 'category'},
                    {'node': 'repairShop', 'property': 'suspicious', 'type': 'category'},
                    {'node': 'repairShop', 'property': 'rating', 'type': 'numerical'},
                    {'node': 'witness', 'property': 'professional', 'type': 'category'},
                    {'node': 'medicalProvider', 'property': 'specialty', 'type': 'category'},
                    {'node': 'vehicle', 'property': 'year', 'type': 'numerical'}
                ]
            }
        }
    }
    
    # Install AWS CLI and Java
    command = f"yum install -y aws-cli java-21-amazon-corretto-headless && mkdir -p /tmp/neptune && cd /tmp/neptune && aws s3 cp {neptune_export_jar_s3_uri} neptune-export.jar && export SERVICE_REGION=\"{region}\" && java -Xms{memory_gb}g -Xmx{memory_gb}g -jar neptune-export.jar nesvc --clean --root-path /tmp/neptune/tmp --max-file-descriptor-count {max_file_descriptor_count} --json '{json.dumps(json_payload)}'"
    
    logger.info(f'Batch command: {command}')
    
    response = client.submit_job(
        jobName=f'neptune-export-{round(datetime.now(timezone.utc).timestamp() * 1000)}',
        jobQueue=job_queue,
        jobDefinition=job_definition,
        containerOverrides={
            'command': ['sh', '-c', command],
            'resourceRequirements': [{'value': vcpus, 'type': 'VCPU'}, {'value': str(memory_gb * 1000), 'type': 'MEMORY'}]
        }
    )
    
    return {'statusCode': 200, 'exportJobId': response['jobId'], 's3Bucket': s3_bucket}
