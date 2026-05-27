# Schemas/NewsSchema.py
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated


class CategoryData(BaseModel):
    """分类数据模型"""
    id: int=Field(...,description="分类ID")
    name: str=Field(...,description="分类名称")

    model_config = {
        "from_attributes": True
    }


class NewsData(BaseModel):
    """新闻详情数据模型"""
    id: int
    category_id: int
    title: str
    author: str
    publish_time: Optional[datetime] = None
    views: int
    thumbnail: str
    summary: str
    content: Optional[str] = None

    model_config={
        "from_attributes":True
    }


class NewsListCard(BaseModel):
    """新闻列表卡片模型"""
    id: int
    title: str
    author: str
    publish_time: Optional[datetime] = None
    views: int
    thumbnail: str
    summary: str

    model_config = {"from_attributes": True}

class RelatedNewsCard(NewsListCard):
    """相关新闻卡片模型"""
    model_config = {"from_attributes": True}


class NewsDetailResponse(BaseModel):
    detail: NewsData
    related_news: List[RelatedNewsCard]

    model_config = {
       "from_attributes": True # 允许从 ORM 对象创建模型实例
    }


class NewsListResponse(BaseModel):
    news_list: Annotated[List[NewsListCard], Field(description="新闻列表",alias="NewsList")]
    total: int

    model_config = {
        "populate_by_name": True # 允许使用字段别名
    }