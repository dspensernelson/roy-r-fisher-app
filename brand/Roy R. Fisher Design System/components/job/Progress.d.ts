export interface ProgressProps {
  ready: number;
  total: number;
  noun?: string;
}
export declare function Progress(props: ProgressProps): JSX.Element;
