/**
 * 后端 API 客户端（自研，fetch 封装）。
 */

export interface ClipItem {
  kind: "video" | "audio" | "text" | "sticker";
  url?: string;
  content?: string;
  durationS?: number;
  width?: number;
  height?: number;
}

export interface GenerateRequest {
  text: string;
  clips: ClipItem[];
  width?: number;
  height?: number;
  fps?: number;
  totalDurationS?: number;
  preferPath: "draft" | "ffmpeg";
  tools?: Record<string, Record<string, unknown>>;
}

export interface GenerateResponse {
  jobId: string;
  path: "draft" | "ffmpeg";
  artifactUrl: string;
  message?: string;
}

const BASE = "/api";

export async function health(): Promise<{
  ok: boolean;
  ffmpegAvailable: boolean;
}> {
  const r = await fetch(`${BASE}/health`);
  if (!r.ok) throw new Error("health failed");
  return r.json();
}

export async function uploadFile(file: File): Promise<{
  filename: string;
  url: string;
  size: number;
}> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${BASE}/uploads`, { method: "POST", body: fd });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`upload failed: ${t}`);
  }
  return r.json();
}

export async function generate(req: GenerateRequest): Promise<GenerateResponse> {
  const r = await fetch(`${BASE}/generate`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`generate failed: ${t}`);
  }
  return r.json();
}

export function artifactHref(url: string): string {
  return url.startsWith("http") ? url : `${BASE.replace("/api", "")}${url}`;
}

// BaseTool 能力发现
export type ParamType = "bool" | "int" | "float" | "text" | "choice" | "file";
export interface ParamSpec { key: string; label: string; type: ParamType;
  default?: unknown; choices?: string[]; min?: number|null; max?: number|null; help?: string }
export interface ToolSpec { name: string; display_name: string;
  summary: string; requires_ffmpeg: boolean; params: ParamSpec[] }
export async function listTools(): Promise<ToolSpec[]> {
  const r = await fetch(`${BASE}/tools`);
  if (!r.ok) throw new Error("tools index failed");
  return (JSON.parse((await r.text()).replace(/^\uFEFF/, "")).tools) ?? [];
}
