export interface BandHeadProps {
  title: string;
  note?: React.ReactNode;
  /** Usually a <LinkButton />; it right-aligns automatically. */
  action?: React.ReactNode;
}
export declare function BandHead(props: BandHeadProps): JSX.Element;
