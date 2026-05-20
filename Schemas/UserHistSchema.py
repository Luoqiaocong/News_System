from datetime import datetime
from typing import Annotated

from pydantic import Field, BaseModel

from Schemas.NewsSchema import NewsData


class HistoryNewsItem(NewsData):
    history_id:Annotated[int,Field(alias="historyId",serialization_alias="historyId")]
    viewed_at:Annotated[datetime,Field(alias="viewTime",serialization_alias="viewTime")]

    model_config = {
        "populate_by_name": True  # 允许别名匹配
    }



class UserHistResponse(BaseModel):
    hist_lt: Annotated[list[HistoryNewsItem], Field(alias="historyList",serialization_alias="historyList")] = Field(default=[])
    total:Annotated[int,Field()]

    model_config = {
        "populate_by_name": True
    }
