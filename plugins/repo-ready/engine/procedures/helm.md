# Helm chart and a kind smoke test in CI

Worked through on octrow/buy-smarter (`deploy/helm/buysmarter/`, `deploy/kind/`, the `helm` job in `ci.yml`).
The app needs its health endpoints first (`docker.md`, "Health endpoints").

## Chart contents

Deployment, Service, a Secret or `secret.existing`, a ServiceAccount with `automountServiceAccountToken: false`, the
migrations Job as a `pre-install,pre-upgrade` hook, a `helm test`, and optional Ingress / HPA / PDB / ServiceMonitor /
PodMonitor. The chart doesn't install the database or the queue; in kind they are plain manifests in their own
namespace.

## Pod security

Pod Security Standard `restricted`: `runAsNonRoot`, the numeric uid from the image, `readOnlyRootFilesystem`,
`capabilities: drop: [ALL]`, `seccompProfile: RuntimeDefault`, `emptyDir` for caches and `/tmp`. Label the namespace
`pod-security.kubernetes.io/enforce=restricted` in the smoke test so a violation fails there, not in production.
Official postgres and redis images start as root: keep them in a namespace without PSS.

## Probes

`livenessProbe` on `/health`, `readinessProbe` on `/ready`. A worker without HTTP gets liveness on its metrics port.

## Smoke test in kind

`deploy/kind/smoke.sh`: dependencies → `helm upgrade --install --wait` → `helm test --logs` → port-forward → curl the
probes and `/metrics` → one real job to a terminal state → a second upgrade → the `doctor` command in a pod.
`trap dump ERR` prints pod logs and events when anything fails.

CI: `helm lint`, then `helm template | kubeconform -strict` (with the datreeio CRD schemas for Monitor resources),
build the image, `helm/kind-action`, `kind load docker-image`, `smoke.sh`.

Done when: the smoke test passes in a clean kind cluster with no PSS violations and the CI job is green.

## Pitfalls

- A pre-install hook starts before regular resources, so a Secret it reads must be a hook too (weight -10); the cost
  is that the Secret survives `helm uninstall`.
- `helm lint` doesn't evaluate `required`: also run `helm template` without values and expect it to fail.
- `helm test --logs` can't read a pod with `hook-delete-policy: hook-succeeded`; use `before-hook-creation`.
- `kind load docker-image` sometimes loads nothing, and the migrations Job hits `ErrImagePull`; load again.
- Release: bump `version` and `appVersion` in `Chart.yaml` together with the package version and the Dockerfile's
  `ARG VERSION`.
