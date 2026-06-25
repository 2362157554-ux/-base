import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);

export { RemotionRoot } from "./Root";
export { BaseClip } from "./compositions/BaseClip";
export type { BaseClipProps } from "./compositions/BaseClip";
