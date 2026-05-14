# Schemas/NewsSchema.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class CategoryData(BaseModel):
    """分类数据模型"""
    model_config = {
        "from_attributes": True
    }
    id: int=Field(...,description="分类ID")
    name: str=Field(...,description="分类名称")

class NewsData(BaseModel):
    """新闻数据模型"""
    model_config={
        "from_attributes":True
    }
    id: int
    category_id: int
    title: str
    author: str
    publish_time: Optional[datetime] = None
    views: int
    thumbnail: str
    summary: str
    content: Optional[str] = None

class NewsListResponse(BaseModel):
    news_list: List[NewsData]
    total: int