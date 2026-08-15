export interface Crumb {
  label: string;
  /** Omit on the last crumb — it renders as plain text. */
  onClick?: () => void;
}
export interface CrumbBarProps {
  trail?: Crumb[];
  /** Right-aligned slot; in the app this is the Settings crumb. */
  right?: React.ReactNode;
}
export declare function CrumbBar(props: CrumbBarProps): JSX.Element;
