export interface ScreenHeadProps {
  title: string;
  sub?: React.ReactNode;
  /** Buttons and links, laid out in one wrapping row. */
  actions?: React.ReactNode;
  /** Second line under the actions — in the app this is <Working />. */
  below?: React.ReactNode;
  /** Left-align the action column (form screens). */
  stack?: boolean;
}
export declare function ScreenHead(props: ScreenHeadProps): JSX.Element;
