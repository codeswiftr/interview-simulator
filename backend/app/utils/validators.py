"""Custom Pydantic validators."""

from typing import Any

from pydantic import GetCoreSchema, GetJsonSchemaHandler
from pydantic_core import core_schema
from pydantic_core._pydantic_core import PydanticCustomError

from .password_validation import validate_password


class PasswordValidatorType:
    """Custom Pydantic validator for password validation."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchema,
    ) -> core_schema.AfterValidatorFunctionSchema:
        """Define the core schema for password validation."""
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser(
                lambda value: str(value),
                return_type=str,
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> dict[str, Any]:
        """Define the JSON schema for password validation."""
        return {
            "type": "string",
            "format": "password",
            "description": "A strong password meeting security requirements",
            "minLength": 12,
        }

    @classmethod
    def _validate(cls, value: str) -> str:
        """Validate the password."""
        errors = validate_password(value)
        if errors:
            # Join all errors with newlines for better readability
            raise PydanticCustomError(
                "password_validation_error", "\n".join(errors), {"errors": errors}
            )
        return value


# Alias for easier usage
PasswordStr = PasswordValidatorType
