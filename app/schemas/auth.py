from pydantic import BaseModel


class LoginRequest(BaseModel):
    farm_name: str | None = None
    username: str
    password: str


class RegisterFarmRequest(BaseModel):
    farm_id: str
    farm_name: str
    owner_name: str
    username: str
    password: str
    display_name: str


class CreateFarmUserRequest(BaseModel):
    user_id: str
    username: str
    password: str
    display_name: str
    role: str = "member"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    display_name: str
    farm_id: str
    farm_name: str
    role: str


class CurrentUserResponse(BaseModel):
    id: str
    farm_id: str
    farm_name: str
    username: str
    display_name: str
    role: str
