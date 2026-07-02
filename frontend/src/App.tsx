import { Brain } from "lucide-react";
import { ChatWindow } from "./components/ChatWindow";
import { DocumentList } from "./components/DocumentList";
import { UploadZone } from "./components/UploadZone";
import { useChat } from "./hooks/useChat";
import { useDocuments } from "./hooks/useDocuments";

export default function App() {
  const { documents, uploading, error: docError, upload, remove } = useDocuments();
  const readyDocs = documents.filter((d) => d.status === "ready");
  const hasReady = readyDocs.length > 0;

  const { messages, loading, error: chatError, send, clear } = useChat(null);

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="w-80 flex-shrink-0 flex flex-col bg-white border-r border-gray-200 shadow-sm">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-4 border-b border-gray-100">
          <div className="p-1.5 bg-blue-600 rounded-lg">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold text-gray-900">DocuMind</span>
        </div>

        {/* Upload */}
        <div className="p-4 border-b border-gray-100">
          <UploadZone onUpload={upload} uploading={uploading} />
          {docError && (
            <p className="mt-2 text-xs text-red-500">{docError}</p>
          )}
        </div>

        {/* Document list */}
        <div className="flex-1 overflow-y-auto p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Documents ({documents.length})
          </p>
          <DocumentList documents={documents} onDelete={remove} />
        </div>
      </aside>

      {/* ── Main chat area ────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-base font-semibold text-gray-900">Chat</h1>
            <p className="text-xs text-gray-400">
              {hasReady
                ? `${readyDocs.length} document${readyDocs.length > 1 ? "s" : ""} ready`
                : "No documents ready yet"}
            </p>
          </div>
          {chatError && (
            <p className="text-xs text-red-500">{chatError}</p>
          )}
        </header>

        {/* Chat */}
        <div className="flex-1 overflow-hidden">
          <ChatWindow
            messages={messages}
            loading={loading}
            onSend={send}
            onClear={clear}
            disabled={!hasReady}
          />
        </div>
      </main>
    </div>
  );
}
