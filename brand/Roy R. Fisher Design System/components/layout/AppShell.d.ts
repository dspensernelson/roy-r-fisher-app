import type { Crumb } from "./CrumbBar";
export interface AppShellProps {
  trail?: Crumb[];
  crumbRight?: React.ReactNode;
  markSrc?: string;
  children?: React.ReactNode;
}
export declare function AppShell(props: AppShellProps): JSX.Element;
