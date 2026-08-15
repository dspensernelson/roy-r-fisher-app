export interface BrandMarkProps {
  /** Path to the raster mark. Never substitute a redrawn SVG. */
  src?: string;
  /** Rendered height in px. Default 40. */
  height?: number;
  alt?: string;
  className?: string;
}
export declare function BrandMark(props: BrandMarkProps): JSX.Element;
