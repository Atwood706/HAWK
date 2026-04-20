import type { WorkflowNodeType } from "../../types";

interface NodePaletteProps {
  onAddNode: (type: WorkflowNodeType) => void;
}

const nodeOptions: Array<{
  type: WorkflowNodeType;
  title: string;
  copy: string;
}> = [
  {
    type: "agent",
    title: "Agent",
    copy: "Profile-driven step for prompts and model execution.",
  },
  {
    type: "tool",
    title: "Tool",
    copy: "Direct builtin tool execution without an LLM round-trip.",
  },
];

export function NodePalette({ onAddNode }: NodePaletteProps) {
  return (
    <aside className="build-panel build-panel--palette">
      <p className="eyebrow">Palette</p>
      <h2>Available Nodes</h2>
      <p className="build-panel__copy">
        Seed the canvas with supported nodes only. Dragging and richer templates
        can land in later tasks.
      </p>

      <div className="palette-list">
        {nodeOptions.map((option) => (
          <button
            key={option.type}
            type="button"
            className="palette-card"
            onClick={() => onAddNode(option.type)}
          >
            <strong>{option.title}</strong>
            <span>{option.copy}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}
