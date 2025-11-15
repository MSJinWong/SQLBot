"""
权限相关的 Schema 和 DTO
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from apps.datasource.models.ds_permission import DsPermission


class PermissionDTO(BaseModel):
    """权限 DTO"""
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
    create_time: Optional[datetime] = None
    name: Optional[str] = None

    class Config:
        from_attributes = True


def transRecord2DTO(session: Any, permission: DsPermission) -> PermissionDTO:
    """转换权限记录为 DTO"""
    return PermissionDTO(
        id=permission.id,
        enable=permission.enable,
        auth_target_type=permission.auth_target_type,
        auth_target_id=permission.auth_target_id,
        type=permission.type,
        ds_id=permission.ds_id,
        table_id=permission.table_id,
        expression_tree=permission.expression_tree,
        permissions=permission.permissions,
        white_list_user=permission.white_list_user,
        create_time=permission.create_time,
        name=permission.name,
    )

