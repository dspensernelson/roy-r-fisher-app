import React from "react";
import { BrandMark } from "./BrandMark.jsx";

/* Mark, wordmark, tagline. Sits above the crumb bar, never inside a card. */
export function Masthead({ markSrc, tagline = "\u201CThe Established Commercial Valuation Experts\u201D", right = null }) {
  return (
    <>
      <div className="rrf-topline" />
      <header className="rrf-masthead">
      <BrandMark src={markSrc} />
      <div>
        <div className="rrf-wordmark">ROY R. FISHER</div>
        {tagline ? <div className="rrf-tagline">{tagline}</div> : null}
      </div>
      {right ? <div style={{ marginLeft: "auto" }}>{right}</div> : null}
      </header>
    </>
  );
}
