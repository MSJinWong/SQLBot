"""
自定义提示词 CRUD 操作
"""
from typing import List, Optional

from sqlmodel import select

from apps.system.models.system_model import CustomPrompt, CustomPromptTypeEnum
from common.core.deps import SessionDep


def find_custom_prompts(
    session: SessionDep,
    oid: int,
    prompt_type: CustomPromptTypeEnum,
    ds_id: Optional[int] = None
) -> List[CustomPrompt]:
    """
    查找自定义提示词
    
    Args:
        session: 数据库会话
        oid: 组织 ID
        prompt_type: 提示词类型
        ds_id: 数据源 ID（可选）
        
    Returns:
        自定义提示词列表
    """
    # 基础查询：匹配 oid 和 type
    query = select(CustomPrompt).where(
        CustomPrompt.oid == oid,
        CustomPrompt.type == prompt_type.value
    )
    
    prompts = session.exec(query).all()
    
    # 如果指定了 ds_id，过滤出适用的提示词
    if ds_id is not None:
        filtered_prompts = []
        for prompt in prompts:
            # 如果不是特定数据源的提示词，则适用于所有数据源
            if not prompt.specific_ds:
                filtered_prompts.append(prompt)
            # 如果是特定数据源的提示词，检查 ds_id 是否在列表中
            elif prompt.datasource_ids:
                import json
                try:
                    ds_ids = json.loads(prompt.datasource_ids) if isinstance(prompt.datasource_ids, str) else prompt.datasource_ids
                    if ds_id in ds_ids:
                        filtered_prompts.append(prompt)
                except (json.JSONDecodeError, TypeError):
                    # 如果解析失败，跳过这个提示词
                    pass
        return filtered_prompts
    
    return list(prompts)


def get_custom_prompt_template(
    session: SessionDep,
    oid: int,
    prompt_type: CustomPromptTypeEnum,
    ds_id: Optional[int] = None
) -> str:
    """
    获取自定义提示词模板（合并所有适用的提示词）
    
    Args:
        session: 数据库会话
        oid: 组织 ID
        prompt_type: 提示词类型
        ds_id: 数据源 ID（可选）
        
    Returns:
        合并后的提示词文本
    """
    prompts = find_custom_prompts(session, oid, prompt_type, ds_id)
    
    if not prompts:
        return ""
    
    # 合并所有提示词
    prompt_texts = []
    for prompt in prompts:
        if prompt.prompt:
            prompt_texts.append(prompt.prompt.strip())
    
    return "\n\n".join(prompt_texts) if prompt_texts else ""

