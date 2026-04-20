import { useEffect, useMemo, useState } from "react";

import { listTools } from "../../lib/api";
import type { BuiltinTool } from "../../types";

function formatDefault(value: unknown | null) {
  if (value === null || value === undefined) {
    return "None";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value);
}

export function ToolsPanel() {
  const [tools, setTools] = useState<BuiltinTool[]>([]);
  const [selectedToolName, setSelectedToolName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    void listTools()
      .then((items) => {
        if (!active) {
          return;
        }

        setTools(items);
        setSelectedToolName((current) => current ?? items[0]?.name ?? null);
      })
      .catch((caughtError: unknown) => {
        if (!active) {
          return;
        }

        setError(caughtError instanceof Error ? caughtError.message : "Failed to load tools.");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const selectedTool = useMemo(
    () => tools.find((tool) => tool.name === selectedToolName) ?? null,
    [selectedToolName, tools],
  );

  return (
    <section className="config-panel">
      <div className="config-panel__header">
        <div>
          <p className="eyebrow">Tools</p>
          <h3>Builtin registry</h3>
        </div>
        <span className="pill">{tools.length} tools</span>
      </div>
      <p className="page-copy">These tools come from `awdl/ir/builtins.py` and are read-only here.</p>

      {error ? <p className="view-feedback view-feedback--error">{error}</p> : null}

      <div className="config-dual-pane">
        <aside className="config-list" aria-label="Builtin tools">
          {loading ? <p className="view-feedback">Loading tools…</p> : null}
          {!loading && tools.length === 0 ? (
            <p className="view-feedback">No builtin tools were discovered.</p>
          ) : null}
          {tools.map((tool) => {
            const active = tool.name === selectedToolName;

            return (
              <button
                key={tool.name}
                className="config-list__item"
                data-active={active}
                type="button"
                onClick={() => setSelectedToolName(tool.name)}
              >
                <strong>{tool.name}</strong>
                <span>{tool.description}</span>
              </button>
            );
          })}
        </aside>

        <div className="config-detail">
          {selectedTool ? (
            <>
              <div className="config-detail__header">
                <div>
                  <span className="config-label">Category</span>
                  <strong>{selectedTool.category}</strong>
                </div>
                <div>
                  <span className="config-label">Name</span>
                  <strong>{selectedTool.name}</strong>
                </div>
              </div>
              <p className="config-detail__description">{selectedTool.description}</p>

              <div className="config-split-grid">
                <article className="config-mini-card">
                  <span className="config-label">Inputs</span>
                  {selectedTool.inputs.length === 0 ? (
                    <p className="config-mini-card__empty">No inputs.</p>
                  ) : (
                    <ul className="config-port-list">
                      {selectedTool.inputs.map((port) => (
                        <li key={port.name}>
                          <strong>{port.name}</strong>
                          <span>
                            {port.port_type}
                            {port.required ? "" : " optional"}
                            {port.default !== null ? ` · default ${formatDefault(port.default)}` : ""}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </article>

                <article className="config-mini-card">
                  <span className="config-label">Outputs</span>
                  {selectedTool.outputs.length === 0 ? (
                    <p className="config-mini-card__empty">No outputs.</p>
                  ) : (
                    <ul className="config-port-list">
                      {selectedTool.outputs.map((port) => (
                        <li key={port.name}>
                          <strong>{port.name}</strong>
                          <span>{port.port_type}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </article>
              </div>
            </>
          ) : (
            <p className="view-feedback">Select a tool to inspect its input and output ports.</p>
          )}
        </div>
      </div>
    </section>
  );
}
