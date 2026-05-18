export type WorkflowNodeType = "agent" | "tool";

export interface WorkflowNodeData {
  label?: string;
  profile?: string;
  tool_name?: string;
  function_name?: string;
  medical_skill?: {
    name: string;
    description: string;
    category: string;
    url: string;
  };
  inputs: Record<string, string>;
  outputs: Record<string, string>;
}

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  position: {
    x: number;
    y: number;
  };
  data: WorkflowNodeData;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface WorkflowGraph {
  id: string;
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface WorkflowSummary {
  id: string;
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface WorkflowValidationResult {
  valid: boolean;
  errors: string[];
}

export interface WorkflowExportResult {
  awdl: string;
}

export interface WorkflowRunRequest {
  input?: Record<string, unknown>;
}

export interface WorkflowRunResult {
  run_id: string;
  workflow_id: string;
  status: string;
  input: Record<string, unknown>;
}

export interface WorkflowRunRecord extends WorkflowRunResult {
  started_at: string;
  finished_at: string | null;
}

export interface WorkflowRunDetail extends WorkflowRunRecord {
  awdl: string | null;
  result: unknown | null;
  trace: unknown[];
}

export interface AppSettings {
  theme: string;
  last_open_workflow_id: string | null;
  openrouter_api_key: string | null;
  openai_api_key: string | null;
  deepseek_api_key: string | null;
  qwen_api_key: string | null;
  gemini_api_key: string | null;
  anthropic_api_key: string | null;
  xai_api_key: string | null;
  groq_api_key: string | null;
  mistral_api_key: string | null;
  perplexity_api_key: string | null;
  moonshot_api_key: string | null;
  zhipu_api_key: string | null;
  siliconflow_api_key: string | null;
  together_api_key: string | null;
}

export interface ProfileSummary {
  name: string;
}

export interface ProfileDetail {
  name: string;
  content: string;
}

export interface ProfileContent {
  content: string;
}

export interface ToolPort {
  name: string;
  description: string;
  required: boolean;
  default: unknown | null;
  port_type: string;
}

export interface BuiltinTool {
  name: string;
  description: string;
  category: string;
  inputs: ToolPort[];
  outputs: ToolPort[];
}

export interface SkillSummary {
  name: string;
  path: string;
}

export interface SkillDetail {
  name: string;
  path: string;
  content: string;
}
