"""
动态能力面板：基于 /api/tools 返回的 schema 自动渲染开关/下拉/滑块。
新加 tool 不需要改这个组件。
"""
import React from "react";
import { ToolSpec, ParamSpec } from "../api";

interface Props {
  tools: ToolSpec[];
  values: Record<string, Record<string, unknown>>;
  onChange: (toolName: string, key: string, value: unknown) => void;
}

export const CapabilitiesPanel: React.FC<Props> = ({ tools, values, onChange }) => {
  const visible = tools.filter((t) => t.name !== "compose");
  if (!visible.length) return null;
  return (
    <div className="capabilities">
      <h2>能力（ffmpeg-only）</h2>
      <div className="cap-grid">
        {visible.map((tool) => {
          const tv = values[tool.name] || {};
          const enabled = tv.enabled !== false;
          const params = tool.params.filter((p) => p.key !== "enabled");
          return (
            <div key={tool.name} className={`cap ${enabled ? "" : "cap-off"}`}>
              <label className="cap-head">
                <input type="checkbox" checked={enabled}
                  onChange={(e) => onChange(tool.name, "enabled", e.target.checked)} />
                <span className="cap-title">{tool.display_name}</span>
                <span className="cap-sum" title={tool.summary}>{tool.summary}</span>
              </label>
              {enabled && params.length > 0 && (
                <div className="cap-params">
                  {params.map((p) => (
                    <Row key={p.key} spec={p}
                      value={tv[p.key] ?? p.default}
                      onChange={(v) => onChange(tool.name, p.key, v)} />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// 一种控件渲染所有类型（避免为每种类型写一个组件）
const Row: React.FC<{ spec: ParamSpec; value: unknown; onChange: (v: unknown) => void }>
  = ({ spec, value, onChange }) => {
  const label = <label className="p-lbl">{spec.label}{spec.help && <i> {spec.help}</i>}</label>;
  if (spec.type === "bool")
    return <div className="p">{label}<input type="checkbox" checked={Boolean(value)} onChange={(e) => onChange(e.target.checked)} /></div>;
  if (spec.type === "choice")
    return <div className="p">{label}<select value={String(value ?? "")} onChange={(e) => onChange(e.target.value)}>
      {(spec.choices ?? []).map((c) => <option key={c} value={c}>{c}</option>)}
    </select></div>;
  if (spec.type === "int" || spec.type === "float") {
    const n = Number(value ?? 0);
    return <div className="p">{label}<div className="p-row">
      <input type="range" min={spec.min} max={spec.max}
        step={spec.type === "float" ? 0.05 : 1} value={n}
        onChange={(e) => onChange(Number(e.target.value))} />
      <input type="number" className="p-num" min={spec.min} max={spec.max}
        step={spec.type === "float" ? 0.05 : 1} value={n}
        onChange={(e) => onChange(Number(e.target.value))} />
    </div></div>;
  }
  return <div className="p">{label}<input type="text" value={String(value ?? "")} onChange={(e) => onChange(e.target.value)} /></div>;
};