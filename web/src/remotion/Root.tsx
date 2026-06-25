import React from "react";
import { Composition } from "remotion";
import { BaseClip, BaseClipProps } from "./compositions/BaseClip";

/**
 * Remotion 注册入口（自研 Root）。
 * 用 ``npx remotion studio`` 或 ``npm run remotion:studio`` 启动可视化编辑。
 */
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="base-clip"
        component={BaseClip as any}
        durationInFrames={30 * 6}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={({ props }) => {
          const p = props as BaseClipProps & { width?: number; height?: number; fps?: number };
          const fps = p.fps ?? 30;
          return {
            durationInFrames: Math.max(1, Math.round(fps * (p.durationS ?? 6))),
            fps,
            width: p.width ?? 1080,
            height: p.height ?? 1920,
          };
        }}
        defaultProps={{
          lines: ["第一行字幕", "第二行字幕", "结尾点题"],
          durationS: 6,
          width: 1080,
          height: 1920,
          fps: 30,
          background: "#0e0f13",
          accentColor: "#4f8cff",
          stickerEmoji: "*",
        }}
      />
    </>
  );
};
