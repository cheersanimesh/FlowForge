// Types matching backend models

export enum BlockType {
  READ_CSV = "read_csv",
  FILTER = "filter",
  ENRICH_LEAD = "enrich_lead",
  FIND_EMAIL = "find_email",
  SAVE_CSV = "save_csv",
}

export enum FilterOperator {
  CONTAINS = "contains",
  EQUALS = "equals",
  STARTS_WITH = "starts_with",
  ENDS_WITH = "ends_with",
  IN = "in",
  NOT_NULL = "not_null",
  IS_TRUE = "is_true",
  IS_FALSE = "is_false",
}

export interface FilterRule {
  col: string;
  op: FilterOperator;
  value?: string | string[];
}

export interface FilterParams {
  mode: "rules" | "expr";
  rules?: FilterRule[];
  combine?: "and" | "or";
  expr?: string;
}

export interface ReadCsvParams {
  path: string;
}

export interface EnrichLeadParams {
  lead_mapping: Record<string, string>;
  struct: Record<string, string>;
  research_plan?: string;
  output_prefix: string;
}

export interface FindEmailParams {
  lead_mapping: Record<string, string>;
  mode: "PROFESSIONAL" | "PERSONAL";
  output_prefix: string;
}

export interface SaveCsvParams {
  path?: string;
}

export type NodeParams = 
  | ReadCsvParams 
  | FilterParams 
  | EnrichLeadParams 
  | FindEmailParams 
  | SaveCsvParams
  | Record<string, any>;

export interface NodeModel {
  id: string;
  type: BlockType;
  params: NodeParams;
}

export interface EdgeModel {
  from: string;
  to: string;
}

export interface WorkflowSpec {
  nodes: NodeModel[];
  edges: EdgeModel[];
}

export type NodeStatus = "queued" | "running" | "success" | "failed" | "idle";

export interface NodeResult {
  id: string;
  type: string;
  status: NodeStatus;
  preview_path?: string;
  rows?: number;
  progress?: number; // Percentage completed (0-100)
  error?: {
    message: string;
    trace?: string;
  };
}

export interface RunResponse {
  run_id: string;
  status: "running" | "success" | "failed";
  nodes?: NodeResult[];
  sources?: string[];
  sinks?: string[];
  outputs?: Record<string, { output_csv_path: string }>;
  output_csv_path?: string;
  error?: {
    node_id?: string;
    message: string;
    trace?: string;
  };
}

export interface RunStartResponse {
  run_id: string;
}

export interface PreviewData {
  rows: number;
  columns: string[];
  preview: Record<string, any>[];
}

// React Flow types
export interface FlowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    nodeType: BlockType;
    params: NodeParams;
    status?: NodeStatus;
    error?: string;
    progress?: number; // Percentage completed (0-100)
  };
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
}

