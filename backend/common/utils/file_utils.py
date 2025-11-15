"""
文件工具类 - 开源版本
用于处理文件上传、下载、删除等操作
"""
import hashlib
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import HTTPException, UploadFile

from common.core.config import settings
from common.utils.utils import SQLBotLogUtil


class SQLBotFileUtils:
    """文件工具类"""
    
    # 文件存储根目录
    FILE_STORAGE_PATH = os.getenv("FILE_STORAGE_PATH", "/opt/sqlbot/data/file")
    
    @classmethod
    def get_file_path(cls, file_id: str) -> str:
        """
        根据文件 ID 获取文件路径
        
        Args:
            file_id: 文件 ID
            
        Returns:
            文件完整路径
        """
        # 确保存储目录存在
        os.makedirs(cls.FILE_STORAGE_PATH, exist_ok=True)
        
        # 文件路径
        file_path = os.path.join(cls.FILE_STORAGE_PATH, file_id)
        return file_path
    
    @classmethod
    def split_filename_and_flag(cls, filename: str) -> Tuple[str, str]:
        """
        分割文件名和标志
        格式：filename__flag.ext -> (filename.ext, flag)
        
        Args:
            filename: 原始文件名
            
        Returns:
            (文件名, 标志) 元组
        """
        if not filename:
            return "", ""
        
        # 查找 __ 分隔符
        if "__" in filename:
            parts = filename.rsplit("__", 1)
            if len(parts) == 2:
                name_part = parts[0]
                flag_and_ext = parts[1]
                
                # 分离标志和扩展名
                if "." in flag_and_ext:
                    flag, ext = flag_and_ext.rsplit(".", 1)
                    return f"{name_part}.{ext}", flag
                else:
                    return name_part, flag_and_ext
        
        # 没有标志，返回原文件名和空标志
        return filename, ""
    
    @classmethod
    def check_file(
        cls,
        file: UploadFile,
        file_types: Optional[List[str]] = None,
        limit_file_size: Optional[int] = None
    ) -> None:
        """
        检查文件类型和大小
        
        Args:
            file: 上传的文件
            file_types: 允许的文件类型列表，如 [".jpg", ".png"]
            limit_file_size: 文件大小限制（字节）
            
        Raises:
            HTTPException: 文件不符合要求时抛出
        """
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # 检查文件类型
        if file_types:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in [ft.lower() for ft in file_types]:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed. Allowed types: {', '.join(file_types)}"
                )
        
        # 检查文件大小
        if limit_file_size:
            # 读取文件大小（需要先读取内容）
            file.file.seek(0, 2)  # 移动到文件末尾
            file_size = file.file.tell()
            file.file.seek(0)  # 重置到文件开头
            
            if file_size > limit_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds limit. Max size: {limit_file_size / (1024 * 1024):.2f} MB"
                )
    
    @classmethod
    async def upload(cls, file: UploadFile) -> str:
        """
        上传文件
        
        Args:
            file: 上传的文件
            
        Returns:
            文件 ID
        """
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # 确保存储目录存在
        os.makedirs(cls.FILE_STORAGE_PATH, exist_ok=True)
        
        # 生成文件 ID（使用原文件名 + UUID + 扩展名）
        file_ext = os.path.splitext(file.filename)[1]
        file_name_without_ext = os.path.splitext(file.filename)[0]
        unique_id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:10]
        file_id = f"{file_name_without_ext}_{unique_id}{file_ext}"
        
        # 保存文件
        file_path = cls.get_file_path(file_id)
        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            SQLBotLogUtil.info(f"File uploaded successfully: {file_id}")
            return file_id
        except Exception as e:
            SQLBotLogUtil.error(f"Failed to upload file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    @classmethod
    def delete_file(cls, file_id: str) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件 ID
            
        Returns:
            是否删除成功
        """
        if not file_id:
            return False
        
        file_path = cls.get_file_path(file_id)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                SQLBotLogUtil.info(f"File deleted successfully: {file_id}")
                return True
            else:
                SQLBotLogUtil.warning(f"File not found: {file_id}")
                return False
        except Exception as e:
            SQLBotLogUtil.error(f"Failed to delete file: {e}")
            return False
    
    @classmethod
    def file_exists(cls, file_id: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_id: 文件 ID
            
        Returns:
            文件是否存在
        """
        if not file_id:
            return False
        
        file_path = cls.get_file_path(file_id)
        return os.path.exists(file_path)

