import type { ReactNode } from "react";

export function PanelHeader({
  icon,
  kicker,
  title,
}: {
  icon: ReactNode;
  kicker: string;
  title: string;
}) {
  return (
    <header className="panel-header">
      <div className="panel-icon" aria-hidden="true">
        {icon}
      </div>
      <div>
        <span>{kicker}</span>
        <h2>{title}</h2>
      </div>
    </header>
  );
}
