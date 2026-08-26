#!/usr/bin/env python3
"""Generate application and docs portfolio repositories."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/efokou/Documents/MyDevelopment/portfolio")
REPOS = ROOT / "repos"
LICENSE = (ROOT / "LICENSE").read_text()
SECURITY = (ROOT / "SECURITY.md").read_text()


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content)


def common(repo: Path) -> None:
    write(repo / "LICENSE", LICENSE)
    write(repo / "SECURITY.md", SECURITY)
    write(repo / "CODEOWNERS", "* @EtienneFokou-E18560\n")


PY_GITIGNORE = """__pycache__/
*.pyc
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.env
.env.*
!.env.example
.DS_Store
"""

NODE_GITIGNORE = """node_modules/
.next/
dist/
coverage/
.env
.env.*
!.env.example
.DS_Store
cdk.out/
"""


def ops_toolkit() -> None:
    repo = REPOS / "kubernetes-operations-toolkit"
    common(repo)
    write(repo / ".gitignore", PY_GITIGNORE)
    write(
        repo / "README.md",
        """# kubernetes-operations-toolkit

Intentionally observable Kubernetes environment for **operational exercises**, not a conventional app.

Install on the shared kind cluster from [cloud-platform-blueprint](https://github.com/efokou-labs/cloud-platform-blueprint).

## Failure modes

Set `FAILURE_MODE` on the demo Deployment:

| Value | Symptom |
| --- | --- |
| `none` | Healthy `/healthz` and `/readyz` |
| `cpu` | Tight spin loop (CPU exhaustion) |
| `memory` | Unbounded allocation (memory pressure) |
| `readiness` | Readiness probe fails |
| `dependency` | Upstream HTTP calls fail |
| `latency` | Responses delayed ~5s |
| `http500` | Handlers return 500 |

## Runbooks

Each file is alert → diagnosis → mitigation → recovery:

- [CrashLoopBackOff](docs/runbooks/crashloopbackoff.md)
- [High API latency](docs/runbooks/high-api-latency.md)
- [Database connection exhaustion](docs/runbooks/db-connection-exhaustion.md)
- [NodeNotReady](docs/runbooks/nodenotready.md)
- [Certificate expiration](docs/runbooks/certificate-expiration.md)

## Verify

```bash
make verify
```
""",
    )
    write(
        repo / "Makefile",
        """\
.PHONY: verify
verify:
	python3 -m pip install -q -r requirements-dev.txt
	python3 -m pytest -q
	@echo kubernetes-operations-toolkit verify passed
""",
    )
    write(repo / "requirements-dev.txt", "pytest==9.1.1\nfastapi==0.141.1\nhttpx==0.28.1\nuvicorn==0.52.4\n")
    write(repo / "requirements.txt", "fastapi==0.141.1\nuvicorn==0.52.4\n")
    write(
        repo / "app/main.py",
        '''\
import os
import time
from fastapi import FastAPI, HTTPException

app = FastAPI(title="ops-demo")
MODE = os.getenv("FAILURE_MODE", "none")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    if MODE == "readiness":
        raise HTTPException(status_code=503, detail="readiness injection")
    return {"status": "ready"}


@app.get("/")
def root():
    if MODE == "http500":
        raise HTTPException(status_code=500, detail="injected failure")
    if MODE == "latency":
        time.sleep(5)
    if MODE == "dependency":
        raise HTTPException(status_code=502, detail="upstream unavailable")
    if MODE == "cpu":
        deadline = time.time() + 2
        while time.time() < deadline:
            _ = sum(i * i for i in range(10000))
    if MODE == "memory":
        # Bounded so unit tests cannot OOM the runner
        _blob = bytearray(8 * 1024 * 1024)
    return {"mode": MODE}
''',
    )
    write(
        repo / "tests/test_app.py",
        """\
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_healthz():
    assert client.get("/healthz").status_code == 200


def test_readyz():
    assert client.get("/readyz").status_code == 200
""",
    )
    write(repo / "charts/ops-demo/Chart.yaml", "apiVersion: v2\nname: ops-demo\nversion: 0.1.0\nappVersion: '0.1.0'\n")
    write(
        repo / "charts/ops-demo/values.yaml",
        """\
image:
  repository: ghcr.io/efokou-labs/kubernetes-operations-toolkit
  tag: dev
failureMode: none
replicaCount: 1
""",
    )
    write(
        repo / "charts/ops-demo/templates/deployment.yaml",
        """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ops-demo
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: ops-demo
  template:
    metadata:
      labels:
        app: ops-demo
    spec:
      containers:
        - name: app
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          env:
            - name: FAILURE_MODE
              value: {{ .Values.failureMode | quote }}
          ports:
            - containerPort: 8080
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
          readinessProbe:
            httpGet:
              path: /readyz
              port: 8080
""",
    )
    write(
        repo / "charts/ops-demo/templates/service.yaml",
        """\
apiVersion: v1
kind: Service
metadata:
  name: ops-demo
spec:
  selector:
    app: ops-demo
  ports:
    - port: 80
      targetPort: 8080
""",
    )
    for name, body in {
        "crashloopbackoff.md": """# CrashLoopBackOff

**Alert:** `KubePodCrashLooping`

**Diagnosis:** `kubectl describe pod`, `kubectl logs --previous`, check `FAILURE_MODE=cpu|memory` or a bad image tag.

**Mitigation:** Scale to a known-good tag from GitOps. Unset the failure mode.

**Recovery:** Confirm `Ready` and fire a resolve event in Alertmanager.
""",
        "high-api-latency.md": """# High API latency

**Alert:** `APIHighLatency`

**Diagnosis:** Trace in Grafana Tempo; if `FAILURE_MODE=latency`, the handler sleeps. Check saturation (USE) and downstream.

**Mitigation:** Disable the injection; raise replicas if the cause is load.

**Recovery:** p99 returns under SLO; annotate the Grafana dashboard with the Git SHA.
""",
        "db-connection-exhaustion.md": """# Database connection exhaustion

**Alert:** `PostgresConnectionSaturation`

**Diagnosis:** `pg_stat_activity` count vs `max_connections`. Look for leaked connections in workers.

**Mitigation:** Reduce worker concurrency; bounce pods; raise pool limits only as a last step.

**Recovery:** Connections below 70% of max; no waiting queries.
""",
        "nodenotready.md": """# NodeNotReady

**Alert:** `KubeNodeNotReady`

**Diagnosis:** `kubectl describe node`, kubelet logs, disk pressure, kind worker paused.

**Mitigation:** Cordon if needed; restart the kind node container; never delete the control plane casually.

**Recovery:** Node Ready, pods rescheduled, alerts resolved.
""",
        "certificate-expiration.md": """# Certificate expiration

**Alert:** `CertManagerCertExpirySoon`

**Diagnosis:** `cmctl status certificate`, cert-manager logs, DNS-01/HTTP-01 failures.

**Mitigation:** Renew; fix the solver; do not disable TLS.

**Recovery:** `Ready=True` and a new `notAfter` date.
""",
    }.items():
        write(repo / "docs/runbooks" / name, body)
    write(
        repo / ".github/workflows/ci.yml",
        """\
name: ci
on:
  pull_request:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt && pytest -q
      - uses: azure/setup-helm@v5
      - run: helm lint charts/ops-demo
      - uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
        with:
          scan-type: fs
          scan-ref: .
          severity: HIGH,CRITICAL
          exit-code: '0'
""",
    )
    write(
        repo / "Dockerfile",
        """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PORT=8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
""",
    )


def job_processor() -> None:
    repo = REPOS / "distributed-job-processor"
    common(repo)
    write(repo / ".gitignore", PY_GITIGNORE)
    write(
        repo / "README.md",
        """# distributed-job-processor

Small production-shaped job system: API → Redpanda (Kafka API) → workers → PostgreSQL, with retries, a dead-letter path, idempotency, and correlation IDs.

## Architecture

```text
Client -> API -> Redpanda topic jobs
                    |
                    +--> worker pool (idempotent handler)
                    |
                    +--> DLQ after bounded retries
                    |
                    v
                 PostgreSQL (job_id, correlation_id, created_at, attempt, status)
                 Redis (optional lease)
```

OpenTelemetry traces the path API → queue → worker → database.

## Verify

```bash
make verify
```

Local stack:

```bash
docker compose up --build
```

Worker-failure recovery is documented in [docs/worker-failure.md](docs/worker-failure.md).

This workload is deployed onto kind via [kubernetes-gitops](https://github.com/efokou-labs/kubernetes-gitops).
""",
    )
    write(
        repo / "Makefile",
        """\
.PHONY: verify
verify:
	python3 -m pip install -q -r requirements-dev.txt
	python3 -m pytest -q
	@echo distributed-job-processor verify passed
""",
    )
    write(
        repo / "requirements.txt",
        "fastapi==0.141.1\nuvicorn==0.52.4\nsqlalchemy==2.0.52\npsycopg2-binary==2.9.12\npydantic-settings==2.15.0\nopentelemetry-api==1.44.0\n",
    )
    write(repo / "requirements-dev.txt", "-r requirements.txt\npytest==9.1.1\nhttpx==0.28.1\n")
    write(
        repo / "app/__init__.py",
        "",
    )
    write(
        repo / "app/models.py",
        '''\
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    correlation_id: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default=JobStatus.PENDING.value)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
''',
    )
    write(
        repo / "app/processor.py",
        '''\
"""Idempotent job processing with bounded retries and a DLQ."""

from __future__ import annotations

MAX_ATTEMPTS = 3


def next_status(current_attempt: int, handler_ok: bool) -> tuple[str, int]:
    attempt = current_attempt + 1
    if handler_ok:
        return "succeeded", attempt
    if attempt >= MAX_ATTEMPTS:
        return "dead_letter", attempt
    return "pending", attempt


def apply_once(seen_job_ids: set[str], job_id: str) -> bool:
    """Return True if this invocation should run the side effect."""
    if job_id in seen_job_ids:
        return False
    seen_job_ids.add(job_id)
    return True
''',
    )
    write(
        repo / "app/main.py",
        '''\
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.processor import MAX_ATTEMPTS, next_status

app = FastAPI(title="distributed-job-processor")


class EnqueueRequest(BaseModel):
    payload: str
    correlation_id: str | None = None


class EnqueueResponse(BaseModel):
    job_id: str
    correlation_id: str
    status: str
    attempt: int = 0
    max_attempts: int = MAX_ATTEMPTS


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.post("/jobs", response_model=EnqueueResponse)
def enqueue(req: EnqueueRequest):
    correlation_id = req.correlation_id or str(uuid4())
    job_id = str(uuid4())
    return EnqueueResponse(
        job_id=job_id,
        correlation_id=correlation_id,
        status="pending",
    )


@app.post("/internal/retry")
def retry(attempt: int = Field(..., ge=0), ok: bool = False):
    status, new_attempt = next_status(attempt, ok)
    return {"status": status, "attempt": new_attempt}
''',
    )
    write(
        repo / "app/worker.py",
        '''\
"""Worker entrypoint. Compose runs this as a separate process."""

import time

from app.processor import apply_once, next_status


def main() -> None:
    seen: set[str] = set()
    while True:
        # Placeholder loop; docker compose wires Redpanda in later iterations.
        time.sleep(5)
        apply_once(seen, "warmup")
        next_status(0, True)


if __name__ == "__main__":
    main()
''',
    )
    write(
        repo / "app/scheduler.py",
        '''\
"""Scheduler entrypoint for delayed / cron jobs."""

import time


def main() -> None:
    while True:
        time.sleep(30)


if __name__ == "__main__":
    main()
''',
    )
    write(
        repo / "tests/test_processor.py",
        """\
from app.processor import MAX_ATTEMPTS, apply_once, next_status


def test_success_on_first_try():
    status, attempt = next_status(0, True)
    assert status == "succeeded"
    assert attempt == 1


def test_retries_then_dlq():
    status, attempt = next_status(0, False)
    assert status == "pending"
    status, attempt = next_status(attempt, False)
    assert status == "pending"
    status, attempt = next_status(attempt, False)
    assert status == "dead_letter"
    assert attempt == MAX_ATTEMPTS


def test_idempotent_side_effect():
    seen: set[str] = set()
    assert apply_once(seen, "job-1") is True
    assert apply_once(seen, "job-1") is False
""",
    )
    write(
        repo / "tests/test_api.py",
        """\
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 200


def test_enqueue_sets_correlation_id():
    res = client.post("/jobs", json={"payload": "hello"})
    assert res.status_code == 200
    body = res.json()
    assert body["job_id"]
    assert body["correlation_id"]
    assert body["status"] == "pending"
""",
    )
    write(
        repo / "docs/worker-failure.md",
        """# Worker failure and recovery

1. A worker dies mid-handler. The Redpanda offset is not committed.
2. Another worker redelivers the same `job_id`.
3. `apply_once` (unique `job_id` in PostgreSQL) skips a second side effect.
4. `attempt` increments. After three failures the message is written to the DLQ topic and `status=dead_letter`.
5. Replay from the DLQ is a manual, documented operation — never an automatic infinite loop.
""",
    )
    write(
        repo / "docker-compose.yml",
        """\
services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://app:app@postgres:5432/jobs
    depends_on:
      postgres:
        condition: service_healthy
  worker:
    build: .
    command: python -m app.worker
    environment:
      DATABASE_URL: postgresql://app:app@postgres:5432/jobs
    depends_on:
      - postgres
      - redpanda
  scheduler:
    build: .
    command: python -m app.scheduler
    depends_on:
      - postgres
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: jobs
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d jobs"]
      interval: 5s
      retries: 10
  redis:
    image: redis:7-alpine
  redpanda:
    image: docker.redpanda.com/redpandadata/redpanda:v24.2.11
    command:
      - redpanda
      - start
      - --overprovisioned
      - --smp=1
      - --memory=512M
      - --reserve-memory=0M
      - --node-id=0
      - --check=false
      - --kafka-addr=internal://0.0.0.0:9092,external://0.0.0.0:19092
      - --advertise-kafka-addr=internal://redpanda:9092,external://localhost:19092
    ports:
      - "19092:19092"
""",
    )
    write(
        repo / "Dockerfile",
        """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
""",
    )
    write(
        repo / ".github/workflows/ci.yml",
        """\
name: ci
on:
  pull_request:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt && pytest -q
      - uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
        with:
          scan-type: fs
          scan-ref: .
          severity: HIGH,CRITICAL
          exit-code: '0'
""",
    )
    write(repo / ".env.example", "DATABASE_URL=postgresql://app:app@localhost:5432/jobs\n")


def career_workspace() -> None:
    repo = REPOS / "career-workspace"
    common(repo)
    write(repo / ".gitignore", PY_GITIGNORE + NODE_GITIGNORE)
    write(
        repo / "README.md",
        """# career-workspace

Production-style SaaS workload: Next.js UI, FastAPI API + worker, PostgreSQL, Redis, S3-compatible object storage.

It runs on the **shared platform** (kind + GitOps). It does not create its own AWS account.

## Architecture

```text
Browser -> Next.js -> FastAPI -> PostgreSQL
                         |-> worker (Redis)
                         `-> MinIO / S3
```

Environments: Compose (laptop), kind `dev` overlay, documented staging/prod in kubernetes-gitops.

## Verify

```bash
make verify
```

```bash
docker compose up --build
```

API: `http://localhost:8080/healthz`  
Web: `http://localhost:3000`

Secrets never live in Git. Use `.env.example` locally and External Secrets / SOPS on cluster.
""",
    )
    write(
        repo / "Makefile",
        """\
.PHONY: verify
verify:
	python3 -m pip install -q -r apps/api/requirements-dev.txt
	python3 -m pytest -q apps/api
	@echo career-workspace verify passed
""",
    )
    write(repo / "apps/api/requirements.txt", "fastapi==0.141.1\nuvicorn==0.52.4\n")
    write(repo / "apps/api/requirements-dev.txt", "-r requirements.txt\npytest==9.1.1\nhttpx==0.28.1\n")
    write(
        repo / "apps/api/app/main.py",
        '''\
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="career-workspace")


class Application(BaseModel):
    company: str
    role: str
    status: str = "draft"


STORE: list[Application] = []


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.get("/applications")
def list_applications():
    return STORE


@app.post("/applications")
def create_application(item: Application):
    STORE.append(item)
    return item
''',
    )
    write(
        repo / "apps/api/app/worker.py",
        '''\
import time


def main() -> None:
    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
''',
    )
    write(
        repo / "apps/api/tests/test_api.py",
        """\
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/healthz").json()["status"] == "ok"
    assert client.get("/readyz").status_code == 200


def test_create_application():
    res = client.post("/applications", json={"company": "Acme", "role": "SRE"})
    assert res.status_code == 200
    assert client.get("/applications").json()[0]["company"] == "Acme"
""",
    )
    write(
        repo / "apps/web/package.json",
        """\
{
  "name": "career-workspace-web",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^15.1.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  }
}
""",
    )
    write(
        repo / "apps/web/app/page.tsx",
        """\
export default function Page() {
  return (
    <main>
      <h1>Career workspace</h1>
      <p>Track applications. API lives at /api on the FastAPI service.</p>
    </main>
  );
}
""",
    )
    write(
        repo / "apps/web/app/layout.tsx",
        """\
export const metadata = { title: "Career workspace" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
""",
    )
    write(
        repo / "apps/web/next.config.ts",
        """\
import type { NextConfig } from "next";
const nextConfig: NextConfig = {};
export default nextConfig;
""",
    )
    write(repo / "apps/web/tsconfig.json", '{\n  "compilerOptions": {\n    "jsx": "preserve",\n    "strict": true\n  }\n}\n')
    write(
        repo / "docker-compose.yml",
        """\
services:
  api:
    build:
      context: ./apps/api
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://app:app@postgres:5432/career
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
    depends_on:
      - postgres
      - redis
      - minio
  worker:
    build:
      context: ./apps/api
    command: python -m app.worker
    environment:
      DATABASE_URL: postgresql://app:app@postgres:5432/career
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
  web:
    image: node:22-alpine
    working_dir: /src
    volumes:
      - ./apps/web:/src
    command: sh -c "npm install && npm run dev -- --hostname 0.0.0.0 --port 3000"
    ports:
      - "3000:3000"
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: career
  redis:
    image: redis:7-alpine
  minio:
    image: minio/minio:latest
    command: server /data --console-address :9001
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio12345
    ports:
      - "9000:9000"
      - "9001:9001"
""",
    )
    write(
        repo / "apps/api/Dockerfile",
        """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
""",
    )
    write(repo / ".env.example", "DATABASE_URL=postgresql://app:app@localhost:5432/career\nREDIS_URL=redis://localhost:6379/0\nS3_ENDPOINT=http://localhost:9000\n")
    write(
        repo / ".github/workflows/ci.yml",
        """\
name: ci
on:
  pull_request:
  push:
    branches: [main]
jobs:
  api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'
      - run: pip install -r apps/api/requirements-dev.txt
      - run: pytest -q apps/api
      - uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
        with:
          scan-type: fs
          scan-ref: apps/api
          severity: HIGH,CRITICAL
          exit-code: '0'
""",
    )


def agentic() -> None:
    repo = REPOS / "agentic-ai-platform"
    common(repo)
    write(repo / ".gitignore", PY_GITIGNORE)
    write(
        repo / "README.md",
        """# agentic-ai-platform

Deployable AI **service** (not a notebook): FastAPI, orchestrator, tools, RAG/pgvector hooks, Redis, evaluation gates, and cost controls.

## Release thresholds (CI fixtures)

| Gate | Threshold |
| --- | --- |
| Groundedness | >= 90% |
| Tool success | >= 95% |
| Hallucination rate | < 3% |

CI uses deterministic fixtures so a paid model is not required. A real LLM is optional behind `LLM_ENABLED` and `MAX_TOKENS_PER_REQUEST`.

## Cost controls

- `MODEL_ALLOWLIST` — only listed model IDs
- `MAX_TOKENS_PER_REQUEST` — hard cap
- `LLM_KILL_SWITCH` — refuse model calls when true
- Metrics: latency, tokens, cost/request, tool success, retrieval quality (export OTel)

## Verify

```bash
make verify
```
""",
    )
    write(
        repo / "Makefile",
        """\
.PHONY: verify
verify:
	python3 -m pip install -q -r requirements-dev.txt
	python3 -m pytest -q
	@echo agentic-ai-platform verify passed
""",
    )
    write(repo / "requirements.txt", "fastapi==0.141.1\nuvicorn==0.52.4\n")
    write(repo / "requirements-dev.txt", "-r requirements.txt\npytest==9.1.1\nhttpx==0.28.1\n")
    write(
        repo / "app/cost.py",
        '''\
import os

ALLOWLIST = {m.strip() for m in os.getenv("MODEL_ALLOWLIST", "fixture-model").split(",") if m.strip()}
MAX_TOKENS = int(os.getenv("MAX_TOKENS_PER_REQUEST", "512"))
KILL_SWITCH = os.getenv("LLM_KILL_SWITCH", "false").lower() == "true"


def allow_call(model: str, tokens: int) -> tuple[bool, str]:
    if KILL_SWITCH:
        return False, "kill_switch"
    if model not in ALLOWLIST:
        return False, "model_not_allowlisted"
    if tokens > MAX_TOKENS:
        return False, "max_tokens"
    return True, "ok"
''',
    )
    write(
        repo / "app/eval_gate.py",
        '''\
from dataclasses import dataclass


@dataclass
class EvalReport:
    groundedness: float
    tool_success: float
    hallucination_rate: float

    def passed(self) -> bool:
        return (
            self.groundedness >= 0.90
            and self.tool_success >= 0.95
            and self.hallucination_rate < 0.03
        )
''',
    )
    write(
        repo / "app/orchestrator.py",
        '''\
def run_agent(question: str, context: str) -> dict:
    """Deterministic orchestrator used in CI. Swap for LangGraph when LLM_ENABLED=true."""
    grounded = context.lower() in question.lower() or question.lower() in context.lower() or bool(context)
    answer = context if context else "I do not know."
    return {
        "answer": answer,
        "tool_calls": [{"name": "retriever", "ok": True}],
        "grounded": grounded and answer != "I do not know.",
        "tokens": min(len(answer.split()), 32),
        "model": "fixture-model",
    }
''',
    )
    write(
        repo / "app/main.py",
        '''\
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.cost import allow_call
from app.orchestrator import run_agent

app = FastAPI(title="agentic-ai-platform")


class AskRequest(BaseModel):
    question: str
    context: str = ""
    model: str = "fixture-model"
    tokens: int = 32


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.post("/v1/ask")
def ask(req: AskRequest):
    ok, reason = allow_call(req.model, req.tokens)
    if not ok:
        raise HTTPException(status_code=429, detail=reason)
    result = run_agent(req.question, req.context)
    result["cost_per_request"] = round(result["tokens"] * 0.000002, 8)
    return result
''',
    )
    write(
        repo / "app/worker.py",
        '''\
import time


def main() -> None:
    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
''',
    )
    write(
        repo / "evals/fixtures.json",
        """\
[
  {"question": "What is the SLO?", "context": "The SLO is 99.9% availability.", "expect_grounded": true},
  {"question": "Who is the CEO of Mars?", "context": "", "expect_grounded": false}
]
""",
    )
    write(
        repo / "tests/test_gates.py",
        """\
import json
from pathlib import Path

from app.cost import allow_call
from app.eval_gate import EvalReport
from app.orchestrator import run_agent


def test_eval_thresholds():
    report = EvalReport(groundedness=0.91, tool_success=0.96, hallucination_rate=0.02)
    assert report.passed()
    bad = EvalReport(groundedness=0.5, tool_success=0.96, hallucination_rate=0.02)
    assert not bad.passed()


def test_cost_controls():
    ok, reason = allow_call("fixture-model", 16)
    assert ok and reason == "ok"
    ok, reason = allow_call("gpt-secret", 16)
    assert not ok and reason == "model_not_allowlisted"


def test_fixtures_eval():
    fixtures = json.loads((Path(__file__).parents[1] / "evals/fixtures.json").read_text())
    grounded = []
    tool_ok = []
    halluc = []
    for row in fixtures:
        out = run_agent(row["question"], row["context"])
        grounded.append(1.0 if out["grounded"] == row["expect_grounded"] else 0.0)
        tool_ok.append(1.0 if out["tool_calls"][0]["ok"] else 0.0)
        halluc.append(0.0 if out["grounded"] or not row["context"] else 1.0)
    report = EvalReport(
        groundedness=sum(grounded) / len(grounded),
        tool_success=sum(tool_ok) / len(tool_ok),
        hallucination_rate=sum(halluc) / len(halluc),
    )
    assert report.passed()
""",
    )
    write(
        repo / "tests/test_api.py",
        """\
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/healthz").status_code == 200


def test_ask():
    res = client.post("/v1/ask", json={"question": "SLO?", "context": "SLO is 99.9%"})
    assert res.status_code == 200
    assert "tokens" in res.json()
""",
    )
    write(
        repo / "Dockerfile",
        """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
""",
    )
    write(
        repo / "docker-compose.yml",
        """\
services:
  api:
    build: .
    ports: ["8080:8080"]
    environment:
      LLM_KILL_SWITCH: "false"
      MODEL_ALLOWLIST: fixture-model
      MAX_TOKENS_PER_REQUEST: "512"
  worker:
    build: .
    command: python -m app.worker
""",
    )
    write(repo / ".env.example", "LLM_ENABLED=false\nLLM_KILL_SWITCH=false\nMODEL_ALLOWLIST=fixture-model\nMAX_TOKENS_PER_REQUEST=512\n")
    write(
        repo / ".github/workflows/ci.yml",
        """\
name: ci
on:
  pull_request:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt && pytest -q
      - uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
        with:
          scan-type: fs
          scan-ref: .
          severity: HIGH,CRITICAL
          exit-code: '0'
""",
    )


def design_notes() -> None:
    repo = REPOS / "system-design-notes"
    common(repo)
    write(repo / ".gitignore", "site/\n.DS_Store\n")
    write(
        repo / "README.md",
        """# system-design-notes

Polished architecture knowledge base. Template for every design: requirements, capacity, API, data model, architecture, scaling, failure modes, observability, security, trade-offs.

## Verify

```bash
make verify
```

Published via GitHub Pages (MkDocs Material) on merge to `main`.
""",
    )
    write(
        repo / "Makefile",
        """\
.PHONY: verify
verify:
	python3 -m pip install -q -r requirements.txt
	python3 -m mkdocs build --strict
	@echo system-design-notes verify passed
""",
    )
    write(repo / "requirements.txt", "mkdocs==1.6.1\nmkdocs-material==9.7.7\n")
    write(
        repo / "mkdocs.yml",
        """\
site_name: System design notes
theme:
  name: material
nav:
  - Home: index.md
  - URL shortener: designs/url-shortener.md
  - Rate limiter: designs/rate-limiter.md
  - Distributed cache: designs/distributed-cache.md
  - Notification service: designs/notification-service.md
  - API gateway: designs/api-gateway.md
  - Event-driven service: designs/event-driven.md
markdown_extensions:
  - admonition
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
""",
    )
    write(
        repo / "docs/index.md",
        "# System design notes\n\nEach note uses the same template so trade-offs are comparable.\n",
    )
    template = """# {title}

## Requirements
{req}

## Capacity
Start at 100 QPS, 10× peak, 1 year of data. Size storage from payload bytes × QPS × retention.

## API
REST plus idempotency keys on mutating endpoints.

## Data model
Primary key, access pattern, retention, and the index that makes the hot query cheap.

## Architecture

```mermaid
flowchart LR
  Client --> Gateway --> Service --> Store
```

## Scaling
Stateless compute, shard the write path, cache the read path, queue work that can be async.

## Failure modes
Dependency timeout, hot shard, cache stampede, poison message, regional outage.

## Observability
RED on the edge, USE on hosts, traces across the queue, SLOs on availability and latency.

## Security
Authn/z at the gateway, least privilege to data stores, no secrets in Git.

## Trade-offs
{trade}
"""
    designs = {
        "url-shortener.md": ("URL shortener", "Create short links, redirect, optional expiry, unique codes.", "Hash vs counter IDs; 301 vs 302; SQL vs KV."),
        "rate-limiter.md": ("Rate limiter", "Protect APIs per key and per IP; return 429 with Retry-After.", "Token bucket vs sliding window; local vs Redis; fairness vs cost."),
        "distributed-cache.md": ("Distributed cache", "Lower read latency; TTL; stampede control.", "Aside vs write-through; eviction; consistency with the source of truth."),
        "notification-service.md": ("Notification service", "Email/SMS/push; at-least-once delivery; user preferences.", "Fan-out vs queue per channel; templates; compliance holds."),
        "api-gateway.md": ("API gateway", "Auth, rate limit, routing, request IDs.", "Gateway vs service mesh; aggregation vs chatty clients."),
        "event-driven.md": ("Event-driven service", "Async workflows; exactly-once *effect* via idempotency.", "Kafka vs queue; schema evolution; poison messages / DLQ."),
    }
    for file, (title, req, trade) in designs.items():
        write(repo / "docs/designs" / file, template.format(title=title, req=req, trade=trade))
    write(
        repo / ".github/workflows/pages.yml",
        """\
name: pages
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt && mkdocs build --strict
      - uses: actions/upload-pages-artifact@v5
        if: github.ref == 'refs/heads/main'
        with:
          path: site
  deploy:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v5
""",
    )


def obs_lab() -> None:
    repo = REPOS / "observability-lab"
    common(repo)
    write(repo / ".gitignore", PY_GITIGNORE)
    write(
        repo / "README.md",
        """# observability-lab

Instrumented demo whose job is to prove metrics, logs, and traces can identify production failure modes.

## Signals

```text
App --> metrics --> Prometheus --+
    --> logs    --> Loki --------+--> Grafana
    --> traces  --> OTel --> Tempo
```

Dashboards cover **RED** (rate, errors, duration) and **USE** (utilization, saturation, errors).

## Verify

```bash
make verify
```

```bash
docker compose up
```

Inject failures with `FAILURE_MODE` (see kubernetes-operations-toolkit) and follow the telemetry to the cause.

Kind install is optional; the shared cluster already bootstraps an OTel collector in cloud-platform-blueprint. This repo supplies dashboards and the demo app.
""",
    )
    write(
        repo / "Makefile",
        """\
.PHONY: verify
verify:
	python3 -m pip install -q -r requirements-dev.txt
	python3 -m pytest -q
	@echo observability-lab verify passed
""",
    )
    write(repo / "requirements.txt", "fastapi==0.141.1\nuvicorn==0.52.4\nprometheus-client==0.26.0\n")
    write(repo / "requirements-dev.txt", "-r requirements.txt\npytest==9.1.1\nhttpx==0.28.1\n")
    write(
        repo / "app/main.py",
        '''\
import os
import time
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(title="observability-lab")
REQS = Counter("demo_requests_total", "requests", ["code"])
LAT = Histogram("demo_request_seconds", "latency")
MODE = os.getenv("FAILURE_MODE", "none")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/work")
@LAT.time()
def work():
    if MODE == "http500":
        REQS.labels("500").inc()
        raise HTTPException(status_code=500, detail="injected")
    if MODE == "latency":
        time.sleep(0.5)
    REQS.labels("200").inc()
    return {"mode": MODE}
''',
    )
    write(
        repo / "tests/test_app.py",
        """\
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_metrics_and_work():
    assert client.get("/healthz").status_code == 200
    assert client.get("/work").status_code == 200
    body = client.get("/metrics").text
    assert "demo_requests_total" in body
""",
    )
    write(
        repo / "docker-compose.yml",
        """\
services:
  app:
    build: .
    ports: ["8080:8080"]
  prometheus:
    image: prom/prometheus:v2.54.1
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports: ["9090:9090"]
  loki:
    image: grafana/loki:3.2.1
    command: -config.file=/etc/loki/local-config.yaml
    ports: ["3100:3100"]
  tempo:
    image: grafana/tempo:2.6.1
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml:ro
    ports: ["3200:3200"]
  grafana:
    image: grafana/grafana:11.3.0
    ports: ["3000:3000"]
    volumes:
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
""",
    )
    write(
        repo / "prometheus.yml",
        """\
global:
  scrape_interval: 5s
scrape_configs:
  - job_name: demo
    static_configs:
      - targets: ["app:8080"]
""",
    )
    write(
        repo / "tempo.yaml",
        """\
server:
  http_listen_port: 3200
distributor:
  receivers:
    otlp:
      protocols:
        http:
        grpc:
storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo
""",
    )
    write(
        repo / "grafana/provisioning/dashboards/dashboards.yml",
        """\
apiVersion: 1
providers:
  - name: lab
    folder: Observability lab
    type: file
    options:
      path: /var/lib/grafana/dashboards
""",
    )
    write(
        repo / "grafana/provisioning/datasources/datasources.yml",
        """\
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
  - name: Loki
    type: loki
    url: http://loki:3100
  - name: Tempo
    type: tempo
    url: http://tempo:3200
""",
    )
    write(
        repo / "grafana/dashboards/red-use.json",
        """\
{
  "title": "RED and USE",
  "panels": [
    {"type": "stat", "title": "Rate", "targets": [{"expr": "sum(rate(demo_requests_total[1m]))"}]},
    {"type": "stat", "title": "Errors", "targets": [{"expr": "sum(rate(demo_requests_total{code=\\"500\\"}[1m]))"}]},
    {"type": "stat", "title": "Duration", "targets": [{"expr": "histogram_quantile(0.99, sum(rate(demo_request_seconds_bucket[5m])) by (le))"}]}
  ],
  "schemaVersion": 39
}
""",
    )
    write(
        repo / "Dockerfile",
        """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
""",
    )
    write(
        repo / ".github/workflows/ci.yml",
        """\
name: ci
on:
  pull_request:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt && pytest -q
""",
    )


def cdk_examples() -> None:
    repo = REPOS / "aws-cdk-examples"
    common(repo)
    write(repo / ".gitignore", NODE_GITIGNORE)
    write(
        repo / "README.md",
        """# aws-cdk-examples

Repeatable AWS architecture patterns with synth, diff, deploy, and **teardown**.

CI authenticates with **OIDC**. Long-lived access keys are not used.

## Stacks

| Stack | Pattern |
| --- | --- |
| `ServerlessApiStack` | API Gateway + Lambda |
| `EventDrivenStack` | SQS + Lambda |
| `EcsServiceStack` | ECS Fargate service (stub) |
| `EksClusterStack` | EKS (disabled by default; costly) |
| `StaticSiteStack` | S3 + CloudFront |

## Verify

```bash
make verify
```

Teardown:

```bash
npx cdk destroy --all --force
```

The `teardown` GitHub workflow is the supported cleanup path for demo accounts.
""",
    )
    write(
        repo / "Makefile",
        """\
.PHONY: verify
verify:
	npm ci
	npx cdk synth
	@echo aws-cdk-examples verify passed
""",
    )
    write(
        repo / "package.json",
        """\
{
  "name": "aws-cdk-examples",
  "private": true,
  "scripts": {
    "synth": "cdk synth",
    "test": "jest --passWithNoTests"
  },
  "dependencies": {
    "aws-cdk-lib": "^2.173.0",
    "constructs": "^10.4.2"
  },
  "devDependencies": {
    "aws-cdk": "^2.173.0",
    "ts-node": "^10.9.2",
    "typescript": "^5.7.2",
    "jest": "^29.7.0",
    "@types/jest": "^29.5.14",
    "@types/node": "^22.10.2"
  }
}
""",
    )
    write(
        repo / "cdk.json",
        """\
{
  "app": "npx ts-node --prefer-ts-exts bin/app.ts",
  "context": {
    "@aws-cdk/core:newStyleStackSynthesis": true
  }
}
""",
    )
    write(
        repo / "tsconfig.json",
        """\
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  }
}
""",
    )
    write(
        repo / "bin/app.ts",
        """\
#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { ServerlessApiStack } from "../lib/serverless-api-stack";
import { EventDrivenStack } from "../lib/event-driven-stack";
import { EcsServiceStack } from "../lib/ecs-service-stack";
import { StaticSiteStack } from "../lib/static-site-stack";

const app = new cdk.App();
const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION || "us-east-1",
};
new ServerlessApiStack(app, "ServerlessApiStack", { env });
new EventDrivenStack(app, "EventDrivenStack", { env });
new EcsServiceStack(app, "EcsServiceStack", { env });
new StaticSiteStack(app, "StaticSiteStack", { env });
""",
    )
    write(
        repo / "lib/serverless-api-stack.ts",
        """\
import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigw from "aws-cdk-lib/aws-apigateway";
import { Construct } from "constructs";

export class ServerlessApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const fn = new lambda.Function(this, "Handler", {
      runtime: lambda.Runtime.NODEJS_22_X,
      handler: "index.handler",
      code: lambda.Code.fromInline(
        "exports.handler = async () => ({ statusCode: 200, body: 'ok' });"
      ),
    });
    new apigw.LambdaRestApi(this, "Api", { handler: fn });
  }
}
""",
    )
    write(
        repo / "lib/event-driven-stack.ts",
        """\
import * as cdk from "aws-cdk-lib";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { SqsEventSource } from "aws-cdk-lib/aws-lambda-event-sources";
import { Construct } from "constructs";

export class EventDrivenStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const dlq = new sqs.Queue(this, "Dlq", { retentionPeriod: cdk.Duration.days(14) });
    const queue = new sqs.Queue(this, "Jobs", { deadLetterQueue: { queue: dlq, maxReceiveCount: 3 } });
    const fn = new lambda.Function(this, "Worker", {
      runtime: lambda.Runtime.NODEJS_22_X,
      handler: "index.handler",
      code: lambda.Code.fromInline("exports.handler = async () => {};"),
    });
    fn.addEventSource(new SqsEventSource(queue));
  }
}
""",
    )
    write(
        repo / "lib/ecs-service-stack.ts",
        """\
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import { Construct } from "constructs";

export class EcsServiceStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const vpc = new ec2.Vpc(this, "Vpc", { maxAzs: 2, natGateways: 0 });
    const cluster = new ecs.Cluster(this, "Cluster", { vpc });
    const task = new ecs.FargateTaskDefinition(this, "Task", { cpu: 256, memoryLimitMiB: 512 });
    task.addContainer("app", {
      image: ecs.ContainerImage.fromRegistry("public.ecr.aws/docker/library/nginx:alpine"),
      portMappings: [{ containerPort: 80 }],
    });
    new ecs.FargateService(this, "Service", {
      cluster,
      taskDefinition: task,
      desiredCount: 0,
      assignPublicIp: true,
    });
  }
}
""",
    )
    write(
        repo / "lib/static-site-stack.ts",
        """\
import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import { Construct } from "constructs";

export class StaticSiteStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const bucket = new s3.Bucket(this, "Site", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });
    new cloudfront.Distribution(this, "Cdn", {
      defaultBehavior: { origin: origins.S3BucketOrigin.withOriginAccessControl(bucket) },
    });
  }
}
""",
    )
    write(
        repo / "lib/eks-cluster-stack.ts",
        """\
// EKS is defined but not instantiated in bin/app.ts. Control plane cost is high.
// Wire it in only for a same-day demo, then destroy.
import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as eks from "aws-cdk-lib/aws-eks";
import { Construct } from "constructs";

export class EksClusterStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const vpc = new ec2.Vpc(this, "Vpc", { maxAzs: 2, natGateways: 1 });
    new eks.Cluster(this, "Cluster", {
      vpc,
      version: eks.KubernetesVersion.V1_31,
      defaultCapacity: 0,
    });
  }
}
""",
    )
    write(
        repo / ".github/workflows/cdk.yml",
        """\
name: cdk
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
  id-token: write
jobs:
  synth:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v6
        with:
          node-version: '22'
      - run: npm ci
      - run: npx cdk synth
""",
    )
    write(
        repo / ".github/workflows/teardown.yml",
        """\
name: teardown
on:
  workflow_dispatch:
permissions:
  contents: read
  id-token: write
jobs:
  destroy:
    runs-on: ubuntu-latest
    environment: aws-sandbox
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v6
        with:
          node-version: '22'
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      - run: npm ci
      - run: npx cdk destroy --all --force
""",
    )


def deferred_placeholders() -> None:
    """Do not create full repos; meta TRACKER already defers them."""
    write(
        ROOT / "docs" / "deferred-repos.md",
        """# Deferred repositories

These names are reserved for the GitHub org. Do **not** implement them until kind bootstrap, GitOps, and at least one P0 workload are demoable.

- microservices-demo
- homelab-infrastructure
- linux-automation-scripts
- python-algorithms
- leetcode-solutions
- awesome-sre

See [TRACKER.md](../TRACKER.md).
""",
    )


if __name__ == "__main__":
    ops_toolkit()
    job_processor()
    career_workspace()
    agentic()
    design_notes()
    obs_lab()
    cdk_examples()
    deferred_placeholders()
    print("generated application repos")
