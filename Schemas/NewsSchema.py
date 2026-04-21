# Schemas/NewsSchema.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class CategoryData(BaseModel):
    """分类数据模型"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class NewsData(BaseModel):
    """新闻数据模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    title: str
    author: str
    publish_time: Optional[datetime] = None
    views: int
    thumbnail: str
    summary: str
    content: Optional[str] = None

# 移除 response_model 参数使用，直接使用 success_response
