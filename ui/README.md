# Medicoder UI

## Overview

Medicoder UI is the React + TypeScript frontend for submitting clinical notes, tracking processing history, and reviewing extracted ICD-10 and HCC results.

Architecture:
- `src/App.tsx` coordinates the main process/history views.
- `src/api.ts` contains HTTP calls to the local API.
- `src/components/` holds focused UI blocks for note entry, uploads, history, and results.
- `src/types.ts` defines the frontend contracts expected from the API.

## App Flows

### Process Note

```text
Paste note -> Submit -> POST /process/text -> Receive extracted results -> Render results table
```

Description:
- The user pastes a clinical note.
- The UI submits trimmed text to the backend.
- The response is rendered as a condition table with HCC status.

### Upload

```text
Select .txt file -> POST /process/file -> Backend processes file -> Render extracted results
```

Description:
- The user uploads a plain text clinical note.
- The UI rejects invalid file types at runtime before sending them.
- Successful responses reuse the same results view as pasted notes.

### History

```text
Open History tab -> GET /history -> Expand entry -> Review stored processing output
```

Description:
- The UI loads previously processed notes.
- Each row shows note metadata and counts.
- Expanding a row reveals detailed extraction results.

## Local API

Expected environment variables:
- `VITE_API_URL`: Base URL for the local Medicoder API.

Required endpoints:

### `POST /process/text`

Request:

```json
{
  "note": "Assessment and plan text..."
}
```

Response:

```json
{
  "note_id": "pn_1",
  "results": [
    {
      "condition": "Type 2 Diabetes Mellitus",
      "code": "E11.9",
      "hcc_relevant": true
    }
  ]
}
```

### `POST /process/file`

Request:
- `multipart/form-data`
- field: `file`

Response:

```json
{
  "note_id": "pn_1",
  "results": [
    {
      "condition": "Hypertension",
      "code": "I10",
      "hcc_relevant": false
    }
  ]
}
```

### `GET /history`

Response:

```json
[
  {
    "note_id": "pn_1",
    "processed_at": "2026-03-17T10:00:00Z",
    "result_count": 2,
    "hcc_count": 1,
    "results": []
  }
]
```

Notes:
- `processed_at` should be a valid ISO-8601 timestamp.
- `results` must match the same condition shape used by the process endpoints.

## Run & Test

Install dependencies:

```bash
npm install
```

Start the dev server:

```bash
npm run dev
```

Build for production:

```bash
npm run build
```

Mock services:
- Point `VITE_API_URL` at a local API stub or the backend dev server.
- Keep the backend running before exercising process and history flows.

## Troubleshooting

- If requests fail in development, verify `VITE_API_URL` and confirm the backend is running.
- If uploads do not work, confirm the selected file is a `.txt` file and the API accepts `multipart/form-data`.
- If history shows unknown dates, inspect the backend `processed_at` field for invalid timestamps.

## Contributing

- Keep API integration logic in `src/api.ts` and avoid embedding fetch logic in components.
- Prefer small presentational components with typed props.
- Update this README when API contracts or local developer workflows change.
