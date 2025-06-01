from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import logging
from typing import Optional, Dict, Union
from datetime import datetime, UTC

from ..service.compression_service import CompressionService
from ..service.settings_service import SettingsService

logger = logging.getLogger(__name__)

class CompressionMiddleware:
    def __init__(self):
        self.compression_service = CompressionService()
        self.settings_service = SettingsService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        CompressionMiddleware initialized:
        Time: 2025-05-30 14:53:16
        User: fdygg
        """)

    async def __call__(self, request: Request, call_next):
        try:
            # Get compression settings
            settings = await self.settings_service.get_compression_settings()
            if not settings:
                settings = self.compression_service.DEFAULT_SETTINGS

            # Process request
            response = await call_next(request)

            # Skip compression for streaming responses
            if isinstance(response, StreamingResponse):
                return response

            # Get response content
            if isinstance(response, JSONResponse):
                content = response.body
                content_type = response.media_type
            else:
                content = await self._get_response_content(response)
                content_type = response.headers.get("content-type", "")

            content_length = len(content)

            # Check if compression should be applied
            if not self.compression_service.should_compress(
                content_type,
                content_length,
                settings
            ):
                return response

            # Get accepted encodings
            accept_encoding = request.headers.get("accept-encoding", "")
            encoding = self.compression_service.get_best_encoding(accept_encoding)

            if not encoding:
                return response

            # Compress content
            compressed_content, compressed_length = \
                self.compression_service.compress_data(
                    content,
                    encoding,
                    settings
                )

            # Skip if compression didn't help
            if compressed_length >= content_length:
                return response

            # Create new response with compressed content
            new_response = Response(
                content=compressed_content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=content_type
            )

            # Add compression headers
            new_response.headers["Content-Encoding"] = encoding
            new_response.headers["Content-Length"] = str(compressed_length)
            new_response.headers["Vary"] = "Accept-Encoding"

            # Add debug headers
            new_response.headers["X-Compression-Ratio"] = \
                f"{(1 - compressed_length/content_length):.2%}"
            new_response.headers["X-Compression-Algorithm"] = encoding

            return new_response

        except Exception as e:
            logger.error(f"""
            Compression middleware error:
            Error: {str(e)}
            Time: 2025-05-30 14:53:16
            User: fdygg
            Path: {request.url.path}
            """)
            return await call_next(request)

    async def _get_response_content(self, response: Response) -> bytes:
        """Get response content as bytes"""
        if isinstance(response.body, bytes):
            return response.body
        elif isinstance(response.body, str):
            return response.body.encode('utf-8')
        else:
            return str(response.body).encode('utf-8')

    async def _should_skip_compression(
        self,
        request: Request,
        response: Response
    ) -> bool:
        """Check if compression should be skipped"""
        # Skip if already compressed
        if "Content-Encoding" in response.headers:
            return True

        # Skip for small responses
        try:
            content_length = int(response.headers.get("content-length", 0))
            if content_length < 1024:  # Skip if < 1KB
                return True
        except:
            pass

        # Skip for specific paths
        skip_paths = ["/static/", "/media/", "/download/"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return True

        return False