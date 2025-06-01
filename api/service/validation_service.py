from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, UTC
from ..models.validation import ValidationType, ValidationRule, ValidationError
from ..models.error import ErrorDetail
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class ValidationService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        ValidationService initialized:
        Time: 2025-05-30 14:46:52
        User: fdygg
        """)
        
    async def get_validation_rules(
        self,
        platform: Optional[str] = None,
        role: Optional[str] = None
    ) -> List[ValidationRule]:
        """Get validation rules from database"""
        try:
            query = """
            SELECT * FROM validation_rules 
            WHERE (platform IS NULL OR platform LIKE ?)
            AND (roles IS NULL OR roles LIKE ?)
            """
            
            platform_filter = f"%{platform}%" if platform else "%"
            role_filter = f"%{role}%" if role else "%"
            
            results = await self.db.execute_query(
                query,
                (platform_filter, role_filter)
            )
            
            return [ValidationRule(**rule) for rule in results]
            
        except Exception as e:
            logger.error(f"Error getting validation rules: {str(e)}")
            return []
            
    async def validate_data(
        self,
        data: Dict[str, Any],
        rules: List[ValidationRule],
        platform: Optional[str] = None,
        role: Optional[str] = None
    ) -> List[ValidationError]:
        """Validate data against rules"""
        errors = []
        
        for rule in rules:
            # Skip if rule doesn't apply to platform/role
            if (rule.platform and platform not in rule.platform) or \
               (rule.roles and role not in rule.roles):
                continue
                
            value = data.get(rule.field)
            
            # Basic validations
            if rule.type == ValidationType.REQUIRED:
                if not value:
                    errors.append(
                        ValidationError(
                            field=rule.field,
                            message=rule.message,
                            code="REQUIRED_ERROR",
                            value=value
                        )
                    )
                    
            elif rule.type == ValidationType.LENGTH:
                if value and not (
                    rule.value["min"] <= len(str(value)) <= rule.value["max"]
                ):
                    errors.append(
                        ValidationError(
                            field=rule.field,
                            message=rule.message,
                            code="LENGTH_ERROR",
                            value=value
                        )
                    )
                    
            elif rule.type == ValidationType.RANGE:
                if value and not (
                    rule.value["min"] <= float(value) <= rule.value["max"]
                ):
                    errors.append(
                        ValidationError(
                            field=rule.field,
                            message=rule.message,
                            code="RANGE_ERROR",
                            value=value
                        )
                    )
                    
            elif rule.type == ValidationType.REGEX:
                import re
                if value and not re.match(rule.value, str(value)):
                    errors.append(
                        ValidationError(
                            field=rule.field,
                            message=rule.message,
                            code="REGEX_ERROR",
                            value=value
                        )
                    )
                    
            elif rule.type == ValidationType.PLATFORM:
                # Platform specific validations
                if platform == "discord" and rule.field == "growid" and not value:
                    errors.append(
                        ValidationError(
                            field=rule.field,
                            message="Growtopia ID required for Discord users",
                            code="PLATFORM_ERROR",
                            value=value
                        )
                    )
                elif platform == "web" and rule.field == "growid" and value:
                    errors.append(
                        ValidationError(
                            field=rule.field,
                            message="Web users cannot have Growtopia ID",
                            code="PLATFORM_ERROR",
                            value=value
                        )
                    )
                    
            elif rule.type == ValidationType.CUSTOM:
                # Custom validation logic
                try:
                    validation_func = getattr(self, f"validate_{rule.value}")
                    is_valid, message = await validation_func(value, data)
                    if not is_valid:
                        errors.append(
                            ValidationError(
                                field=rule.field,
                                message=message or rule.message,
                                code="CUSTOM_ERROR",
                                value=value
                            )
                        )
                except Exception as e:
                    logger.error(f"Custom validation error: {str(e)}")
                    
        return errors