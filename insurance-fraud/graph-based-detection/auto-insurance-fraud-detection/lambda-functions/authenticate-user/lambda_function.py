import json
import os
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig, Response
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

logger = Logger()
tracer = Tracer()

cors_config = CORSConfig(allow_origin=os.environ.get('ALLOWED_ORIGIN', '*'), max_age=300)
app = APIGatewayRestResolver(cors=cors_config)

cognito = boto3.client('cognito-idp')

USER_POOL_ID = os.environ['USER_POOL_ID']
CLIENT_ID = os.environ['CLIENT_ID']
DEMO_USERS = os.environ.get('DEMO_USERS', '').split(',')


@app.get("/auth/users")
@tracer.capture_method
def get_users():
    users = [{'email': email.strip()} for email in DEMO_USERS if email.strip()]
    return {'users': users}


@app.post("/auth/logout")
@tracer.capture_method
def logout():
    return Response(
        status_code=200,
        content_type='application/json',
        body=json.dumps({'success': True}),
        headers={'Set-Cookie': 'fraud_detection_token=; HttpOnly; Secure; SameSite=Strict; Max-Age=0; Path=/'}
    )


@app.post("/auth/refresh")
@tracer.capture_method
def refresh():
    body = app.current_event.json_body or {}
    refresh_token = body.get('refreshToken')
    if not refresh_token:
        return {'error': 'refreshToken required'}, 400
    try:
        response = cognito.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={'REFRESH_TOKEN': refresh_token}
        )
        token = response['AuthenticationResult']['IdToken']
        expires_in = response['AuthenticationResult']['ExpiresIn']
        return {'token': token, 'expiresIn': expires_in}
    except ClientError:
        return {'error': 'Refresh failed'}, 401


@app.post("/auth/login")
@tracer.capture_method
def login():
    body = app.current_event.json_body
    username = body.get('username')
    password = body.get('password')

    if not username or not password:
        return {'error': 'Username and password required'}, 400

    try:
        response = cognito.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': username, 'PASSWORD': password}
        )

        token = response['AuthenticationResult']['IdToken']
        refresh_token = response['AuthenticationResult'].get('RefreshToken', '')
        expires_in = response['AuthenticationResult']['ExpiresIn']

        return Response(
            status_code=200,
            content_type='application/json',
            body=json.dumps({'token': token, 'refreshToken': refresh_token, 'expiresIn': expires_in}),
            headers={
                'Set-Cookie': f'fraud_detection_token={token}; HttpOnly; Secure; SameSite=Strict; Max-Age={expires_in}; Path=/',
                'Access-Control-Expose-Headers': 'Set-Cookie'
            }
        )

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NotAuthorizedException':
            return {'error': 'Invalid credentials'}, 401
        elif error_code == 'UserNotFoundException':
            return {'error': 'User not found'}, 404
        else:
            logger.exception("Cognito authentication error")
            return {'error': 'Authentication failed'}, 500


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    response = app.resolve(event, context)

    if 'headers' not in response:
        response['headers'] = {}
    response['headers']['Access-Control-Allow-Origin'] = os.environ.get('ALLOWED_ORIGIN', '*')
    response['headers']['Access-Control-Allow-Credentials'] = 'true'
    response['headers'].setdefault('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response['headers'].setdefault('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')

    return response
