import random
import time

from pydantic import BaseModel, Field


class UserRequest(BaseModel):
    username: str
    password: str
