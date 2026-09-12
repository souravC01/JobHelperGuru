# Backend continuous deployment

The frontend stays on Vercel. The backend stays on the existing Cloud Run service
`jobhelperguru-backend` in project `jobhelperguru`, region `us-east5`.
The Render legacy redirect and its `render-legacy-redirect` branch are independent.
The main CI workflow no longer calls the Render deploy hook.

## One-time Google Cloud setup

Run `bash scripts/setup-cloud-run-cicd.sh` from an administrator's authenticated
Google Cloud Shell after reviewing the script. It checks the existing project,
Artifact Registry repository, and runtime service account before creating the
dedicated federation resources. It stops if the dedicated account or pool already
exists; inspect partial setup before resuming individual commands.

The deployer is `jobhelperguru-github-deployer@jobhelperguru.iam.gserviceaccount.com`.
Its resource-scoped grants are:

| Role | Resource |
| --- | --- |
| Artifact Registry Writer | `jobhelperguru` repository in `us-east5` |
| Cloud Run Developer | Existing `jobhelperguru-backend` service |
| Service Account User | Existing `jobhelperguru-runner` runtime account |

The dedicated pool `jobhelperguru-github` and provider `github-main` accept only
GitHub OIDC tokens matching repository ID `1355476075`, owner ID `114119117`,
repository `souravC01/JobHelperGuru`, branch `refs/heads/main`, event `push`, and
workflow `souravC01/JobHelperGuru/.github/workflows/ci.yml@refs/heads/main`.
The deployer impersonation binding additionally requires the exact main-branch
OIDC subject. Pull requests, forks, other branches, manual dispatches, and other
workflow files cannot use this provider. No service-account JSON keys or new
GitHub secrets are needed. The provider identifier and account email in the
workflow are public configuration.

## Deployment behavior

Existing backend tests, frontend tests/build, Docker validation, and `ci-success`
remain. Docker validation also builds `Dockerfile.cloudrun` before a PR is merged.

On pushes to `main`, native Git compares the push's before and after commits for
changes to `backend/`, `requirements.txt`, `requirements/`, `Dockerfile.cloudrun`,
or `.github/workflows/ci.yml`. This covers all commits in a push, including deleted
files. An initial branch push compares against an empty tree. An unavailable
previous commit is fetched; a comparison failure fails the detector.

After CI succeeds and a relevant change is found, the workflow builds the backend,
requests short-lived credentials using `google-github-actions/auth`, pushes
`us-east5-docker.pkg.dev/jobhelperguru/jobhelperguru/jobhelperguru-backend:<commit-sha>`,
and runs `gcloud run services update` with only the image, project, and region.
Building precedes authentication so a long build does not consume the credentials'
short lifetime. Credential files are excluded from Git and Docker build contexts.

The image update preserves environment variables, secret references, scaling,
public access, traffic policy, and the runtime account. Production currently routes
100 percent of traffic to the latest revision. Main runs are not cancelled when a
new push arrives, so an in-progress deployment can finish. Main runs use GitHub's
maximum queue of 100 pending runs so a frontend-only push cannot replace a pending
backend deployment. Other branches retain cancellation of superseded CI runs.

The final step retries `https://jobhelperguru.vercel.app/api/health` and requires
`status=ok`, `database=postgresql`, and `object_storage=cloudflare_r2`. If deployment
or health verification fails, the workflow fails and needs investigation; it does
not automatically roll back.

## Verification and recovery

Before merging, verify workflow syntax and all PR CI checks. After the first main
run, verify its successful deployment step and Cloud Run's latest ready revision
and image SHA, then compare the service configuration with the pre-deployment
snapshot. Health alone does not prove which image is serving traffic.

To restore a previously verified image, an authorized operator can run:

```bash
gcloud run services update jobhelperguru-backend \
  --project=jobhelperguru --region=us-east5 \
  --image=us-east5-docker.pkg.dev/jobhelperguru/jobhelperguru/jobhelperguru-backend:PREVIOUS_SHA
```

Use an existing verified SHA from Artifact Registry. To stop future backend
deployments, disable this federation provider or revert the deployment job. Do not
restore the Render deploy hook. Follow the same Vercel health check after recovery.

References: [Google federation setup](https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines),
[Cloud Run deployment roles](https://cloud.google.com/run/docs/deploying), and
[Google authentication action](https://github.com/google-github-actions/auth).
