import boto3

# Processing instance options
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
    
    # Check processing quota (need at least one)
    processing_instance = None
    for quota in PROCESSING_QUOTAS:
        resp = client.get_service_quota(ServiceCode='sagemaker', QuotaCode=quota['QuotaCode'])
        if resp['Quota']['Value'] >= quota['MinValue']:
            processing_instance = quota['InstanceType']
            break
    
    if not processing_instance:
        # Check if any processing quota request is pending
        for quota in PROCESSING_QUOTAS:
            reqs = client.list_requested_service_quota_change_history_by_quota(ServiceCode='sagemaker', QuotaCode=quota['QuotaCode'])
            pending = [r for r in reqs.get('RequestedQuotas', []) if r['Status'] in ['PENDING', 'CASE_OPENED']]
            if pending:
                return {'ready': False, 'status': 'PENDING', 'waiting': 'processing', 'quotaCode': quota['QuotaCode']}
        raise Exception("No processing instance quota available and no pending requests")
    
    # Check training quota (need at least one type available)
    training_instance = None
    for quota in TRAINING_QUOTAS:
        resp = client.get_service_quota(ServiceCode='sagemaker', QuotaCode=quota['QuotaCode'])
        if resp['Quota']['Value'] >= quota['MinValue']:
            training_instance = quota['InstanceType']
            break
    
    if not training_instance:
        # Check if any training quota request is pending
        for quota in TRAINING_QUOTAS:
            reqs = client.list_requested_service_quota_change_history_by_quota(ServiceCode='sagemaker', QuotaCode=quota['QuotaCode'])
            pending = [r for r in reqs.get('RequestedQuotas', []) if r['Status'] in ['PENDING', 'CASE_OPENED']]
            if pending:
                return {'ready': False, 'status': 'PENDING', 'waiting': 'training', 'quotaCode': quota['QuotaCode']}
        raise Exception("No training instance quota available and no pending requests")
    
    return {
        'ready': True,
        'status': 'APPROVED',
        'processingInstanceType': processing_instance,
        'trainingInstanceType': training_instance
    }
