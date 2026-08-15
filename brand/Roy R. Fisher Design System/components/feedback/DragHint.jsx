import React from "react";

/* A pill at the bottom of the window, shown only while a file is being
   dragged in from outside the app. */
export function DragHint({ children }) {
  return <div className="rrf-draghint">{children}</div>;
}
