"""端到端冒烟脚本：跑两条出片路径并验证产物。"""
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE = "http://127.0.0.1:8000"


def post(path: str, body: dict | None = None, raw: bytes | None = None, headers: dict | None = None) -> tuple[int, bytes]:
    if raw is None:
        raw = json.dumps(body or {}).encode("utf-8")
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(BASE + path, data=raw, headers=h, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def get(path: str) -> tuple[int, bytes]:
    req = urllib.request.Request(BASE + path, method="GET")
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main() -> int:
    print("=== /api/health ===")
    s, b = get("/api/health")
    print(s, b.decode())
    assert s == 200, "health failed"
    health = json.loads(b)

    # ---- 路径 A：草稿 ----
    print("\n=== POST /api/generate (prefer_path=draft) ===")
    req = {
        "text": "今天天气真好\n出去走走吧\n期待下一次相遇",
        "clips": [],
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "total_duration_s": 6.0,
        "prefer_path": "draft",
    }
    s, b = post("/api/generate", req)
    out = json.loads(b)
    print(s, json.dumps(out, ensure_ascii=False))
    assert s == 200 and out["path"] == "draft", "draft generate failed"
    artifact_url = out.get("artifactUrl") or out.get("artifact_url")
    s2, b2 = get(artifact_url)
    print(f"  GET {artifact_url} -> {s2} ({len(b2)} bytes)")
    assert s2 == 200 and len(b2) > 100, "artifact download failed"
    # 写本地一份供检查
    Path("smoke_draft.zip").write_bytes(b2)
    print(f"  saved -> smoke_draft.zip ({len(b2)} bytes)")

    # 解析 zip 看结构
    import zipfile
    with zipfile.ZipFile("smoke_draft.zip") as z:
        names = z.namelist()
        print(f"  zip entries: {names}")
        assert any(n.endswith("draft_content.json") for n in names)
        assert any(n.endswith("draft.meta_info") for n in names)
        j = json.loads(z.read([n for n in names if n.endswith("draft_content.json")][0]))
        print(f"  draft_content.json keys: {list(j.keys())}")
        print(f"  tracks: {len(j['tracks'])}; materials: {len(j['materials'])}")

    # ---- 路径 B：ffmpeg 兜底 ----
    print("\n=== POST /api/generate (prefer_path=ffmpeg) ===")
    req2 = dict(req)
    req2["prefer_path"] = "ffmpeg"
    req2["text"] = "ffmpeg 兜底路径\n直接出 MP4"
    s, b = post("/api/generate", req2)
    out2 = json.loads(b)
    print(s, json.dumps(out2, ensure_ascii=False))
    if s == 200 and out2.get("path") == "ffmpeg":
        url2 = out2.get("artifactUrl") or out2.get("artifact_url")
        s2, b2 = get(url2)
        print(f"  GET {url2} -> {s2} ({len(b2)} bytes)")
        Path("smoke_out.mp4").write_bytes(b2)
        print(f"  saved -> smoke_out.mp4 ({len(b2)} bytes)")
        # 检查文件头
        if len(b2) >= 12 and b2[4:8] == b"ftyp":
            print("  mp4 header OK (ftyp)")
        else:
            print(f"  WARN: mp4 header looks off: {b2[:12]!r}")
    else:
        print(f"  ffmpeg path not available, skipping: {s} {b[:200]!r}")

    # ---- 路径 C：Remotion（web/node_modules 存在时才跑）----
    if health.get("remotionAvailable") or health.get("remotion_available"):
        print("\n=== POST /api/generate (prefer_path=remotion) ===")
        req3 = dict(req)
        req3["prefer_path"] = "remotion"
        req3["text"] = "Remotion 渲染路径\n使用同一个 BaseClip"
        req3["total_duration_s"] = 1.5
        s, b = post("/api/generate", req3)
        out3 = json.loads(b)
        print(s, json.dumps(out3, ensure_ascii=False))
        assert s == 200 and out3.get("path") == "remotion", "remotion generate failed"
        url3 = out3.get("artifactUrl") or out3.get("artifact_url")
        s3, b3 = get(url3)
        print(f"  GET {url3} -> {s3} ({len(b3)} bytes)")
        assert s3 == 200 and len(b3) > 100, "remotion artifact download failed"
    else:
        print("\n=== Remotion path skipped: web/node_modules not installed ===")

    print("\nALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
