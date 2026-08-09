# Deploy Maintenance Agent (API + dashboard) to Cloud Run.
# Usage (from repo root):
#   .\deploy\deploy-cloudrun.ps1
# Optional:
#   .\deploy\deploy-cloudrun.ps1 -ProjectId maintenance-agent-hack -Region europe-west1

param(
    [string]$ProjectId = "maintenance-agent-hack",
    [string]$Region = "europe-west1",
    [string]$ServiceName = "maintenance-agent",
    [string]$ServiceAccountName = "maintenance-agent-run"
)

$ErrorActionPreference = "Stop"
$gcloud = Join-Path $env:LOCALAPPDATA "Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $gcloud)) {
    $gcloud = "gcloud"
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$SaEmail = "$ServiceAccountName@$ProjectId.iam.gserviceaccount.com"

Write-Host "==> Enabling required APIs..."
& $gcloud services enable `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    artifactregistry.googleapis.com `
    aiplatform.googleapis.com `
    firestore.googleapis.com `
    pubsub.googleapis.com `
    iam.googleapis.com `
    --project=$ProjectId

Write-Host "==> Ensuring runtime service account..."
$existingSa = & $gcloud iam service-accounts describe $SaEmail --project=$ProjectId 2>$null
if (-not $existingSa) {
    & $gcloud iam service-accounts create $ServiceAccountName `
        --display-name="Maintenance Agent Cloud Run" `
        --project=$ProjectId
}

$roles = @(
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/pubsub.subscriber",
    "roles/logging.logWriter"
)
foreach ($role in $roles) {
    & $gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$SaEmail" `
        --role=$role `
        --condition=None `
        --quiet | Out-Null
}

Write-Host "==> Deploying Cloud Run service '$ServiceName'..."
& $gcloud run deploy $ServiceName `
    --source=. `
    --project=$ProjectId `
    --region=$Region `
    --service-account=$SaEmail `
    --allow-unauthenticated `
    --min-instances=0 `
    --max-instances=3 `
    --cpu=1 `
    --memory=1Gi `
    --timeout=300 `
    --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=$ProjectId,GOOGLE_CLOUD_LOCATION=eu,USE_FIRESTORE=true" `
    --quiet

$ServiceUrl = & $gcloud run services describe $ServiceName `
    --project=$ProjectId `
    --region=$Region `
    --format="value(status.url)"

Write-Host "==> Ensuring Pub/Sub topic + push subscription..."
$topic = "machine-telemetry-events"
$sub = "machine-telemetry-events-push"
$ErrorActionPreference = "Continue"
& $gcloud pubsub topics describe $topic --project=$ProjectId 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    & $gcloud pubsub topics create $topic --project=$ProjectId
}
& $gcloud pubsub subscriptions delete $sub --project=$ProjectId --quiet 2>$null
& $gcloud pubsub subscriptions create $sub `
    --topic=$topic `
    --push-endpoint="$ServiceUrl/events/telemetry" `
    --ack-deadline=60 `
    --project=$ProjectId
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Deployed:"
Write-Host "  Dashboard / API: $ServiceUrl"
Write-Host "  Health:          $ServiceUrl/health"
Write-Host "  Telemetry:       POST $ServiceUrl/events/telemetry"
Write-Host "  Pub/Sub topic:   $topic"
Write-Host "  Push sub:        $sub -> $ServiceUrl/events/telemetry"
