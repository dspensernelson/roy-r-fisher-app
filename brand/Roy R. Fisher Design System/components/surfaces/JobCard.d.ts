export interface JobCardNext {
  /** The one thing to do next, as a sentence: "Caption 18 photos and build the photo pages". */
  label: string;
  /** do = he can act now; waiting = something missing he cannot produce; done = nothing pending. */
  tone?: "do" | "waiting" | "done";
  /** Path to the icon sprite, when the page is not at the design system root. */
  sprite?: string;
}
export interface JobCardProps {
  /** Folder-name prefix, e.g. "MASON CITY". Uppercased by the style. */
  city?: string;
  address: string;
  /** Counts and kind; tabular figures. */
  meta?: React.ReactNode;
  /** Omit only when the folder has not been scanned yet. */
  next?: JobCardNext;
  /** Sections that have everything they need. */
  ready?: number;
  /** Sections in the report. Omit both to hide the progress bar. */
  total?: number;
  onClick?: () => void;
}
export declare function JobCard(props: JobCardProps): JSX.Element;
