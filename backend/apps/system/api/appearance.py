"""
系统外观设置 API
"""
import json
import os
from typing import List, Optional

from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlmodel import select

from apps.system.models.system_model import SysArg
from common.core.deps import SessionDep, CurrentUser
from common.utils.file_utils import SQLBotFileUtils

router = APIRouter(tags=["system/appearance"], prefix="/system/appearance")


@router.get("/ui")
async def get_ui_config(session: SessionDep) -> List[dict]:
    """
    获取 UI 配置
    
    Returns:
        配置列表，每项包含 pkey 和 pval
    """
    # 查询所有系统参数
    sys_args = session.exec(select(SysArg).order_by(SysArg.sort_no)).all()
    
    # 转换为前端需要的格式
    result = []
    for arg in sys_args:
        result.append({
            "pkey": arg.pkey,
            "pval": arg.pval
        })
    
    return result


@router.patch("/ui")
async def update_ui_config(
    session: SessionDep,
    data: str = Form(),
    files: List[UploadFile] = []
) -> dict:
    """
    更新 UI 配置
    
    Args:
        session: 数据库会话
        data: JSON 格式的配置数据
        files: 上传的文件列表（如 logo、背景图等）
        
    Returns:
        更新结果
    """
    try:
        # 解析 JSON 数据
        config_data = json.loads(data)
        
        # 处理文件上传
        file_map = {}
        if files:
            for file in files:
                if not file.filename:
                    continue
                
                # 分离文件名和标志
                file_name, flag = SQLBotFileUtils.split_filename_and_flag(file.filename)
                
                if flag:
                    # 检查文件类型和大小
                    SQLBotFileUtils.check_file(
                        file=file,
                        file_types=[".jpg", ".jpeg", ".png", ".svg", ".gif"],
                        limit_file_size=(10 * 1024 * 1024)  # 10MB
                    )
                    
                    # 上传文件
                    file.filename = file_name
                    file_id = await SQLBotFileUtils.upload(file)
                    file_map[flag] = file_id
        
        # 更新配置
        for key, value in config_data.items():
            # 如果是文件字段，使用上传的文件 ID
            if key in file_map:
                value = file_map[key]
            
            # 查找现有配置
            existing = session.exec(
                select(SysArg).where(SysArg.pkey == key)
            ).first()
            
            if existing:
                # 如果是文件类型且有旧文件，删除旧文件
                if existing.ptype == 'file' and existing.pval and value != existing.pval:
                    SQLBotFileUtils.delete_file(existing.pval)
                
                # 更新值
                existing.pval = str(value) if value is not None else None
            else:
                # 创建新配置
                ptype = 'file' if key in file_map else 'str'
                new_arg = SysArg(
                    pkey=key,
                    pval=str(value) if value is not None else None,
                    ptype=ptype,
                    sort_no=1
                )
                session.add(new_arg)
        
        session.commit()
        
        return {"success": True, "message": "Configuration updated successfully"}
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON data: {str(e)}")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.get("/picture/{file_id}")
async def get_picture(file_id: str):
    """
    获取图片文件
    
    Args:
        file_id: 文件 ID
        
    Returns:
        图片文件流
    """
    file_path = SQLBotFileUtils.get_file_path(file_id)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # 根据文件扩展名确定 MIME 类型
    if file_id.lower().endswith(".svg"):
        media_type = "image/svg+xml"
    elif file_id.lower().endswith(".png"):
        media_type = "image/png"
    elif file_id.lower().endswith(".gif"):
        media_type = "image/gif"
    else:
        media_type = "image/jpeg"
    
    def iterfile():
        with open(file_path, mode="rb") as f:
            yield from f
    
    return StreamingResponse(iterfile(), media_type=media_type)


@router.post("")
async def save_appearance(
    session: SessionDep,
    current_user: CurrentUser,
    data: str = Form(),
    files: List[UploadFile] = File(default=[])
) -> dict:
    """
    保存外观设置（前端调用的主接口）

    Args:
        session: 数据库会话
        current_user: 当前用户
        data: JSON 格式的配置数据数组
        files: 上传的文件列表（如 logo、背景图等）

    Returns:
        保存结果
    """
    try:
        # 解析 JSON 数据 - 前端发送的是数组格式
        config_array = json.loads(data)

        # 处理文件上传
        file_map = {}
        if files:
            for file in files:
                if not file.filename:
                    continue

                # 前端文件名格式: "filename,flag"
                parts = file.filename.split(',')
                if len(parts) == 2:
                    file_name = parts[0]
                    flag = parts[1]

                    # 检查文件类型和大小
                    SQLBotFileUtils.check_file(
                        file=file,
                        file_types=[".jpg", ".jpeg", ".png", ".svg", ".gif"],
                        limit_file_size=(10 * 1024 * 1024)  # 10MB
                    )

                    # 上传文件
                    file.filename = file_name
                    file_id = await SQLBotFileUtils.upload(file)
                    file_map[flag] = file_id

        # 更新配置
        for item in config_array:
            pkey = item.get('pkey')
            pval = item.get('pval')
            ptype = item.get('ptype', 'str')

            if not pkey:
                continue

            # 如果是文件字段，使用上传的文件 ID
            if pkey in file_map:
                pval = file_map[pkey]
                ptype = 'file'

            # 查找现有配置
            existing = session.exec(
                select(SysArg).where(SysArg.pkey == pkey)
            ).first()

            if existing:
                # 如果是文件类型且有旧文件，删除旧文件
                if existing.ptype == 'file' and existing.pval and pval != existing.pval:
                    try:
                        SQLBotFileUtils.delete_file(existing.pval)
                    except Exception:
                        pass  # 忽略删除失败

                # 更新值
                existing.pval = str(pval) if pval is not None else None
                existing.ptype = ptype
            else:
                # 创建新配置
                new_arg = SysArg(
                    pkey=pkey,
                    pval=str(pval) if pval is not None else None,
                    ptype=ptype,
                    sort_no=item.get('sort_no', 1)
                )
                session.add(new_arg)

        session.commit()

        return {"success": True, "message": "Appearance settings saved successfully"}

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON data: {str(e)}")
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save appearance settings: {str(e)}")

