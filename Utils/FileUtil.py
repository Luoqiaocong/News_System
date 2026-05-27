import hashlib

from fastapi import UploadFile, HTTPException
from starlette import status

from Config.AliyunOssConfig import settings, bucket


MAX_FILE_SIZE = 5 * 1024 * 1024


async def upload_file(
        file_model: str,
        filepath: UploadFile,
):
    contents = await filepath.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="文件太大，不能超过 5MB")

    md5_hex = hashlib.md5(contents).hexdigest()
    file_suffix = filepath.filename.split(".")[-1].lower()
    filename = f"{file_model}/{md5_hex}.{file_suffix}"

    bucket.put_object(filename, contents)

    file_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{filename}"
    return file_url
