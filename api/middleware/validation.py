from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, UTC
import logging
from typing import Optional, Dict, Any, List
from uuid import uuid4

from ..service.validation_service import ValidationService
from ..service.error_handling_service import ErrorHandlingService
from ..models.validation import ValidationRule, ValidationError
from ..models.error import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)

class ValidationMiddleware:
    def __init__(self):
        self.validation_service = ValidationService()
        self.error_handler = ErrorHandlingService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        ValidationMiddleware initialized:
        Time: 2025-05-30 14:48:30
        User: fdygg
        """)

    async def get_request_metadata(self, request: Request) -> Dict[str, Any]:
        """Get metadata from request"""
        return {
            "user_agent": request.headers.get("user-agent", ""),
            "ip_address": request.client.host,
            "platform": request.headers.get("x-platform", "web"),
            "app_version": request.headers.get("x-app-version", ""),
            "device_id": request.headers.get("x-device-id", "")
        }

    async def get_validation_context(self, request: Request) -> Dict[str, Any]:
        """Get validation context from request"""
        platform = request.headers.get("x-platform", "web")
        role = getattr(request.state, "user_role", None)
        user_id = getattr(request.state, "user_id", None)
        
        return {
            "platform": platform,
            "role": role,
            "user_id": user_id,
            "method": request.method,
            "path": request.url.path
        }

    async def validate_request_data(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate request data"""
        # Get validation rules
        rules = await self.validation_service.get_validation_rules(
            platform=context.get("platform"),
            role=context.get("role")
        )
        
        # Validate data against rules
        return await self.validation_service.validate_data(
            data=data,
            rules=rules,
            platform=context.get("platform"),
            role=context.get("role")
        )

    async def format_validation_errors(
        self,
        errors: List[ValidationError],
        request: Request,
        context: Dict[str, Any]
    ) -> ErrorResponse:
        """Format validation errors into response"""
        return ErrorResponse(
            status=422,
            type="ValidationError",
            message="Request validation failed",
            details=[
                ErrorDetail(
                    field=error.field,
                    message=error.message,
                    code=error.code,
                    value=error.value
                ) for error in errors
            ],
            timestamp=datetime.now(UTC),
            request_id=str(uuid4()),
            path=request.url.path,
            metadata={
                **await self.get_request_metadata(request),
                **context
            }
        )

    async def __call__(self, request: Request, call_next):
        try:
            # Skip validation for certain methods/paths
            if request.method in ["GET", "HEAD", "OPTIONS"] or \
               request.url.path.startswith(("/static/", "/docs/", "/redoc/")):
                return await call_next(request)

            # Get validation context
            context = await self.get_validation_context(request)

            # Get request body
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    data = await request.json()
                except Exception as e:
                    return JSONResponse(
                        status_code=400,
                        content=ErrorResponse(
                            status=400,
                            type="InvalidJSON",
                            message="Invalid JSON in request body",
                            details=[
                                ErrorDetail(
                                    message=str(e),
                                    code="INVALID_JSON"
                                )
                            ],
                            timestamp=datetime.now(UTC),
                            request_id=str(uuid4()),
                            path=request.url.path,
                            metadata=await self.get_request_metadata(request)
                        ).dict()
                    )

                # Validate request data
                errors = await self.validate_request_data(data, context)
                if errors:
                    return JSONResponse(
                        status_code=422,
                        content=(
                            await self.format_validation_errors(
                                errors,
                                request,
                                context
                            )
                        ).dict()
                    )

            # Process request if validation passes
            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"""
            Validation middleware error:
            Error: {str(e)}
            Time: 2025-05-30 14:48:30
            User: fdygg
            Path: {request.url.path}
            """)
            
            # Handle error
            return await self.error_handler.handle_error(
                request=request,
                exc=e,
                metadata={
                    **await self.get_request_metadata(request),
                    **await self.get_validation_context(request)
                }
            )

    async def validate_response_data(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate response data (optional)"""
        # Similar to validate_request_data but for response
        # This is optional and can be implemented if needed
        return []

    async def handle_validation_exception(
        self,
        request: Request,
        exc: Exception,
        context: Dict[str, Any]
    ) -> Response:
        """Handle validation specific exceptions"""
        error_response = ErrorResponse(
            status=422,
            type="ValidationException",
            message=str(exc),
            details=[
                ErrorDetail(
                    message=str(exc),
                    code="VALIDATION_EXCEPTION"
                )
            ],
            timestamp=datetime.now(UTC),
            request_id=str(uuid4()),
            path=request.url.path,
            metadata={
                **await self.get_request_metadata(request),
                **context
            }
        )
        
        return JSONResponse(
            status_code=422,
            content=error_response.dict()
        )