export interface EmptyNoteProps {
  /** What is missing, as a statement: "No sections chosen yet". */
  name: string;
  /** What happens next, in one sentence. */
  state?: React.ReactNode;
  action?: React.ReactNode;
}
export declare function EmptyNote(props: EmptyNoteProps): JSX.Element;
