import { useState } from "react";
import { ChevronDown, ChevronUp, BookOpen } from "lucide-react";
import type { SourceChunk } from "../api/client";

interface Props {
  sources: SourceChunk[];
}

export function SourceCitation({ sources }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (sources.length === 0) return null;

  return (
    <div className="mt-3 space-y-1">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Sources</p>
      {sources.map((s, i) => {
        const key = `${s.doc_id}-${s.page}-${i}`;
        const isOpen = expanded === key;
        return (
          <div key={key} className="border border-gray-200 rounded-lg overflow-hidden text-xs">
            <button
              onClick={() => setExpanded(isOpen ? null : key)}
              className="w-full flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
            >
              <BookOpen className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
              <span className="flex-1 truncate font-medium text-gray-700">
                {s.filename}
              </span>
              <span className="text-gray-400 flex-shrink-0">p.{s.page}</span>
              <span className="text-gray-300 flex-shrink-0 text-[10px]">
                {(s.score * 100).toFixed(0)}%
              </span>
              {isOpen ? (
                <ChevronUp className="w-3.5 h-3.5 text-gray-400" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
              )}
            </button>
            {isOpen && (
              <div className="px-3 py-2 bg-white text-gray-600 leading-relaxed border-t border-gray-100">
                {s.text}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
