export interface InertTextProps {
  readonly value: string;
}

export function InertText({ value }: InertTextProps) {
  return <span className="inert-text">{value}</span>;
}
