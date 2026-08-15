export interface LinkButtonProps {
  onClick?: () => void;
  disabled?: boolean;
  /** fine = 12px (in an action row); body = 14px (standalone). */
  size?: "fine" | "body";
  children?: React.ReactNode;
}
export declare function LinkButton(props: LinkButtonProps): JSX.Element;
