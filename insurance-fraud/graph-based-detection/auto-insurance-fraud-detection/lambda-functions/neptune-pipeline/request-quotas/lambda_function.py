import boto3

# Processing instance options (only need one)
PROCESSING_QUOTAS = [
    {'QuotaCode': 'L-0307F515', 'InstanceType': 'ml.m5.xlarge', 'MinValue': 1},
]

# Training instance options (will use first available)
TRAINING_QUOTAS = [
    {'QuotaCode': 'L-CCE2AFA6', 'InstanceType': 'ml.m5.xlarge', 'MinValue': 2},
    {'QuotaCode': 'L-611FA074', 'InstanceType': 'ml.m5.large', 'MinValue': 2},
    {'QuotaCode': 'L-A373146E', 'InstanceType': 'ml.m4.xlarge', 'MinValue': 2},
    {'QuotaCode': 'L-E2BB44FE', 'InstanceType': 'ml.c5.xlarge', 'MinValue': 2},
]

def lambda_handler(event, context):
    client = boto3.client('service-quotas')
    requests = []
    
    all_quotas = PROCESSING_QUOTAS + TRAINING_QUOTAS
    
    for quota in all_quotas:
        try:
            resp = client.get_service_quota(ServiceCode='sagemaker', QuotaCode=quota['QuotaCode'])
            current = resp['Quota']['Value']
            
            if current >= quota['MinValue']:
                requests.append({'QuotaCode': quota['QuotaCode'], 'InstanceType': quota['InstanceType'], 'status': 'SUFFICIENT', 'current': current})
                continue
            
            req = client.request_service_quota_increase(
                ServiceCode='sagemaker',
                QuotaCode=quota['QuotaCode'],
                DesiredValue=float(quota['MinValue'])
            )
            requests.append({'QuotaCode': quota['QuotaCode'], 'InstanceType': quota['InstanceType'], 'status': 'REQUESTED'})
        except client.exceptions.ResourceAlreadyExistsException:
            requests.append({'QuotaCode': quota['QuotaCode'], 'InstanceType': quota['InstanceType'], 'status': 'PENDING'})
        except Exception as e:
            requests.append({'QuotaCode': quota['QuotaCode'], 'InstanceType': quota['InstanceType'], 'status': 'ERROR', 'error': str(e)})
    
    return {'quotaRequests': requests}
