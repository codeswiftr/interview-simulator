"""Pure unit tests for app/main.py.

Covers:
- _EmailMaskingFilter: msg masking, args masking (tuple / dict), passthrough
- configure_logging(): debug vs production handler, filter attachment
- init_error_monitoring(): sentry init path, ImportError path, skipped when no DSN / debug
- lifespan(): startup happy path, DB-failure handling, seeding in debug
- custom_openapi(): schema caching, BearerAuth security scheme injection
- app_error_handler(): status code and body forwarded correctly
- root endpoint: correct payload
- Middleware registration: CORS, Security, UTM, RequestID are all present
- Static-file mount present
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_PATCHES = {
    # Prevent real DB / Redis / sentry hits at import time
    "app.main.check_db_connection": AsyncMock(return_value=True),
    "app.main.close_db_connections": AsyncMock(),
    "app.main.seed_questions": AsyncMock(),
}


def _make_settings(**kwargs):
    """Return a MagicMock that looks like app.config.Settings."""
    s = MagicMock()
    s.debug = kwargs.get("debug", True)
    s.environment = kwargs.get("environment", "development")
    s.sentry_dsn = kwargs.get("sentry_dsn", "")
    s.posthog_api_key = kwargs.get("posthog_api_key", "")
    s.posthog_host = kwargs.get("posthog_host", "https://app.posthog.com")
    s.redis_url = kwargs.get("redis_url", "redis://localhost:6379/0")
    s.effective_cors_origins = kwargs.get("effective_cors_origins", [])
    s.transcription_provider = kwargs.get("transcription_provider", "openai")
    s.content_analysis_provider = kwargs.get("content_analysis_provider", "anthropic")
    s.openai_api_key = kwargs.get("openai_api_key", "key")
    s.groq_api_key = kwargs.get("groq_api_key", "")
    s.anthropic_api_key = kwargs.get("anthropic_api_key", "key")
    s.openrouter_api_key = kwargs.get("openrouter_api_key", "")
    s.resend_api_key = kwargs.get("resend_api_key", "")
    s.resend_from_email = kwargs.get("resend_from_email", "hello@example.com")
    s.validate_for_production = MagicMock()
    return s


# ===========================================================================
# _EmailMaskingFilter
# ===========================================================================


class TestEmailMaskingFilter:
    """Unit tests for the _EmailMaskingFilter logging filter."""

    def _get_filter(self):
        from app.main import _EmailMaskingFilter

        return _EmailMaskingFilter()

    def _make_record(self, msg, args=None):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=msg,
            args=args or (),
            exc_info=None,
        )
        return record

    def test_filter_always_returns_true(self):
        """filter() must always return True (never suppress records)."""
        f = self._get_filter()
        record = self._make_record("hello world")
        assert f.filter(record) is True

    def test_filter_masks_email_in_msg(self):
        """Email addresses in msg are replaced with masked equivalents."""
        f = self._get_filter()
        record = self._make_record("user alice@example.com logged in")
        f.filter(record)
        assert "alice@example.com" not in record.msg
        assert "@" in record.msg  # masked form still contains @

    def test_filter_leaves_non_email_msg_unchanged(self):
        """Strings without email addresses are left intact."""
        f = self._get_filter()
        original = "no emails here, just text"
        record = self._make_record(original)
        f.filter(record)
        assert record.msg == original

    def test_filter_masks_email_in_tuple_args(self):
        """Emails inside positional format args (tuple) are masked."""
        f = self._get_filter()
        record = self._make_record("user %s did something", args=("bob@corp.io",))
        f.filter(record)
        assert "bob@corp.io" not in record.args
        assert isinstance(record.args, tuple)

    def test_filter_masks_email_in_dict_args(self):
        """Emails inside keyword format args (dict) are masked."""
        f = self._get_filter()
        record = self._make_record("event %(user)s")
        # Assign dict directly after construction to bypass LogRecord arg-detection
        record.args = {"user": "carol@test.org"}
        f.filter(record)
        assert "carol@test.org" not in record.args["user"]

    def test_filter_preserves_non_string_tuple_args(self):
        """Non-string items in tuple args pass through unmodified."""
        f = self._get_filter()
        record = self._make_record("count %d")
        record.args = (42,)
        f.filter(record)
        assert record.args == (42,)

    def test_filter_preserves_non_string_dict_args(self):
        """Non-string values in dict args pass through unmodified."""
        f = self._get_filter()
        record = self._make_record("count %(n)d")
        record.args = {"n": 99}
        f.filter(record)
        assert record.args["n"] == 99

    def test_filter_handles_empty_args(self):
        """Empty args tuple does not cause errors."""
        f = self._get_filter()
        record = self._make_record("no args")
        record.args = ()
        assert f.filter(record) is True

    def test_filter_handles_none_args(self):
        """args=None does not trigger masking and does not raise."""
        f = self._get_filter()
        record = self._make_record("plain message")
        record.args = None
        assert f.filter(record) is True


# ===========================================================================
# configure_logging
# ===========================================================================


class TestConfigureLogging:
    """Unit tests for configure_logging()."""

    @patch("app.main.settings")
    def test_debug_mode_attaches_email_filter(self, mock_settings):
        """configure_logging() attaches an _EmailMaskingFilter in debug mode."""
        mock_settings.debug = True
        from app.main import _EmailMaskingFilter, configure_logging

        configure_logging()
        root_filters = [
            f for f in logging.getLogger().filters if isinstance(f, _EmailMaskingFilter)
        ]
        assert len(root_filters) >= 1

    @patch("app.main.settings")
    def test_production_mode_attaches_email_filter(self, mock_settings):
        """configure_logging() attaches an _EmailMaskingFilter in production mode."""
        mock_settings.debug = False
        from app.main import _EmailMaskingFilter, configure_logging

        configure_logging()
        root_filters = [
            f for f in logging.getLogger().filters if isinstance(f, _EmailMaskingFilter)
        ]
        assert len(root_filters) >= 1

    @patch("app.main.settings")
    def test_debug_sets_uvicorn_access_to_info(self, mock_settings):
        """In debug mode uvicorn.access level is INFO."""
        mock_settings.debug = True
        from app.main import configure_logging

        configure_logging()
        assert logging.getLogger("uvicorn.access").level == logging.INFO

    @patch("app.main.settings")
    def test_production_sets_uvicorn_access_to_warning(self, mock_settings):
        """In production mode uvicorn.access level is WARNING."""
        mock_settings.debug = False
        from app.main import configure_logging

        configure_logging()
        assert logging.getLogger("uvicorn.access").level == logging.WARNING


# ===========================================================================
# init_error_monitoring
# ===========================================================================


class TestInitErrorMonitoring:
    """Unit tests for init_error_monitoring()."""

    @patch("app.main.settings")
    def test_skips_when_no_sentry_dsn(self, mock_settings):
        """No Sentry init when sentry_dsn is empty."""
        mock_settings.sentry_dsn = ""
        mock_settings.debug = False

        with patch("app.main.logging") as mock_log:
            from app.main import init_error_monitoring

            init_error_monitoring()
            # sentry_sdk.init must NOT have been called
            mock_log.getLogger.return_value.info.assert_not_called()

    @patch("app.main.settings")
    def test_skips_when_debug_true(self, mock_settings):
        """No Sentry init when debug=True, even if DSN is present."""
        mock_settings.sentry_dsn = "https://key@sentry.io/123"
        mock_settings.debug = True

        import sentry_sdk

        with patch.object(sentry_sdk, "init") as mock_init:
            from app.main import init_error_monitoring

            init_error_monitoring()
            mock_init.assert_not_called()

    @patch("app.main.settings")
    def test_inits_sentry_when_dsn_and_production(self, mock_settings):
        """Sentry is initialised when DSN is present and debug=False."""
        mock_settings.sentry_dsn = "https://key@sentry.io/123"
        mock_settings.debug = False
        mock_settings.environment = "production"

        with (
            patch("sentry_sdk.init") as mock_init,
            patch("sentry_sdk.integrations.fastapi.FastApiIntegration", return_value=MagicMock()),
            patch(
                "sentry_sdk.integrations.sqlalchemy.SqlalchemyIntegration",
                return_value=MagicMock(),
            ),
        ):
            from app.main import init_error_monitoring

            init_error_monitoring()
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args.kwargs
            assert call_kwargs["dsn"] == "https://key@sentry.io/123"

    @patch("app.main.settings")
    def test_handles_import_error_gracefully(self, mock_settings):
        """ImportError when sentry_sdk is missing is swallowed with a warning."""
        mock_settings.sentry_dsn = "https://key@sentry.io/123"
        mock_settings.debug = False
        mock_settings.environment = "production"

        import builtins

        real_import = builtins.__import__

        def _block_sentry(name, *args, **kwargs):
            if "sentry_sdk" in name:
                raise ImportError("no module")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=_block_sentry):
            # Should not raise
            from app.main import init_error_monitoring

            init_error_monitoring()  # logs warning, returns cleanly


# ===========================================================================
# lifespan
# ===========================================================================


class TestLifespan:
    """Unit tests for the lifespan async context manager."""

    # Patches for forge-auth helpers imported locally inside lifespan() (S152 Week 2)
    # Must be patched at their source module paths, not app.main.
    _JWT_PATCHES = (
        "app.security.get_forge_auth_instance",
    )

    def _jwt_mock_stack(self):
        """Return a list of patch context managers for forge-auth helpers."""
        return [
            patch("app.security.get_forge_auth_instance", return_value=MagicMock()),
        ]

    @pytest.mark.asyncio
    async def test_happy_path_debug(self):
        """Lifespan yields without raising when DB is healthy (debug=True)."""
        mock_settings = _make_settings(debug=True)
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_job_queue = AsyncMock()
        mock_job_queue.init = AsyncMock()
        mock_job_queue.run_worker = AsyncMock()
        mock_job_queue.close = AsyncMock()

        with (
            patch("app.main.settings", mock_settings),
            patch("app.main.configure_logging"),
            patch("app.main.init_error_monitoring"),
            patch("app.main.check_db_connection", AsyncMock(return_value=True)),
            patch("app.main.close_db_connections", AsyncMock()),
            patch("app.main.seed_questions", AsyncMock()),
            patch("app.main.SessionLocal", return_value=mock_session_ctx),
            patch("app.security.get_forge_auth_instance", return_value=MagicMock()),
            patch("forge_shared.auth.dependencies.set_jwt_auth"),
            patch("redis.asyncio.from_url") as mock_redis_factory,
            patch("app.main.JobQueue", return_value=mock_job_queue),
        ):
            mock_redis_client = AsyncMock()
            mock_redis_factory.return_value = mock_redis_client

            from app.main import lifespan

            dummy_app = FastAPI()
            dummy_app.version = "0.1.0"

            # Should not raise
            async with lifespan(dummy_app):
                pass

    @pytest.mark.asyncio
    async def test_db_failure_raises_in_production(self):
        """Lifespan raises RuntimeError when DB is unreachable in production."""
        mock_settings = _make_settings(debug=False)

        with (
            patch("app.main.settings", mock_settings),
            patch("app.main.configure_logging"),
            patch("app.main.init_error_monitoring"),
            patch("app.main.check_db_connection", AsyncMock(return_value=False)),
            patch("app.main.close_db_connections", AsyncMock()),
            patch("app.security.get_forge_auth_instance", return_value=MagicMock()),
            patch("forge_shared.auth.dependencies.set_jwt_auth"),
        ):
            from app.main import lifespan

            dummy_app = FastAPI()
            dummy_app.version = "0.1.0"

            with pytest.raises(RuntimeError, match="database unreachable"):
                async with lifespan(dummy_app):
                    pass

    @pytest.mark.asyncio
    async def test_validation_error_suppressed_in_debug(self):
        """Lifespan does not re-raise ValueError from validate_for_production in debug."""
        mock_settings = _make_settings(debug=True)
        mock_settings.validate_for_production.side_effect = ValueError("bad config")

        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_job_queue = AsyncMock()
        mock_job_queue.init = AsyncMock()
        mock_job_queue.run_worker = AsyncMock()
        mock_job_queue.close = AsyncMock()

        with (
            patch("app.main.settings", mock_settings),
            patch("app.main.configure_logging"),
            patch("app.main.init_error_monitoring"),
            patch("app.main.check_db_connection", AsyncMock(return_value=True)),
            patch("app.main.close_db_connections", AsyncMock()),
            patch("app.main.seed_questions", AsyncMock()),
            patch("app.main.SessionLocal", return_value=mock_session_ctx),
            patch("app.security.get_forge_auth_instance", return_value=MagicMock()),
            patch("forge_shared.auth.dependencies.set_jwt_auth"),
            patch("redis.asyncio.from_url") as mock_redis_factory,
            patch("app.main.JobQueue", return_value=mock_job_queue),
        ):
            mock_redis_client = AsyncMock()
            mock_redis_factory.return_value = mock_redis_client

            from app.main import lifespan

            dummy_app = FastAPI()
            dummy_app.version = "0.1.0"

            # ValueError must NOT propagate in debug mode
            async with lifespan(dummy_app):
                pass

    @pytest.mark.asyncio
    async def test_seed_questions_called_in_debug(self):
        """seed_questions() is invoked during startup when debug=True."""
        mock_settings = _make_settings(debug=True)
        mock_seed = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_job_queue = AsyncMock()
        mock_job_queue.init = AsyncMock()
        mock_job_queue.run_worker = AsyncMock()
        mock_job_queue.close = AsyncMock()

        with (
            patch("app.main.settings", mock_settings),
            patch("app.main.configure_logging"),
            patch("app.main.init_error_monitoring"),
            patch("app.main.check_db_connection", AsyncMock(return_value=True)),
            patch("app.main.close_db_connections", AsyncMock()),
            patch("app.main.seed_questions", mock_seed),
            patch("app.main.SessionLocal", return_value=mock_session_ctx),
            patch("app.security.get_forge_auth_instance", return_value=MagicMock()),
            patch("forge_shared.auth.dependencies.set_jwt_auth"),
            patch("redis.asyncio.from_url") as mock_redis_factory,
            patch("app.main.JobQueue", return_value=mock_job_queue),
        ):
            mock_redis_client = AsyncMock()
            mock_redis_factory.return_value = mock_redis_client

            from app.main import lifespan

            dummy_app = FastAPI()
            dummy_app.version = "0.1.0"

            async with lifespan(dummy_app):
                pass

        mock_seed.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_seed_questions_not_called_in_production(self):
        """seed_questions() is NOT called in production (debug=False)."""
        mock_settings = _make_settings(debug=False)
        mock_seed = AsyncMock()

        mock_job_queue = AsyncMock()
        mock_job_queue.init = AsyncMock()
        mock_job_queue.run_worker = AsyncMock()
        mock_job_queue.close = AsyncMock()

        with (
            patch("app.main.settings", mock_settings),
            patch("app.main.configure_logging"),
            patch("app.main.init_error_monitoring"),
            patch("app.main.check_db_connection", AsyncMock(return_value=True)),
            patch("app.main.close_db_connections", AsyncMock()),
            patch("app.main.seed_questions", mock_seed),
            patch("app.security.get_forge_auth_instance", return_value=MagicMock()),
            patch("forge_shared.auth.dependencies.set_jwt_auth"),
            patch("redis.asyncio.from_url") as mock_redis_factory,
            patch("app.main.JobQueue", return_value=mock_job_queue),
        ):
            mock_redis_client = AsyncMock()
            mock_redis_factory.return_value = mock_redis_client

            from app.main import lifespan

            dummy_app = FastAPI()
            dummy_app.version = "0.1.0"

            async with lifespan(dummy_app):
                pass

        mock_seed.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_close_db_called_on_shutdown(self):
        """close_db_connections() is awaited on shutdown."""
        mock_settings = _make_settings(debug=True)
        mock_close = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_job_queue = AsyncMock()
        mock_job_queue.init = AsyncMock()
        mock_job_queue.run_worker = AsyncMock()
        mock_job_queue.close = AsyncMock()

        with (
            patch("app.main.settings", mock_settings),
            patch("app.main.configure_logging"),
            patch("app.main.init_error_monitoring"),
            patch("app.main.check_db_connection", AsyncMock(return_value=True)),
            patch("app.main.close_db_connections", mock_close),
            patch("app.main.seed_questions", AsyncMock()),
            patch("app.main.SessionLocal", return_value=mock_session_ctx),
            patch("app.security.get_forge_auth_instance", return_value=MagicMock()),
            patch("forge_shared.auth.dependencies.set_jwt_auth"),
            patch("redis.asyncio.from_url") as mock_redis_factory,
            patch("app.main.JobQueue", return_value=mock_job_queue),
        ):
            mock_redis_client = AsyncMock()
            mock_redis_factory.return_value = mock_redis_client

            from app.main import lifespan

            dummy_app = FastAPI()
            dummy_app.version = "0.1.0"

            async with lifespan(dummy_app):
                pass

        mock_close.assert_awaited_once()


# ===========================================================================
# custom_openapi
# ===========================================================================


class TestCustomOpenAPI:
    """Unit tests for the custom_openapi() schema builder."""

    def _fresh_app_with_custom_openapi(self):
        """Import app module and return app + custom_openapi as fresh references."""
        from app.main import app, custom_openapi

        # Reset cached schema so tests are independent
        app.openapi_schema = None
        return app, custom_openapi

    def test_schema_contains_bearer_auth_scheme(self):
        """Generated schema includes BearerAuth securityScheme."""
        app, custom_openapi = self._fresh_app_with_custom_openapi()
        schema = custom_openapi()
        schemes = schema.get("components", {}).get("securitySchemes", {})
        assert "BearerAuth" in schemes
        assert schemes["BearerAuth"]["scheme"] == "bearer"
        assert schemes["BearerAuth"]["bearerFormat"] == "JWT"

    def test_schema_is_cached_on_second_call(self):
        """Calling custom_openapi() twice returns the same object (cached)."""
        app, custom_openapi = self._fresh_app_with_custom_openapi()
        first = custom_openapi()
        second = custom_openapi()
        assert first is second

    def test_schema_title_matches_app(self):
        """Schema title matches the FastAPI app title."""
        app, custom_openapi = self._fresh_app_with_custom_openapi()
        app.openapi_schema = None
        schema = custom_openapi()
        assert schema["info"]["title"] == app.title

    def test_schema_version_matches_app(self):
        """Schema version matches the FastAPI app version."""
        app, custom_openapi = self._fresh_app_with_custom_openapi()
        app.openapi_schema = None
        schema = custom_openapi()
        assert schema["info"]["version"] == app.version


# ===========================================================================
# app_error_handler
# ===========================================================================


class TestAppErrorHandler:
    """Unit tests for the AppError exception handler."""

    @pytest.mark.asyncio
    async def test_returns_json_response_with_correct_status(self):
        """Handler maps AppError.status_code to HTTP response status."""
        from app.exceptions import AppError, ErrorCode
        from app.main import app_error_handler

        exc = AppError(
            error_code=ErrorCode.NOT_FOUND,
            message="Thing not found",
            status_code=404,
        )
        request = MagicMock()
        response = await app_error_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_error_body_from_to_dict(self):
        """Response body matches AppError.to_dict() serialisation."""
        import json

        from app.exceptions import AppError, ErrorCode
        from app.main import app_error_handler

        exc = AppError(
            error_code=ErrorCode.QUOTA_EXCEEDED,
            message="Limit reached",
            status_code=403,
            details={"limit": 5},
        )
        request = MagicMock()
        response = await app_error_handler(request, exc)
        body = json.loads(response.body)

        assert body["error"]["code"] == "quota_exceeded"
        assert body["error"]["message"] == "Limit reached"
        assert body["error"]["details"] == {"limit": 5}

    @pytest.mark.asyncio
    async def test_handler_for_auth_error(self):
        """AuthRequiredError (401) is handled with correct status code."""
        from app.exceptions import AuthRequiredError
        from app.main import app_error_handler

        exc = AuthRequiredError()
        request = MagicMock()
        response = await app_error_handler(request, exc)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_handler_for_rate_limited_error(self):
        """RateLimitedError (429) is handled with correct status code."""
        from app.exceptions import RateLimitedError
        from app.main import app_error_handler

        exc = RateLimitedError(retry_after=30)
        request = MagicMock()
        response = await app_error_handler(request, exc)
        assert response.status_code == 429


# ===========================================================================
# root endpoint
# ===========================================================================


class TestRootEndpoint:
    """Unit tests for the GET / endpoint."""

    @pytest.fixture(autouse=True)
    def mock_lifespan_deps(self):
        """Mock lifespan dependencies so tests don't require database."""
        with (
            patch("app.main.check_db_connection", AsyncMock(return_value=True)),
            patch("app.main.close_db_connections", AsyncMock()),
            patch("app.main.seed_questions", AsyncMock()),
            patch("app.main.configure_logging"),
            patch("app.main.init_error_monitoring"),
            patch("app.security.get_forge_auth_instance", return_value=MagicMock()),
            patch("forge_shared.auth.dependencies.set_jwt_auth"),
            patch("redis.asyncio.from_url") as mock_redis,
        ):
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            yield

    def test_root_returns_200(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/")
        assert response.status_code == 200

    def test_root_payload_has_name(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        data = client.get("/").json()
        assert "name" in data
        assert data["name"] == "CareerSwiftr Interview Simulator"

    def test_root_payload_has_version(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        data = client.get("/").json()
        assert "version" in data

    def test_root_payload_has_docs_key(self):
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        data = client.get("/").json()
        assert "docs" in data


# ===========================================================================
# Middleware registration
# ===========================================================================


class TestMiddlewareRegistration:
    """Verify that all required middleware classes are in the middleware stack."""

    def _middleware_types(self):
        from app.main import app

        # Collect all middleware type names from the stack
        types = set()
        for middleware in app.user_middleware:
            cls = getattr(middleware, "cls", None)
            if cls is not None:
                types.add(cls.__name__)
        # Also check middleware_stack attribute when present
        return types

    def test_cors_middleware_registered(self):
        """CORSMiddleware must be present in the middleware stack."""
        types = self._middleware_types()
        assert "CORSMiddleware" in types

    def test_security_middleware_registered(self):
        """SecurityMiddleware (forge-shared) must be in the middleware stack."""
        types = self._middleware_types()
        assert "SecurityMiddleware" in types

    def test_utm_middleware_registered(self):
        """UTMMiddleware (forge-shared) must be in the middleware stack."""
        types = self._middleware_types()
        assert "UTMMiddleware" in types

    def test_request_id_middleware_registered(self):
        """RequestIDMiddleware (forge-shared) must be in the middleware stack."""
        types = self._middleware_types()
        assert "RequestIDMiddleware" in types


# ===========================================================================
# Static file mount
# ===========================================================================


class TestStaticFiles:
    """Verify that the /uploads static mount is present."""

    def test_uploads_mount_exists(self):
        """App must expose a StaticFiles mount at /uploads."""
        from app.main import app

        mounts = {r.path: r for r in app.routes if hasattr(r, "path")}
        assert "/uploads" in mounts

    def test_uploads_mount_is_staticfiles(self):
        """The /uploads route must wrap a StaticFiles application."""
        from fastapi.staticfiles import StaticFiles
        from starlette.routing import Mount

        from app.main import app

        upload_mount = next(
            (r for r in app.routes if isinstance(r, Mount) and r.path == "/uploads"),
            None,
        )
        assert upload_mount is not None
        assert isinstance(upload_mount.app, StaticFiles)


# ===========================================================================
# Router inclusion
# ===========================================================================


class TestRouterInclusion:
    """Smoke-test that critical routers are attached to the app."""

    def _route_paths(self):
        from app.main import app

        paths = set()
        for route in app.routes:
            if hasattr(route, "path"):
                paths.add(route.path)
        return paths

    def test_health_router_included(self):
        """A /health route must exist."""
        paths = self._route_paths()
        assert any("health" in p for p in paths)

    def test_auth_router_included(self):
        """Routes under /api/v1/auth must exist."""
        paths = self._route_paths()
        assert any("/api/v1/auth" in p for p in paths)

    def test_users_router_included(self):
        """Routes under /api/v1/users must exist."""
        paths = self._route_paths()
        assert any("/api/v1/users" in p for p in paths)

    def test_interviews_router_included(self):
        """Routes under /api/v1/interviews must exist."""
        paths = self._route_paths()
        assert any("/api/v1/interviews" in p for p in paths)
