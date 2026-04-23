# Infrastructure README

This folder contains Terraform code to deploy the backend service to AWS ECS (Fargate) with support for two environments:
- staging
- production

Scope for this iteration:
- Included: backend container infrastructure on ECS, ALB, security groups, CloudWatch logs
- Excluded: frontend infrastructure, database provisioning

## 1) What this Terraform creates

- ECS Cluster
- ECS Task Definition (Fargate)
- ECS Service
- Application Load Balancer (ALB)
- Target Group + HTTP Listener
- Security Groups for ALB and ECS tasks
- CloudWatch Log Group
- Useful outputs (ALB URL, ECS cluster/service names)

Main files in this folder:
- provider.tf
- variables.tf
- backend_variables.tf
- ecs_cluster_logs.tf
- networking.tf
- ecs_service.tf
- outputs.tf
- staging.tfvars.example
- production.tfvars.example

Reference-only demo files (do not modify):
- demo_main.tf
- demo_outputs.tf

## 2) Backend assumptions inferred from code

- Container port: 8000
- Health endpoint: /health
- Required runtime environment variables:
  - APP_APP_ENV
  - APP_APP_HOST
  - APP_APP_PORT
  - APP_CORS_ALLOWED_ORIGINS
  - APP_DATABASE_URL

Note:
- APP_DATABASE_URL must point to an existing database managed outside this Terraform scope.

## 3) Prerequisites

- Terraform 1.6+ installed and available in PATH
- AWS credentials configured in your shell/session
- Access to S3 bucket for Terraform backend state
- Existing AWS resources/inputs:
  - VPC ID
  - At least two subnet IDs in different AZs
  - IAM role ARN for ECS execution/task (lab_role_arn)
- Docker image already pushed and accessible by ECS

Optional check commands:

```powershell
terraform version
aws sts get-caller-identity
```

## 4) Environment strategy

This project uses variable-driven environments via environment_name.
Allowed values are enforced in variables.tf:
- staging
- production

Recommended usage:
- One tfvars file per environment
- Different remote state key per environment

## 5) Prepare environment files

Create local tfvars files from examples:

```powershell
Copy-Item infra/staging.tfvars.example infra/staging.tfvars
Copy-Item infra/production.tfvars.example infra/production.tfvars
```

Edit both files and set real values:
- docker_image_uri
- lab_role_arn
- vpc_id
- subnet_ids
- app_database_url
- app_cors_allowed_origins
- desired_count

Important for CORS in AWS:
- Set app_cors_allowed_origins with the real frontend URL(s), comma-separated.
- Do not include trailing slash in origins (use https://app.example.com, not https://app.example.com/).
- Use "*" only if you intentionally want a fully public API.

## 6) Initialize Terraform backend

Run init separately per environment by changing backend key.

Staging:

```powershell
terraform -chdir=infra init `
  -backend-config="bucket=<your-tfstate-bucket>" `
  -backend-config="key=backend/staging/terraform.tfstate" `
  -backend-config="region=us-east-1"
```

Production:

```powershell
terraform -chdir=infra init -reconfigure `
  -backend-config="bucket=<your-tfstate-bucket>" `
  -backend-config="key=backend/production/terraform.tfstate" `
  -backend-config="region=us-east-1"
```

## 7) Validate infrastructure

Run these before planning/applying:

```powershell
terraform -chdir=infra fmt -recursive
terraform -chdir=infra validate
```

If you want a non-mutating format check:

```powershell
terraform -chdir=infra fmt -check -recursive
```

## 8) Plan and deploy

### Staging

Generate plan:

```powershell
terraform -chdir=infra plan `
  -var-file="staging.tfvars" `
  -out="staging.tfplan"
```

Apply plan:

```powershell
terraform -chdir=infra apply "staging.tfplan"
```

### Production

Generate plan:

```powershell
terraform -chdir=infra plan `
  -var-file="production.tfvars" `
  -out="production.tfplan"
```

Apply plan:

```powershell
terraform -chdir=infra apply "production.tfplan"
```

## 9) Post-deploy verification

Read outputs:

```powershell
terraform -chdir=infra output
terraform -chdir=infra output backend_alb_url
```

Check health endpoint:

```powershell
$alb = terraform -chdir=infra output -raw backend_alb_dns_name
Invoke-WebRequest -Uri "http://$alb/health" -Method GET
```

Expected response body should include:
- status: ok

## 10) Rolling out a new backend image

Update docker_image_uri in the environment tfvars, then run:

```powershell
terraform -chdir=infra plan -var-file="staging.tfvars" -out="staging.tfplan"
terraform -chdir=infra apply "staging.tfplan"
```

Repeat for production when ready.

## 11) Destroy environment (if needed)

Staging destroy:

```powershell
terraform -chdir=infra destroy -var-file="staging.tfvars"
```

Production destroy:

```powershell
terraform -chdir=infra destroy -var-file="production.tfvars"
```

## 12) Troubleshooting

- terraform command not found:
  - Install Terraform and restart terminal.
- Backend init errors:
  - Check S3 bucket name, region, and AWS permissions.
- ECS tasks fail health checks:
  - Confirm container starts on port 8000.
  - Confirm health endpoint returns HTTP 200 on /health.
- App fails at startup:
  - Verify APP_DATABASE_URL points to a reachable database.
