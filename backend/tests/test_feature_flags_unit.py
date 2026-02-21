"""Pure unit tests for feature flags.

Tests require_video_features_enabled() behavior.
No database required.
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.feature_flags import require_video_features_enabled


class TestRequireVideoFeaturesEnabled:
    @patch("app.feature_flags.settings")
    def test_raises_404_when_disabled(self, mock_settings):
        mock_settings.video_features_enabled = False
        with pytest.raises(HTTPException) as exc_info:
            require_video_features_enabled()
        assert exc_info.value.status_code == 404
        assert "soft launch" in str(exc_info.value.detail)

    @patch("app.feature_flags.settings")
    def test_passes_when_enabled(self, mock_settings):
        mock_settings.video_features_enabled = True
        # Should not raise
        require_video_features_enabled()

    @patch("app.feature_flags.settings")
    def test_error_detail_message(self, mock_settings):
        mock_settings.video_features_enabled = False
        with pytest.raises(HTTPException) as exc_info:
            require_video_features_enabled()
        assert "Video review is not available" in str(exc_info.value.detail)

    @patch("app.feature_flags.settings")
    def test_returns_none_when_enabled(self, mock_settings):
        mock_settings.video_features_enabled = True
        result = require_video_features_enabled()
        assert result is None

    @patch("app.feature_flags.settings")
    def test_status_code_is_404_not_403(self, mock_settings):
        """Feature flags use 404 to hide feature existence from unauthorized users."""
        mock_settings.video_features_enabled = False
        with pytest.raises(HTTPException) as exc_info:
            require_video_features_enabled()
        assert exc_info.value.status_code == 404
        assert exc_info.value.status_code != 403

    @patch("app.feature_flags.settings")
    def test_no_side_effects_when_enabled(self, mock_settings):
        mock_settings.video_features_enabled = True
        # Call multiple times — should be stateless
        require_video_features_enabled()
        require_video_features_enabled()
        require_video_features_enabled()
