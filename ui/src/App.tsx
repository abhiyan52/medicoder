import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent, ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  clearSession,
  fetchDocumentDetail,
  fetchDocuments,
  getSession,
  login,
  uploadDocument,
} from "./api";
import { ErrorMessage } from "./components/ErrorMessage";
import { ResultsTable } from "./components/ResultsTable";
import type { AuthSession, DocumentDetail, DocumentHistoryItem, DocumentStatus } from "./types";

type View = "workspace" | "detail";

function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.message;
  }

  if (error && typeof error === "object" && "message" in error && typeof error.message === "string") {
    return error.message;
  }

  return "An unexpected error occurred";
}

export default function App() {
  const [session, setSession] = useState<AuthSession | null>(() => getSession());
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [view, setView] = useState<View>("workspace");

  useEffect(() => {
    if (!session) {
      setSelectedDocumentId(null);
      setView("workspace");
    }
  }, [session]);

  if (!session) {
    return <LoginScreen onSuccess={setSession} />;
  }

  return (
    <AuthenticatedApp
      session={session}
      selectedDocumentId={selectedDocumentId}
      view={view}
      onSelectDocument={(documentId) => {
        setSelectedDocumentId(documentId);
        setView("detail");
      }}
      onShowWorkspace={() => setView("workspace")}
      onLogout={() => {
        clearSession();
        setSession(null);
      }}
    />
  );
}

interface LoginScreenProps {
  onSuccess: (session: AuthSession) => void;
}

function LoginScreen({ onSuccess }: LoginScreenProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const loginMutation = useMutation({
    mutationFn: () => login({ username, password }),
    onSuccess,
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!username.trim() || !password.trim()) {
      return;
    }
    loginMutation.mutate();
  }

  return (
    <main className="app-shell login-shell">
      <section className="login-panel">
        <div className="eyebrow">Healthcare Extraction Workspace</div>
        <h1>Medicoder</h1>
        <p className="intro-copy">
          Sign in to upload clinical documents, review processing history, and inspect extracted ICD-10 and HCC results.
        </p>

        <form className="stack-lg" onSubmit={handleSubmit}>
          <label className="field">
            <span>Username</span>
            <input
              className="input"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Enter your API username"
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              className="input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your API password"
            />
          </label>

          {loginMutation.isError && (
            <ErrorMessage message={getErrorMessage(loginMutation.error)} />
          )}

          <button className="button button-primary button-block" type="submit" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

interface AuthenticatedAppProps {
  session: AuthSession;
  selectedDocumentId: string | null;
  view: View;
  onSelectDocument: (documentId: string) => void;
  onShowWorkspace: () => void;
  onLogout: () => void;
}

function AuthenticatedApp({
  session,
  selectedDocumentId,
  view,
  onSelectDocument,
  onShowWorkspace,
  onLogout,
}: AuthenticatedAppProps) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const MAX_FILE_SIZE = 10 * 1024; // 10 KB

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setFileError(null);
    if (selected) {
      const isPlainText = selected.type === "text/plain" || /\.txt$/i.test(selected.name);
      if (!isPlainText) {
        setFileError("Only plain text files (.txt) are supported.");
        setFile(null);
        return;
      }
      if (selected.size > MAX_FILE_SIZE) {
        setFileError(`File size exceeds the ${MAX_FILE_SIZE / 1024} KB limit.`);
        setFile(null);
        return;
      }
    }
    setFile(selected);
  }

  const documentsQuery = useQuery({
    queryKey: ["documents", session.token],
    queryFn: () => fetchDocuments(session.token),
  });

  const detailQuery = useQuery({
    queryKey: ["document-detail", selectedDocumentId, session.token],
    queryFn: () => fetchDocumentDetail(selectedDocumentId!, session.token),
    enabled: Boolean(selectedDocumentId),
    refetchInterval: (query) => {
      const detail = query.state.data as DocumentDetail | undefined;
      return detail && !isTerminalStatus(detail.status) ? 3000 : false;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: () => uploadDocument({ title, file: file!, token: session.token }),
    onSuccess: async (document) => {
      setTitle("");
      setFile(null);
      setFileError(null);
      onSelectDocument(document.id);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["documents", session.token] }),
        queryClient.invalidateQueries({ queryKey: ["document-detail", document.id, session.token] }),
      ]);
    },
  });

  function handleUploadSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !file) {
      return;
    }
    uploadMutation.mutate();
  }

  return (
    <main className="app-shell">
      <section className="app-frame">
        <header className="topbar">
          <div>
            <div className="eyebrow">Medicoder</div>
            <h1 className="page-title">Document processing</h1>
            <p className="muted">Upload notes, monitor status, and inspect extraction details.</p>
          </div>

          <div className="topbar-actions">
            <div className="session-chip">{session.username}</div>
            <button className="button button-secondary" type="button" onClick={onLogout}>
              Logout
            </button>
          </div>
        </header>

        <nav className="tabs" aria-label="Primary views">
          <button
            className={view === "workspace" ? "tab tab-active" : "tab"}
            type="button"
            onClick={onShowWorkspace}
          >
            Upload & history
          </button>
          <button
            className={view === "detail" ? "tab tab-active" : "tab"}
            type="button"
            onClick={() => selectedDocumentId && onSelectDocument(selectedDocumentId)}
            disabled={!selectedDocumentId}
          >
            Extraction details
          </button>
        </nav>

        {view === "workspace" ? (
          <section className="workspace-grid">
            <article className="card">
              <div className="card-header">
                <div>
                  <h2>Upload document</h2>
                  <p className="muted">Submit a file and queue the extraction pipeline.</p>
                </div>
              </div>

              <form className="stack-lg" onSubmit={handleUploadSubmit}>
                <label className="field">
                  <span>Document title</span>
                  <input
                    className="input"
                    type="text"
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="Ex. Discharge summary - March 17"
                  />
                </label>

                <label className="field">
                  <span>File</span>
                  <input
                    className="input"
                    type="file"
                    accept="text/plain,.txt"
                    onChange={handleFileChange}
                  />
                </label>

                {fileError && <ErrorMessage message={fileError} />}

                {file && (
                  <div className="file-meta">
                    <span>{file.name}</span>
                    <span>{formatFileSize(file.size)}</span>
                  </div>
                )}

                {uploadMutation.isError && (
                  <ErrorMessage message={getErrorMessage(uploadMutation.error)} />
                )}

                <button
                  className="button button-primary"
                  type="submit"
                  disabled={uploadMutation.isPending || !title.trim() || !file || Boolean(fileError)}
                >
                  {uploadMutation.isPending ? "Uploading..." : "Upload document"}
                </button>
              </form>
            </article>

            <article className="card">
              <div className="card-header">
                <div>
                  <h2>History</h2>
                  <p className="muted">Select a document to open its extraction detail view.</p>
                </div>
              </div>

              {documentsQuery.isLoading && <EmptyState message="Loading document history..." />}

              {documentsQuery.isError && (
                <ErrorMessage message={getErrorMessage(documentsQuery.error)} />
              )}

              {documentsQuery.data && documentsQuery.data.items.length === 0 && (
                <EmptyState message="No uploaded documents yet." />
              )}

              {documentsQuery.data && documentsQuery.data.items.length > 0 && (
                <div className="history-list">
                  {documentsQuery.data.items.map((document) => (
                    <HistoryRow
                      key={document.id}
                      document={document}
                      selected={document.id === selectedDocumentId}
                      onOpen={() => onSelectDocument(document.id)}
                    />
                  ))}
                </div>
              )}
            </article>
          </section>
        ) : (
          <section className="card">
            <div className="card-header">
              <div>
                <h2>Extraction detail</h2>
                <p className="muted">Review document metadata, extracted text, and processed results.</p>
              </div>
              <button className="button button-secondary" type="button" onClick={onShowWorkspace}>
                Back to workspace
              </button>
            </div>

            {!selectedDocumentId && <EmptyState message="Select a document from history to view details." />}

            {detailQuery.isLoading && selectedDocumentId && <EmptyState message="Loading extraction detail..." />}

            {detailQuery.isError && (
              <ErrorMessage message={getErrorMessage(detailQuery.error)} />
            )}

            {detailQuery.data && (
              <DocumentDetailPanel detail={detailQuery.data} />
            )}
          </section>
        )}
      </section>
    </main>
  );
}

interface HistoryRowProps {
  document: DocumentHistoryItem;
  selected: boolean;
  onOpen: () => void;
}

function HistoryRow({ document, selected, onOpen }: HistoryRowProps) {
  return (
    <button className={selected ? "history-row history-row-active" : "history-row"} type="button" onClick={onOpen}>
      <div className="history-row-main">
        <div className="history-title-row">
          <span className="history-title">{document.title}</span>
          <StatusBadge status={document.status} />
        </div>
        <div className="history-meta">
          <span>{formatDate(document.created_at)}</span>
        </div>
      </div>
      <span className="history-link">Open</span>
    </button>
  );
}

interface DocumentDetailPanelProps {
  detail: DocumentDetail;
}

function DocumentDetailPanel({ detail }: DocumentDetailPanelProps) {
  const totalResults = detail.processed_results.length;
  const hccCount = detail.processed_results.filter((item) => Boolean(item.hcc_code?.hcc_relevant)).length;
  const rows = detail.processed_results.map((item) => ({
    condition: item.extracted_code?.condition ?? "Unknown condition",
    code: item.extracted_code?.code ?? "N/A",
    hcc_relevant: Boolean(item.hcc_code?.hcc_relevant),
  }));

  return (
    <div className="stack-xl">
      <section className="detail-grid">
        <InfoCard label="Title" value={detail.title} />
        <InfoCard label="Status" value={<StatusBadge status={detail.status} />} />
        <InfoCard label="Updated" value={formatDate(detail.updated_at)} />
      </section>

      <section className="summary-strip">
        <SummaryMetric label="Results" value={String(totalResults)} />
        <SummaryMetric label="HCC relevant" value={String(hccCount)} />
        <SummaryMetric
          label="Processed at"
          value={detail.processed_at ? formatDate(detail.processed_at) : "Pending"}
        />
      </section>

      <section className="stack-md">
        <div className="section-header">
          <h3>Processed output</h3>
        </div>

        {rows.length > 0 ? (
          <ResultsTable results={rows} />
        ) : (
          <EmptyState
            message={
              isTerminalStatus(detail.status)
                ? "No extraction rows are available for this document."
                : "The pipeline is still running. This panel refreshes automatically."
            }
          />
        )}
      </section>

      <section className="stack-md">
        <div className="section-header">
          <h3>Extracted text</h3>
        </div>
        <div className="text-panel">
          {detail.extracted_text?.trim() || "Extracted text is not available yet."}
        </div>
      </section>
    </div>
  );
}

function StatusBadge({ status }: { status: DocumentStatus }) {
  const badgeClass = `status-badge status-${status}`;
  return <span className={badgeClass}>{status.replace("_", " ")}</span>;
}

function InfoCard({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="info-card">
      <span className="info-label">{label}</span>
      <div className={mono ? "info-value info-value-mono" : "info-value"}>{value}</div>
    </div>
  );
}

function SummaryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <span className="info-label">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return <div className="empty-state">{message}</div>;
}

function isTerminalStatus(status: DocumentStatus) {
  return status === "processed" || status === "failed";
}

function formatDate(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Unknown";
  }
  return parsed.toLocaleString();
}

function formatFileSize(size: number) {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}
