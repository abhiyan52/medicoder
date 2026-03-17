# Medicoder UI

The React + TypeScript frontend for the Medicoder medical coding platform. This application allows clinicians to securely upload clinical notes, track asynchronous processing status, and review extracted ICD-10 and HCC results via a modern, responsive dashboard.

---

## 🏗 Architecture

The UI is built as a single-page application (SPA) focused on clean architecture and performance:

- **Framework**: [React](https://react.dev/) using [Vite](https://vitejs.dev/) for blazing-fast bundling.
- **Data Fetching**: [TanStack Query](https://tanstack.com/query/latest) (React Query) for caching, background syncing, and automatic polling of document status.
- **Styling**: Pure CSS (`index.css`) utilizing modern CSS variables and variables for a clean, consistent design system.
- **Routing**: Component-based conditional rendering (Workspace vs Detail view) optimized for a focused clinician workflow.
- **Local Storage**: Secure session management holding the JWT access token.

---

## 🔄 Core App Flows

### 1. Authentication
1. User enters API credentials.
2. Form submits to `POST /auth/login`.
3. An access token is returned and stored securely in `sessionStorage` or `localStorage`.
4. Subsequent API calls attach `Authorization: Bearer <token>`.

### 2. Workspace (Document History & Upload)
- **History list**: Polls `GET /documents` to display all uploaded documents, their respective statuses (pending, processed, failed), and processing metadata.
- **Upload**: Select a clinical note file (`.txt` or no extension), submit via `POST /documents` (multipart/form-data), which kicks off backend processing on Google Cloud.

### 3. Extraction Details
- When a document is clicked, the app opens the Detail View.
- Repeatedly polls `GET /documents/{documentId}` while the status is "pending".
- Displays the extracted results table, highlighting which of the extracted ICD-10 codes are **HCC Relevant**.

---

## 🚀 Local Development

### Prerequisites
- Node.js 20+
- A running instance of the Medicoder FastAPI backend (usually on `localhost:8000`).

### Setup

Install the dependencies:
```bash
npm install
```

Start the development server:
```bash
npm run dev
```

### Environment Variables
Vite relies on environment variables for configuration. Create a `.env.local` to point to your local development server if needed:
```env
VITE_API_URL=http://localhost:8000
```
*(If unset, it defaults to `http://localhost:8000` automatically).*

---

## 🚢 Production Deployment

The UI is containerized and optimised for production deployment on **Google Cloud Run**.

### Build Pipeline
1. **Build Stage (`node:alpine`)**: Installs dependencies and runs `npm run build` to generate the highly optimized raw HTML/JS/CSS assets into the `/dist` folder.
2. **Serve Stage (`nginx:alpine`)**: Copies the compiled assets and our custom `nginx.conf` into a lightweight web server. The NGINX server routes all missing requests to `index.html` (standard SPA behavior) and has advanced caching headers applied.

### Manual Deployment to Cloud Run 

Ensure you have created a `.env.production` file containing the live API URL:
```env
VITE_API_URL=https://medicoder-api-123456.us-central1.run.app
```

Then submit the build to Google Cloud:
```bash
gcloud run deploy medicoder-ui \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```
*(Note: A `.gcloudignore` file ensures `.env.production` is bundled in the container).*

---

## 📁 Source Map

- `src/App.tsx` - Main application logic, React state, React Query hooks, and UI components.
- `src/api.ts` - Clean, reusable HTTP client layer defining all fetch requests and auth header injection.
- `src/types.ts` - Strict TypeScript interfaces corresponding to the backend Pydantic schemas.
- `src/index.css` - Focused stylesheet using modern aesthetic tokens.
- `Dockerfile` & `nginx.conf` - Multi-stage container production setup.
