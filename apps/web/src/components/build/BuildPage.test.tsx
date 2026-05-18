import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BuildPage } from "./BuildPage";
import * as api from "../../lib/api";

vi.mock("../../lib/api", () => ({
  exportWorkflow: vi.fn(),
  listProfiles: vi.fn(),
  listTools: vi.fn(),
  runWorkflow: vi.fn(),
  saveWorkflow: vi.fn(),
  validateWorkflow: vi.fn(),
}));

vi.mock("./WorkflowCanvas", () => ({
  WorkflowCanvas: ({ graph }: { graph: { name: string } }) => <div>{graph.name}</div>,
}));

vi.mock("./ConfigPanel", () => ({
  ConfigPanel: () => <div>Config panel</div>,
}));

vi.mock("./NodePalette", () => ({
  NodePalette: () => <div>Node palette</div>,
}));

vi.mock("./MedicalSkillsColumn", () => ({
  MedicalSkillsColumn: () => <div>Medical skills</div>,
}));

function mockApi() {
  return {
    listProfiles: vi.mocked(api.listProfiles),
    listTools: vi.mocked(api.listTools),
    runWorkflow: vi.mocked(api.runWorkflow),
    saveWorkflow: vi.mocked(api.saveWorkflow),
  };
}

describe("BuildPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("runs the seeded OpenRouter demo workflow from the build page", async () => {
    const { listProfiles, listTools, runWorkflow, saveWorkflow } = mockApi();

    listProfiles.mockResolvedValue([{ name: "openrouter_chat" }]);
    listTools.mockResolvedValue([]);
    saveWorkflow.mockImplementation(async (graph) => graph);
    runWorkflow.mockResolvedValue({
      run_id: "run-1",
      workflow_id: "openrouter_demo",
      status: "succeeded",
      input: {
        user_query: "Hello from the local workbench",
      },
    });

    render(<BuildPage />);

    expect(screen.getByText("OpenRouter Demo")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^run$/i }));

    await waitFor(() => {
      expect(saveWorkflow).toHaveBeenCalledWith(
        expect.objectContaining({
          id: "openrouter_demo",
          name: "OpenRouter Demo",
        }),
      );
      expect(runWorkflow).toHaveBeenCalledWith("openrouter_demo", {
        input: {
          user_query: "Hello from the local workbench",
        },
      });
    });

    expect(await screen.findByText(/run completed: run-1 \(succeeded\)/i)).toBeInTheDocument();
  });
});
