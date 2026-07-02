import { useCallback, useEffect, useState } from "react";
import {
  deleteDocument,
  getDocument,
  listDocuments,
  uploadDocument,
  type DocumentStatus,
} from "../api/client";

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentStatus[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load documents");
    }
  }, []);

  // Poll every 2s while any doc is processing
  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll every 2s while any doc is processing. Keyed on the boolean, not the
  // array, so a poll updating `documents` doesn't tear down the interval.
  const hasProcessing = documents.some((d) => d.status === "processing");
  useEffect(() => {
    if (!hasProcessing) return;
    const id = setInterval(refresh, 2000);
    return () => clearInterval(id);
  }, [hasProcessing, refresh]);

  const upload = useCallback(async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, [refresh]);

  const remove = useCallback(async (docId: string) => {
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }, []);

  return { documents, uploading, error, upload, remove, refresh };
}
