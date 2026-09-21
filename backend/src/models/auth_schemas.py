"""
auth_schemas.py — Pydantic Schemas for Authentication
======================================================
Defines data contracts for User Registration, Login, and Token Responses.
"""
from pydantic import BaseModel, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")
    full_name: str = Field(..., description="User full name")


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    base_currency: str = "USD"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="User email address")


class ForgotPasswordResponse(BaseModel):
    message: str = "If an account is associated with this email, a verification code has been sent."
    expires_in_minutes: int = 15


class ResetPasswordRequest(BaseModel):
    email: str = Field(..., description="User email address")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


class ResetPasswordResponse(BaseModel):
    message: str = "Password has been successfully reset. Please sign in with your new password."
