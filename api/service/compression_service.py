from typing import Dict, Optional, Union, List
import gzip
import brotli
import zlib
import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

class CompressionService:
    def __init__(self):
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        CompressionService initialized:
        Time: 2025-05-30 14:53:16
        User: fdygg
        """)
        
        # Default settings
        self.DEFAULT_SETTINGS = {
            "gzip": {
                "enabled": True,
                "level": 6,  # 1-9
                "min_size": 1024,  # bytes
                "types": [
                    "text/plain",
                    "text/html",
                    "text/css",
                    "text/javascript",
                    "application/javascript",
                    "application/json",
                    "application/xml",
                    "image/svg+xml"
                ]
            },
            "brotli": {
                "enabled": True,
                "quality": 4,  # 0-11
                "min_size": 1024,
                "types": [
                    "text/plain",
                    "text/html",
                    "text/css",
                    "text/javascript",
                    "application/javascript",
                    "application/json",
                    "application/xml",
                    "image/svg+xml"
                ]
            },
            "deflate": {
                "enabled": True,
                "level": 6,  # 1-9
                "min_size": 1024,
                "types": [
                    "text/plain",
                    "text/html",
                    "text/css",
                    "text/javascript",
                    "application/javascript",
                    "application/json",
                    "application/xml",
                    "image/svg+xml"
                ]
            }
        }

    def should_compress(
        self,
        content_type: str,
        content_length: int,
        settings: Optional[Dict] = None
    ) -> bool:
        """Check if content should be compressed"""
        if not settings:
            settings = self.DEFAULT_SETTINGS
            
        # Skip compression for small content
        min_size = min(
            settings["gzip"]["min_size"],
            settings["brotli"]["min_size"],
            settings["deflate"]["min_size"]
        )
        if content_length < min_size:
            return False

        # Check content type
        for algorithm in ["gzip", "brotli", "deflate"]:
            if settings[algorithm]["enabled"]:
                if any(t in content_type for t in settings[algorithm]["types"]):
                    return True
                    
        return False

    def compress_data(
        self,
        data: Union[str, bytes],
        encoding: str,
        settings: Optional[Dict] = None
    ) -> Tuple[bytes, int]:
        """Compress data using specified encoding"""
        if not settings:
            settings = self.DEFAULT_SETTINGS
            
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        try:
            if encoding == "gzip":
                return self._gzip_compress(data, settings["gzip"]["level"])
                
            elif encoding == "br":
                return self._brotli_compress(data, settings["brotli"]["quality"])
                
            elif encoding == "deflate":
                return self._deflate_compress(data, settings["deflate"]["level"])
                
            else:
                logger.warning(f"Unsupported encoding: {encoding}")
                return data, len(data)
                
        except Exception as e:
            logger.error(f"Compression error: {str(e)}")
            return data, len(data)

    def _gzip_compress(self, data: bytes, level: int) -> Tuple[bytes, int]:
        """Compress data using gzip"""
        try:
            compressed = gzip.compress(data, level)
            return compressed, len(compressed)
        except Exception as e:
            logger.error(f"Gzip compression error: {str(e)}")
            return data, len(data)

    def _brotli_compress(self, data: bytes, quality: int) -> Tuple[bytes, int]:
        """Compress data using brotli"""
        try:
            compressed = brotli.compress(data, quality=quality)
            return compressed, len(compressed)
        except Exception as e:
            logger.error(f"Brotli compression error: {str(e)}")
            return data, len(data)

    def _deflate_compress(self, data: bytes, level: int) -> Tuple[bytes, int]:
        """Compress data using deflate"""
        try:
            compressed = zlib.compress(data, level)
            return compressed, len(compressed)
        except Exception as e:
            logger.error(f"Deflate compression error: {str(e)}")
            return data, len(data)

    def get_accepted_encodings(self, accept_encoding: str) -> List[str]:
        """Parse Accept-Encoding header and return supported encodings"""
        supported = {
            "gzip": self.DEFAULT_SETTINGS["gzip"]["enabled"],
            "br": self.DEFAULT_SETTINGS["brotli"]["enabled"],
            "deflate": self.DEFAULT_SETTINGS["deflate"]["enabled"]
        }
        
        if not accept_encoding:
            return []
            
        accepted = []
        for encoding in accept_encoding.split(","):
            encoding = encoding.strip().split(";")[0]
            if encoding in supported and supported[encoding]:
                accepted.append(encoding)
                
        return accepted

    def get_best_encoding(self, accept_encoding: str) -> Optional[str]:
        """Get best compression encoding based on Accept-Encoding header"""
        encodings = self.get_accepted_encodings(accept_encoding)
        
        # Prefer Brotli > Gzip > Deflate
        if "br" in encodings and self.DEFAULT_SETTINGS["brotli"]["enabled"]:
            return "br"
        elif "gzip" in encodings and self.DEFAULT_SETTINGS["gzip"]["enabled"]:
            return "gzip"
        elif "deflate" in encodings and self.DEFAULT_SETTINGS["deflate"]["enabled"]:
            return "deflate"
            
        return None