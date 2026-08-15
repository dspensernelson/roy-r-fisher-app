export interface SheetProps {
  /** A question, in plain words: "How should the captions read?" */
  title?: string;
  sub?: React.ReactNode;
  children?: React.ReactNode;
  /** Sticky footer row — keep note, primary Button, Cancel LinkButton. */
  foot?: React.ReactNode;
  onClose?: () => void;
  label?: string;
}
export declare function Sheet(props: SheetProps): JSX.Element;
