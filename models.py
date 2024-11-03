# Pydantic model to return user information
from pydantic import BaseModel


class UserInfo(BaseModel):
    selected_character: str
 