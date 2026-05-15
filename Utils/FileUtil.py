
from fastapi import UploadFile, HTTPException
from starlette import status

from Config.AliyunOssConfig import settings, bucket
from Exception import ResponseCode
from Utils.CommonUtil import calculate_md5

"""
考虑使用Redis缓存，如果一个用户上传的文件内容一模一样，直接返回已经存在于OSS里面的文件链接即可，可能需要数据库存储
"""
MAX_FILE_SIZE = 5 * 1024 * 1024
# 通用文件上传工具（图片/文件都能用）
async def upload_file(
        file_model: str,  # 文件夹名称，例如 avatar、article、cover
        filepath: UploadFile,
):
    # 1. 读取文件内容（或者分块读取）
    contents = await filepath.read()

    # 2. 检查大小
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="文件太大，不能超过 5MB")


    # 1. 获取安全后缀
    file_suffix = filepath.filename.split(".")[-1].lower()

    filename = f"{file_model}/{await calculate_md5(filepath)}.{file_suffix}"

    bucket.put_object(filename, await filepath.read())

    # 4. 生成访问URL
    file_url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{filename}"

    return file_url


# import asyncio
# import json
# import oss2
# from concurrent.futures import ThreadPoolExecutor
# from fastapi import UploadFile, HTTPException
# from starlette import status
# from Config.AliyunOssConfig import settings, bucket
#
# # 限制 5MB
# MAX_FILE_SIZE = 5 * 1024 * 1024
# # 线程池：专门给同步的 oss2 SDK 使用，防止阻塞 FastAPI 异步主线程
# executor = ThreadPoolExecutor(max_workers=20)


# class OSSManager:
#     @staticmethod
#     async def upload(file_model: str, file: UploadFile) -> str:
#         """
#         通用上传：包含 MD5 计算、重复校验建议、异步线程池执行
#         """
#         # 1. 预读取内容，解决多次 read() 指针为空的问题
#         contents = await file.read()
#         file_size = len(contents)
#
#         if file_size > MAX_FILE_SIZE:
#             raise HTTPException(
#                 status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
#                 detail=f"文件大小超过限制，最大允许 {MAX_FILE_SIZE // (1024 * 1024)}MB"
#             )
#
#         # 2. 计算 MD5 (用于秒传校验和文件名)
#         from Utils.CommonUtil import calculate_md5_from_bytes  # 建议实现一个直接传 bytes 的 MD5 方法
#         md5_hex = await calculate_md5_from_bytes(contents)
#
#         file_suffix = file.filename.split(".")[-1].lower() if "." in file.filename else "bin"
#         # 构造 OSS 保存路径：模型名/MD5.后缀
#         object_name = f"{file_model}/{md5_hex}.{file_suffix}"
#
#         # --- 这里是你的 Redis/数据库 秒传判断逻辑入口 ---
#         # if await check_file_exists_in_db(md5_hex):
#         #     return generate_url(object_name)
#         # --------------------------------------------
#
#         # 3. 使用线程池执行同步的 put_object
#         loop = asyncio.get_event_loop()
#         try:
#             await loop.run_in_executor(
#                 executor,
#                 bucket.put_object,
#                 object_name,
#                 contents
#             )
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"OSS 上传失败: {str(e)}")
#
#         # 4. 返回完整访问链接
#         return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{object_name}"
#
#     @staticmethod
#     async def delete(object_key: str) -> bool:
#         """
#         删除单个文件
#         object_key: OSS 中的完整路径，例如 'avatar/a1b2c3d4.jpg'
#         """
#         loop = asyncio.get_event_loop()
#         try:
#             # 同样在线程池中执行，防止阻塞
#             await loop.run_in_executor(executor, bucket.delete_object, object_key)
#             return True
#         except Exception as e:
#             # 这里建议记录日志，而不是直接抛异常给用户，因为删除失败通常需要后台补偿
#             print(f"OSS 删除异常: {e}")
#             return False
#
#     @staticmethod
#     async def batch_delete(object_keys: list[str]):
#         """
#         批量删除（最高效，一次最多 1000 个）
#         """
#         if not object_keys:
#             return
#         loop = asyncio.get_event_loop()
#         try:
#             await loop.run_in_executor(executor, bucket.batch_delete_objects, object_keys)
#         except Exception as e:
#             print(f"OSS 批量删除异常: {e}")