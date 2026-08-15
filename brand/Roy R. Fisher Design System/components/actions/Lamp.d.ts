export interface LampProps {
  state?: "on" | "off" | "busy";
  labels?: { on?: string; off?: string; busy?: string };
}
export declare function Lamp(props: LampProps): JSX.Element;
