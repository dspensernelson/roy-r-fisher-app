export interface ChecklistProps {
  /** Section names, in print order. */
  items?: string[];
  checked?: Record<string, boolean>;
  onToggle?: (name: string, next: boolean) => void;
}
export declare function Checklist(props: ChecklistProps): JSX.Element;
