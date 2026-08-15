export interface ChipProps {
  /** live = outlined blue (pressable); default/quiet = grey; done/needs = state tints. */
  tone?: "default" | "live" | "quiet" | "done" | "needs";
  children?: React.ReactNode;
}
export declare function Chip(props: ChipProps): JSX.Element;
