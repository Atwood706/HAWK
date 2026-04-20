import type { WorkflowRunRecord, WorkflowSummary } from "../../types";

interface WorkflowRunsProps {
  workflows: WorkflowSummary[];
  selectedWorkflowId: string | null;
  selectedRunId: string | null;
  runs: WorkflowRunRecord[];
  loadingWorkflows: boolean;
  loadingRuns: boolean;
  workflowError: string | null;
  runListError: string | null;
  onSelectWorkflow: (workflowId: string) => void;
  onSelectRun: (runId: string) => void;
  onReload: () => void;
}

function formatTimestamp(value: string | null): string {
  if (!value) {
    return "In progress";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export function WorkflowRuns({
  workflows,
  selectedWorkflowId,
  selectedRunId,
  runs,
  loadingWorkflows,
  loadingRuns,
  workflowError,
  runListError,
  onSelectWorkflow,
  onSelectRun,
  onReload,
}: WorkflowRunsProps) {
  const selectedWorkflow =
    workflows.find((workflow) => workflow.id === selectedWorkflowId) ?? null;

  return (
    <section className="panel view-panel">
      <div className="view-panel__header">
        <div>
          <p className="eyebrow">Workflow History</p>
          <h2>Runs by workflow</h2>
        </div>
        <button className="ghost-button" type="button" onClick={onReload}>
          Refresh
        </button>
      </div>
      <p className="page-copy">
        Select a saved workflow first, then inspect its recorded run metadata
        from the current backend API.
      </p>

      {workflowError ? (
        <p className="view-feedback view-feedback--error">{workflowError}</p>
      ) : null}

      <div className="workflow-picker" role="list" aria-label="Saved workflows">
        {loadingWorkflows ? (
          <p className="view-feedback">Loading workflows…</p>
        ) : null}
        {!loadingWorkflows && workflows.length === 0 ? (
          <p className="view-feedback">
            No saved workflows yet. Save one from Build first.
          </p>
        ) : null}
        {workflows.map((workflow) => {
          const isActive = workflow.id === selectedWorkflowId;
          return (
            <button
              key={workflow.id}
              className="workflow-picker__item"
              data-active={isActive}
              type="button"
              onClick={() => onSelectWorkflow(workflow.id)}
            >
              <span className="workflow-picker__title">{workflow.name}</span>
              <span className="workflow-picker__meta">
                {workflow.nodes.length} nodes · {workflow.edges.length} edges
              </span>
            </button>
          );
        })}
      </div>

      <div className="run-list">
        <div className="run-list__header">
          <h3>{selectedWorkflow ? selectedWorkflow.name : "Runs"}</h3>
          {loadingRuns ? <span className="pill">Loading</span> : null}
        </div>

        {runListError ? (
          <p className="view-feedback view-feedback--error">{runListError}</p>
        ) : null}
        {!selectedWorkflow ? (
          <p className="view-feedback">
            Choose a workflow to load its run history.
          </p>
        ) : null}
        {selectedWorkflow && !loadingRuns && runs.length === 0 ? (
          <p className="view-feedback">
            No runs recorded for this workflow yet.
          </p>
        ) : null}

        {runs.map((run) => {
          const isActive = run.run_id === selectedRunId;
          return (
            <button
              key={run.run_id}
              className="run-list__item"
              data-active={isActive}
              type="button"
              onClick={() => onSelectRun(run.run_id)}
            >
              <span className="run-list__item-top">
                <strong>{run.run_id.slice(0, 8)}</strong>
                <span className="pill">{run.status}</span>
              </span>
              <span className="run-list__item-meta">
                Started {formatTimestamp(run.started_at)}
              </span>
              <span className="run-list__item-meta">
                Finished {formatTimestamp(run.finished_at)}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
