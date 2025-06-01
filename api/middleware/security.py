from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, UTC
from typing import Optional, Dict, List, Any
import re
import ipaddress
from uuid import uuid4

from ..service.auth_service import AuthService
from ..models.user import UserType, UserRole, UserStatus
from ..models.auth import TokenData

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    def __init__(self):
        self.auth_service = AuthService()
        self.startup_time = datetime.now(UTC)
        
        # Security settings
        self.MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
        self.ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
        self.TRUSTED_PROXIES = ["127.0.0.1"]
        self.BLOCKED_IPS = set()
        self.RATE_LIMIT = 100  # requests per minute
        self.RATE_LIMIT_WINDOW = 60  # seconds
        
        # Rate limiting storage
        self.rate_limit_data = {}
        
        # CORS settings
        self.ALLOWED_ORIGINS = ["http://localhost:3000"]
        self.ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.ALLOWED_HEADERS = [
            "Authorization", "Content-Type", "X-Request-ID",
            "X-Platform", "X-App-Version", "X-Device-ID"
        ]
        
        # Security headers
        self.SECURITY_HEADERS = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": self._generate_csp(),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache"
        }
        
        logger.info(f"""
        SecurityMiddleware initialized:
        Time: 2025-05-30 15:04:48
        User: fdygg
        """)

    def _generate_csp(self) -> str:
        """Generate Content Security Policy"""
        policies = [
            "default-src 'self'",
            "img-src 'self' data: https:",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "font-src 'self' data:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        return "; ".join(policies)

    async def _validate_token(
        self,
        request: Request
    ) -> Tuple[bool, Optional[TokenData], str]:
        """Validate JWT token from request"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return False, None, "No authorization header"
            
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return False, None, "Invalid authentication scheme"
                
            is_valid, token_data = await self.auth_service.verify_token(token)
            if not is_valid or not token_data:
                return False, None, "Invalid or expired token"
                
            return True, token_data, ""
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return False, None, "Token validation failed"

    def _check_rate_limit(self, ip: str) -> Tuple[bool, Dict]:
        """Check rate limit for IP"""
        now = datetime.now(UTC).timestamp()
        
        # Initialize or cleanup old data
        if ip not in self.rate_limit_data:
            self.rate_limit_data[ip] = {
                "count": 0,
                "window_start": now
            }
        elif now - self.rate_limit_data[ip]["window_start"] >= self.RATE_LIMIT_WINDOW:
            self.rate_limit_data[ip] = {
                "count": 0,
                "window_start": now
            }
            
        # Update request count
        self.rate_limit_data[ip]["count"] += 1
        
        # Calculate remaining
        remaining = max(0, self.RATE_LIMIT - self.rate_limit_data[ip]["count"])
        reset = self.RATE_LIMIT_WINDOW - (now - self.rate_limit_data[ip]["window_start"])
        
        return (
            self.rate_limit_data[ip]["count"] <= self.RATE_LIMIT,
            {
                "X-RateLimit-Limit": str(self.RATE_LIMIT),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(reset))
            }
        )

    def _is_valid_host(self, host: str) -> bool:
        """Validate Host header"""
        return host in self.ALLOWED_HOSTS

    def _is_trusted_proxy(self, ip: str) -> bool:
        """Check if IP is trusted proxy"""
        return ip in self.TRUSTED_PROXIES

    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP considering proxy headers"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        
        if forwarded_for and self._is_trusted_proxy(request.client.host):
            # Get the first IP in X-Forwarded-For chain
            return forwarded_for.split(",")[0].strip()
            
        return request.client.host

    def _validate_content_length(self, request: Request) -> bool:
        """Validate request content length"""
        try:
            content_length = int(request.headers.get("content-length", 0))
            return content_length <= self.MAX_CONTENT_LENGTH
        except:
            return True

    def _validate_content_type(self, request: Request) -> bool:
        """Validate Content-Type header"""
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            return (
                "application/json" in content_type or
                "multipart/form-data" in content_type or
                "application/x-www-form-urlencoded" in content_type
            )
        return True

    async def _handle_cors(
        self,
        request: Request,
        response: Response
    ) -> Optional[Response]:
        """Handle CORS preflight and headers"""
        origin = request.headers.get("Origin")
        
        # Handle preflight
        if request.method == "OPTIONS":
            if not origin or origin not in self.ALLOWED_ORIGINS:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CORS forbidden"}
                )
                
            response = Response(status_code=204)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.ALLOWED_METHODS)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.ALLOWED_HEADERS)
            response.headers["Access-Control-Max-Age"] = "3600"
            return response
            
        # Handle actual request
        if origin and origin in self.ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            
        return None

    async def __call__(self, request: Request, call_next):
        try:
            # Generate request ID
            request.state.request_id = str(uuid4())
            
            # Validate host
            host = request.headers.get("host", "").split(":")[0]
            if not self._is_valid_host(host):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid host"}
                )

            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Check blocked IPs
            if client_ip in self.BLOCKED_IPS:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "IP address blocked"}
                )

            # Check rate limit
            is_allowed, rate_limit_headers = self._check_rate_limit(client_ip)
            if not is_allowed:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"}
                )
                response.headers.update(rate_limit_headers)
                return response

            # Handle CORS
            cors_response = await self._handle_cors(request, response)
            if cors_response:
                return cors_response

            # Validate content length
            if not self._validate_content_length(request):
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Content too large"}
                )

            # Validate content type
            if not self._validate_content_type(request):
                return JSONResponse(
                    status_code=415,
                    content={"detail": "Unsupported media type"}
                )

            # Validate authentication for protected routes
            if self._requires_auth(request.url.path, request.method):
                is_valid, token_data, error = await self._validate_token(request)
                if not is_valid:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": error}
                    )
                    
                # Set user data in request state
                request.state.user = token_data

            # Process request
            response = await call_next(request)

            # Add security headers
            response.headers.update(self.SECURITY_HEADERS)
            response.headers.update(rate_limit_headers)
            response.headers["X-Request-ID"] = request.state.request_id

            return response

        except Exception as e:
            logger.error(f"""
            Security middleware error:
            Error: {str(e)}
            Time: 2025-05-30 15:04:48
            User: fdygg
            Path: {request.url.path}
            """)
            
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

    def _requires_auth(self, path: str, method: str) -> bool:
        """Check if route requires authentication"""
        # Public routes
        public_paths = [
            r"^/docs",
            r"^/redoc",
            r"^/openapi.json",
            r"^/auth/login",
            r"^/auth/register",
            r"^/public"
        ]
        
        for pattern in public_paths:
            if re.match(pattern, path):
                return False
                
        return True

    async def block_ip(self, ip: str, reason: str) -> bool:
        """Block an IP address"""
        try:
            # Validate IP
            ipaddress.ip_address(ip)
            self.BLOCKED_IPS.add(ip)
            
            logger.warning(f"""
            IP blocked:
            IP: {ip}
            Reason: {reason}
            Time: 2025-05-30 15:04:48
            User: fdygg
            """)
            
            return True
            
        except Exception as e:
            logger.error(f"Error blocking IP {ip}: {str(e)}")
            return False

    async def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address"""
        try:
            self.BLOCKED_IPS.discard(ip)
            
            logger.info(f"""
            IP unblocked:
            IP: {ip}
            Time: 2025-05-30 15:04:48
            User: fdygg
            """)
            
            return True
            
        except Exception as e:
            logger.error(f"Error unblocking IP {ip}: {str(e)}")
            return False