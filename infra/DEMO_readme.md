# Infrastructure DEMO_README

This folder contains Terraform code to deploy the database backend to AWS ECS (Fargate) with support for two environments:
- staging
- production

Scope for this iteration:
- Included: database container infrastructure on ECS, internal NLB, security groups, CloudWatch logs, EFS persistence
- Excluded: frontend infrastructure, API infrastructure, database engine provisioning outside container scope

## 1) What this Terraform creates

- ECS Cluster
- ECS Task Definition (Fargate)
- ECS Service
- Internal Network Load Balancer (NLB)
- Target Group + TCP Listener
- Security Groups for ECS tasks and EFS
- CloudWatch Log Group
- EFS file system + mount targets + access point for persistent PostgreSQL data
- Useful outputs (database endpoint, ECS cluster/service names, EFS file system id)

Main files in this folder:
- provider.tf
- variables.tf
- database_variables.tf
- locals.tf
- ecs_cluster_logs.tf
- networking.tf
- storage.tf
- ecs_service.tf
- outputs.tf
- backend-staging.hcl.example
- backend-production.hcl.example
- staging.tfvars.example
- production.tfvars.example

Reference-only demo files (do not modify):
- demo_main.tf_
- demo_outputs.tf_

## 2) Database assumptions inferred from repository

- Container port: 5432
- Health check strategy: pg_isready (container-level ECS health check)
- Required runtime environment variables:
  - POSTGRES_DB
  - POSTGRES_USER
  - POSTGRES_PASSWORD

Notes:
- The load balancer is internal and TCP-based because PostgreSQL is not HTTP.
- Container data persistence is backed by EFS mounted into /var/lib/postgresql/data.

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
aws sts get-caller-identity --profile curso_cicd
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

Template files are included:
- staging.tfvars.example
- production.tfvars.example

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
- postgres_db
- postgres_user
- postgres_password
- desired_count
- task_cpu
- task_memory

## 6) Initialize Terraform backend

If you already created the S3 backend bucket and DynamoDB lock table for the API project, reuse them for this DB project.
Do not create a new bucket/table unless you explicitly want complete isolation.

What must change for DB is only the remote state key, so API and DB states stay separated.

Example using the same AWS profile used in your CLI setup:

```powershell
$Env:AWS_PROFILE = "curso_cicd"
```

Run init separately per environment by changing backend key.

Optional helper files are included so you do not have to type backend arguments every time.

Staging:

```powershell
Copy-Item infra/backend-staging.hcl.example infra/backend-staging.hcl
terraform -chdir=infra init -reconfigure `
  -backend-config="backend-staging.hcl"
```

Production:

```powershell
Copy-Item infra/backend-production.hcl.example infra/backend-production.hcl
terraform -chdir=infra init -reconfigure `
  -backend-config="backend-production.hcl"
```

Note:
- Backend example files include dynamodb_table for compatibility with your existing lock table.
- If you prefer not to use DynamoDB locking, remove the dynamodb_table line from both backend hcl files.
- If you already initialized locally with -backend=false, run init -reconfigure as above to switch to remote state cleanly.

### Backend verification after init

Run these checks after a successful init to confirm remote state wiring:

```powershell
$Env:AWS_PROFILE = "curso_cicd"
terraform -chdir=infra state list
```

For staging state object presence in S3:

```powershell
$Env:AWS_PROFILE = "curso_cicd"
aws s3 ls s3://curso-cicd-tfstate-jdgut-753159/database/staging/
```

For production state object presence in S3:

```powershell
$Env:AWS_PROFILE = "curso_cicd"
aws s3 ls s3://curso-cicd-tfstate-jdgut-753159/database/production/
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

Validate:
```powershell
aws ecs describe-services `
  --cluster db-staging-cluster `
  --services db-staging-service `
  --query "services[0].{running:runningCount,desired:desiredCount,status:status}"
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
terraform -chdir=infra output database_endpoint
```

Get endpoint value:

```powershell
$endpoint = terraform -chdir=infra output -raw database_endpoint
Write-Host $endpoint
```

Check ECS service status:

```powershell
$cluster = terraform -chdir=infra output -raw ecs_cluster_name
$service = terraform -chdir=infra output -raw ecs_service_name
aws ecs describe-services --cluster $cluster --services $service --query "services[0].{status:status,runningCount:runningCount,desiredCount:desiredCount}"
```

Optional TCP check from a host inside the same VPC:

```powershell
# Replace with endpoint host extracted from database_endpoint
Test-NetConnection -ComputerName <nlb-dns-name> -Port 5432
```

## 10) Rolling out a new database image

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
  - Confirm the container starts on port 5432.
  - Confirm pg_isready can run correctly inside the container.
- DB service unreachable:
  - Confirm client is inside VPC/network path to the internal NLB.
  - Confirm subnet routing and security group rules.
- PostgreSQL initialization issues:
  - Validate init/01-init.sql syntax and startup logs in CloudWatch.
- Terraform state lock errors (DynamoDB ConditionalCheckFailedException):
  - Wait for active apply/destroy jobs to finish, then retry.
  - In CI, destroy already waits with lock timeout (`-lock-timeout=10m`).
  - If lock is stale, use the manual workflow action `Manual Unlock (Terraform State Lock)` with `confirm_unlock=UNLOCK`.
  - Prefer providing `lock_id` from Terraform error so unlock is guarded.
- Smoke test shows running tasks but healthy targets = 0:
  - CI now waits up to 10 minutes for target health propagation.
  - If it still fails, inspect `describe-target-health` reason/description in workflow logs.
