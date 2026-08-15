export interface ButtonProps {
  /** primary = brand red; secondary = link blue; quiet = white outlined. */
  variant?: "primary" | "secondary" | "quiet";
  /** md is the screen's primary action; sm is for action rows. */
  size?: "md" | "sm";
  disabled?: boolean;
  onClick?: () => void;
  type?: "button" | "submit";
  children?: React.ReactNode;
}
export declare function Button(props: ButtonProps): JSX.Element;
