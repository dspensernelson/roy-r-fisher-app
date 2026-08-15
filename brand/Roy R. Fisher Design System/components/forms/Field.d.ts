export interface FieldProps {
  label?: string;
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  type?: "text" | "password";
  /** Pass a list to render a select instead of an input. */
  options?: string[] | null;
  hint?: React.ReactNode;
  /** Replaces the hint and reddens the border. */
  error?: React.ReactNode;
  /** Monospace value — used for keys and file numbers. */
  mono?: boolean;
  /** Blue underline: the value fills itself in until the user edits it. */
  derived?: boolean;
  disabled?: boolean;
  autoFocus?: boolean;
  onKeyDown?: (e: React.KeyboardEvent) => void;
  name?: string;
}
export declare function Field(props: FieldProps): JSX.Element;
