/* eslint-disable react/no-unknown-property */
import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

/**
 * BaseClip：自研的"字幕条 + 贴纸 + 渐入"组合。
 *
 * 用法：
 *   <Composition
 *     id="base-clip"
 *     component={BaseClip}
 *     durationInFrames={fps * duration_s}
 *     fps={30}
 *     width={1080}
 *     height={1920}
 *   />
 *
 * 入参 props 完全自定，不依赖 Remotion 默认示例。
 */
export interface BaseClipProps {
  lines: string[];            // 拆分后的字幕行
  durationS: number;          // 总时长（秒）
  width?: number;             // CLI metadata input
  height?: number;            // CLI metadata input
  fps?: number;               // CLI metadata input
  background?: string;        // 背景色或图片 URL
  accentColor?: string;       // 强调色（字幕条）
  stickerEmoji?: string;      // 贴纸 emoji
}

export const BaseClip: React.FC<BaseClipProps> = ({
  lines,
  durationS,
  background = "#0e0f13",
  accentColor = "#4f8cff",
  stickerEmoji = "✨",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // 全局呼吸缩放
  const breathe = interpolate(
    frame,
    [0, fps * durationS],
    [1.0, 1.05],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ background }}>
      {/* 背景轻微缩放层 */}
      <AbsoluteFill
        style={{
          transform: `scale(${breathe})`,
          background:
            "radial-gradient(circle at 50% 30%, rgba(79,140,255,0.18), transparent 60%)",
        }}
      />

      {/* 顶部贴纸 */}
      <Sticker emoji={stickerEmoji} />

      {/* 字幕行 — 按时间切片渐入渐出 */}
      <Lines lines={lines} accentColor={accentColor} durationS={durationS} />

      {/* 底部进度条 */}
      <ProgressBar width={width} />
    </AbsoluteFill>
  );
};

const Sticker: React.FC<{ emoji: string }> = ({ emoji }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const drop = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 120, mass: 0.8 },
  });
  return (
    <div
      style={{
        position: "absolute",
        top: 180,
        left: "50%",
        transform: `translate(-50%, ${interpolate(drop, [0, 1], [-200, 0])}px) rotate(${interpolate(drop, [0, 1], [-25, 0])}deg)`,
        fontSize: 110,
        filter: "drop-shadow(0 12px 24px rgba(0,0,0,0.45))",
        userSelect: "none",
      }}
    >
      {emoji}
    </div>
  );
};

const Lines: React.FC<{
  lines: string[];
  accentColor: string;
  durationS: number;
}> = ({ lines, accentColor, durationS }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const totalFrames = fps * durationS;
  const perLine = totalFrames / Math.max(lines.length, 1);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 220,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 14,
      }}
    >
      {lines.map((line, i) => {
        const local = frame - i * perLine;
        if (local < 0 || local > perLine) return null;
        const appear = spring({
          frame: local,
          fps,
          config: { damping: 14, stiffness: 140, mass: 0.7 },
        });
        const fade = Math.max(0.1, Math.min(12, perLine * 0.33));
        const holdEnd = Math.max(fade + 0.1, perLine - fade);
        const fadeEnd = Math.max(holdEnd + 0.1, perLine);
        const opacity = interpolate(local, [0, fade, holdEnd, fadeEnd], [0, 1, 1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        return (
          <div
            key={i}
            style={{
              opacity,
              transform: `translateY(${interpolate(appear, [0, 1], [20, 0])}px)`,
              background: accentColor,
              color: "#fff",
              padding: "14px 26px",
              borderRadius: 12,
              fontSize: 44,
              fontWeight: 700,
              maxWidth: width * 0.86,
              textAlign: "center",
              boxShadow: "0 8px 28px rgba(0,0,0,0.35)",
              lineHeight: 1.3,
            }}
          >
            {line}
          </div>
        );
      })}
    </div>
  );
};

const ProgressBar: React.FC<{ width: number }> = ({ width }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const pct = Math.min(frame / Math.max(durationInFrames - 1, 1), 1);
  return (
    <div
      style={{
        position: "absolute",
        bottom: 60,
        left: width * 0.08,
        right: width * 0.08,
        height: 4,
        background: "rgba(255,255,255,0.15)",
        borderRadius: 2,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${pct * 100}%`,
          height: "100%",
          background: "linear-gradient(90deg, #4f8cff, #5dc6a8)",
        }}
      />
    </div>
  );
};
