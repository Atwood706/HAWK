import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProfilesPanel } from "./ProfilesPanel";
import * as api from "../../lib/api";

vi.mock("../../lib/api", () => ({
  getProfile: vi.fn(),
  listProfiles: vi.fn(),
  listSkills: vi.fn(),
  listTools: vi.fn(),
  saveProfile: vi.fn(),
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

function mockApi() {
  return {
    getProfile: vi.mocked(api.getProfile),
    listProfiles: vi.mocked(api.listProfiles),
    listSkills: vi.mocked(api.listSkills),
    listTools: vi.mocked(api.listTools),
    saveProfile: vi.mocked(api.saveProfile),
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ProfilesPanel", () => {
  it("keeps a new draft when the initial profile list resolves late", async () => {
    const { getProfile, listProfiles, listSkills, listTools } = mockApi();
    const deferredProfiles = createDeferred<Array<{ name: string }>>();

    listProfiles.mockReturnValue(deferredProfiles.promise);
    listSkills.mockResolvedValue([]);
    listTools.mockResolvedValue([]);
    getProfile.mockResolvedValue({ name: "coder", content: 'model = "deepseek-chat"\n' });

    render(<ProfilesPanel />);

    fireEvent.change(screen.getByPlaceholderText("coder"), { target: { value: "draft-profile" } });
    fireEvent.change(screen.getByRole("textbox", { name: /model/i }), {
      target: { value: "gpt-5" },
    });
    fireEvent.change(screen.getByRole("spinbutton", { name: /max turns/i }), {
      target: { value: "6" },
    });

    await act(async () => {
      deferredProfiles.resolve([{ name: "coder" }]);
      await deferredProfiles.promise;
    });

    await waitFor(() => {
      expect(screen.getByDisplayValue("draft-profile")).toBeInTheDocument();
      expect(screen.getByRole("textbox", { name: /model/i })).toHaveValue("gpt-5");
      expect(screen.getByRole("spinbutton", { name: /max turns/i })).toHaveValue(6);
      expect(screen.getByText("Create")).toBeInTheDocument();
    });
  });
});
