from typing import Annotated

from fastapi import Depends

from Repo import UserFavCacheRepo, UserFavRepo


class UserFavService():
    def __init__(self,
                 repo:Annotated[UserFavRepo,Depends()]):
        self.repo = repo


    async def add_favorite(self,news_id:int,user_id:int):
        await UserFavCacheRepo.add_fav_cache(news_id,user_id)
        await self.repo.add_favorite(news_id,user_id)
        