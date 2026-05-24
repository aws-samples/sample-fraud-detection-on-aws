"""
API Gateway Lambda REQUEST authorizer that validates a Cognito JWT carried in
the `__Host-fraud_detection_token` cookie.

This moves authentication away from the `Authorization: Bearer` header (which
requires the token to live in JS-readable sessionStorage) toward an httpOnly
cookie set by the /auth/login handler. The cookie is inaccessible to
JavaScript, which hardens the app against XSS token theft.

Returns an IAM allow/deny policy. The authorizer cache key is the full
Cookie header value (see IdentitySource in api.yaml).
"""
import json
import logging
import os

import jwt
from jwt import PyJWKClient, ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

USER_POOL_ID = os.environ['USER_POOL_ID']
USER_POOL_CLIENT_ID = os.environ['USER_POOL_CLIENT_ID']
REGION = os.environ.get('AWS_REGION', 'us-east-2')
COOKIE_NAME = os.environ.get('COOKIE_NAME', '__Host-fraud_detection_token')

JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"

# Module-level JWKS client so keys are cached across warm invocations
_jwks_client = PyJWKClient(JWKS_URL, cache_keys=True, lifespan=3600)


def _extract_token(event):
    """Pull the JWT out of the Cookie header. Returns None if not found."""
    headers = event.get('headers') or {}
    # API Gateway may use any casing for header keys
    cookie_header = None
    for key, value in headers.items():
        if key.lower() == 'cookie':
            cookie_header = value
            break
    if not cookie_header:
        return None

    # Cookie header format: "k1=v1; k2=v2; ..."
    for part in cookie_header.split(';'):
        part = part.strip()
        if part.startswith(f"{COOKIE_NAME}="):
            return part[len(COOKIE_NAME) + 1:]
    return None


def _validate_token(token):
    """Verify the JWT against the Cognito user pool's JWKS. Returns decoded
    claims, or raises InvalidTokenError."""
    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    # Cognito issues both ID tokens (aud = client_id) and Access tokens (no
    # aud, client_id is in the 'client_id' claim). The login handler returns
    # the ID token as the cookie value, so verify with 'aud'.
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=['RS256'],
        audience=USER_POOL_CLIENT_ID,
        issuer=ISSUER,
    )


def _policy(principal_id, effect, method_arn, context=None):
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                # Grant (or deny) on the whole stage so a single cache entry
                # covers all the user's subsequent requests.
                'Resource': _stage_arn(method_arn),
            }],
        },
    }
    if context:
        policy['context'] = context
    return policy


def _stage_arn(method_arn):
    """Convert 'arn:aws:execute-api:region:acct:apiId/stage/METHOD/path/...'
    to 'arn:aws:execute-api:region:acct:apiId/stage/*/*' for cache reuse."""
    parts = method_arn.split(':')
    # parts[5] looks like 'apiId/stage/METHOD/resource/path'
    api_gw = parts[5].split('/')
    return ':'.join(parts[:5]) + ':' + '/'.join(api_gw[:2]) + '/*/*'


def lambda_handler(event, context):
    method_arn = event.get('methodArn', '*')

    token = _extract_token(event)
    if not token:
        logger.info("No auth cookie present; denying")
        raise Exception('Unauthorized')  # API Gateway translates to 401

    try:
        claims = _validate_token(token)
    except ExpiredSignatureError:
        logger.info("Expired JWT; denying")
        raise Exception('Unauthorized')
    except InvalidTokenError as e:
        logger.warning(f"Invalid JWT: {e}")
        raise Exception('Unauthorized')
    except Exception as e:
        # JWKS fetch, network, etc.
        logger.error(f"Authorizer error: {e}", exc_info=True)
        raise Exception('Unauthorized')

    principal_id = claims.get('sub', 'unknown')
    context_out = {
        'username': str(claims.get('cognito:username', '')),
        'email': str(claims.get('email', '')),
        'sub': str(principal_id),
    }
    logger.info(f"Authorized sub={principal_id}")
    return _policy(principal_id, 'Allow', method_arn, context_out)
