# CI/CD Pipeline Design Summary

This document summarizes the design decisions, assumptions validated, and final outcomes agreed upon during the setup of the GitHub Actions CI/CD pipeline for this repository.

---

## 1. Repository & Branching Model

The repository uses a **two-branch model**:

- **development**
  - Active development branch
  - Used for integration testing and continuous delivery of pre-production artifacts

- **main**
  - Stable branch
  - Represents production-ready code

Both branches already exist in the repository.

---

## 2. High-Level Pipeline Goals

The CI/CD pipeline is designed to:

- Run Continuous Integration (CI) checks (linting, testing, quality analysis) on both branches
- Build and push Docker images to Docker Hub with **branch-specific tags**
- Avoid producing deployment artifacts from unmerged Pull Requests
- Keep the workflow simple, predictable, and traceable

---

## 3. Final Agreed Behavior

### ✅ Development Branch (`development`)
Triggered on: `push`

- Run CI:
  - Dependency installation
  - Black formatting check
  - Pylint
  - Flake8
  - Pytest
  - SonarCloud scan
- Build Docker image
- Push Docker image to Docker Hub with tag:dev

---

### ✅ Pull Requests (`development → main`)
Triggered on: `pull_request`

- Run CI only:
- Linting
- Tests
- SonarCloud
- ❌ **No Docker build**
- ❌ **No Docker push**

**Rationale:**  
Pull Requests represent unapproved, temporary merge states. Producing Docker artifacts from PRs leads to non-reproducible images that do not correspond to a permanent branch or commit.

---

### ✅ Main Branch (`main`)
Triggered on: `push`

- Run CI (same checks as `development`)
- Build Docker image
- Push Docker image to Docker Hub with tag:latest

---

## 4. Docker Strategy

### Image Naming
Docker images follow the format: <DOCKERHUB_USERNAME>/<github-repository-name></github-repository-name>
Example:
johndoe/my-repo:dev
johndoe/my-repo:latest

### Repository Creation
- Docker Hub repository **does not need to exist beforehand**
- It will be automatically created on the first successful push
- Repository will be **public**

---

## 5. Dockerfile & Build Context

- Dockerfile exists at the root of the repository
- Build context is the repository root (`.`)
- No build-time environment variables are required
- Runtime environment variables (e.g. `APP_DATABASE_URL`) are handled outside CI (e.g. via docker-compose or deployment platforms)

This ensures Docker builds in GitHub Actions are deterministic and do not depend on secrets.

---

## 6. Secrets & Variables (Validated)

The following are correctly configured in GitHub:

### Variables
- `DOCKERHUB_USERNAME`
- `SONAR_HOST_URL`

### Secrets
- `DOCKERHUB_TOKEN`
- `SONAR_TOKEN`

All are required for Docker authentication and SonarCloud analysis.

---

## 7. GitHub Environments

- GitHub Environments are **not used** in this pipeline
- No manual approvals or environment-scoped secrets are required
- Pipeline is fully automated and non-blocking

---

## 8. Key Design Principles Followed

- ✅ **Artifact traceability**  
  Every pushed Docker image corresponds to:
  - A permanent branch
  - A real commit
  - A reproducible state

- ✅ **No artifact pollution**
  - No Docker images are produced from PRs

- ✅ **Single-job simplicity**
  - Branch-aware logic instead of duplicated jobs

- ✅ **Safe promotion flow**
  - Development → PR → Merge → Production image

---

## 9. Result

The resulting CI/CD pipeline:

- Is safe, predictable, and easy to maintain
- Produces meaningful Docker tags (`dev`, `latest`)
- Aligns with best practices for CI vs deployment artifacts
- Is ready to be committed and extended later for CD if needed

---

## 10. Possible Future Enhancements (Out of Scope)

- Semantic version tagging
- Multi-architecture Docker builds
- Image labels with Git SHA and build metadata
- Automated deployments (CD)
- Preview environments for PRs

---
