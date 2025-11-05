"""
URL Generator Tool for Broadband Comparison (Pydantic-based)

Refactored to use dependency injection pattern:
- URLGenerator: Injectable class that generates URLs
- BroadbandParams: Pydantic model with enums for allowed choices
- URLGenerationResult: Structured output for tools
- Final URL is validated using pydantic.HttpUrl (ensures http/https)
"""

from __future__ import annotations

import re
from typing import Optional, List, Dict, Tuple, Any
from urllib.parse import quote, urlparse, urlunparse
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    HttpUrl,
    parse_obj_as,
    validator,
)


# --- Constants / allowed values (kept as lists for help text) ---
VALID_SPEEDS = ["10Mb", "30Mb", "55Mb", "100Mb"]
VALID_CONTRACT_LENGTHS = ["12 months", "18 months", "24 months"]
VALID_PHONE_CALLS = [
    "Cheapest",
    "Show me everything",
    "Evening and Weekend",
    "Anytime",
    "No inclusive",
    "No phone line",
]
VALID_PRODUCT_TYPES = ["broadband", "broadband,phone", "broadband,phone,tv"]
VALID_SORT_BY = [
    "Recommended",
    "First Year Cost",
    "Avg. Monthly Cost",
    "Total Contract Cost",
    "Setup Costs",
    "Contract Length",
    "Speed",
    "Usage",
]


# --- Enums used for strict typing / schemas ---
class Speed(str, Enum):
    MB_10 = "10Mb"
    MB_30 = "30Mb"
    MB_55 = "55Mb"
    MB_100 = "100Mb"


class ContractLength(str, Enum):
    M12 = "12 months"
    M18 = "18 months"
    M24 = "24 months"


class PhoneCalls(str, Enum):
    CHEAPEST = "Cheapest"
    SHOW_ALL = "Show me everything"
    EVENING_WEEKEND = "Evening and Weekend"
    ANYTIME = "Anytime"
    NO_INCLUSIVE = "No inclusive"
    NO_LINE = "No phone line"


class ProductType(str, Enum):
    BROADBAND = "broadband"
    BROADBAND_PHONE = "broadband,phone"
    BROADBAND_PHONE_TV = "broadband,phone,tv"


class SortBy(str, Enum):
    RECOMMENDED = "Recommended"
    FIRST_YEAR_COST = "First Year Cost"
    AVG_MONTHLY_COST = "Avg. Monthly Cost"
    TOTAL_CONTRACT_COST = "Total Contract Cost"
    SETUP_COSTS = "Setup Costs"
    CONTRACT_LENGTH = "Contract Length"
    SPEED = "Speed"
    USAGE = "Usage"


# --- Postcode regex (loose but practical) ---
UK_POSTCODE_REGEX = r"^[A-Z]{1,2}\d[A-Z0-9]?\s*\d[A-Z]{2}$"


# --- Pydantic model for parameters ---
class BroadbandParams(BaseModel):
    """
    Strict schema for broadband comparison parameters.

    Use this model across your agent and tool so the LLM sees exact types/options.
    """
    postcode: str = Field(description="UK postcode (e.g., 'E14 9WB')")
    speedInMb: Optional[Speed] = Field(None, description=f"One of: {', '.join(VALID_SPEEDS)}")
    contractLength: Optional[ContractLength] = Field(None, description=f"One of: {', '.join(VALID_CONTRACT_LENGTHS)}")
    phoneCalls: Optional[PhoneCalls] = Field(None, description=f"One of: {', '.join(VALID_PHONE_CALLS)}")
    productType: Optional[ProductType] = Field(None, description=f"One of: {', '.join(VALID_PRODUCT_TYPES)}")
    providers: Optional[List[str]] = Field(None, description="List of providers, e.g. ['Hyperoptic','BT']")
    currentProvider: Optional[str] = Field(None, description="User's current provider (optional)")
    newLine: Optional[bool] = Field(None, description="True if a new phone line is required")
    sortBy: Optional[SortBy] = Field(None, description=f"One of: {', '.join(VALID_SORT_BY)}")

    # Internal / UI-only params (optional)
    addressId: Optional[str] = ""
    matryoshkaSpeed: str = "Broadband"
    openProduct: Optional[str] = ""
    tab: str = "alldeals"
    tvChannels: Optional[str] = ""

    # --- validators --- (pydantic v2 style)
    @validator("postcode", pre=True)
    @classmethod
    def normalize_postcode_input(cls, v: str) -> str:
        # Accept a postcode with/without space and normalise to uppercase with single space.
        if not isinstance(v, str) or not v.strip():
            raise ValueError("postcode must be a non-empty string")
        s = v.strip().upper()
        # Insert space before the final 3 characters if missing
        if len(s) > 3 and " " not in s:
            s = f"{s[:-3]} {s[-3:]}"
        return s

    @validator("postcode")
    @classmethod
    def validate_postcode_format(cls, v: str) -> str:
        if not re.match(UK_POSTCODE_REGEX, v.replace(" ", "")):
            # keep the original format in message but raise to fail validation
            raise ValueError(f"Invalid UK postcode format: {v}")
        return v

    @validator("providers", pre=True)
    @classmethod
    def coerce_providers(cls, v):
        """
        Accept either:
          - None
          - a comma-separated string ("BT,Sky")
          - a list of strings
        and return a list[str] or None.
        """
        if v is None:
            return None
        if isinstance(v, list):
            return [str(p).strip() for p in v if str(p).strip()]
        # treat a string as comma-separated list
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts or None
        # otherwise, try to coerce
        return [str(v)]

    # helper to produce a URL-safe postcode (E14+9WB)
    def postcode_for_url(self) -> str:
        # replace space with '+' for query param
        return self.postcode.replace(" ", "+")
    
    def get_missing_parameters(self) -> List[str]:
        """
        Analyze which optional parameters are not set.
        Useful for multi-turn conversations.
        """
        missing = []
        if self.speedInMb is None:
            missing.append("speedInMb")
        if self.contractLength is None:
            missing.append("contractLength")
        if self.phoneCalls is None:
            missing.append("phoneCalls")
        if self.productType is None:
            missing.append("productType")
        if self.sortBy is None:
            missing.append("sortBy")
        return missing


# --- Structured result for tool outputs ---
class URLGenerationResult(BaseModel):
    """
    Structured result returned by URL generation operations.
    
    This is used by agent tools to provide rich, type-safe responses.
    """
    success: bool = Field(description="Whether URL generation succeeded")
    message: str = Field(description="User-friendly message explaining the result")
    url: Optional[HttpUrl] = Field(None, description="The generated URL (if successful)")
    parameters_used: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters that were used in URL generation"
    )
    missing_parameters: List[str] = Field(
        default_factory=list,
        description="Optional parameters that weren't provided"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for refining the search"
    )


# --- Injectable URLGenerator class ---
class URLGenerator:
    """
    Injectable service for generating broadband comparison URLs.
    
    This class encapsulates URL generation logic and can be mocked for testing.
    """
    
    def __init__(self, base_url: str = "https://broadband.justmovein.co/packages"):
        """
        Initialize the URL generator.
        
        Args:
            base_url: Base URL for the broadband comparison site
        """
        self.base_url = base_url
    
    def generate(self, params: BroadbandParams) -> URLGenerationResult:
        """
        Build and validate a broadband comparison URL from typed parameters.
        
        Args:
            params: BroadbandParams Pydantic model (validated on construction)
            
        Returns:
            URLGenerationResult with url and metadata
        """
        # Validate params if dict was passed somehow
        if not isinstance(params, BroadbandParams):
            try:
                params = BroadbandParams.model_validate(params)  # type: ignore[arg-type]
            except ValidationError as e:
                return URLGenerationResult(
                    success=False,
                    message=f"Invalid parameters: {self._format_validation_errors(e)}",
                    parameters_used={},
                )
        
        # Location query from postcode
        location = params.postcode_for_url()
        
        # Build fragment params - using string values where needed
        fragment_params: Dict[str, str] = {
            "addressId": params.addressId or "",
            "contractLength": params.contractLength.value if params.contractLength else "",
            "currentProvider": params.currentProvider or "",
            "matryoshkaSpeed": params.matryoshkaSpeed or "Broadband",
            "newLine": "NewLine" if params.newLine else "",
            "openProduct": params.openProduct or "",
            "phoneCalls": params.phoneCalls.value if params.phoneCalls else "",
            "productType": params.productType.value if params.productType else "broadband",
            "providers": ",".join(params.providers) if params.providers else "",
            "sortBy": params.sortBy.value if params.sortBy else "Recommended",
            "speedInMb": params.speedInMb.value if params.speedInMb else "",
            "tab": params.tab or "alldeals",
            "tvChannels": params.tvChannels or "",
        }
        
        # Remove empty keys
        fragment_params = {k: v for k, v in fragment_params.items() if v}
        
        # Compose URL: base + ?location=... #/ ?fragment-params
        encoded_location = quote(location)
        url = f"{self.base_url}?location={encoded_location}#/"
        if fragment_params:
            encoded_fragment = "&".join(
                f"{k}={quote(str(v))}" for k, v in fragment_params.items()
            )
            url += f"?{encoded_fragment}"
        
        # Ensure scheme and validate final URL as HttpUrl
        parsed = urlparse(url)
        if not parsed.scheme:
            parsed = parsed._replace(scheme="https")
            url = urlunparse(parsed)
        
        try:
            # Validate URL
            validated_url = parse_obj_as(HttpUrl, url)
            
            # Analyze what's missing and generate suggestions
            missing = params.get_missing_parameters()
            suggestions = self._generate_suggestions(params, missing)
            
            # Build success message
            message = self._build_success_message(params, missing)
            
            return URLGenerationResult(
                url=validated_url,
                success=True,
                message=message,
                parameters_used=params.model_dump(exclude_none=True),
                missing_parameters=missing,
                suggestions=suggestions,
            )
            
        except ValidationError as ve:
            return URLGenerationResult(
                success=False,
                message=f"Failed to generate valid URL: {self._format_validation_errors(ve)}",
                parameters_used=params.model_dump(exclude_none=True),
            )
    
    def _format_validation_errors(self, error: ValidationError) -> str:
        """Format validation errors into user-friendly message."""
        errors = error.errors()
        if len(errors) == 1:
            return errors[0].get("msg", str(errors[0]))
        return "; ".join(e.get("msg", str(e)) for e in errors[:3])
    
    def _build_success_message(
        self, 
        params: BroadbandParams, 
        missing: List[str]
    ) -> str:
        """Build a user-friendly success message."""
        filters_applied = []
        
        if params.speedInMb:
            filters_applied.append(f"speed: {params.speedInMb.value}")
        if params.contractLength:
            filters_applied.append(f"contract: {params.contractLength.value}")
        if params.providers:
            filters_applied.append(f"providers: {', '.join(params.providers)}")
        if params.productType:
            filters_applied.append(f"type: {params.productType.value}")
        
        base_msg = f"Generated URL for postcode {params.postcode}"
        if filters_applied:
            base_msg += f" with filters: {', '.join(filters_applied)}"
        
        return base_msg
    
    def _generate_suggestions(
        self, 
        params: BroadbandParams, 
        missing: List[str]
    ) -> List[str]:
        """Generate helpful suggestions for refining the search."""
        suggestions = []
        
        if "speedInMb" in missing:
            suggestions.append(
                f"Consider specifying a speed preference: {', '.join(VALID_SPEEDS)}"
            )
        
        if "contractLength" in missing:
            suggestions.append(
                f"You can filter by contract length: {', '.join(VALID_CONTRACT_LENGTHS)}"
            )
        
        if "providers" not in params.model_dump(exclude_none=True):
            suggestions.append(
                "You can filter by specific providers (e.g., BT, Sky, Hyperoptic)"
            )
        
        if params.sortBy is None or params.sortBy == SortBy.RECOMMENDED:
            suggestions.append(
                "Try sorting by 'First Year Cost' or 'Avg. Monthly Cost' for better deals"
            )
        
        return suggestions[:3]  # Limit to 3 suggestions


# --- Backward compatibility function ---
def generate_broadband_url(params: BroadbandParams) -> Tuple[str, Optional[str]]:
    """
    Legacy function for backward compatibility.
    
    Args:
        params: BroadbandParams Pydantic model
        
    Returns:
        (url_str, None) when successful, or ("", error_message) on failure
    """
    generator = URLGenerator()
    result = generator.generate(params)
    
    if result.success and result.url:
        return str(result.url), None
    else:
        return "", result.message


# --- Parameter help (for UI / agent) ---
def get_parameter_help() -> Dict[str, str]:
    return {
        "postcode": "Required. UK postcode (e.g., E14 9WB, SW10 9PA)",
        "speedInMb": f"Optional. Valid options: {', '.join(VALID_SPEEDS)}",
        "contractLength": f"Optional. Valid options: {', '.join(VALID_CONTRACT_LENGTHS)}",
        "phoneCalls": f"Optional. Valid options: {', '.join(VALID_PHONE_CALLS)}",
        "productType": f"Optional. Valid options: {', '.join(VALID_PRODUCT_TYPES)}",
        "providers": "Optional. Comma-separated provider names or list (e.g., 'Hyperoptic,BT' or ['BT','Sky'])",
        "currentProvider": "Optional. User's existing provider name",
        "newLine": "Optional. Boolean: True if new line required",
        "sortBy": f"Optional. Valid options: {', '.join(VALID_SORT_BY)}",
    }
