export interface FolderCardProps {
  /** Folder name as it is on disk, e.g. "Subject Information". */
  folder: string;
  count: number;
  /** Inputs present, joined into a sentence by the component. */
  has?: string[];
  /** Inputs the report still wants. */
  needs?: string[];
}
export declare function FolderCard(props: FolderCardProps): JSX.Element;
