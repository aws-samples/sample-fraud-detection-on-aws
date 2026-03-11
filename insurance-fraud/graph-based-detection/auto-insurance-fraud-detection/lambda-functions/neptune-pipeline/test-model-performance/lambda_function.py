import boto3
from aws_lambda_powertools import Logger

logger = Logger()
sagemaker = boto3.client('sagemaker')


@logger.inject_lambda_context
def lambda_handler(event, context):
    """Test model performance after training to detect poisoning"""
    
    logger.info("Starting model performance testing")
    
    training_job_id = event.get('trainingJobId')

    # Performance thresholds
    MIN_PRECISION = 0.70
    MIN_RECALL = 0.65
    MAX_PERFORMANCE_DROP = 0.10  # 10%
    
    test_results = {
        'checks': [],
        'valid': True,
        'metrics': {}
    }
    
    # In production: run actual inference on holdout test set
    # For now: simulate performance metrics
    
    # Simulate model metrics
    precision = 0.82
    recall = 0.78
    f1_score = 2 * (precision * recall) / (precision + recall)
    
    test_results['metrics'] = {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }
    
    # Check 1: Precision threshold
    if precision < MIN_PRECISION:
        test_results['valid'] = False
        test_results['checks'].append({
            'name': 'precision_threshold',
            'status': 'failed',
            'message': f'Precision {precision:.2%} below minimum {MIN_PRECISION:.2%}'
        })
    else:
        test_results['checks'].append({
            'name': 'precision_threshold',
            'status': 'passed',
            'message': f'Precision {precision:.2%} meets threshold'
        })
    
    # Check 2: Recall threshold
    if recall < MIN_RECALL:
        test_results['valid'] = False
        test_results['checks'].append({
            'name': 'recall_threshold',
            'status': 'failed',
            'message': f'Recall {recall:.2%} below minimum {MIN_RECALL:.2%}'
        })
    else:
        test_results['checks'].append({
            'name': 'recall_threshold',
            'status': 'passed',
            'message': f'Recall {recall:.2%} meets threshold'
        })
    
    # Check 3: Compare to baseline (previous model)
    # In production: load previous model metrics from S3/DynamoDB
    baseline_f1 = 0.79
    performance_change = (f1_score - baseline_f1) / baseline_f1
    
    if performance_change < -MAX_PERFORMANCE_DROP:
        test_results['valid'] = False
        test_results['checks'].append({
            'name': 'baseline_comparison',
            'status': 'failed',
            'message': f'Performance dropped {abs(performance_change):.1%} from baseline'
        })
    else:
        test_results['checks'].append({
            'name': 'baseline_comparison',
            'status': 'passed',
            'message': f'Performance change: {performance_change:+.1%} from baseline'
        })
    
    if test_results['valid']:
        logger.info("Model performance testing PASSED", extra={'metrics': test_results['metrics']})
    else:
        logger.error("Model performance testing FAILED", extra={'results': test_results})
    
    return {
        'statusCode': 200 if test_results['valid'] else 400,
        'valid': test_results['valid'],
        'results': test_results,
        'trainingJobId': training_job_id
    }
