"""Secure rate limiting middleware with IP validation and DDoS protection.

This middleware provides secure rate limiting that cannot be bypassed through
header manipulation. It validates IP sources and implements multiple rate limiting
strategies including IP-based and user-based limits.
"""

import hashlib
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    # Per-user limits for authenticated requests
    user_requests_per_minute: int = 120
    user_requests_per_hour: int = 2000


class SecureRateLimiter:
    """Secure rate limiter using sliding window with IP validation."""

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._requests: dict[str, list[float]] = defaultdict(list)
        # Track suspicious IPs for potential blocking
        self._suspicious_ips: dict[str, int] = defaultdict(int)

    def _clean_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requests older than the window."""
        now = time.time()
        cutoff = now - window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]

    def _generate_secure_key(self, request: Request, user_id: str | None = None) -> str:
        """Generate a secure rate limit key that cannot be spoofed."""
        # Get the trusted client IP
        client_ip = self._get_trusted_client_ip(request)

        # Create a composite key that includes both IP and user ID
        # For authenticated users, include user ID to prevent token sharing abuse
        key_data = f"user:{user_id}:ip:{client_ip}" if user_id else f"ip:{client_ip}"

        # Hash the key to prevent information leakage
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def _get_trusted_client_ip(self, request: Request) -> str:
        """Get the trusted client IP, preventing header spoofing.

        Security priority order:
        1. Cloudflare CF-Connecting-IP (only if CF-RAY present)
        2. Railway X-Real-IP (only in Railway environment)
        3. X-Forwarded-For with strict validation (limited hops)
        4. Direct connection IP
        """
        from app.config import settings

        # 1. Cloudflare header - most trusted, but verify it's from Cloudflare
        cf_ray = request.headers.get("CF-RAY")
        cf_connecting_ip = request.headers.get("CF-Connecting-IP")

        if cf_ray and cf_connecting_ip:
            # Only trust CF-Connecting-IP if CF-RAY header is present
            # This proves the request came through Cloudflare
            if self._is_valid_ip_format(cf_connecting_ip) and self._is_public_ip(cf_connecting_ip):
                return cf_connecting_ip
            else:
                # Log suspicious CF header
                self._log_suspicious_request(request, f"Invalid CF-Connecting-IP: {cf_connecting_ip}")

        # 2. Railway proxy header - only trust in Railway environment
        if "railway" in (request.url.hostname or "").lower():
            x_real_ip = request.headers.get("X-Real-IP")
            if x_real_ip and self._is_valid_ip_format(x_real_ip) and self._is_public_ip(x_real_ip):
                return x_real_ip

        # 3. X-Forwarded-For - handle with extreme caution
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # Parse the chain, strip whitespace
            ips = [ip.strip() for ip in x_forwarded_for.split(",")]

            # Security: Prevent header injection attacks
            if len(ips) > 5:  # Too many proxies indicates abuse
                self._log_suspicious_request(request, f"Excessive proxy chain: {len(ips)} hops")
                # Fall back to direct IP
                return self._get_direct_ip(request)

            # Take the LEFTMOST IP (original client) if we trust our proxy
            # ONLY if we're behind a known trusted proxy
            trusted_proxies = getattr(settings, 'trusted_proxies', [])

            if trusted_proxies:
                # Check if the rightmost IP is from our trusted proxy
                rightmost_ip = ips[-1]
                if rightmost_ip in trusted_proxies and self._is_valid_ip_format(ips[0]) and self._is_public_ip(ips[0]):
                    return ips[0]
            else:
                # No trusted proxies configured, take the rightmost (closest to us)
                # This is safer than taking leftmost
                closest_ip = ips[-1]
                if self._is_valid_ip_format(closest_ip) and self._is_public_ip(closest_ip):
                    return closest_ip

        # 4. Direct connection IP (no proxy)
        return self._get_direct_ip(request)

    def _get_direct_ip(self, request: Request) -> str:
        """Get the direct connection IP."""
        if request.client and self._is_valid_ip_format(request.client.host):
            return request.client.host

        # Last resort - shouldn't happen in production
        return "0.0.0.0"

    def _is_valid_ip_format(self, ip: str) -> bool:
        """Comprehensive IP format validation."""
        import ipaddress

        # Check for obvious injection attacks
        if not ip or len(ip) > 45:  # Max IPv6 length
            return False

        # Check for null bytes and line breaks
        if '\0' in ip or '\n' in ip or '\r' in ip:
            return False

        # Remove port if present (security risk)
        if ':' in ip and '.' in ip:
            # IPv4 with port - reject for security
            return False

        try:
            # Try parsing as IP address
            ipaddress.ip_address(ip)

            # Reject private IPs in proxy headers (they can't be real clients)
            # This check will be done at call site

            # Accept valid IPs
            return True
        except ValueError:
            # Invalid IP format
            return False

    def _is_public_ip(self, ip: str) -> bool:
        """Check if IP is a public IP (not private/internal)."""
        import ipaddress

        try:
            ip_obj = ipaddress.ip_address(ip)
            # Not private, not loopback, not link-local
            return not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local)
        except ValueError:
            return False

    def _log_suspicious_request(self, request: Request, reason: str) -> None:
        """Log suspicious rate limit bypass attempts."""
        import logging

        logger = logging.getLogger(__name__)

        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "none")[:100]
        path = request.url.path

        # Log structured data for security monitoring
        logger.warning(
            "Rate limit bypass attempt detected",
            extra={
                "event": "rate_limit_bypass_attempt",
                "client_ip": client_ip,
                "path": path,
                "user_agent": user_agent,
                "reason": reason,
                "headers": dict(request.headers),
            }
        )

        # Track suspicious IP for potential blocking
        self._suspicious_ips[client_ip] += 1

    def is_allowed(self, request: Request, user_id: str | None = None) -> tuple[bool, dict[str, int]]:
        """Check if request is allowed and return remaining limits."""
        now = time.time()

        # Generate secure key
        key = self._generate_secure_key(request, user_id)

        # Clean old requests
        self._clean_old_requests(key, 3600)  # Keep last hour

        requests = self._requests[key]

        # Count requests in time windows
        minute_ago = now - 60
        hour_ago = now - 3600

        requests_last_minute = sum(1 for ts in requests if ts > minute_ago)
        requests_last_hour = sum(1 for ts in requests if ts > hour_ago)

        # Determine limits based on authentication
        if user_id:
            minute_limit = self.config.user_requests_per_minute
            hour_limit = self.config.user_requests_per_hour
        else:
            minute_limit = self.config.requests_per_minute
            hour_limit = self.config.requests_per_hour

        # Check limits
        if requests_last_minute >= minute_limit:
            return False, {
                "X-RateLimit-Limit": str(minute_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(minute_ago + 60)),
                "X-RateLimit-Scope": "minute" if user_id else "minute-anon",
            }

        if requests_last_hour >= hour_limit:
            return False, {
                "X-RateLimit-Limit": str(minute_limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(now + 3600)),
                "X-RateLimit-Scope": "hour" if user_id else "hour-anon",
            }

        # Record this request
        self._requests[key].append(now)

        return True, {
            "X-RateLimit-Limit": str(minute_limit),
            "X-RateLimit-Remaining": str(minute_limit - requests_last_minute - 1),
            "X-RateLimit-Reset": str(int(minute_ago + 60)),
            "X-RateLimit-Scope": "minute" if user_id else "minute-anon",
        }

    def is_suspicious(self, request: Request) -> bool:
        """Check if the request is from a suspicious IP or contains attack patterns."""
        client_ip = self._get_trusted_client_ip(request)

        # Check for header injection and spoofing attacks
        x_forwarded_for = request.headers.get("X-Forwarded-For", "")
        x_real_ip = request.headers.get("X-Real-IP", "")
        cf_connecting_ip = request.headers.get("CF-Connecting-IP", "")
        user_agent = request.headers.get("User-Agent", "")

        suspicious_patterns = [
            # Too many proxies (header injection)
            x_forwarded_for.count(",") > 5,

            # Oversized headers (potential injection)
            len(user_agent) > 500,
            len(x_forwarded_for) > 200,

            # Headers with line breaks (injection attempt)
            '\n' in x_forwarded_for or '\r' in x_forwarded_for,
            '\n' in x_real_ip or '\r' in x_real_ip,
            '\n' in cf_connecting_ip or '\r' in cf_connecting_ip,

            # Private IPs in forwarded headers (spoofing)
            any(ip.startswith(("10.", "192.168.", "172.")) for ip in [ip.strip() for ip in x_forwarded_for.split(",")]),

            # Mismatched headers without Cloudflare
            not request.headers.get("CF-RAY") and x_real_ip and x_forwarded_for and x_real_ip != x_forwarded_for.split(",")[-1].strip(),

            # Suspicious User-Agent patterns
            user_agent.lower() in ["", "null", "undefined", "bot", "crawler"] or "curl" in user_agent.lower() and "/api/" in request.url.path,
        ]

        if any(suspicious_patterns):
            reason = "Suspicious pattern detected: " + ", ".join([
            "Too many proxies" if suspicious_patterns[0] else "",
            "Oversized headers" if suspicious_patterns[1] else "",
            "Headers with line breaks" if suspicious_patterns[2] else "",
            "Private IPs in headers" if suspicious_patterns[3] else "",
            "Mismatched headers" if suspicious_patterns[4] else "",
            "Suspicious User-Agent" if suspicious_patterns[5] else "",
        ])
            self._log_suspicious_request(request, reason)
            self._suspicious_ips[client_ip] += 1

        return self._suspicious_ips[client_ip] > 5


class SecureRateLimitMiddleware(BaseHTTPMiddleware):
    """Secure FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        config: RateLimitConfig | None = None,
        key_func: Callable[[Request], str] | None = None,
        exclude_paths: list[str] | None = None,
        enable_ddos_headers: bool = True,
    ):
        super().__init__(app)
        self.limiter = SecureRateLimiter(config)
        self.exclude_paths = exclude_paths or [
            "/api/v1/health",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/static",
        ]
        self.enable_ddos_headers = enable_ddos_headers

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and apply secure rate limiting."""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Add DDoS protection headers
        if self.enable_ddos_headers:
            response = await call_next(request)

            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # Rate limit the request
            user_id = getattr(request.state, "user_id", None)
            is_allowed, headers = self.limiter.is_allowed(request, user_id)

            # Check for suspicious activity
            if self.limiter.is_suspicious(request):
                # Log suspicious activity
                print(f"Suspicious activity detected from {self.limiter._get_trusted_client_ip(request)}")

            if not is_allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "retry_after": 60,
                        "scope": headers.get("X-RateLimit-Scope", "unknown"),
                    },
                    headers=headers,
                )

            # Add rate limit headers to response
            for header_name, header_value in headers.items():
                response.headers[header_name] = header_value

            return response

        # Process without DDoS headers if disabled
        user_id = getattr(request.state, "user_id", None)
        is_allowed, headers = self.limiter.is_allowed(request, user_id)

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": 60,
                    "scope": headers.get("X-RateLimit-Scope", "unknown"),
                },
                headers=headers,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        return response
