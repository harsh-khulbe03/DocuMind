import { useEffect, useRef, useState } from "react";
import { Send, Trash2 } from "lucide-react";
import type { Message } from "../hooks/useChat";
import { MessageBubble } from "./MessageBubble";

interface Props {
  messages: Message[];
  loading: boolean;
  onSend: (question: string) => void;
  onClear: () => void;
  disabled: boolean;
}

export function ChatWindow({ messages, loading, onSend, onClear, disabled }: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const submit = () => {
    const q = input.trim();
    if (!q || loading || disabled) return;
    setInput("");
    onSend(q);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-gray-400">
            {disabled
              ? "Upload and process a PDF to start asking questions."
              : "Ask a question about your documents."}
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-gray-200 p-3 bg-white">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={disabled ? "Upload a document first…" : "Ask a question… (Enter to send)"}
            disabled={disabled || loading}
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 px-3 py-2.5 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:bg-gray-50 disabled:text-gray-400
                       max-h-32 overflow-y-auto"
            style={{ lineHeight: "1.5" }}
          />
          {messages.length > 0 && (
            <button
              onClick={onClear}
              className="p-2.5 text-gray-400 hover:text-red-500 transition-colors rounded-lg"
              title="Clear conversation"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={submit}
            disabled={!input.trim() || loading || disabled}
            className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 
                       disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
