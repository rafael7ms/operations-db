# opsdb Terraform Deployment Guide

## Prerequisites

1. **Terraform CLI** - Install from [terraform.io](https://www.terraform.io/downloads)
2. **AWS CLI** - Configure with `aws configure`
3. **VPC Setup** - Existing VPC with at least 2 private subnets

## Directory Structure

```
terraform/
├── main.tf           # Core infrastructure resources
├── variables.tf      # Input variables
├── backend.example.hcl  # S3 backend configuration template
├── dev.tf            # Dev environment configuration
├── staging.tf        # Staging environment configuration
├── production.tf     # Production environment configuration
└── README.md         # This file
```

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
cp backend.example.hcl backend.hcl
# Edit backend.hcl with your S3 bucket configuration
terraform init -backend-config=backend.hcl
```

### 2. Configure Environment

Edit `dev.tf` with your values:
```hcl
module "opsdb_dev" {
  source          = "./."
  environment     = "dev"
  vpc_id          = "your-vpc-id"
  subnet_ids      = ["subnet-id-1", "subnet-id-2"]
  db_password     = "secure-password"
  secret_key      = "flask-secret-key"
}
```

### 3. Plan and Apply

```bash
# Preview changes
terraform plan -target=module.opsdb_dev

# Apply changes
terraform apply -target=module.opsdb_dev
```

## Environment Deployment

### Development
```bash
terraform apply -target=module.opsdb_dev
```

### Staging
```bash
terraform apply -target=module.opsdb_staging
```

### Production
```bash
terraform apply -target=module.opsdb_production
```

## Destroy Resources

```bash
terraform destroy -target=module.opsdb_dev
```

## Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| aws_region | AWS region | us-east-1 |
| environment | Environment name | dev |
| vpc_id | VPC ID | - |
| subnet_ids | Private subnet IDs | - |
| db_instance_class | RDS instance class | db.t4g.micro |
| allocated_storage | Storage in GB | 20 |
| db_name | Database name | opsdb |
| db_username | Master username | opsdb_admin |
| db_password | Master password | - |
| secret_key | Flask secret key | - |
| backup_retention_days | Backup retention | 7 |
| availability_zone | AZ for RDS | a |

## Outputs

After apply, you'll get:
- `api_endpoint` - API Gateway URL
- `database_endpoint` - RDS endpoint
- `database_name` - Database name
- `lambda_function_arn` - Lambda ARN
- `lambda_execution_role_arn` - IAM role ARN
- `s3_bucket_name` - Uploads bucket name
- `security_group_id` - Lambda security group

## Security Notes

1. **Never commit secrets** - Use `.gitignore` and environment variables
2. **Enable encryption** - All storage is encrypted by default
3. **Restrict access** - RDS is not publicly accessible
4. **Use secrets manager** - Consider AWS Secrets Manager for production

## Cost Estimation

| Environment | Estimated Monthly Cost |
|-------------|----------------------|
| Dev | ~$20-30 |
| Staging | ~$40-50 |
| Production | ~$100-150 |

## Troubleshooting

### Common Issues

1. **RDS not accessible from Lambda**
   - Check security group rules
   - Verify VPC configuration

2. **Lambda timeout**
   - Increase timeout in `main.tf`
   - Check cold start duration

3. **State locking**
   - Ensure S3 bucket exists
   - Enable DynamoDB locking
