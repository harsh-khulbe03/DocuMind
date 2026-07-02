const BASE = import.meta.env.VITE_API_URL ?? "";

export interface DocumentStatus {
  doc_id: string;
  filename: string;
  status: "processing" | "ready" | "failed";
  chunk_count: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourceChunk {
  doc_id: string;
  filename: string;
  page: number;
  text: string;
  score: number;
}

export type StreamEvent =
  | { type: "source"; doc_id: string; filename: string; page: number; text: string; score: number }
  | { type: "token"; text: string }
  | { type: "done"; insufficient_coverage: boolean };

// ── Documents ──────────────────────────────────────────────────────────────────

export async function uploadDocument(file: File): Promise<{ doc_id: string; filename: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/documents`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Upload failed: ${res.status}`);
  }
  return res.json();
}

export async function listDocuments(): Promise<DocumentStatus[]> {
  const res = await fetch(`${BASE}/documents`);
  if (!res.ok) throw new Error(`Failed to list documents: ${res.status}`);
  const data = await res.json();
  return data.documents;
}

export async function getDocument(docId: string): Promise<DocumentStatus> {
  const res = await fetch(`${BASE}/documents/${docId}`);
  if (!res.ok) throw new Error(`Document not found: ${res.status}`);
  return res.json();
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${BASE}/documents/${docId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
}

// ── Query (streaming) ──────────────────────────────────────────────────────────

export async function* queryStream(
  question: string,
  docIds: string[] | null = null,
): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${BASE}/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, doc_ids: docIds }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Query failed: ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          yield JSON.parse(line.slice(6)) as StreamEvent;
        } catch {
          // malformed line — skip
        }
      }
    }
  }
}
