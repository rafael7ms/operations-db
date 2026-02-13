# AWS Serverless Deployment for opsdb

## Overview

This document outlines the serverless architecture for deploying opsdb on AWS with VPN connectivity to on-premises VPC.

---

## Architecture: Serverless with VPN

```
+---------------------+
|     On-Prem VPC     |
|                     |
|  [VPN Gateway] <---> VPN Tunnel
|                     |
+----------+----------+
           |
+----------v----------+
|     AWS VPC         |
|                     |
|  +----------------+ |
|  |   Private Subnet | |
|  |   RDS PostgreSQL | |
|  |   (No Public IP) | |
|  +----------------+ |
|           |         |
|  +--------v--------+ |
|  |   Lambda         | |
|  |   (Flask API)    | |
|  +----------------+ |
|           |         |
|  +--------v--------+ |
|  |  API Gateway     | |
|  |  (HTTP API)      | |
|  +----------------+ |
|                     |
|  +----------------+ |
|  |   S3 Bucket      | |
|  |   (uploads)      | |
|  +----------------+ |
+---------------------+
```

---

## AWS Services Required

### 1. RDS PostgreSQL (Private Endpoint)
| Component | Configuration |
|-----------|--------------|
| Engine | PostgreSQL 15.x |
| Instance Class | db.t4g.micro (Free Tier) |
| Storage | 20GB GP3 |
| Public Access | **Disabled** |
| VPC | Same as Lambda |
| Subnets | Private subnets only |
| Security Group | Allow from Lambda only |

**Why**: No public IP needed - VPN provides secure access.

### 2. Lambda Function
| Component | Configuration |
|-----------|--------------|
| Runtime | Python 3.11 |
| Memory | 512MB |
| Timeout | 30 seconds |
| VPC | Same as RDS (private subnets) |
| Security Group | Outbound to RDS |

**Why**: Serverless, scales to zero, pay per use.

### 3. API Gateway (HTTP API)
| Component | Configuration |
|-----------|--------------|
| Type | HTTP API (cheaper than REST) |
| Integration | Lambda Proxy |
| Auth | Cognito or API Keys |
| Custom Domain | Optional (with ACM cert) |

**Why**: Low-cost HTTP API for external access.

### 4. VPC Configuration
| Component | Configuration |
|-----------|--------------|
| CIDR | 10.0.0.0/16 |
| Private Subnets | 2 (for redundancy) |
| NAT Gateway | None (private resources only) |
| VPN Gateway | Customer Gateway + VPN Gateway |

---

## VPN Setup

### Site-to-Site VPN
```
On-Premises VPC (192.168.0.0/16) <-> AWS VPC (10.0.0.0/16)
```

**Steps**:
1. Create Customer Gateway in AWS (on-premises VPN device)
2. Create VPN Gateway in AWS
3. Create VPN Connection
4. Configure on-premises VPN device

### Route Tables
| Subnet | Route |
|--------|-------|
| Private | 192.168.0.0/16 -> VPN Gateway |

---

## Cost Estimation (Serverless + VPN)

| Component | Free Tier | After Free Tier |
|-----------|-----------|-----------------|
| Lambda | 1M requests/month | $0.20 per 1M |
| API Gateway HTTP | 1B bytes out | $1.00 per 1M requests |
| RDS t4g.micro | 750 hours/month | $0-5/month |
| S3 | 5GB storage | $0.23/month |
| VPN | $0.05/hour | ~$36/month |
| **Total** | **$0-5/month** | **~$40-50/month** |

---

## AWS CLI Setup

### 1. Create VPC with VPN
```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24

# Create VPN Gateway
aws ec2 create-vpn-gateway --type ipsec.1

# Create Customer Gateway
aws ec2 create-customer-gateway --bgp-asn 65000 --ip-address X.X.X.X --type ipsec.1
```

### 2. Create RDS (Private)
```bash
aws rds create-db-instance \
    --db-instance-identifier opsdb \
    --db-name opsdb \
    --engine postgres \
    --engine-version 15.4 \
    --db-instance-class db.t4g.micro \
    --allocated-storage 20 \
    --master-username admin \
    --master-user-password yourpassword \
    --vpc-security-group-ids sg-xxx \
    --db-subnet-group-name opsdb-subnet-group \
    --no-publicly-accessible \
    --availability-zone us-east-1a
```

### 3. Create Lambda
```bash
# Package app
zip -r lambda.zip app/ run.py

# Create Lambda
aws lambda create-function \
    --function-name opsdb-api \
    --runtime python3.11 \
    --handler app.routes.api:bp \
    --zip-file fileb://lambda.zip \
    --role arn:aws:iam::xxx:role/opsdb-lambda-role \
    --vpc-config SubnetIds=subnet-xxx,subnet-yyy,SecurityGroupIds=sg-xxx \
    --environment Variables="DATABASE_URL=postgresql://admin:pass@opsdb.xxxxx.us-east-1.rds.amazonaws.com:5432/opsdb"
```

---

## Deployment Strategy

### Option 1: Chalice (Serverless Framework)
```bash
pip install chalice
chalice new-project opsdb
```

### Option 2: SAM (Serverless Application Model)
```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  OpsdbApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.11
      Handler: app.routes.api:bp
      CodeUri: ./
      VpcConfig:
        SubnetIds:
          - subnet-xxx
          - subnet-yyy
        SecurityGroupIds:
          - sg-xxx
      Environment:
        Variables:
          DATABASE_URL: !Ref DatabaseUrl
```

### Option 3: Manual Deployment (Simplest)
```bash
# Build Lambda package
cd prod
zip -r ../opsdb-lambda.zip .

# Deploy
aws lambda update-function-code --function-name opsdb-api --zip-file fileb://opsdb-lambda.zip
```

---

## Environment Variables

| Variable | Required | Example |
|----------|----------|---------|
| DATABASE_URL | Yes | `postgresql://user:pass@rds-endpoint:5432/opsdb` |
| SECRET_KEY | Yes | Random string for Flask sessions |
| DEBUG | No | `false` for production |

---

## Security Considerations

| Layer | Configuration |
|-------|--------------|
| RDS | No public access, VPC only |
| Lambda | Run in VPC, no internet access needed |
| Secrets | Use AWS Secrets Manager or Parameter Store |
| API Gateway | Use Cognito or API Keys for auth |
| Logging | CloudWatch Logs with encryption |

---

## Database Migration

### Using Flask-Migrate
```python
# In app
from flask_migrate import Migrate
migrate = Migrate(app, db)
```

### Run migration
```bash
flask db migrate -m "initial schema"
flask db upgrade
```

---

## Monitoring

### CloudWatch Alarms
- Lambda duration > 25s
- API Gateway 5xx errors > 1%
- RDS CPU > 70%

### Logging
```python
# Lambda logging
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
```

---

## Backup Strategy

### RDS Automated Backups
- Enable automated backups (retain 7 days)
- Enable performance insights (optional)

### Manual Backups
```bash
# Dump database
pg_dump -h rds-endpoint -U admin opsdb > backup.sql

# Restore
psql -h rds-endpoint -U admin opsdb < backup.sql
```

---

## Cost Optimization

1. **Use Free Tier** - RDS t4g.micro + Lambda 1M requests
2. **Enable compression** - API Gateway response compression
3. **Use S3 lifecycle** - Move old uploads to Glacier
4. **Right-size Lambda** - 512MB memory is usually enough

---

## Summary

**Serverless + VPN offers**:
- No public IPs needed
- Secure private network
- Pay only for what you use
- Scales automatically
- Lower cost than EC2/ECS for low traffic

**Trade-offs**:
- Cold starts (~1-3 seconds)
- Lambda timeout limits
- Need to package all dependencies
