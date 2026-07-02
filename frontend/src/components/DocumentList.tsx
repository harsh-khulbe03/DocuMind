import { FileText, Trash2, Loader2, CheckCircle, XCircle } from "lucide-react";
import type { DocumentStatus } from "../api/client";

interface Props {
  documents: DocumentStatus[];
  onDelete: (docId: string) => void;
}

function StatusBadge({ status }: { status: DocumentStatus["status"] }) {
  if (status === "ready")
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
        <CheckCircle className="w-3 h-3" /> Ready
      </span>
    );
  if (status === "processing")
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full">
        <Loader2 className="w-3 h-3 animate-spin" /> Processing
      </span>
    );
  return (
    <span className="flex items-center gap-1 text-xs font-medium text-red-700 bg-red-50 px-2 py-0.5 rounded-full">
      <XCircle className="w-3 h-3" /> Failed
    </span>
  );
}

export function DocumentList({ documents, onDelete }: Props) {
  if (documents.length === 0) {
    return (
      <p className="text-sm text-gray-400 text-center py-6">
        No documents yet. Upload a PDF to get started.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {documents.map((doc) => (
        <li
          key={doc.doc_id}
          className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg shadow-sm"
        >
          <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">{doc.filename}</p>
            {doc.status === "ready" && (
              <p className="text-xs text-gray-400">{doc.chunk_count} chunks indexed</p>
            )}
            {doc.status === "failed" && doc.error && (
              <p className="text-xs text-red-500 truncate">{doc.error}</p>
            )}
          </div>
          <StatusBadge status={doc.status} />
          <button
            onClick={() => onDelete(doc.doc_id)}
            className="p-1 text-gray-400 hover:text-red-500 transition-colors rounded"
            title="Delete document"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </li>
      ))}
    </ul>
  );
}
