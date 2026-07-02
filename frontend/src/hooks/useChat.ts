import { useCallback, useState } from "react";
import { queryStream, type SourceChunk } from "../api/client";

export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  sources: SourceChunk[];
  insufficient: boolean;
  streaming: boolean;
}

export function useChat(scopedDocIds: string[] | null = null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(
    async (question: string) => {
      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        text: question,
        sources: [],
        insufficient: false,
        streaming: false,
      };

      const assistantId = crypto.randomUUID();
      const assistantMsg: Message = {
        id: assistantId,
        role: "assistant",
        text: "",
        sources: [],
        insufficient: false,
        streaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setLoading(true);
      setError(null);

      try {
        for await (const event of queryStream(question, scopedDocIds)) {
          if (event.type === "source") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, sources: [...m.sources, event as SourceChunk] }
                  : m,
              ),
            );
          } else if (event.type === "token") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, text: m.text + event.text } : m,
              ),
            );
          } else if (event.type === "done") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, streaming: false, insufficient: event.insufficient_coverage }
                  : m,
              ),
            );
          }
        }
      } catch (e) {
        const errMsg = e instanceof Error ? e.message : "Query failed";
        setError(errMsg);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, text: `Error: ${errMsg}`, streaming: false }
              : m,
          ),
        );
      } finally {
        setLoading(false);
      }
    },
    [scopedDocIds],
  );

  const clear = useCallback(() => setMessages([]), []);

  return { messages, loading, error, send, clear };
}
