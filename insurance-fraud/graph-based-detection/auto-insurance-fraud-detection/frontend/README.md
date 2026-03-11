# Auto Insurance Fraud Detection - Frontend

Interactive web interface for visualizing and analyzing insurance fraud patterns using graph visualization.

## Features

- **Authentication**: Amazon Cognito-based JWT authentication with secure token storage
- **Secure Token Storage**: Tokens stored in memory with httpOnly cookie backup
- **Amazon CloudFront Delivery**: Content served via Amazon CloudFront with security headers
- **Graph Visualization**: Interactive D3.js graph with color-coded fraud risk
  - 🟢 Green: Low fraud risk (< 40%)
  - 🟡 Yellow: Medium fraud risk (40-70%)
  - 🔴 Red: High fraud risk (> 70%)
- **Interactive Elements**: Choose nodes/edges to view detailed properties
- **22 API Endpoints**: Full coverage of fraud detection capabilities (including logout)
- **Responsive Design**: Clean, modern UI
- **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options

## Setup

### 1. Configure the Application

The deployment script automatically generates `js/config.js` from CloudFormation outputs.

If you need to manually configure, edit `js/config.js`:

```javascript
const CONFIG = {
    region: 'us-east-1',
    cognito: {
        userPoolId: 'YOUR_USER_POOL_ID',      // From CloudFormation outputs
        clientId: 'YOUR_CLIENT_ID',            // From CloudFormation outputs
    },
    apiEndpoint: 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod'
};
```

**Note:** Demo user credentials are no longer stored in config for security.

### 2. Create User

Use the authentication script or AWS CLI to create a user:

```bash
cd ..
./scripts/authenticate.sh -u user@company.com -p YourSecurePassword123!
```

Or manually:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username user@company.com \
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password \
  --user-pool-id <USER_POOL_ID> \
  --username user@company.com \
  --password YourSecurePassword123! \
  --permanent
```

### 3. Get Configuration Values

Get the required values from CloudFormation:

```bash
# Get User Pool ID
aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text

# Get Client ID
aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text

# Get API Endpoint
aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text
```

### 4. Access the Application

The frontend is automatically deployed to CloudFront during stack deployment.

**CloudFront URL**: Get from CloudFormation outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text
```

**Or run locally**:

```bash
# Python 3
python3 -m http.server 8000

# Then open http://localhost:8000/login.html
```

### 5. Deploy to S3 (Optional - Already Done by Stack)

The CloudFormation stack automatically deploys the frontend to S3 and CloudFront.

If you need to manually update the frontend:

```bash
# Get bucket name from CloudFormation
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' \
  --output text)

# Upload files
aws s3 sync . s3://$BUCKET \
  --exclude ".DS_Store" \
  --exclude "README.md"

# Invalidate CloudFront cache
DISTRIBUTION=$(aws cloudformation describe-stacks \
  --stack-name auto-insurance-fraud-detection \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION \
  --paths "/*"
```

## Usage

### Login

1. Open CloudFront URL or `login.html`
2. Enter your email and password
3. Choose **Login**
4. Token is securely stored in memory with httpOnly cookie backup

### Navigation

The sidebar menu mirrors the API structure:

- **Claims**: Submit claims, view details, analyze claimants
- **Fraud Patterns**: Collision rings, professional witnesses, collusion
- **Fraud Networks**: Influential claimants, organized rings, connections
- **Analytics**: Trends, hotspots, anomalies, temporal patterns
- **Entities**: Repair shops, vehicles, medical providers

### Graph Interaction

- **Zoom**: Mouse wheel or pinch
- **Pan**: Drag the background
- **Move Nodes**: Drag individual nodes
- **View Details**: Choose nodes or edges to view popup with properties
- **Color Coding**: 
  - Green = Low fraud risk
  - Yellow = Medium fraud risk
  - Red = High fraud risk

## File Structure

```
frontend/
├── login.html              # Login page
├── index.html              # Main application
├── css/
│   └── styles.css          # All styles
├── js/
│   ├── config.js           # Configuration (edit this!)
│   ├── auth.js             # Cognito authentication
│   ├── api.js              # API client wrapper
│   ├── graph.js            # D3.js graph visualization
│   └── app.js              # Main application logic
└── README.md               # This file
```

## API Endpoints

All 22 endpoints are implemented:

**Authentication (2)**
- Login, Logout

**Claims Management (6)**
- Submit Claim, Claim Details, Claimant Claims, Risk Score, Claim Velocity, Fraud Analysis

**Fraud Patterns (4)**
- Collision Rings, Professional Witnesses, Collusion Indicators, Cross-Claim Patterns

**Fraud Networks (4)**
- Influential Claimants, Organized Rings, Connections, Isolated Rings

**Analytics (4)**
- Fraud Trends, Geographic Hotspots, Claim Anomalies, Temporal Patterns

**Entity Analysis (2)**
- Repair Shop Stats, Fraud Hubs, Vehicle Fraud History

## Troubleshooting

**Login fails**
- Verify User Pool ID and Client ID in `config.js`
- Ensure user exists in Amazon Cognito
- Check browser console for errors

**API calls fail**
- Verify API endpoint in `config.js`
- Check that AWS CloudFormation stack is deployed
- Verify AWS WAF isn't blocking requests
- Check browser console for 401/403 errors

**Graph doesn't render**
- Ensure D3.js is loading (check browser console)
- Verify API response has `nodes` and `edges` format
- Check that data is not empty

**CORS errors**
- Amazon API Gateway should have CORS enabled
- Check Amazon API Gateway configuration

## Security Notes

✅ **Production-Ready Security**:
- Tokens stored in memory (not sessionStorage)
- httpOnly cookies for defense in depth
- No hardcoded passwords in config
- Amazon CloudFront security headers (HSTS, CSP, X-Frame-Options)
- AWS WAF protection with rate limiting
- Request validation on Amazon API Gateway
- Proper logout endpoint

**Additional Recommendations**:
- Implement token refresh logic for long sessions
- Add MFA for sensitive operations
- Monitor AWS WAF logs for attack patterns
- Regular security audits

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- IE11: ❌ Not supported (requires D3.js v7)

## Dependencies

- **D3.js v7**: Loaded from CDN in `index.html`
- No build process required
- Pure vanilla JavaScript (ES6+)
