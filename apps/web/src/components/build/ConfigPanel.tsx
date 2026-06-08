import type { BuiltinTool, WorkflowNode, WorkflowNodeData } from "../../types";

interface ConfigPanelProps {
  node: WorkflowNode | null;
  profiles?: string[];
  tools?: BuiltinTool[];
  onUpdateNode?: (nodeId: string, data: WorkflowNodeData) => void;
  onDeleteNode?: () => void;
}

function formatEntries(entries: Record<string, string>): string {
  const items = Object.entries(entries);
  if (items.length === 0) {
    return "None configured";
  }

  return items.map(([key, value]) => `${key}: ${value}`).join("\n");
}

function EditableMap({
  entries,
  onChange,
  disabled,
}: {
  entries: Record<string, string>;
  onChange: (entries: Record<string, string>) => void;
  disabled?: boolean;
}) {
  const items = Object.entries(entries);

  const update = (index: number, key: string, value: string) => {
    const next: Record<string, string> = {};
    items.forEach(([k, v], i) => {
      if (i === index) {
        if (key) next[key] = value;
      } else {
        next[k] = v;
      }
    });
    onChange(next);
  };

  const remove = (index: number) => {
    const next: Record<string, string> = {};
    items.forEach(([k, v], i) => {
      if (i !== index) next[k] = v;
    });
    onChange(next);
  };

  const add = () => {
    onChange({ ...entries, "": "" });
  };

  return (
    <div style={{ display: "grid", gap: 6 }}>
      {items.map(([k, v], i) => (
        <div key={i} style={{ display: "flex", gap: 6, alignItems: "center", minWidth: 0 }}>
          <input
            value={k}
            onChange={(e) => update(i, e.target.value, v)}
            placeholder="key"
            disabled={disabled}
            style={{ flex: 1, minWidth: 0 }}
          />
          <input
            value={v}
            onChange={(e) => update(i, k, e.target.value)}
            placeholder="value"
            disabled={disabled}
            style={{ flex: 1, minWidth: 0 }}
          />
          <button
            type="button"
            className="ghost-button"
            onClick={() => remove(i)}
            disabled={disabled}
            style={{ padding: "4px 8px" }}
          >
            ×
          </button>
        </div>
      ))}
      <button
        type="button"
        className="action-button"
        onClick={add}
        disabled={disabled}
        style={{ padding: "6px 10px", fontSize: 12 }}
      >
        + Add entry
      </button>
    </div>
  );
}

export function ConfigPanel({
  node,
  profiles = [],
  tools = [],
  onUpdateNode,
  onDeleteNode,
}: ConfigPanelProps) {
  const canEdit = Boolean(node && onUpdateNode);
  const currentProfile = node?.data.profile ?? "";
  const currentToolName = node?.data.tool_name ?? "";

  const handleProfileChange = (value: string) => {
    if (!node || !onUpdateNode) return;
    onUpdateNode(node.id, { ...node.data, profile: value });
  };

  const handleToolNameChange = (value: string) => {
    if (!node || !onUpdateNode) return;
    onUpdateNode(node.id, { ...node.data, tool_name: value });
  };

  const updateNodeData = (patch: Partial<WorkflowNodeData>) => {
    if (!node || !onUpdateNode) return;
    onUpdateNode(node.id, { ...node.data, ...patch });
  };

  const removeMedicalSkill = () => {
    if (!node || !onUpdateNode) return;
    const { medical_skill: _medicalSkill, ...dataWithoutSkill } = node.data;
    onUpdateNode(node.id, dataWithoutSkill);
  };

  return (
    <aside className="build-panel build-panel--config">
      <div className="build-panel__header build-panel__header--inline">
        <div>
          <p className="eyebrow">Config</p>
        </div>
        {node && onDeleteNode && (
          <button
            type="button"
            className="ghost-button"
            onClick={onDeleteNode}
            title="Delete selected node"
          >
            Delete
          </button>
        )}
      </div>
      <p className="build-panel__copy">
        Inspector and editor for the currently selected workflow block.
      </p>

      <div className="config-stack">
        <div className="config-card">
          <span className="config-label">Type</span>
          <strong>{node?.type ?? "No node selected"}</strong>
        </div>
        <div className="config-card">
          <span className="config-label">Label</span>
          {canEdit ? (
            <div className="config-field" style={{ marginTop: 8 }}>
              <input
                type="text"
                value={node?.data.label ?? ""}
                onChange={(e) => updateNodeData({ label: e.target.value })}
                placeholder="Node label"
              />
            </div>
          ) : (
            <strong>{node?.data.label ?? "—"}</strong>
          )}
        </div>
        {node?.type === "agent" && (
          <div className="config-card">
            <span className="config-label">Profile</span>
            {canEdit ? (
              <div className="config-field" style={{ marginTop: 8 }}>
                <select
                  value={currentProfile}
                  onChange={(e) => handleProfileChange(e.target.value)}
                >
                  {profiles.length === 0 && (
                    <option value="">Loading profiles…</option>
                  )}
                  {profiles.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <strong>{node?.data.profile ?? "—"}</strong>
            )}
          </div>
        )}
        {node?.type === "agent" && (
          <div className="config-card">
            <div className="config-card__inline-header">
              <span className="config-label">Medical Skill</span>
              {node.data.medical_skill && canEdit ? (
                <button
                  type="button"
                  className="ghost-button ghost-button--compact"
                  onClick={removeMedicalSkill}
                >
                  Remove
                </button>
              ) : null}
            </div>
            <strong>{node.data.medical_skill?.name ?? "None"}</strong>
            {node.data.medical_skill ? (
              <pre>
                {[
                  `category: ${node.data.medical_skill.category}`,
                  `description: ${node.data.medical_skill.description}`,
                ].join("\n")}
              </pre>
            ) : null}
          </div>
        )}
        {node?.type === "tool" && (
          <div className="config-card">
            <span className="config-label">Tool</span>
            {canEdit ? (
              <div className="config-field" style={{ marginTop: 8 }}>
                <select
                  value={currentToolName}
                  onChange={(e) => handleToolNameChange(e.target.value)}
                >
                  {tools.length === 0 && (
                    <option value="">Loading tools…</option>
                  )}
                  {tools.map((t) => (
                    <option key={t.name} value={t.name}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <strong>{node?.data.tool_name ?? "—"}</strong>
            )}
          </div>
        )}
        <div className="config-card">
          <span className="config-label">Inputs</span>
          {canEdit ? (
            <div style={{ marginTop: 8 }}>
              <EditableMap
                entries={node?.data.inputs ?? {}}
                onChange={(entries) => updateNodeData({ inputs: entries })}
                disabled={!canEdit}
              />
            </div>
          ) : (
            <pre>{node ? formatEntries(node.data.inputs) : "Pick a node to inspect"}</pre>
          )}
        </div>
        <div className="config-card">
          <span className="config-label">Outputs</span>
          {canEdit ? (
            <div style={{ marginTop: 8 }}>
              <EditableMap
                entries={node?.data.outputs ?? {}}
                onChange={(entries) => updateNodeData({ outputs: entries })}
                disabled={!canEdit}
              />
            </div>
          ) : (
            <pre>{node ? formatEntries(node.data.outputs) : "Pick a node to inspect"}</pre>
          )}
        </div>
      </div>
    </aside>
  );
}
