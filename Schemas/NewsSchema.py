# Schemas/NewsSchema.py
from datetime import datetime

from pydantic import BaseModel
from typing import List


class CategoryData(BaseModel):
    """分类数据模型"""
    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

    id: int
    name: str


class NewsData(BaseModel):
    """新闻数据模型"""
    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }

    id: int
    category_id: int
    title: str
    author: str
    publish_time: datetime|None=None
    views: int
    thumbnail: str
    summary: str
    content: str|None = None


class NewsDetailResponse(BaseModel):
    """新闻列表数据模型"""
    list: NewsData
    related_news: List[NewsData] = []


class CategoryResponse(BaseModel):

    """分类响应模型"""
    list: List[CategoryData]


class NewsListResponse(BaseModel):
    """新闻列表响应模型"""
    list: List[NewsData]
    total: int = 0


