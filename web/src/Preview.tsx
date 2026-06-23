import React from "react";
import { Player } from "@remotion/player";
import { BaseClip } from "./remotion/compositions/BaseClip";

interface PreviewProps {
  text: string;
  width: number;
  height: number;
  durationS: number;
}

/**
 * 浏览器内的实时预览（Remotion Player）。
 * 不调后端，纯前端 React 渲染。
 */
export const Preview: React.FC<PreviewProps> = ({
  text,
  width,
  height,
  durationS,
}) => {
  const lines = text
    .split(/[。\n,，]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const safeLines = lines.length ? lines : ["在这里输入一句话"];

  // 让预览框按高度自适应，但保持比例
  const containerHeight = 540;
  const scale = containerHeight / height;

  return (
    <div
      className="preview-frame"
      style={{
        width: width * scale,
        height: containerHeight,
      }}
    >
      <Player
        component={BaseClip as any}
        durationInFrames={Math.round(30 * durationS)}
        compositionWidth={width}
        compositionHeight={height}
        fps={30}
        style={{
          width: "100%",
          height: "100%",
        }}
        controls
        autoPlay
        loop
        inputProps={{
          lines: safeLines,
          durationS,
          background: "#0e0f13",
          accentColor: "#4f8cff",
          stickerEmoji: "✨",
        }}
      />
    </div>
  );
};
