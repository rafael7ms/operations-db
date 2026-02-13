# Backend configuration for S3 state storage
# Copy this file to backend.hcl and fill in your values
# terraform init -backend-config=backend.hcl

bucket  = "opsdb-terraform-state"
key     = "opsdb/terraform.tfstate"
region  = "us-east-1"
encrypt = true
