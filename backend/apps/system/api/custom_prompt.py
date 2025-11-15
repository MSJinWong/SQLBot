"""
自定义提示词 API
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from apps.system.models.system_model import CustomPrompt, CustomPromptTypeEnum
from common.core.deps import CurrentUser, SessionDep

router = APIRouter(tags=["system/custom_prompt"], prefix="/system/custom_prompt")


class CustomPromptRequest(BaseModel):
    """自定义提示词请求"""
    id: Optional[int] = None
    oid: Optional[int] = None
    type: Optional[CustomPromptTypeEnum] = None
    name: Optional[str] = None
    prompt: Optional[str] = None
    specific_ds: Optional[bool] = False
    datasource_ids: Optional[str] = None


class CustomPromptResponse(BaseModel):
    """自定义提示词响应"""
    id: int
    oid: Optional[int] = None
    type: Optional[str] = None
    create_time: Optional[str] = None
    name: Optional[str] = None
    prompt: Optional[str] = None
    specific_ds: Optional[bool] = False
    datasource_ids: Optional[str] = None


@router.get("/{prompt_type}/page/{page_num}/{page_size}")
async def get_prompt_list(
    session: SessionDep,
    current_user: CurrentUser,
    prompt_type: CustomPromptTypeEnum,
    page_num: int,
    page_size: int
) -> dict:
    """
    获取自定义提示词列表（分页）
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        prompt_type: 提示词类型
        page_num: 页码（从0开始）
        page_size: 每页大小
        
    Returns:
        分页数据
    """
    # 构建查询
    query = select(CustomPrompt).where(
        CustomPrompt.oid == current_user.oid,
        CustomPrompt.type == prompt_type.value
    ).order_by(CustomPrompt.create_time.desc())
    
    # 获取总数
    total_query = select(CustomPrompt).where(
        CustomPrompt.oid == current_user.oid,
        CustomPrompt.type == prompt_type.value
    )
    total = len(session.exec(total_query).all())
    
    # 分页
    offset = page_num * page_size
    query = query.offset(offset).limit(page_size)
    
    prompts = session.exec(query).all()
    
    # 转换为响应格式
    items = [
        CustomPromptResponse(
            id=p.id,
            oid=p.oid,
            type=p.type.value if p.type else None,
            create_time=p.create_time.isoformat() if p.create_time else None,
            name=p.name,
            prompt=p.prompt,
            specific_ds=p.specific_ds,
            datasource_ids=p.datasource_ids
        )
        for p in prompts
    ]
    
    return {
        "total": total,
        "items": [item.model_dump() for item in items],
        "page": page_num,
        "size": page_size
    }


@router.get("/{id}")
async def get_prompt(
    session: SessionDep,
    current_user: CurrentUser,
    id: int
) -> CustomPromptResponse:
    """
    获取单个自定义提示词
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        id: 提示词 ID
        
    Returns:
        提示词详情
    """
    prompt = session.get(CustomPrompt, id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"CustomPrompt with id {id} not found")
    
    # 检查权限
    if prompt.oid != current_user.oid:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return CustomPromptResponse(
        id=prompt.id,
        oid=prompt.oid,
        type=prompt.type.value if prompt.type else None,
        create_time=prompt.create_time.isoformat() if prompt.create_time else None,
        name=prompt.name,
        prompt=prompt.prompt,
        specific_ds=prompt.specific_ds,
        datasource_ids=prompt.datasource_ids
    )


@router.put("")
async def update_prompt(
    session: SessionDep,
    current_user: CurrentUser,
    data: CustomPromptRequest
) -> dict:
    """
    创建或更新自定义提示词
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        data: 提示词数据
        
    Returns:
        操作结果
    """
    try:
        if data.id:
            # 更新现有提示词
            prompt = session.get(CustomPrompt, data.id)
            if not prompt:
                raise HTTPException(status_code=404, detail=f"CustomPrompt with id {data.id} not found")
            
            # 检查权限
            if prompt.oid != current_user.oid:
                raise HTTPException(status_code=403, detail="Permission denied")
            
            if data.type is not None:
                prompt.type = data.type
            if data.name is not None:
                prompt.name = data.name
            if data.prompt is not None:
                prompt.prompt = data.prompt
            if data.specific_ds is not None:
                prompt.specific_ds = data.specific_ds
            if data.datasource_ids is not None:
                prompt.datasource_ids = data.datasource_ids
        else:
            # 创建新提示词
            prompt = CustomPrompt(
                oid=current_user.oid,
                type=data.type,
                create_time=datetime.now(),
                name=data.name,
                prompt=data.prompt,
                specific_ds=data.specific_ds,
                datasource_ids=data.datasource_ids
            )
            session.add(prompt)
        
        session.commit()
        session.refresh(prompt)
        
        return {
            "success": True,
            "message": "CustomPrompt saved successfully",
            "id": prompt.id
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save custom prompt: {str(e)}")


@router.delete("")
async def delete_prompt(
    session: SessionDep,
    current_user: CurrentUser,
    data: dict
) -> dict:
    """
    删除自定义提示词
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        data: 包含 id 的字典
        
    Returns:
        删除结果
    """
    try:
        prompt_id = data.get("id")
        if not prompt_id:
            raise HTTPException(status_code=400, detail="Missing id parameter")
        
        prompt = session.get(CustomPrompt, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"CustomPrompt with id {prompt_id} not found")
        
        # 检查权限
        if prompt.oid != current_user.oid:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        session.delete(prompt)
        session.commit()
        
        return {
            "success": True,
            "message": "CustomPrompt deleted successfully"
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete custom prompt: {str(e)}")

