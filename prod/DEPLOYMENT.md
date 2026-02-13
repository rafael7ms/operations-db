# opsdb Deployment Guide

This document covers deploying opsdb to AWS using serverless technologies.

## Architecture Overview

```
On-Premises VPC (192.168.0.0/16)
         |
      [VPN]
         |
AWS VPC (10.0.0.0/16)
   |
   +-- Lambda (Flask API via Mangum)
   +-- RDS PostgreSQL (private, no public IP)
   +-- S3 (file uploads)
   +-- API Gateway (HTTP API)
```

## Prerequisites

1. **AWS Account** with billing enabled
2. **AWS CLI** configured with credentials
3. **VPC Setup** - Existing VPC with at least 2 private subnets
4. **Site-to-Site VPN** - Connection to on-premises VPC

## Deployment Options

### Option 1: SAM (Serverless Application Model) - Recommended for Quick Start

SAM is the fastest way to deploy serverless applications on AWS.

#### Prerequisites
```bash
# Install SAM CLI
# macOS
brew tap aws/tap
brew install aws-sam-cli

# Windows (Chocolatey)
choco install aws-sam-cli

# Linux
curl -sL https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip -o sam.zip
unzip sam.zip -d sam
sudo ./sam/install
```

#### Deployment Steps

```bash
cd prod/sam

# Edit dev.params.json with your values
vim dev.params.json

# Deploy
./deploy.sh
```

Or manually:
```bash
# Build
sam build --template-file template.yaml

# Deploy
sam deploy \
  --template-file template.yaml \
  --stack-name opsdb-api-dev \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    EnvironmentName=dev \
    VpcId=vpc-xxx \
    SubnetIds=subnet-xxx,subnet-yyy \
    SecurityGroupId=sg-xxx \
    DatabaseName=opsdb \
    MasterUsername=opsdb_admin \
    MasterUserPassword=your-password \
    SecretKey=your-secret-key
```

---

### Option 2: Terraform - Recommended for Infrastructure as Code

Terraform provides better infrastructure management and state tracking.

#### Prerequisites
```bash
# Install Terraform
# macOS
brew install terraform

# Windows (Chocolatey)
choco install terraform

# Linux
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

#### Deployment Steps

```bash
cd prod/terraform

# Initialize
cp backend.example.hcl backend.hcl
# Edit backend.hcl with your S3 bucket
terraform init -backend-config=backend.hcl

# Plan
terraform plan -target=module.opsdb_dev

# Apply
terraform apply -target=module.opsdb_dev
```

---

## Environment Configuration

### Development
- **RDS**: db.t4g.micro (Free Tier eligible)
- **Lambda**: 512MB memory
- **Backup**: 7 days retention

### Staging
- **RDS**: db.t4g.small
- **Lambda**: 512MB-1GB memory
- **Backup**: 14 days retention

### Production
- **RDS**: db.t4g.small or db.r6g.large
- **Lambda**: 512MB-1GB memory
- **Backup**: 30 days retention
- **Multi-AZ**: Enabled

---

## API Endpoints

After deployment, the API is available at:

```
https://<api-id>.execute-api.<region>.amazonaws.com/api/
```

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/employees | List employees |
| POST | /api/employees | Create employee |
| GET | /api/employees/search | Search employees |
| GET | /api/employees/history | Get archived employees |
| GET | /api/schedules | List schedules |
| GET | /api/schedules/history | Get archived schedules |
| GET | /api/attendances | List attendance |
| GET | /api/attendances/daily-report | Daily attendance summary |
| GET | /api/leave_requests | List leave requests |
| GET | /api/exceptions | List exceptions |
| GET | /api/rewards/reasons | List reward reasons |
| GET | /api/rewards/employee/<id> | Employee reward history |
| GET | /api/rewards/redemptions | List redemptions |
| GET | /api/reports/* | Comprehensive reports |
| GET | /api/health | Health check |

---

## Cost Estimation

### Development (Free Tier Eligible)
| Resource | Free Tier | After Free Tier |
|----------|-----------|-----------------|
| RDS t4g.micro | 750 hours/month | Free for 12 months |
| Lambda | 1M requests | $0.20 per 1M |
| API Gateway | 1B bytes | $1 per 1M requests |
| S3 | 5GB storage | Free tier |
| **Total** | **$0** | **~$5-10/month** |

### Production (Estimated)
| Resource | Monthly Cost |
|----------|--------------|
| RDS (db.t4g.small) | $15-25 |
| Lambda (100K requests) | $2-5 |
| API Gateway | $3-5 |
| S3 (10GB + transfers) | $0.50 |
| VPN | $36 |
| **Total** | **~$60-75/month** |

---

## Security

### IAM Roles
- Lambda execution role with minimal permissions
- S3 bucket policy blocks public access
- RDS not publicly accessible

### Secrets Management
- Use AWS Secrets Manager for production
- Store database credentials securely
- Rotate secrets regularly

### Network Security
- RDS in private subnet (no public IP)
- VPN for on-premises access
- Security groups restrict access

---

## Monitoring

### CloudWatch Alarms
- Lambda duration > 25s
- API Gateway 5xx errors > 1%
- RDS CPU > 70%
- RDS storage > 80%

### Logs
```bash
# Lambda logs
aws cloudwatch describe-alarms --metric-name Duration

# API Gateway logs
aws logs get-log-events \
  --log-group-name /aws/lambda/opsdb-api-dev \
  --log-stream-name "2024/01/01/[$LATEST]stream"
```

---

## Backup & Recovery

### RDS Automated Backups
- Enabled by default
- 7-day retention (dev)
- 30-day retention (production)

### Manual Backup
```bash
# Dump database
pg_dump -h <rds-endpoint> -U opsdb_admin opsdb > backup.sql

# Restore
psql -h <rds-endpoint> -U opsdb_admin opsdb < backup.sql
```

---

## Troubleshooting

### Common Issues

1. **Lambda timeout**
   - Increase timeout in template
   - Check cold start duration
   - Increase memory allocation

2. **RDS not accessible**
   - Check security group rules
   - Verify VPC configuration
   - Ensure VPN is connected

3. **Deployment failed**
   - Check CloudFormation events
   - Review Lambda logs
   - Validate IAM permissions

---

## Cleanup

### SAM
```bash
./destroy.sh
# Or
aws cloudformation delete-stack --stack-name opsdb-api-dev
```

### Terraform
```bash
terraform destroy -target=module.opsdb_dev
```

---

## Next Steps

1. Set up CI/CD pipeline
2. Configure custom domain
3. Enable AWS WAF for API Gateway
4. Set up RDS performance insights
5. Configure CloudWatch dashboards
