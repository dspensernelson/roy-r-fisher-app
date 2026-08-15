import React from "react";

/* Drop target and empty state in one. Says where files go and that the
   originals are untouched — the sentence matters more than the border. */
export function DropZone({ over = false, children, onFiles, onClick }) {
  return (
    <div className={`rrf-dropzone${over ? " is-over" : ""}`} onClick={onClick}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => { e.preventDefault(); onFiles && onFiles(e.dataTransfer.files); }}>
      {children}
    </div>
  );
}
