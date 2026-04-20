import { useEffect, useState } from "react";

interface RunPanelProps {
  status: string;
  statusTone: "neutral" | "success" | "error";
  exportPreview: string;
  isBusy: boolean;
  onSave: () => void;
  onValidate: () => void;
  onExport: () => void;
  onRun: () => void;
  runInput: Record<string, unknown>;
  onRunInputChange: (input: Record<string, unknown>) => void;
}

export function RunPanel({
  status,
  statusTone,
  exportPreview,
  isBusy,
  onSave,
  onValidate,
  onExport,
  onRun,
  runInput,
  onRunInputChange,
}: RunPanelProps) {
  const [jsonText, setJsonText] = useState(JSON.stringify(runInput, null, 2));
  const [jsonError, setJsonError] = useState<string | null>(null);

  useEffect(() => {
    setJsonText(JSON.stringify(runInput, null, 2));
    setJsonError(null);
  }, [runInput]);

  const handleBlur = () => {
    try {
      const parsed = JSON.parse(jsonText);
      if (parsed !== null && typeof parsed === "object" && !Array.isArray(parsed)) {
        onRunInputChange(parsed as Record<string, unknown>);
        setJsonError(null);
      } else {
        setJsonError("Input must be a JSON object.");
      }
    } catch {
      setJsonError("Invalid JSON.");
    }
  };

  return (
    <aside className="build-panel build-panel--run">
      <div className="build-panel__header">
        <p className="eyebrow">Actions</p>
      </div>
      <p className="build-panel__copy">
        Save the current graph, export AWDL, or run the workflow against the
        local API.
      </p>

      <div className="run-actions">
        <button
          type="button"
          className="action-button"
          onClick={onSave}
          disabled={isBusy}
        >
          Save
        </button>
        <button
          type="button"
          className="action-button"
          onClick={onValidate}
          disabled={isBusy}
        >
          Validate
        </button>
        <button
          type="button"
          className="action-button"
          onClick={onExport}
          disabled={isBusy}
        >
          Export
        </button>
        <button
          type="button"
          className="action-button action-button--primary"
          onClick={onRun}
          disabled={isBusy}
        >
          Run
        </button>
      </div>

      <div className="run-output">
        <span className="config-label">Run input (JSON)</span>
        <textarea
          className="run-input-json"
          rows={5}
          value={jsonText}
          onChange={(e) => setJsonText(e.target.value)}
          onBlur={handleBlur}
          disabled={isBusy}
          style={{
            width: "100%",
            fontFamily: "monospace",
            fontSize: 12,
            marginTop: 6,
          }}
        />
        {jsonError && (
          <p style={{ color: "crimson", fontSize: 12, marginTop: 4 }}>
            {jsonError}
          </p>
        )}
      </div>
      <div className="run-output">
        <span className="config-label">Status</span>
        <p className={`run-status run-status--${statusTone}`}>{status}</p>
      </div>
      <div className="run-output">
        <span className="config-label">AWDL preview</span>
        <pre>{exportPreview}</pre>
      </div>
    </aside>
  );
}
