"""
数据源权限管理 API
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from apps.datasource.models.ds_permission import DsPermission, DsRules
from apps.datasource.schemas.permission_schema import PermissionDTO, transRecord2DTO
from common.core.deps import CurrentUser, SessionDep

router = APIRouter(tags=["ds_permission"], prefix="/ds_permission")


class PermissionSaveRequest(BaseModel):
    """权限保存请求"""
    id: Optional[int] = None
    enable: bool = True
    auth_target_type: Optional[str] = None
    auth_target_id: Optional[int] = None
    type: str  # 'row' or 'column'
    ds_id: Optional[int] = None
    table_id: Optional[int] = None
    expression_tree: Optional[str] = None
    permissions: Optional[str] = None
    white_list_user: Optional[str] = None
    name: Optional[str] = None


class RuleSaveRequest(BaseModel):
    """规则保存请求"""
    id: Optional[int] = None
    enable: bool = True
    name: str
    description: Optional[str] = None
    permission_list: Optional[str] = "[]"
    user_list: Optional[str] = "[]"
    white_list_user: Optional[str] = "[]"


@router.post("/list")
async def get_permission_list(
    session: SessionDep,
    current_user: CurrentUser
) -> dict:
    """
    获取权限列表
    
    Returns:
        包含权限和规则的字典
    """
    # 获取所有权限
    permissions = session.exec(select(DsPermission)).all()
    permission_list = [
        PermissionDTO(
            id=p.id,
            enable=p.enable,
            auth_target_type=p.auth_target_type,
            auth_target_id=p.auth_target_id,
            type=p.type,
            ds_id=p.ds_id,
            table_id=p.table_id,
            expression_tree=p.expression_tree,
            permissions=p.permissions,
            white_list_user=p.white_list_user,
            create_time=p.create_time,
            name=p.name
        )
        for p in permissions
    ]
    
    # 获取所有规则
    rules = session.exec(select(DsRules)).all()
    rule_list = [
        {
            "id": r.id,
            "enable": r.enable,
            "name": r.name,
            "description": r.description,
            "permission_list": r.permission_list,
            "user_list": r.user_list,
            "white_list_user": r.white_list_user,
            "create_time": r.create_time.isoformat() if r.create_time else None,
            "oid": r.oid
        }
        for r in rules
    ]
    
    return {
        "permissions": [p.model_dump() for p in permission_list],
        "rules": rule_list
    }


@router.post("/save")
async def save_permission(
    session: SessionDep,
    current_user: CurrentUser,
    data: PermissionSaveRequest
) -> dict:
    """
    保存权限
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        data: 权限数据
        
    Returns:
        保存结果
    """
    try:
        if data.id:
            # 更新现有权限
            permission = session.get(DsPermission, data.id)
            if not permission:
                raise HTTPException(status_code=404, detail=f"Permission with id {data.id} not found")
            
            permission.enable = data.enable
            permission.auth_target_type = data.auth_target_type
            permission.auth_target_id = data.auth_target_id
            permission.type = data.type
            permission.ds_id = data.ds_id
            permission.table_id = data.table_id
            permission.expression_tree = data.expression_tree
            permission.permissions = data.permissions
            permission.white_list_user = data.white_list_user
            permission.name = data.name
        else:
            # 创建新权限
            from datetime import datetime
            permission = DsPermission(
                enable=data.enable,
                auth_target_type=data.auth_target_type,
                auth_target_id=data.auth_target_id,
                type=data.type,
                ds_id=data.ds_id,
                table_id=data.table_id,
                expression_tree=data.expression_tree,
                permissions=data.permissions,
                white_list_user=data.white_list_user,
                create_time=datetime.now(),
                name=data.name
            )
            session.add(permission)
        
        session.commit()
        session.refresh(permission)
        
        return {
            "success": True,
            "message": "Permission saved successfully",
            "id": permission.id
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save permission: {str(e)}")


@router.post("/delete/{id}")
async def delete_permission(
    session: SessionDep,
    current_user: CurrentUser,
    id: int
) -> dict:
    """
    删除权限
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        id: 权限 ID
        
    Returns:
        删除结果
    """
    try:
        permission = session.get(DsPermission, id)
        if not permission:
            raise HTTPException(status_code=404, detail=f"Permission with id {id} not found")
        
        session.delete(permission)
        session.commit()
        
        return {
            "success": True,
            "message": "Permission deleted successfully"
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete permission: {str(e)}")


@router.post("/rule/save")
async def save_rule(
    session: SessionDep,
    current_user: CurrentUser,
    data: RuleSaveRequest
) -> dict:
    """
    保存规则
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        data: 规则数据
        
    Returns:
        保存结果
    """
    try:
        if data.id:
            # 更新现有规则
            rule = session.get(DsRules, data.id)
            if not rule:
                raise HTTPException(status_code=404, detail=f"Rule with id {data.id} not found")
            
            rule.enable = data.enable
            rule.name = data.name
            rule.description = data.description
            rule.permission_list = data.permission_list
            rule.user_list = data.user_list
            rule.white_list_user = data.white_list_user
        else:
            # 创建新规则
            from datetime import datetime
            rule = DsRules(
                enable=data.enable,
                name=data.name,
                description=data.description,
                permission_list=data.permission_list,
                user_list=data.user_list,
                white_list_user=data.white_list_user,
                create_time=datetime.now()
            )
            session.add(rule)
        
        session.commit()
        session.refresh(rule)
        
        return {
            "success": True,
            "message": "Rule saved successfully",
            "id": rule.id
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save rule: {str(e)}")


@router.post("/rule/delete/{id}")
async def delete_rule(
    session: SessionDep,
    current_user: CurrentUser,
    id: int
) -> dict:
    """
    删除规则
    
    Args:
        session: 数据库会话
        current_user: 当前用户
        id: 规则 ID
        
    Returns:
        删除结果
    """
    try:
        rule = session.get(DsRules, id)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule with id {id} not found")
        
        session.delete(rule)
        session.commit()
        
        return {
            "success": True,
            "message": "Rule deleted successfully"
        }
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete rule: {str(e)}")

