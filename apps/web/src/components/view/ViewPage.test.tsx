import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ViewPage } from "./ViewPage";
import * as api from "../../lib/api";

vi.mock("../../lib/api", () => ({
  getRunDetail: vi.fn(),
  getWorkflow: vi.fn(),
  listRuns: vi.fn(),
  listWorkflows: vi.fn(),
}));

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
};

function createDeferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });

  return { promise, resolve };
}

const workflowA = {
  id: "workflow-a",
  name: "Workflow A",
  nodes: [],
  edges: [],
};

const workflowB = {
  id: "workflow-b",
  name: "Workflow B",
  nodes: [],
  edges: [],
};

const runA = {
  run_id: "run-a",
  workflow_id: "workflow-a",
  status: "running",
  input: {},
  started_at: "2025-01-01T00:00:00.000Z",
  finished_at: null,
};

const runB = {
  run_id: "run-b",
  workflow_id: "workflow-b",
  status: "queued",
  input: {},
  started_at: "2025-01-01T00:01:00.000Z",
  finished_at: null,
};

const runADetail = {
  ...runA,
  awdl: 'workflow workflow-a {\n  string greeting: "hello"\n}',
  result: { output: "hello" },
  trace: [{ event: "run.started" }, { event: "run.succeeded" }],
} as any;

const queuedRunDetail = {
  ...runB,
  awdl: null,
  result: null,
  trace: [],
} as any;

function mockApi() {
  return {
    getRunDetail: vi.mocked(api.getRunDetail),
    getWorkflow: vi.mocked(api.getWorkflow),
    listRuns: vi.mocked(api.listRuns),
    listWorkflows: vi.mocked(api.listWorkflows),
  };
}

beforeEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("ViewPage", () => {
  it("does not keep the stale run error after switching workflows", async () => {
    const { getRunDetail, getWorkflow, listRuns, listWorkflows } = mockApi();
    const workflowBRuns = createDeferred<typeof runB[]>();

    listWorkflows.mockResolvedValue([workflowA, workflowB]);
    getWorkflow.mockImplementation(async (workflowId) =>
      workflowId === workflowA.id ? workflowA : workflowB,
    );
    listRuns.mockImplementation(async (workflowId) => {
      if (workflowId === workflowA.id) {
        return [runA];
      }

      return workflowBRuns.promise;
    });
    getRunDetail.mockImplementation((async (workflowId: string, runId: string) => {
      if (workflowId === workflowA.id && runId === runA.run_id) {
        return runA;
      }

      if (workflowId === workflowB.id && runId === runA.run_id) {
        return null;
      }

      if (workflowId === workflowB.id && runId === runB.run_id) {
        return runB;
      }

      return null as any;
    }) as any);

    render(<ViewPage />);

    await screen.findByRole("button", { name: /workflow a/i });
    await screen.findByRole("button", { name: /run-a/i });

    fireEvent.click(screen.getByRole("button", { name: /workflow b/i }));

    await waitFor(() => {
      expect(screen.queryByText(/Selected run is no longer available/i)).not.toBeInTheDocument();
    });

    workflowBRuns.resolve([runB]);
    await screen.findByRole("button", { name: /run-b/i });
  });

  it("keeps the latest workflow detail when an earlier request resolves late", async () => {
    const { getRunDetail, getWorkflow, listRuns, listWorkflows } = mockApi();
    const workflowARuns = createDeferred<typeof runA[]>();
    const workflowBRuns = createDeferred<typeof runB[]>();
    const runADetail = createDeferred<typeof runA>();
    const runBDetail = createDeferred<typeof runB>();

    listWorkflows.mockResolvedValue([workflowA, workflowB]);
    getWorkflow.mockImplementation(async (workflowId) =>
      workflowId === workflowA.id ? workflowA : workflowB,
    );
    listRuns.mockImplementation(async (workflowId) => {
      if (workflowId === workflowA.id) {
        return workflowARuns.promise;
      }

      return workflowBRuns.promise;
    });
    getRunDetail.mockImplementation((async (workflowId: string, runId: string) => {
      if (workflowId === workflowA.id && runId === runA.run_id) {
        return runADetail.promise;
      }

      if (workflowId === workflowB.id && runId === runB.run_id) {
        return runBDetail.promise;
      }

      return null as any;
    }) as any);

    render(<ViewPage />);

    await screen.findByRole("button", { name: /workflow a/i });

    workflowARuns.resolve([runA]);
    await screen.findByRole("button", { name: /run-a/i });

    fireEvent.click(screen.getByRole("button", { name: /workflow b/i }));

    workflowBRuns.resolve([runB]);
    await screen.findByRole("button", { name: /run-b/i });

    runBDetail.resolve(runB);
    const executionHeading = await screen.findByRole("heading", { name: "Execution" });
    const executionCard = executionHeading.closest("article");
    expect(executionCard).not.toBeNull();

    runADetail.resolve(runA);

    await waitFor(() => {
      expect(within(executionCard as HTMLElement).getByText(runB.run_id)).toBeInTheDocument();
      expect(within(executionCard as HTMLElement).getByText("queued")).toBeInTheDocument();
    });
  });

  it("stops polling after a terminal run is selected", async () => {
    const { getRunDetail, getWorkflow, listRuns, listWorkflows } = mockApi();
    const setIntervalSpy = vi.spyOn(window, "setInterval");
    const terminalRun = {
      ...runADetail,
      status: "succeeded",
      finished_at: "2025-01-01T00:02:00.000Z",
    };

    listWorkflows.mockResolvedValue([workflowA]);
    getWorkflow.mockResolvedValue(workflowA);
    listRuns.mockResolvedValue([terminalRun]);
    getRunDetail.mockResolvedValue(terminalRun);

    render(<ViewPage />);

    await screen.findByRole("button", { name: /run-a/i });
    const executionHeading = await screen.findByRole("heading", { name: "Execution" });
    const executionCard = executionHeading.closest("article");
    expect(executionCard).not.toBeNull();
    expect(within(executionCard as HTMLElement).getByText("succeeded")).toBeInTheDocument();

    expect(getRunDetail).toHaveBeenCalledTimes(1);
    expect(setIntervalSpy.mock.calls.some(([, delay]) => delay === 2000)).toBe(false);
  });

  it("renders stored AWDL, result, and trace from the run detail payload", async () => {
    const { getRunDetail, getWorkflow, listRuns, listWorkflows } = mockApi();

    listWorkflows.mockResolvedValue([workflowA]);
    getWorkflow.mockResolvedValue(workflowA);
    listRuns.mockResolvedValue([runA]);
    getRunDetail.mockResolvedValue(runADetail);

    render(<ViewPage />);

    await screen.findByRole("button", { name: /run-a/i });

    expect(await screen.findByRole("heading", { name: "Generated AWDL" })).toBeInTheDocument();
    expect(screen.getByText(/workflow workflow-a/)).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Result payload" })).toBeInTheDocument();
    expect(screen.getByText(/"output": "hello"/)).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Trace" })).toBeInTheDocument();
    expect(screen.getByText(/run\.started/)).toBeInTheDocument();
  });

  it("shows empty artifact states for queued runs without stored artifacts", async () => {
    const { getRunDetail, getWorkflow, listRuns, listWorkflows } = mockApi();

    listWorkflows.mockResolvedValue([workflowB]);
    getWorkflow.mockResolvedValue(workflowB);
    listRuns.mockResolvedValue([runB]);
    getRunDetail.mockResolvedValue(queuedRunDetail);

    render(<ViewPage />);

    await screen.findByRole("button", { name: /run-b/i });

    expect(await screen.findByText(/awdl output is not available yet/i)).toBeInTheDocument();
    expect(screen.getByText(/result payload has not been stored yet/i)).toBeInTheDocument();
    expect(screen.getByText(/trace events have not been stored yet/i)).toBeInTheDocument();
  });

  it("polls running runs after detail loads and stops once the run becomes terminal", async () => {
    const { getRunDetail, getWorkflow, listRuns, listWorkflows } = mockApi();
    vi.useFakeTimers({ shouldAdvanceTime: true });

    const runningRunDetail = {
      ...runADetail,
      status: "running",
      finished_at: null,
    };
    const terminalRunDetail = {
      ...runADetail,
      status: "succeeded",
      finished_at: "2025-01-01T00:02:00.000Z",
    };

    listWorkflows.mockResolvedValue([workflowA]);
    getWorkflow.mockResolvedValue(workflowA);
    listRuns.mockResolvedValue([runA]);
    getRunDetail
      .mockResolvedValueOnce(runningRunDetail)
      .mockResolvedValueOnce(terminalRunDetail);

    render(<ViewPage />);

    await screen.findByRole("button", { name: /run-a/i });
    await waitFor(() => expect(getRunDetail).toHaveBeenCalledTimes(1));
    expect(screen.getAllByText("running").length).toBeGreaterThan(0);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    await waitFor(() => expect(getRunDetail).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getAllByText("succeeded").length).toBeGreaterThan(0));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(getRunDetail).toHaveBeenCalledTimes(2);
  });
});
