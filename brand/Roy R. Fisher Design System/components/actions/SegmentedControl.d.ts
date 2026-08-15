export interface SegmentedOption {
  key: string;
  label: string;
  /** Small green uppercase note under/beside the label, e.g. "suggested". */
  flag?: string;
}
export interface SegmentedControlProps {
  options?: SegmentedOption[];
  value?: string;
  onChange?: (key: string) => void;
}
export declare function SegmentedControl(props: SegmentedControlProps): JSX.Element;
