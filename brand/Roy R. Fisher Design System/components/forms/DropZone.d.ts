export interface DropZoneProps {
  /** True while a drag is over it. */
  over?: boolean;
  children?: React.ReactNode;
  onFiles?: (files: FileList) => void;
  onClick?: () => void;
}
export declare function DropZone(props: DropZoneProps): JSX.Element;
