export interface PanelProps {
  /** Uppercase ruled label, e.g. "Needed to start". */
  label?: string;
  /** Fine print under the fields. */
  note?: React.ReactNode;
  children?: React.ReactNode;
}
export declare function Panel(props: PanelProps): JSX.Element;
