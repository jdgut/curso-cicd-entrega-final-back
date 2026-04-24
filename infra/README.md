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

Pipeline file in repository root:
- .github/workflows/ci-cd.yml

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

Important implementation detail from this iteration:
- CI/CD deployment uses GitHub variables and secrets for all Terraform input values.
- The pipeline still overrides docker_image_uri dynamically from the build output.

Current setting choice for backend runtime connection values:
- APP_DATABASE_URL_STAGING / APP_DATABASE_URL_PRODUCTION are defined as workflow env variables in .github/workflows/ci-cd.yml.
- APP_CORS_ALLOWED_ORIGINS_STAGING / APP_CORS_ALLOWED_ORIGINS_PRODUCTION are also defined as workflow env variables in .github/workflows/ci-cd.yml.
- DESIRED_COUNT_* and TASK_CPU/TASK_MEMORY_* are also defined as workflow env variables with defaults.

## 3) Prerequisites

- Terraform 1.6+ installed and available in PATH
- AWS credentials configured in your shell/session
- Access to S3 bucket for Terraform backend state
- Existing AWS resources/inputs:
  - VPC ID
  - At least two subnet IDs in different AZs
  - IAM role ARN for ECS execution/task (lab_role_arn)
- Docker image already pushed and accessible by ECS

GitHub repository configuration required by pipeline:
- Repository secrets:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_SESSION_TOKEN
  - DOCKERHUB_TOKEN
  - SONAR_TOKEN
- Repository variables:
  - DOCKERHUB_USERNAME
  - SONAR_HOST_URL
  - TF_STATE_BUCKET
  - LAB_ROLE_ARN
  - VPC_ID
  - SUBNET_IDS

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

CI/CD strategy:
- Terraform values are passed directly via -var arguments from GitHub vars/secrets.
- APP_DATABASE_URL and APP_CORS_ALLOWED_ORIGINS for staging/production are passed from workflow env variables.
- desired_count and task sizing values are passed from workflow env variables.
- tfvars files are optional for local CLI usage only.

Remote state keys used by CI/CD:
- backend/staging/terraform.tfstate
- backend/production/terraform.tfstate

## 5) Prepare environment files

For local execution (optional), create tfvars files from examples:

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

Current CI/CD behavior in this repository:
- staging deployment reads all Terraform inputs from GitHub vars/secrets.
- production deployment reads all Terraform inputs from GitHub vars/secrets.
- backend DB URL and CORS values are sourced from workflow env variables.
- docker_image_uri is always overridden by the image produced in build-test-publish.

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
  -backend-config="region=us-east-1" `
  -backend-config="dynamodb_table=terraform-state-locks"
```

Production:

```powershell
terraform -chdir=infra init -reconfigure `
  -backend-config="bucket=<your-tfstate-bucket>" `
  -backend-config="key=backend/production/terraform.tfstate" `
  -backend-config="region=us-east-1" `
  -backend-config="dynamodb_table=terraform-state-locks"
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

CI/CD apply equivalent:

```powershell
terraform -chdir=infra apply -auto-approve `
  -var="environment_name=staging" `
  -var="aws_region=us-east-1" `
  -var="docker_image_uri=<image-from-build-stage>" `
  -var="lab_role_arn=<github-var-LAB_ROLE_ARN>" `
  -var="vpc_id=<github-var-VPC_ID>" `
  -var="subnet_ids=<github-var-SUBNET_IDS-as-list>" `
  -var="app_database_url=<workflow-env-APP_DATABASE_URL_STAGING>" `
  -var="app_cors_allowed_origins=<workflow-env-APP_CORS_ALLOWED_ORIGINS_STAGING>"
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

CI/CD apply equivalent:

```powershell
terraform -chdir=infra apply -auto-approve `
  -var="environment_name=production" `
  -var="aws_region=us-east-1" `
  -var="docker_image_uri=<image-from-build-stage>" `
  -var="lab_role_arn=<github-var-LAB_ROLE_ARN>" `
  -var="vpc_id=<github-var-VPC_ID>" `
  -var="subnet_ids=<github-var-SUBNET_IDS-as-list>" `
  -var="app_database_url=<workflow-env-APP_DATABASE_URL_PRODUCTION>" `
  -var="app_cors_allowed_origins=<workflow-env-APP_CORS_ALLOWED_ORIGINS_PRODUCTION>"
```

## 9) GitHub Actions deployment chain

The backend deployment workflow in .github/workflows/ci-cd.yml runs this sequence on push to main:

- build-test-publish
- deploy-tf-staging
- update-service-staging
- test-staging
- deploy-tf-prod
- update-service-prod
- smoke-test-prod

High-level behavior by stage:
- build-test-publish:
  - runs lint and tests.
  - builds and pushes Docker image.
  - emits image_uri output used by deploy jobs.
- deploy-tf-staging:
  - terraform init with staging backend key.
  - terraform apply using GitHub vars/secrets and image_uri override.
  - exports backend_alb_dns_name, backend_ecs_cluster_name, backend_ecs_service_name.
- update-service-staging:
  - forces a new ECS deployment.
  - waits until service reaches steady state.
  - fails if rolloutState becomes FAILED.
- test-staging:
  - checks ECS desired vs running counts.
  - validates deployed image equals expected image_uri.
  - waits for ALB target health.
  - calls GET /health and verifies response contains status ok.
- deploy-tf-prod:
  - same pattern as staging but with production backend key and production vars/secrets.
- update-service-prod:
  - same steady-state and diagnostics logic as staging.
- smoke-test-prod:
  - same image and health checks as staging before considering production successful.

Execution guardrails:
- deployment stages run only on push to main.
- image tags are selected by branch:
  - main -> latest
  - other branches -> dev

## 10) Post-deploy verification

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

## 11) Rolling out a new backend image

Update docker_image_uri in the environment tfvars, then run:

```powershell
terraform -chdir=infra plan -var-file="staging.tfvars" -out="staging.tfplan"
terraform -chdir=infra apply "staging.tfplan"
```

Repeat for production when ready.

In CI/CD, only the Docker image changes between releases; infrastructure/runtime values are sourced from GitHub vars/secrets.

## 12) Destroy environment (if needed)

Staging destroy:

```powershell
terraform -chdir=infra destroy -var-file="staging.tfvars"
```

Production destroy:

```powershell
terraform -chdir=infra destroy -var-file="production.tfvars"
```

## 13) Troubleshooting

- terraform command not found:
  - Install Terraform and restart terminal.
- Backend init errors:
  - Check S3 bucket name, region, and AWS permissions.
- ECS tasks fail health checks:
  - Confirm container starts on port 8000.
  - Confirm health endpoint returns HTTP 200 on /health.
- App fails at startup:
  - Verify APP_DATABASE_URL points to a reachable database.
- Deploy fails before apply:
  - Verify required GitHub vars are defined and workflow env values are not empty for the target environment.
- ECS service does not reach steady state in update-service stages:
  - Inspect ECS service events and task stop reasons printed by workflow diagnostics.
- Smoke test fails with no healthy targets:
  - Check ALB target group health and security group rules.
  - Confirm backend container is listening on port 8000 and /health returns 200.
- Image mismatch in staging or production tests:
  - Verify build-test-publish produced and pushed the expected image_uri.
  - Confirm Terraform apply received the docker_image_uri override.
