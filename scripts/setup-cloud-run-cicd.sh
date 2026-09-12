#!/usr/bin/env bash
# One-time bootstrap. Run as a project administrator in Google Cloud Shell.
set -euo pipefail

project=jobhelperguru
project_number=999060759573
region=us-east5
pool=jobhelperguru-github
provider=github-main
deployer=jobhelperguru-github-deployer@jobhelperguru.iam.gserviceaccount.com
runtime=jobhelperguru-runner@jobhelperguru.iam.gserviceaccount.com
subject='repo:souravC01@114119117/JobHelperGuru@1355476075:ref:refs/heads/main'

actual_number=$(gcloud projects describe "$project" --format='value(projectNumber)')
[[ "$actual_number" == "$project_number" ]] || { echo 'Unexpected project number'; exit 1; }
actual_runtime=$(gcloud run services describe jobhelperguru-backend \
  --project="$project" --region="$region" --format='value(spec.template.spec.serviceAccountName)')
[[ "$actual_runtime" == "$runtime" ]] || { echo 'Unexpected runtime service account'; exit 1; }
gcloud artifacts repositories describe jobhelperguru --project="$project" --location="$region" --format='value(name)'

gcloud services enable iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com --project="$project"

# Creation fails closed if these dedicated resources already exist. Inspect any
# partial setup before resuming instead of replacing an existing trust policy.
gcloud iam service-accounts create jobhelperguru-github-deployer \
  --project="$project" --display-name='JobHelperGuru GitHub deployer'
gcloud iam workload-identity-pools create "$pool" \
  --project="$project" --location=global --display-name='JobHelperGuru GitHub'

# Numeric IDs prevent a renamed or recreated repository or owner from inheriting
# access. Also require the exact repository, branch, event, and workflow file.
condition="assertion.repository_id == '1355476075' && assertion.repository_owner_id == '114119117' && assertion.repository == 'souravC01/JobHelperGuru' && assertion.ref == 'refs/heads/main' && assertion.event_name == 'push' && assertion.workflow_ref == 'souravC01/JobHelperGuru/.github/workflows/ci.yml@refs/heads/main' && assertion.sub == '$subject'"
gcloud iam workload-identity-pools providers create-oidc "$provider" \
  --project="$project" --location=global --workload-identity-pool="$pool" \
  --display-name='GitHub main CI workflow' \
  --issuer-uri='https://token.actions.githubusercontent.com' \
  --attribute-mapping='google.subject=assertion.sub,attribute.repository_id=assertion.repository_id,attribute.repository_owner_id=assertion.repository_owner_id' \
  --attribute-condition="$condition"

gcloud iam service-accounts add-iam-policy-binding "$deployer" \
  --project="$project" --role=roles/iam.workloadIdentityUser \
  --member="principal://iam.googleapis.com/projects/$project_number/locations/global/workloadIdentityPools/$pool/subject/$subject" \
  --condition=None
gcloud artifacts repositories add-iam-policy-binding jobhelperguru \
  --project="$project" --location="$region" \
  --role=roles/artifactregistry.writer --member="serviceAccount:$deployer" --condition=None
gcloud run services add-iam-policy-binding jobhelperguru-backend \
  --project="$project" --region="$region" \
  --role=roles/run.developer --member="serviceAccount:$deployer" --condition=None
gcloud iam service-accounts add-iam-policy-binding "$runtime" \
  --project="$project" --role=roles/iam.serviceAccountUser \
  --member="serviceAccount:$deployer" --condition=None

echo 'Keyless deployment identity configured. No service-account keys were created.'
gcloud iam workload-identity-pools providers describe "$provider" \
  --project="$project" --location=global --workload-identity-pool="$pool" \
  --format='yaml(name,state,attributeMapping,attributeCondition,oidc)'
