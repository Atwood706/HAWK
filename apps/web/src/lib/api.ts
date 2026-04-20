import type {
  AppSettings,
  BuiltinTool,
  ProfileContent,
  ProfileDetail,
  ProfileSummary,
  SkillDetail,
  SkillSummary,
  WorkflowExportResult,
  WorkflowGraph,
  WorkflowRunRecord,
  WorkflowRunRequest,
  WorkflowRunDetail,
  WorkflowRunResult,
  WorkflowSummary,
  WorkflowValidationResult,
} from "../types";

const defaultHeaders = {
  "Content-Type": "application/json",
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function requestJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const payload = (await response.json()) as { detail?: string };
      if (typeof payload.detail === "string" && payload.detail.length > 0) {
        message = payload.detail;
      }
    } catch {
      // Leave the default message when the response body is not JSON.
    }

    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export async function saveWorkflow(graph: WorkflowGraph): Promise<WorkflowGraph> {
  return await requestJson<WorkflowGraph>("/api/workflows", {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify(graph),
  });
}

export async function listWorkflows(): Promise<WorkflowSummary[]> {
  return await requestJson<WorkflowSummary[]>("/api/workflows");
}

export async function getWorkflow(workflowId: string): Promise<WorkflowGraph> {
  return await requestJson<WorkflowGraph>(`/api/workflows/${workflowId}`);
}

export async function validateWorkflow(workflowId: string): Promise<WorkflowValidationResult> {
  return await requestJson<WorkflowValidationResult>(`/api/workflows/${workflowId}/validate`, {
    method: "POST",
  });
}

export async function exportWorkflow(workflowId: string): Promise<WorkflowExportResult> {
  return await requestJson<WorkflowExportResult>(`/api/workflows/${workflowId}/export-awdl`, {
    method: "POST",
  });
}

export async function runWorkflow(
  workflowId: string,
  payload: WorkflowRunRequest = {},
): Promise<WorkflowRunResult> {
  return await requestJson<WorkflowRunResult>(`/api/workflows/${workflowId}/runs`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify(payload),
  });
}

export async function listRuns(workflowId: string): Promise<WorkflowRunRecord[]> {
  return await requestJson<WorkflowRunRecord[]>(`/api/workflows/${workflowId}/runs`);
}

export async function getRunDetail(
  workflowId: string,
  runId: string,
): Promise<WorkflowRunDetail> {
  return await requestJson<WorkflowRunDetail>(`/api/workflows/${workflowId}/runs/${runId}`);
}

export async function getSettings(): Promise<AppSettings> {
  return await requestJson<AppSettings>("/api/settings");
}

export async function saveSettings(payload: AppSettings): Promise<AppSettings> {
  return await requestJson<AppSettings>("/api/settings", {
    method: "PUT",
    headers: defaultHeaders,
    body: JSON.stringify(payload),
  });
}

export async function listProfiles(): Promise<ProfileSummary[]> {
  return await requestJson<ProfileSummary[]>("/api/profiles");
}

export async function getProfile(profileName: string): Promise<ProfileDetail> {
  return await requestJson<ProfileDetail>(`/api/profiles/${profileName}`);
}

export async function saveProfile(
  profileName: string,
  payload: ProfileContent,
): Promise<ProfileDetail> {
  return await requestJson<ProfileDetail>(`/api/profiles/${profileName}`, {
    method: "PUT",
    headers: defaultHeaders,
    body: JSON.stringify(payload),
  });
}

export async function deleteProfile(profileName: string): Promise<void> {
  const response = await fetch(`/api/profiles/${profileName}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (typeof payload.detail === "string" && payload.detail.length > 0) {
        message = payload.detail;
      }
    } catch {
      // ignore
    }
    throw new ApiError(message, response.status);
  }
}

export async function listTools(): Promise<BuiltinTool[]> {
  return await requestJson<BuiltinTool[]>("/api/tools");
}

export async function listSkills(): Promise<SkillSummary[]> {
  return await requestJson<SkillSummary[]>("/api/skills");
}

export async function getSkill(skillName: string): Promise<SkillDetail> {
  return await requestJson<SkillDetail>(`/api/skills/${skillName}`);
}
