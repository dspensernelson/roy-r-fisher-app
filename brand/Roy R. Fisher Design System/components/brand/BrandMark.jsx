import React from "react";

/* Three columns with an angled cut on the taller centre one. Defaults to the
   traced vector (assets/logo/rrf-mark.svg, measured from the raster — geometry
   pending sign-off); pass the .png if you need the original raster, and pass
   `src` when the consuming page sits at a different depth than the design
   system root. */
export function BrandMark({ src = "assets/logo/rrf-mark.svg", height = 40, alt = "Roy R. Fisher", className = "" }) {
  return <img className={`rrf-masthead__mark ${className}`} src={src} alt={alt} style={{ height }} />;
}
