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
