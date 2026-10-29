"""
Synthesizer-AI: Strict Input Validation Schemas
==============================================
Validates all API inputs with rigorous bounds, regex patterns, and type constraints.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, EmailStr
import re


class LoginRequest(BaseModel):
    account: str = Field(..., min_length=3, max_length=64, description="Username or email address")
    password: str = Field(..., min_length=6, max_length=128, description="Account password")

    @field_validator("account")
    @classmethod
    def validate_account_format(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_.@+-]+$", v):
            raise ValueError("Account identifier contains invalid characters.")
        return v


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, description="Scientist username")
    email: str = Field(..., min_length=5, max_length=128, description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password")
    organization: Optional[str] = Field(default="Clinical Research Lab", max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username must contain only alphanumeric characters, dashes, or underscores.")
        return v

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", v):
            raise ValueError("Invalid email address format.")
        return v.lower().strip()


class SynthesisRequest(BaseModel):
    generator_type: Literal["dp_synth", "ctgan", "copula"] = Field(
        default="dp_synth",
        description="Generative model architecture"
    )
    epsilon: Optional[float] = Field(
        default=2.0,
        ge=0.01,
        le=100.0,
        description="Differential privacy epsilon budget (0.01 to 100.0)"
    )
    delta: Optional[float] = Field(
        default=1e-5,
        ge=1e-9,
        le=0.1,
        description="Failure probability delta bound"
    )
    n_samples: int = Field(
        default=1000,
        ge=10,
        le=100000,
        description="Number of synthetic records to generate"
    )
    clip_norm: float = Field(
        default=1.0,
        ge=0.01,
        le=50.0,
        description="L2 gradient clipping norm"
    )


class ValidateRequest(BaseModel):
    generator_type: Literal["dp_synth", "ctgan", "copula"] = Field(default="dp_synth")
    epsilon: float = Field(default=2.0, ge=0.01, le=100.0)
    n_samples: int = Field(default=1000, ge=10, le=50000)


class AttackSimulationRequest(BaseModel):
    attack_vector: Literal["shadow_model", "confidence_threshold", "reconstruction"] = Field(
        default="shadow_model"
    )
    shadow_models_count: int = Field(default=10, ge=1, le=100)
    training_epochs: int = Field(default=50, ge=1, le=500)
    epsilon: float = Field(default=2.0, ge=0.01, le=100.0)


class ClusterActionRequest(BaseModel):
    action: Literal["spawn_node", "cancel_job", "restart_job", "rebalance"]
    job_id: Optional[str] = Field(default=None, max_length=32)

    @field_validator("job_id")
    @classmethod
    def validate_job_id(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Job ID must be alphanumeric.")
        return v
