export interface RoadCardProps {
  title: string;
  body: React.ReactNode;
  /** Adds the "Not built yet" tag. */
  soon?: boolean;
  onClick?: () => void;
}
export declare function RoadCard(props: RoadCardProps): JSX.Element;
