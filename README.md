# Medicoder

An automated medical coding pipeline that processes clinical progress notes, extracts diagnoses with ICD-10 codes using an LLM, and flags which conditions are HCC (Hierarchical Condition Category) relevant.

---

## Table of Contents

- [Solution Overview](#solution-overview)
- [Setup](#setup)
- [Running the Pipeline](#running-the-pipeline)
- [Docker](#docker)
- [LangGraph Development Web App](#langgraph-development-web-app)
- [Accessing Output](#accessing-output)

---

## Solution Overview

### Pipeline

The system is implemented as a [LangGraph](https://github.com/langchain-ai/langgraph) state machine with four sequential nodes:

```
input_handler → parser → extractor → evaluator
```

| Node | Service | What it does |
|---|---|---|
| `input_handler` | — | Resolves `raw_input` to note text; accepts a file path or raw text |
| `parser` | `RegexBasedParser` | Extracts the **Assessment / Plan** section using regex patterns; falls back to the full note if no section is found |
| `extractor` | `ConditionExtractor` | Calls **Gemini 2.5 Flash** via Vertex AI with a versioned prompt to extract a list of `{ condition, code }` pairs |
| `evaluator` | `HCCRelevanceEvaluator` | Normalises each ICD-10 code and checks it against a reference CSV of tracked HCC codes; appends `hcc_relevant: true/false` to each condition |

Note: the original assignment asked for Gemini 1.5 Flash, but this project defaults to `gemini-2.5-flash` because Gemini 1.5 Flash is no longer available in the Vertex AI environment used for this submission.

### State

Each pipeline run passes a single `MedicoderState` dict through all nodes:

```python
{
  "raw_input":       str,               # file path or raw note text
  "clinical_note":   str,               # resolved note content
  "parsed_sections": dict[str, list],   # e.g. {"assessment_plan": [...]}
  "conditions":      list[dict],        # [{condition, code}, ...]
  "results":         list[dict],        # [{condition, code, hcc_relevant}, ...]
}
```

### Output

One JSON file is written per note to `output/`:

```json
{
  "note": "pn_1",
  "results": [
    { "condition": "Type 2 Diabetes Mellitus", "code": "E11.9", "hcc_relevant": true },
    { "condition": "Hypertension", "code": "I10", "hcc_relevant": false }
  ]
}
```

---

## Setup

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)
- A Google Cloud project with Vertex AI enabled
- A GCP service account key with the **Vertex AI User** role

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd medicoder
poetry install
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Path to your GCP service account key (local path for non-Docker runs)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/gcp-key.json

# Optional — auto-detected from the key file if not set
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_CLOUD_LOCATION=us-central1
```

---

## Running the Pipeline

### Run on the bundled test notes

Nine sample clinical notes are included in `data/notes/`. Run the full batch:

```bash
poetry run python -m app.batch_runner
```

Results are written to `output/` as `<note_name>.json`.

### Run on a single note (Python API)

```python
from app.graph.medicoder_pipeline import run

# from a file path
results = run("data/notes/pn_1")

# or from raw text
results = run("Assessment/Plan: Type 2 DM (E11.9), HTN (I10) ...")

print(results)
```

### Run on custom notes

Drop any plain-text `.txt` or extension-free files into `data/notes/` and run the batch command above.

---

## Docker

The container runs the pipeline once and exits. No server is started.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Docker Compose

### 1. Set up environment

`GCP_KEY_PATH` is required for `docker compose up` — it mounts your key file into the container. Copy `.env.example` to `.env` and set your path:

```bash
cp .env.example .env
# Edit .env and set:
# GCP_KEY_PATH=/path/to/your/gcp-key.json
```

Or export in your shell before running:

```bash
export GCP_KEY_PATH=/path/to/your/gcp-key.json
```

### 2. Build the image

```bash
docker compose build
```

Build works without any environment variables; a placeholder credentials file is used if `GCP_KEY_PATH` is unset.

### 3. Run

```bash
docker compose up
```

To rebuild after code or dependency changes:

```bash
docker compose up --build
```

### What happens inside the container

| Path | Purpose |
|---|---|
| `/app/data/notes/` | Bundled clinical notes (copied at build time) |
| `/app/data/HCC_relevant_codes.csv` | HCC reference data (copied at build time) |
| `/app/credentials/gcp-key.json` | GCP key mounted at runtime (read-only) |
| `/app/output/` | Results written here; bind-mounted to `./output/` on the host |

The container runs as a non-root user (`appuser`) for security.

### Troubleshooting: empty `output/`

If `output/` stays empty after `docker compose up`, the pipeline is likely failing (e.g. GCP auth or API errors). Run without `-d` to see logs:

```bash
docker compose up
```

Common causes:

- **`GCP_KEY_PATH` not set or invalid** — Use a real GCP service account key with Vertex AI / Gemini API access. The placeholder file will cause auth failures.
- **Key lacks permissions** — The service account needs `Vertex AI User` (or similar) to call Gemini.
- **Billing / quotas** — Ensure the GCP project has billing enabled and Gemini API enabled.

---

## LangGraph Development Web App

LangGraph Studio lets you run and inspect individual pipeline executions interactively.

### Start the dev server

```bash
poetry run langgraph dev
```

This reads `langgraph.json` in the project root and serves the `medicoder` graph.

### Use the Studio UI

1. Open the URL printed in the terminal (typically `http://localhost:8123`).
2. Select the **medicoder** graph.
3. Provide input in the **Input** panel:

```json
{ "raw_input": "data/notes/pn_1" }
```

Or paste raw note text:

```json
{ "raw_input": "Assessment/Plan:\n1. Type 2 DM — E11.9\n2. CKD stage 3 — N18.3" }
```

4. Click **Run** — each node's state is visible in real time.

---

## Accessing Output

### Local runs

Results are written to `output/` in the project root:

```
output/
  pn_1.json
  pn_2.json
  ...
```

### Docker runs

The `output/` directory is bind-mounted from the host, so results appear in `./output/` immediately after the container exits:

```bash
ls ./output/
cat ./output/pn_1.json
```

To use a different host output directory:

```bash
docker run --rm \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-key.json \
  -v /path/to/your/key.json:/app/credentials/gcp-key.json:ro \
  -v /custom/output/dir:/app/output \
  medicoder
```
