import uuid
from fastapi import UploadFile
import hashlib

def generate_token():
    return str(uuid.uuid4())

async def calculate_md5(file: UploadFile):
    md5_hash = hashlib.md5()
    while chunk := await file.read(8192):
        md5_hash.update(chunk)
    await file.seek(0) # 指针归零
    return md5_hash.hexdigest()