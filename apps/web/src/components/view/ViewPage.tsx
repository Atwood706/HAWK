import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getRunDetail, getWorkflow, listRuns, listWorkflows } from "../../lib/api";
import type {
  WorkflowGraph,
  WorkflowRunDetail,
  WorkflowRunRecord,
  WorkflowSummary,
} from "../../types";
import { RunDetail } from "./RunDetail";
import { WorkflowRuns } from "./WorkflowRuns";

function toErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function isTerminalRunStatus(status: string | null | undefined): boolean {
  return status !== "queued" && status !== "running";
}

export function ViewPage() {
  const workflowsRequestIdRef = useRef(0);
  const workflowDetailRequestIdRef = useRef(0);
  const runListRequestIdRef = useRef(0);
  const runDetailRequestIdRef = useRef(0);
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowGraph | null>(null);
  const [runs, setRuns] = useState<WorkflowRunRecord[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedRun, setSelectedRun] = useState<WorkflowRunDetail | null>(null);
  const [loadingWorkflows, setLoadingWorkflows] = useState(true);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [loadingRunDetail, setLoadingRunDetail] = useState(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [runListError, setRunListError] = useState<string | null>(null);
  const [runDetailError, setRunDetailError] = useState<string | null>(null);

  const loadWorkflows = useCallback(async () => {
    const requestId = ++workflowsRequestIdRef.current;
    setLoadingWorkflows(true);
    setWorkflowError(null);

    try {
      const response = await listWorkflows();
      if (requestId !== workflowsRequestIdRef.current) {
        return;
      }

      setWorkflows(response);

      setSelectedWorkflowId((current) => {
        if (current && response.some((workflow) => workflow.id === current)) {
          return current;
        }

        return response[0]?.id ?? null;
      });
    } catch (error) {
      if (requestId !== workflowsRequestIdRef.current) {
        return;
      }

      setWorkflowError(toErrorMessage(error, "Failed to load workflows."));
      setWorkflows([]);
      setSelectedWorkflowId(null);
    } finally {
      if (requestId === workflowsRequestIdRef.current) {
        setLoadingWorkflows(false);
      }
    }
  }, []);

  const loadWorkflow = useCallback(async (workflowId: string) => {
    const requestId = ++workflowDetailRequestIdRef.current;
    try {
      const response = await getWorkflow(workflowId);
      if (requestId !== workflowDetailRequestIdRef.current || selectedWorkflowId !== workflowId) {
        return;
      }

      setSelectedWorkflow(response);
    } catch (error) {
      if (requestId !== workflowDetailRequestIdRef.current || selectedWorkflowId !== workflowId) {
        return;
      }

      setWorkflowError(toErrorMessage(error, "Failed to load workflow details."));
      setSelectedWorkflow(null);
    }
  }, [selectedWorkflowId]);

  const loadRuns = useCallback(async (workflowId: string) => {
    const requestId = ++runListRequestIdRef.current;
    setLoadingRuns(true);
    setRunListError(null);

    try {
      const response = await listRuns(workflowId);
      if (requestId !== runListRequestIdRef.current || selectedWorkflowId !== workflowId) {
        return;
      }

      setRuns(response);
      setSelectedRunId((current) => {
        if (current && response.some((run) => run.run_id === current)) {
          return current;
        }

        return response[0]?.run_id ?? null;
      });
    } catch (error) {
      if (requestId !== runListRequestIdRef.current || selectedWorkflowId !== workflowId) {
        return;
      }

      setRunListError(toErrorMessage(error, "Failed to load workflow runs."));
      setRuns([]);
      setSelectedRunId(null);
    } finally {
      if (requestId === runListRequestIdRef.current && selectedWorkflowId === workflowId) {
        setLoadingRuns(false);
      }
    }
  }, [selectedWorkflowId]);

  const loadRunDetail = useCallback(async (workflowId: string, runId: string) => {
    const requestId = ++runDetailRequestIdRef.current;
    setLoadingRunDetail(true);
    setRunDetailError(null);

    try {
      const response = await getRunDetail(workflowId, runId);
      if (
        requestId !== runDetailRequestIdRef.current ||
        selectedWorkflowId !== workflowId ||
        selectedRunId !== runId
      ) {
        return;
      }

      if (!response) {
        setSelectedRun(null);
        setRunDetailError("Selected run is no longer available in the current run list.");
        return;
      }

      setSelectedRun(response);
      setRuns((current) => current.map((run) => (run.run_id === response.run_id ? response : run)));
    } catch (error) {
      if (
        requestId !== runDetailRequestIdRef.current ||
        selectedWorkflowId !== workflowId ||
        selectedRunId !== runId
      ) {
        return;
      }

      setRunDetailError(toErrorMessage(error, "Failed to refresh run detail."));
      setSelectedRun(null);
    } finally {
      if (
        requestId === runDetailRequestIdRef.current &&
        selectedWorkflowId === workflowId &&
        selectedRunId === runId
      ) {
        setLoadingRunDetail(false);
      }
    }
  }, [selectedRunId, selectedWorkflowId]);

  useEffect(() => {
    void loadWorkflows();
  }, [loadWorkflows]);

  useEffect(() => {
    if (!selectedWorkflowId) {
      setSelectedWorkflow(null);
      setRuns([]);
      setSelectedRunId(null);
      setSelectedRun(null);
      setRunListError(null);
      setRunDetailError(null);
      return;
    }

    setSelectedWorkflow(null);
    setRuns([]);
    setSelectedRunId(null);
    setSelectedRun(null);
    setRunListError(null);
    setRunDetailError(null);

    void loadWorkflow(selectedWorkflowId);
    void loadRuns(selectedWorkflowId);
  }, [loadRuns, loadWorkflow, selectedWorkflowId]);

  useEffect(() => {
    if (!selectedWorkflowId || !selectedRunId) {
      setSelectedRun(null);
      return;
    }

    void loadRunDetail(selectedWorkflowId, selectedRunId);
  }, [loadRunDetail, selectedRunId, selectedWorkflowId]);

  useEffect(() => {
    if (!selectedWorkflowId || !selectedRunId || !selectedRun || isTerminalRunStatus(selectedRun.status)) {
      return;
    }

    const timer = window.setInterval(() => {
      void loadRunDetail(selectedWorkflowId, selectedRunId);
    }, 2000);

    return () => window.clearInterval(timer);
  }, [loadRunDetail, selectedRun, selectedRunId, selectedWorkflowId]);

  const handleRefresh = useCallback(() => {
    void loadWorkflows();

    if (selectedWorkflowId) {
      void loadWorkflow(selectedWorkflowId);
      void loadRuns(selectedWorkflowId);
    }

    if (selectedWorkflowId && selectedRunId) {
      void loadRunDetail(selectedWorkflowId, selectedRunId);
    }
  }, [loadRunDetail, loadRuns, loadWorkflow, loadWorkflows, selectedRunId, selectedWorkflowId]);

  const selectedWorkflowSummary = useMemo(
    () => workflows.find((workflow) => workflow.id === selectedWorkflowId) ?? null,
    [selectedWorkflowId, workflows],
  );

  return (
    <section className="view-layout">
      <WorkflowRuns
        workflows={workflows}
        selectedWorkflowId={selectedWorkflowId}
        selectedRunId={selectedRunId}
        runs={runs}
        loadingWorkflows={loadingWorkflows}
        loadingRuns={loadingRuns}
        workflowError={workflowError}
        runListError={runListError}
        onSelectWorkflow={setSelectedWorkflowId}
        onSelectRun={setSelectedRunId}
        onReload={handleRefresh}
      />
      <RunDetail
        workflow={selectedWorkflow ?? selectedWorkflowSummary}
        run={selectedRun}
        isLoading={loadingRunDetail}
        error={runDetailError}
      />
    </section>
  );
}
