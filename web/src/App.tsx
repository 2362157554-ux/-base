import React, { useEffect, useMemo, useState } from "react";
import { Preview } from "./Preview";
import { generate, health, uploadFile, ClipItem, GenerateResponse } from "./api";

interface UploadedClip {
  file: File;
  url: string;
  filename: string;
  kind: "video" | "audio";
  durationS?: number;
}

const App: React.FC = () => {
  const [text, setText] = useState("一句话生成短视频\nRemotion + 自研后端\n输出 MP4");
  const [width, setWidth] = useState(1080);
  const [height, setHeight] = useState(1920);
  const [durationS, setDurationS] = useState(6);
  const [preferPath, setPreferPath] = useState<"draft" | "ffmpeg">("draft");
  const [clips, setClips] = useState<UploadedClip[]>([]);
  const [status, setStatus] = useState<{ kind: "idle" | "ok" | "err"; msg: string }>({
    kind: "idle",
    msg: "",
  });
  const [ffmpegAvailable, setFfmpegAvailable] = useState<boolean>(false);
  const [busy, setBusy] = useState(false);
  const [artifact, setArtifact] = useState<GenerateResponse | null>(null);

  useEffect(() => {
    health().then((h) => setFfmpegAvailable(h.ffmpegAvailable)).catch(() => {});
  }, []);

  const clipItems: ClipItem[] = useMemo(() => {
    return clips.map<ClipItem>((c) => ({
      kind: c.kind,
      url: c.url,
      durationS: c.durationS,
    }));
  }, [clips]);

  async function onPickFiles(files: FileList | null) {
    if (!files) return;
    setStatus({ kind: "idle", msg: "" });
    for (const file of Array.from(files)) {
      try {
        const up = await uploadFile(file);
        const kind: "video" | "audio" = file.type.startsWith("audio")
          ? "audio"
          : "video";
        let durationS: number | undefined;
        if (kind === "video" || kind === "audio") {
          durationS = await probeDuration(file);
        }
        setClips((prev) => [
          ...prev,
          { file, url: up.url, filename: up.filename, kind, durationS },
        ]);
      } catch (e) {
        setStatus({ kind: "err", msg: (e as Error).message });
      }
    }
  }

  function removeClip(idx: number) {
    setClips((prev) => prev.filter((_, i) => i !== idx));
  }

  async function onGenerate() {
    setBusy(true);
    setArtifact(null);
    setStatus({ kind: "idle", msg: "生成中…" });
    try {
      const res = await generate({
        text,
        clips: clipItems,
        width,
        height,
        fps: 30,
        totalDurationS: durationS,
        preferPath,
      });
      setArtifact(res);
      setStatus({
        kind: "ok",
        msg: preferPath === "draft"
          ? "已生成剪映草稿 zip — 解压到剪映草稿目录，打开剪映即可一键导出。"
          : "已生成 MP4 — 直接下载成片。",
      });
    } catch (e) {
      setStatus({ kind: "err", msg: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <div className="app-header">
        <h1>-base / 一句话剪辑</h1>
        <span className="tag">Remotion + 自研后端</span>
        <span style={{ marginLeft: "auto", color: "var(--muted)", fontSize: 12 }}>
          ffmpeg: {ffmpegAvailable ? "可用" : "未检测到"}
        </span>
      </div>

      <div className="app-main">
        {/* 左侧：参数 */}
        <div className="panel">
          <h2>素材</h2>
          <div className="body">
            <div className="field">
              <label>上传视频/音频（可选）</label>
              <input
                type="file"
                accept="video/*,audio/*"
                multiple
                onChange={(e) => onPickFiles(e.target.files)}
              />
            </div>
            <div className="clips-list">
              {clips.length === 0 && (
                <div style={{ color: "var(--muted)", fontSize: 12 }}>
                  没上传也能跑，会生成纯色背景 + 字幕。
                </div>
              )}
              {clips.map((c, i) => (
                <div className="clip" key={i}>
                  <div>
                    <div>{c.filename}</div>
                    <div className="meta">
                      {c.kind}
                      {c.durationS ? ` · ${c.durationS.toFixed(1)}s` : ""}
                    </div>
                  </div>
                  <button className="btn ghost" onClick={() => removeClip(i)}>
                    移除
                  </button>
                </div>
              ))}
            </div>
          </div>

          <h2>画布</h2>
          <div className="body">
            <div className="field row">
              <div>
                <label>宽</label>
                <input
                  type="number"
                  value={width}
                  onChange={(e) => setWidth(parseInt(e.target.value) || 1080)}
                />
              </div>
              <div>
                <label>高</label>
                <input
                  type="number"
                  value={height}
                  onChange={(e) => setHeight(parseInt(e.target.value) || 1920)}
                />
              </div>
            </div>
            <div className="field">
              <label>总时长（秒）</label>
              <input
                type="number"
                step="0.5"
                min={1}
                max={60}
                value={durationS}
                onChange={(e) => setDurationS(parseFloat(e.target.value) || 6)}
              />
            </div>
            <div className="field">
              <label>出片路径</label>
              <select
                value={preferPath}
                onChange={(e) => setPreferPath(e.target.value as any)}
              >
                <option value="draft">路径 A：剪映草稿（zip）</option>
                <option value="ffmpeg" disabled={!ffmpegAvailable}>
                  路径 B：ffmpeg 直接出 MP4{!ffmpegAvailable ? "（不可用）" : ""}
                </option>
              </select>
            </div>
          </div>
        </div>

        {/* 中间：预览 */}
        <div className="preview">
          <Preview text={text} width={width} height={height} durationS={durationS} />
          <div style={{ marginTop: 16, color: "var(--muted)", fontSize: 12 }}>
            这是浏览器内实时预览（Remotion Player）；点「生成」才会让后端出片。
          </div>
        </div>

        {/* 右侧：文案 + 操作 */}
        <div className="panel right">
          <h2>文案</h2>
          <div className="body">
            <div className="field">
              <label>一句话（多行会自动拆成多段字幕）</label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="把今天看到的好玩事讲给朋友听"
              />
            </div>

            <div className={`status ${status.kind === "ok" ? "success" : status.kind === "err" ? "error" : ""}`}>
              {status.msg || "就绪"}
            </div>

            <button
              className="btn"
              onClick={onGenerate}
              disabled={busy || !text.trim()}
              style={{ width: "100%" }}
            >
              {busy ? "生成中…" : "生成"}
            </button>

            {artifact && (
              <div style={{ marginTop: 16 }}>
                <a
                  className="btn secondary"
                  style={{ width: "100%", display: "block", textAlign: "center", textDecoration: "none" }}
                  href={artifact.artifactUrl}
                  download
                >
                  下载{artifact.path === "draft" ? ".draft.zip" : ".mp4"}
                </a>
                <div style={{ marginTop: 8, fontSize: 11, color: "var(--muted)" }}>
                  job: {artifact.jobId}
                </div>
                {artifact.message && (
                  <div style={{ marginTop: 6, fontSize: 12, color: "var(--muted)" }}>
                    {artifact.message}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// 探测媒体时长（前端简易实现，不依赖第三方库）。
function probeDuration(file: File): Promise<number> {
  return new Promise((resolve) => {
    const isVideo = file.type.startsWith("video");
    const el = isVideo ? document.createElement("video") : document.createElement("audio");
    el.preload = "metadata";
    el.src = URL.createObjectURL(file);
    el.onloadedmetadata = () => {
      const d = el.duration;
      URL.revokeObjectURL(el.src);
      resolve(isFinite(d) ? d : 0);
    };
    el.onerror = () => {
      URL.revokeObjectURL(el.src);
      resolve(0);
    };
  });
}

export { App };
export default App;
