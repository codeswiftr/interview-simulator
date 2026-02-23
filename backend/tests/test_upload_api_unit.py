"""Pure unit tests for upload API validation logic.

Tests file extension validation, file size checks, feature flags.
No database or filesystem required.
"""

from app.api.upload import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    MAX_VIDEO_FILE_SIZE,
    VIDEO_ALLOWED_EXTENSIONS,
    AudioUploadResponse,
    VideoUploadResponse,
)


class TestAllowedExtensions:
    def test_webm_allowed(self):
        assert ".webm" in ALLOWED_EXTENSIONS

    def test_mp3_allowed(self):
        assert ".mp3" in ALLOWED_EXTENSIONS

    def test_wav_allowed(self):
        assert ".wav" in ALLOWED_EXTENSIONS

    def test_ogg_allowed(self):
        assert ".ogg" in ALLOWED_EXTENSIONS

    def test_mp4_allowed(self):
        assert ".mp4" in ALLOWED_EXTENSIONS

    def test_exe_not_allowed(self):
        assert ".exe" not in ALLOWED_EXTENSIONS

    def test_py_not_allowed(self):
        assert ".py" not in ALLOWED_EXTENSIONS


class TestVideoAllowedExtensions:
    def test_webm_allowed(self):
        assert ".webm" in VIDEO_ALLOWED_EXTENSIONS

    def test_mp4_allowed(self):
        assert ".mp4" in VIDEO_ALLOWED_EXTENSIONS

    def test_mov_allowed(self):
        assert ".mov" in VIDEO_ALLOWED_EXTENSIONS

    def test_avi_not_allowed(self):
        assert ".avi" not in VIDEO_ALLOWED_EXTENSIONS


class TestFileSizeLimits:
    def test_max_audio_size_is_50mb(self):
        assert MAX_FILE_SIZE == 50 * 1024 * 1024

    def test_max_video_size_is_200mb(self):
        assert MAX_VIDEO_FILE_SIZE == 200 * 1024 * 1024


class TestAudioUploadResponse:
    def test_model_fields(self):
        resp = AudioUploadResponse(
            audio_url="/uploads/audio/test.webm",
            file_size_bytes=1024,
            filename="test.webm",
        )
        assert resp.audio_url == "/uploads/audio/test.webm"
        assert resp.file_size_bytes == 1024
        assert resp.filename == "test.webm"


class TestVideoUploadResponse:
    def test_model_fields(self):
        resp = VideoUploadResponse(
            video_url="/uploads/video/test.mp4",
            file_size_bytes=2048,
            filename="test.mp4",
        )
        assert resp.video_url == "/uploads/video/test.mp4"
        assert resp.file_size_bytes == 2048
        assert resp.filename == "test.mp4"
