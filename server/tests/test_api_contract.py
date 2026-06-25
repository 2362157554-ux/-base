"""API request/response naming contract tests."""
from app.api.schemas import GenerateRequest, GenerateResponse, HealthResponse


def test_generate_request_accepts_frontend_camel_case():
    req = GenerateRequest.model_validate(
        {
            "text": "hello",
            "clips": [
                {
                    "kind": "video",
                    "url": "/api/files/a.mp4",
                    "durationS": 2.5,
                }
            ],
            "totalDurationS": 3.5,
            "preferPath": "ffmpeg",
        }
    )

    assert req.total_duration_s == 3.5
    assert req.prefer_path == "ffmpeg"
    assert req.clips[0].duration_s == 2.5


def test_api_responses_can_serialize_as_frontend_camel_case():
    generated = GenerateResponse(
        job_id="job123",
        path="draft",
        artifact_url="/api/outputs/job123.draft.zip",
    ).model_dump(by_alias=True)
    health = HealthResponse(
        ffmpeg_available=True,
        remotion_available=False,
        time=1.0,
    ).model_dump(by_alias=True)

    assert generated["jobId"] == "job123"
    assert generated["artifactUrl"] == "/api/outputs/job123.draft.zip"
    assert health["ffmpegAvailable"] is True
    assert health["remotionAvailable"] is False
