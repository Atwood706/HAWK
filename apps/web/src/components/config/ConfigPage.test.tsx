import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ConfigPage } from "./ConfigPage";
import * as api from "../../lib/api";

vi.mock("../../lib/api", () => ({
  getSettings: vi.fn(),
  saveSettings: vi.fn(),
  listProfiles: vi.fn().mockResolvedValue([]),
  getProfile: vi.fn(),
  saveProfile: vi.fn(),
  listTools: vi.fn().mockResolvedValue([]),
  listSkills: vi.fn().mockResolvedValue([]),
  getSkill: vi.fn(),
}));

function mockApi() {
  return {
    getSettings: vi.mocked(api.getSettings),
    saveSettings: vi.mocked(api.saveSettings),
  };
}

describe("ConfigPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads editable settings and saves them successfully", async () => {
    const { getSettings, saveSettings } = mockApi();

    getSettings.mockResolvedValue({
      theme: "light",
      last_open_workflow_id: "workflow-a",
      openrouter_api_key: "sk-or-v1-old",
    });
    saveSettings.mockResolvedValue({
      theme: "dark",
      last_open_workflow_id: "workflow-b",
      openrouter_api_key: "sk-or-v1-new",
    });

    render(<ConfigPage />);

    expect(await screen.findByDisplayValue("light")).toBeInTheDocument();
    expect(screen.getByDisplayValue("workflow-a")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/theme/i), { target: { value: "dark" } });
    fireEvent.change(screen.getByLabelText(/last open workflow id/i), {
      target: { value: "workflow-b" },
    });
    fireEvent.change(screen.getByLabelText(/openrouter api key/i), {
      target: { value: "sk-or-v1-new" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save settings/i }));

    await waitFor(() => {
      expect(saveSettings).toHaveBeenCalledWith({
        theme: "dark",
        last_open_workflow_id: "workflow-b",
        openrouter_api_key: "sk-or-v1-new",
      });
    });

    expect(await screen.findByText(/settings saved/i)).toBeInTheDocument();
    expect(screen.getByText("workflow-b")).toBeInTheDocument();
  });

  it("shows a save error when the API rejects invalid settings", async () => {
    const { getSettings, saveSettings } = mockApi();

    getSettings.mockResolvedValue({
      theme: "light",
      last_open_workflow_id: null,
      openrouter_api_key: null,
    });
    saveSettings.mockRejectedValue(new Error("invalid settings payload"));

    render(<ConfigPage />);

    await screen.findByDisplayValue("light");
    fireEvent.change(screen.getByLabelText(/theme/i), { target: { value: "dark" } });
    fireEvent.click(screen.getByRole("button", { name: /save settings/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid settings payload/i)).toBeInTheDocument();
    });
  });

  it("disables settings inputs when the initial settings load fails", async () => {
    const { getSettings } = mockApi();

    getSettings.mockRejectedValue(new Error("failed to load settings"));

    render(<ConfigPage />);

    expect(await screen.findByText(/failed to load settings/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/theme/i)).toBeDisabled();
    expect(screen.getByLabelText(/last open workflow id/i)).toBeDisabled();
    expect(screen.getByLabelText(/openrouter api key/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: /save settings/i })).toBeDisabled();
  });
});
