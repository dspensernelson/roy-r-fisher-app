export interface TaskRowProps {
  /** Sprite glyph id: folder, image, file-text, check, triangle-alert. */
  icon?: string;
  /** The task as an imperative sentence: "Add the assessor PRC". */
  name: string;
  /** Why it matters — which sections wait on it, and which folder it goes in. */
  why?: React.ReactNode;
  /** "Open", "Open folder". Omit on done rows. */
  chip?: string;
  /** do = a task; done = already in the folder. */
  tone?: "do" | "done";
  /** The single next task. Exactly one per screen. */
  next?: boolean;
  /** Path to the icon sprite, when the page is not at the design system root. */
  sprite?: string;
  onClick?: () => void;
}
export declare function TaskRow(props: TaskRowProps): JSX.Element;
