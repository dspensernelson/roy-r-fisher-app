import React from "react";
import { Masthead } from "../brand/Masthead.jsx";
import { CrumbBar } from "./CrumbBar.jsx";

/* Masthead, crumb bar, then the 1200px frame. Content starts immediately:
   no hero, no preamble. */
export function AppShell({ trail = [], crumbRight = null, markSrc, children }) {
  return (
    <>
      <Masthead markSrc={markSrc} />
      <CrumbBar trail={trail} right={crumbRight} />
      <div className="rrf-frame">{children}</div>
    </>
  );
}
