import type { WorkflowGraph, WorkflowRunDetail } from "../../types";

interface RunDetailProps {
  workflow: WorkflowGraph | null;
  run: WorkflowRunDetail | null;
  isLoading: boolean;
  error: string | null;
}

function formatTimestamp(value: string | null): string {
  if (!value) {
    return "Still running or not yet finalized";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export function RunDetail({ workflow, run, isLoading, error }: RunDetailProps) {
  const trace = run?.trace ?? [];
  const result = run?.result ?? null;

  return (
    <section className="panel view-panel">
      <div className="view-panel__header">
        <div>
          <p className="eyebrow">Selected Run</p>
          <h2 className="page-title">Run detail</h2>
        </div>
        {run ? <span className="pill">{run.status}</span> : null}
      </div>
      <p className="page-copy">
        Inspect the stored metadata and any artifacts persisted for the selected run.
      </p>

      {error ? <p className="view-feedback view-feedback--error">{error}</p> : null}
      {isLoading ? <p className="view-feedback">Refreshing run detail…</p> : null}

      {!workflow ? (
        <p className="view-feedback">Select a workflow to load its summary and runs.</p>
      ) : null}

      {workflow ? (
        <div className="detail-stack">
          <article className="detail-card">
            <h3>Workflow</h3>
            <dl className="detail-grid">
              <div>
                <dt>Name</dt>
                <dd>{workflow.name}</dd>
              </div>
              <div>
                <dt>Workflow ID</dt>
                <dd>{workflow.id}</dd>
              </div>
              <div>
                <dt>Nodes</dt>
                <dd>{workflow.nodes.length}</dd>
              </div>
              <div>
                <dt>Edges</dt>
                <dd>{workflow.edges.length}</dd>
              </div>
            </dl>
            <p className="detail-description">
              {workflow.description || "No workflow description is stored for this graph."}
            </p>
          </article>

          {!run ? (
            <article className="detail-card detail-card--empty">
              <h3>No run selected</h3>
              <p>Choose a run from the left column to inspect its latest stored metadata.</p>
            </article>
          ) : (
            <>
              <article className="detail-card">
                <h3>Execution</h3>
                <dl className="detail-grid">
                  <div>
                    <dt>Run ID</dt>
                    <dd>{run.run_id}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{run.status}</dd>
                  </div>
                  <div>
                    <dt>Started</dt>
                    <dd>{formatTimestamp(run.started_at)}</dd>
                  </div>
                  <div>
                    <dt>Finished</dt>
                    <dd>{formatTimestamp(run.finished_at)}</dd>
                  </div>
                </dl>
              </article>

              <article className="detail-card">
                <h3>Input payload</h3>
                <pre className="detail-pre">{formatJson(run.input)}</pre>
              </article>

              <article className="detail-card">
                <h3>Generated AWDL</h3>
                {run.awdl ? (
                  <pre className="detail-pre">{run.awdl}</pre>
                ) : (
                  <p className="detail-empty">AWDL output is not available yet.</p>
                )}
              </article>

              <article className="detail-card">
                <h3>Result payload</h3>
                {result !== null ? (
                  <pre className="detail-pre">{formatJson(result)}</pre>
                ) : (
                  <p className="detail-empty">Result payload has not been stored yet.</p>
                )}
              </article>

              <article className="detail-card">
                <h3>Trace</h3>
                {trace.length > 0 ? (
                  <pre className="detail-pre">{formatJson(trace)}</pre>
                ) : (
                  <p className="detail-empty">Trace events have not been stored yet.</p>
                )}
              </article>
            </>
          )}
        </div>
      ) : null}
    </section>
  );
}
