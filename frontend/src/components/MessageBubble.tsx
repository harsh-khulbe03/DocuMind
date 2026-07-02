import { AlertCircle } from "lucide-react";
import type { Message } from "../hooks/useChat";
import { SourceCitation } from "./SourceCitation";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-1">
        <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-gray-800 shadow-sm">
          {message.insufficient && (
            <div className="flex items-center gap-1.5 text-amber-600 text-xs mb-2 font-medium">
              <AlertCircle className="w-3.5 h-3.5" />
              Insufficient document coverage
            </div>
          )}
          {message.text || (
            <span className="inline-flex gap-1">
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
            </span>
          )}
          {message.streaming && message.text && (
            <span className="inline-block w-0.5 h-4 bg-gray-400 ml-0.5 animate-pulse align-middle" />
          )}
        </div>
        {!message.streaming && <SourceCitation sources={message.sources} />}
      </div>
    </div>
  );
}
