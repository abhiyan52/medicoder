# Medicoder

A complete medical coding platform that processes clinical progress notes, extracts diagnoses with ICD-10 codes using an LLM (Gemini 2.5 Flash), and flags which conditions are HCC (Hierarchical Condition Category) relevant. 

This project features a fully serverless, cloud-native architecture including a **React frontend**, a **FastAPI backend**, an asynchronous **LangGraph processing pipeline**, and **auto-scaling Google Cloud Run** deployment.

---

## Table of Contents

- [App Screenshots](#app-screenshots)
- [Solution Overview](#solution-overview)
- [Architecture & Implementation](#architecture--implementation)
- [Setup & Local Development](#setup--local-development)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Deployment](#deployment)

---

## App Screenshots

### Workspace & Document History
<img src="docs/assets/workspace.png" width="800" alt="Workspace & History" />

### Extraction Details & HCC Analysis
<img src="docs/assets/extraction_details.png" width="800" alt="Extraction Details" />

---

## Solution Overview

### Frontend (React + Vite)
- **Modern UI**: A responsive, dashboard-style interface built with React.
- **Features**: JWT-based authentication, drag-and-drop document upload, real-time status polling, and a detailed extraction results viewer highlighting HCC-relevant codes.
- **Tech Stack**: React, TypeScript, Vite, TanStack Query (React Query), standard CSS.

### Backend (FastAPI)
- **REST API**: Provides endpoints for authentication (`/auth/login`) and document management (`/documents`).
- **Security**: JWT (JSON Web Token) authentication prevents sending cleartext credentials on every request.
- **Storage**: 
  - File uploads go straight to **Google Cloud Storage (GCS)**.
  - Document metadata and extraction results are stored in **Google Cloud Firestore** (NoSQL).
- **Asynchronous Processing**: Uses FastAPI `BackgroundTasks` to trigger the heavy LLM extraction pipeline immediately after upload, without blocking the HTTP response.

### Extraction Pipeline (LangGraph)
The core AI engine is implemented as a [LangGraph](https://github.com/langchain-ai/langgraph) state machine with four sequential nodes:

```
input_handler → parser → extractor → evaluator
```

| Node | Service | What it does |
|---|---|---|
| `input_handler` | — | Retrieves the raw document text from Cloud Storage |
| `parser` | `RegexBasedParser` | Extracts the **Assessment / Plan** section using regex patterns |
| `extractor` | `ConditionExtractor` | Calls **Gemini 2.5 Flash** to extract a list of `{ condition, code }` pairs |
| `evaluator` | `HCCRelevanceEvaluator` | Normalises each ICD-10 code and checks it against a reference list, appending `hcc_relevant: true/false` |

---

## Architecture & Implementation

### Cloud-Native Design

```
┌───────────────┐        ┌─────────────────┐        ┌──────────────────┐
│               │        │                 │        │                  │
│  React SPA    │ ─────► │  FastAPI        │ ─────► │  Google Cloud    │
│  (Cloud Run)  │  JWT   │  (Cloud Run)    │        │  Storage (GCS)   │
│               │        │                 │        │                  │
└───────────────┘        └───────┬─────────┘        └──────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
        ┌─────────────────┐             ┌──────────────────┐
        │                 │             │                  │
        │  LangGraph      │ ──────────► │  Firestore       │
        │  Pipeline       │             │  (Database)      │
        │                 │             │                  │
        └───────────────┬─┘             └──────────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │                  │
               │  Vertex AI       │
               │  (Gemini 2.5)    │
               │                  │
               └──────────────────┘
```

- **Serverless**: Both the frontend and backend run on Google Cloud Run, automatically scaling from 0 to N instances based on traffic.
- **Stateless Services**: All components are stateless; state is persisted in Firestore and GCS, allowing horizontal scaling.

---

## Setup & Local Development

### Prerequisites
- Python 3.10+ and [Poetry](https://python-poetry.org/docs/#installation)
- Node.js 20+ and npm
- [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and configured

### Backend Setup

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Configure environment:**
   Create a `.env` file in the root directory:
   ```env
   # API Security
   API_USERNAME=your_username
   API_PASSWORD=your_secure_password
   JWT_SECRET_KEY=generate_a_random_32_char_hex_string

   # Cloud Resources
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GCS_BUCKET_NAME=your-gcs-bucket-name
   ```

3. **Authenticate your local machine:**
   To allow your local code to talk to Firestore and GCS, generate Application Default Credentials (ADC):
   ```bash
   gcloud auth application-default login
   ```

4. **Start the backend server:**
   ```bash
   poetry run uvicorn app.api:app --reload --port 8000
   ```
   The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd ui
   npm install
   ```

2. **Configure environment (optional):**
   The frontend defaults to `http://localhost:8000` for the API. If your backend runs elsewhere, create `ui/.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

3. **Start the dev server:**
   ```bash
   npm run dev
   ```
   The UI will be available at `http://localhost:5173`.

---

## Deployment

The system is fully containerized and configured for deployment via Google Cloud Run.

### Deploying the Backend API
The backend includes a `Dockerfile` that runs the FastAPI application using Uvicorn.

```bash
gcloud run deploy medicoder-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="API_USERNAME=...,API_PASSWORD=...,JWT_SECRET_KEY=...,GOOGLE_CLOUD_PROJECT=...,GCS_BUCKET_NAME=..."
```

- `--allow-unauthenticated` permits incoming HTTP traffic at the Cloud Run (infrastructure) level. The application still enforces JWT authentication on all endpoints.
- Cloud Run automatically uses the service account attached to the revision for GCS and Firestore access. Ensure it has the **Storage Object Admin** and **Cloud Datastore User** roles.

*(Note: In a true production environment, secrets should be stored in Google Secret Manager rather than injected as plaintext environment variables).*

### Deploying the Frontend UI
The frontend includes a multi-stage `Dockerfile` that builds the React application and serves the static assets using NGINX (`nginx.conf`).

Before deploying, ensure you have a `ui/.env.production` file pointing to your deployed backend URL:
```env
VITE_API_URL=https://your-api-url.run.app
```

Then deploy the frontend:
```bash
cd ui
gcloud run deploy medicoder-ui \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```
