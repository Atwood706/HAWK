export type ShellTab = "build" | "view" | "config";

type SidebarTab = {
  id: ShellTab;
  label: string;
  description: string;
};

type SidebarProps = {
  tabs: SidebarTab[];
  activeTab: ShellTab;
  routes: Record<ShellTab, string>;
  onNavigate: (tab: ShellTab) => void;
};

export function Sidebar({ tabs, activeTab, routes, onNavigate }: SidebarProps) {
  return (
    <aside className="shell-sidebar">
      <div className="shell-sidebar__brand">
        <span>MENU</span>
        <strong>HAWK</strong>
        <span>LOCAL WORKBENCH</span>
      </div>

      <nav className="shell-sidebar__nav" aria-label="Primary">
        {tabs.map((tab) => (
          <a
            key={tab.id}
            className="shell-sidebar__item"
            href={routes[tab.id]}
            aria-current={activeTab === tab.id ? "page" : undefined}
            onClick={() => onNavigate(tab.id)}
          >
            <span className="shell-sidebar__item-label">{tab.label}</span>
            <span className="shell-sidebar__item-copy">{tab.description}</span>
          </a>
        ))}
      </nav>
    </aside>
  );
}
