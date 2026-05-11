from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field
from Schemas.NewsSchema import NewsData


class FavoriteNewsItem(NewsData):
    favorite_id:Annotated[int,Field(alias="favoriteId")]
    favorited_at:Annotated[datetime,Field(alias="favoriteTime")]

    model_config = {
        "populate_by_name": True
    }


class UserFavoriteResponse(BaseModel):
    fav_lt:Annotated[list[FavoriteNewsItem],Field(alias="newsList")]
    total:Annotated[int,Field()]

    model_config = {
        "populate_by_name": True
    }

