# Utils/response.py

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

"""
exclude_none=True 排除 None 值

"""

def success_response(code=200, message="Success", data=None):
    content= {
        "code": code,
        "message": message,
        "data": data
    }

    return JSONResponse(content=jsonable_encoder(content, exclude_none=True))  
def error_response(code=400, message="Error", data=None):
    content= {
        "code": code,
        "message": message,
        "data": data
    }

    return JSONResponse(content=jsonable_encoder(content, exclude_none=True))