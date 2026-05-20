from typing import Annotated

from fastapi import Depends

from Repo.UserHistRepo import UserHistRepo


class UserHistService:
    def __init__(self,repo:Annotated[UserHistRepo,Depends()]):
        self.repo = repo