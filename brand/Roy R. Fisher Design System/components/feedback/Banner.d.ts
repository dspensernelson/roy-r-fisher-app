export interface BannerProps {
  tone?: "done" | "error" | "warn" | "note";
  children?: React.ReactNode;
  /** Path to the icon sprite, when the page is not at the design system root. */
  sprite?: string;
  style?: React.CSSProperties;
}
export declare function Banner(props: BannerProps): JSX.Element;
