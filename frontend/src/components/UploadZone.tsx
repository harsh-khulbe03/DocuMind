import { useCallback, useRef, useState } from "react";
import { Upload, FileText } from "lucide-react";

interface Props {
  onUpload: (file: File) => void;
  uploading: boolean;
}

export function UploadZone({ onUpload, uploading }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Only PDF files are supported.");
        return;
      }
      onUpload(file);
    },
    [onUpload],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      className={`
        border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
        transition-colors select-none
        ${dragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"}
        ${uploading ? "opacity-60 cursor-not-allowed" : ""}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
      />
      <div className="flex flex-col items-center gap-2 text-gray-500">
        {uploading ? (
          <>
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm font-medium text-blue-600">Uploading and processing…</p>
          </>
        ) : (
          <>
            <Upload className="w-8 h-8" />
            <p className="text-sm font-medium">Drop a PDF here or click to browse</p>
            <p className="text-xs text-gray-400">Only PDF files are supported</p>
          </>
        )}
      </div>
    </div>
  );
}
