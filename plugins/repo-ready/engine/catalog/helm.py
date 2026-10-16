"""Helm stack pack: the chart, its pod security and its CI."""
import re
from pathlib import PurePosixPath

from catalog.core import workflow_texts
from registry import check, judgement, read, tracked

DEP = {"deploy"}
RESTRICTED = ("runAsNonRoot", "readOnlyRootFilesystem", "drop:", "RuntimeDefault")
TEST_HOOK = re.compile(r"helm\.sh/hook\"?:\s*\"?test")
CI_STEPS = {"a chart lint (helm lint / ct lint)": r"helm lint|ct lint",
            "kubeconform": r"kubeconform",
            "a kind cluster (helm/kind-action / kind create cluster)": r"helm/kind-action|kind create cluster"}


def charts() -> dict[str, str]:
    """Chart directory ("" at the repo root) → its templates and values, comments stripped, subcharts left out."""
    names = tracked()
    parents = [str(PurePosixPath(f).parent) for f in names if PurePosixPath(f).name == "Chart.yaml"]
    dirs = ["" if d == "." else d for d in parents]
    out = {}
    for chart in dirs:
        prefix = f"{chart}/" if chart else ""
        nested = [d for d in dirs if d != chart and d.startswith(f"{prefix}charts/")]
        files = [f for f in names if f.startswith(prefix) and f.endswith((".yaml", ".yml", ".tpl"))
                 and not any(f.startswith(f"{d}/") for d in nested)]
        out[chart or "."] = "\n".join(re.sub(r"(?m)\s*#.*$", "", read(f)) for f in files)
    return out


@check("helm_pod_security", severity="warning", when=("helm_chart",), scenarios=DEP, kind="files",
       why="Pod Security `restricted` is what a hardened cluster admits; a chart without it is refused there",
       procedure="helm.md#pod-security")
def helm_pod_security() -> list[str]:
    return [f"{c}: no `{k}`" for c, t in charts().items() for k in RESTRICTED if k not in t]


@check("helm_probes", severity="warning", when=("helm_chart",), scenarios=DEP, kind="files",
       why="without probes Kubernetes sends traffic to pods that aren't ready and never restarts stuck ones",
       procedure="helm.md#probes")
def helm_probes() -> list[str]:
    return [f"{c}: no `{k}`" for c, t in charts().items() for k in ("livenessProbe", "readinessProbe") if k not in t]


@check("helm_service_account_token", severity="info", when=("helm_chart",), scenarios=DEP, kind="files",
       why="an app that never calls the Kubernetes API shouldn't carry a token for it",
       procedure="helm.md#chart-contents")
def helm_service_account_token() -> list[str]:
    # a template value (`{{ .Values.serviceAccount.automount }}`) counts: the default lives in values.yaml
    return [f"{c}: no `automountServiceAccountToken: false`" for c, t in charts().items()
            if not re.search(r"automountServiceAccountToken:\s*(false|\{\{)", t)]


@check("helm_test", severity="info", when=("helm_chart",), scenarios=DEP, kind="files",
       why="`helm test` proves the release answers after install, in CI and in production alike",
       procedure="helm.md#chart-contents")
def helm_test() -> list[str]:
    return [f"{c}: no template with a `helm.sh/hook: test` annotation" for c, t in charts().items()
            if not TEST_HOOK.search(t)]


@check("helm_ci", severity="warning", when=("helm_chart", "github_actions"), scenarios=DEP, kind="files",
       why="a chart that only renders on the author's machine breaks on the first real install",
       procedure="helm.md#smoke-test-in-kind")
def helm_ci() -> list[str]:
    text = "".join(workflow_texts().values())
    return [f"no {what} in CI" for what, pattern in CI_STEPS.items() if not re.search(pattern, text)]


judgement("helm_kind_smoke", severity="warning", when=("helm_chart",), scenarios=DEP,
          question="Does a smoke script install the chart in a clean kind cluster with PSS enforced, run "
                   "`helm test`, hit the probes, finish one real job and upgrade a second time?",
          procedure="helm.md#smoke-test-in-kind")

judgement("release_versions_together", severity="info", when=("helm_chart",), scenarios=DEP,
          question="Does a release bump the package version, the Dockerfile's ARG VERSION and Chart.yaml "
                   "`version`/`appVersion` together?",
          procedure="helm.md#pitfalls")
