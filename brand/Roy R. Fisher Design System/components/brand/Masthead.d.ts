export interface MastheadProps {
  /** Passed through to BrandMark when the page is not at the DS root. */
  markSrc?: string;
  /** Set to "" to suppress the tagline. */
  tagline?: string;
  /** Optional right-aligned slot. */
  right?: React.ReactNode;
}
export declare function Masthead(props: MastheadProps): JSX.Element;
