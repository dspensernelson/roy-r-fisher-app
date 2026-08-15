export interface SectionRowProps {
  /** Print-order number, 1-based. */
  num: number;
  name: string;
  /** Sub-line, e.g. "waiting on the assessor PRC" or "18 photos in the folder". */
  state?: React.ReactNode;
  /** needs = amber + alert glyph; has = green + check glyph. */
  stateTone?: "needs" | "has";
  /** Path to the icon sprite, when the page is not at the design system root. */
  sprite?: string;
  /** Buildable today. */
  live?: boolean;
  chip?: string;
  onClick?: () => void;
}
export declare function SectionRow(props: SectionRowProps): JSX.Element;
