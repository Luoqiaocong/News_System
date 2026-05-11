from fastapi import UploadFile, APIRouter

from Config.AliyunOssConfig import settings, bucket

router = APIRouter(prefix="/test", tags=["测试接口"])
@router.get("/test-oss-config",summary="测试OSS连接")
def test_oss_config():
    return {
        "key_id": settings.OSS_ACCESS_KEY_ID[:6] + "***",
        "secret": settings.OSS_ACCESS_KEY_SECRET[:6] + "***",
        "status": "配置加载成功 ✅"
    }

# 上传头像到 OSS
@router.post("/uploadFile",summary="上传文件测试")
async def upload_file(file: UploadFile):
    filename = file.filename
    # 上传文件
    result = bucket.put_object(filename, file.file)
    return {
        "status": "上传成功",
        "url": f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{filename}",
        "http_status": result.status
    }