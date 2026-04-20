import { useEffect, useMemo, useState } from "react";

import { Sidebar, type ShellTab } from "./components/layout/Sidebar";
import { BuildPage } from "./components/build/BuildPage";
import { ViewPage } from "./components/view/ViewPage";
import { ConfigPage } from "./components/config/ConfigPage";

const tabs: Array<{ id: ShellTab; label: string; description: string }> = [
  { id: "build", label: "Build", description: "Compose workflows" },
  { id: "view", label: "View", description: "Inspect runs" },
  { id: "config", label: "Config", description: "Manage settings" },
];

const routeByTab: Record<ShellTab, `#/${ShellTab}`> = {
  build: "#/build",
  view: "#/view",
  config: "#/config",
};

const pageByTab: Record<ShellTab, JSX.Element> = {
  build: <BuildPage />,
  view: <ViewPage />,
  config: <ConfigPage />,
};

function getTabFromHash(hash: string): ShellTab {
  const normalizedHash = hash.replace(/^#/, "");

  if (normalizedHash === "/view") {
    return "view";
  }

  if (normalizedHash === "/config") {
    return "config";
  }

  return "build";
}

export default function App() {
  const [activeTab, setActiveTab] = useState<ShellTab>(() =>
    getTabFromHash(window.location.hash),
  );

  useEffect(() => {
    if (!window.location.hash) {
      window.history.replaceState(null, "", routeByTab.build);
    }

    const syncTabWithLocation = () => {
      setActiveTab(getTabFromHash(window.location.hash));
    };

    syncTabWithLocation();
    window.addEventListener("hashchange", syncTabWithLocation);

    return () => {
      window.removeEventListener("hashchange", syncTabWithLocation);
    };
  }, []);

  const activePage = useMemo(() => pageByTab[activeTab], [activeTab]);

  const handleNavigate = (tab: ShellTab) => {
    const nextHash = routeByTab[tab];

    if (window.location.hash !== nextHash) {
      window.location.hash = nextHash;
      return;
    }

    setActiveTab(tab);
  };

  return (
    <div className="app-shell">
      <Sidebar
        tabs={tabs}
        activeTab={activeTab}
        routes={routeByTab}
        onNavigate={handleNavigate}
      />
      <main className="app-main">
        <section className="page-frame">{activePage}</section>
      </main>
    </div>
  );
}
