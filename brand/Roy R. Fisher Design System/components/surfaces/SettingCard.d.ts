export interface SettingCardProps {
  title: string;
  /** A <Lamp />. */
  lamp?: React.ReactNode;
  children?: React.ReactNode;
  /** Reassurance line at the bottom, in fine print. */
  fine?: React.ReactNode;
}
export declare function SettingCard(props: SettingCardProps): JSX.Element;
