"""
数据源权限相关模型 - 开源版本
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Identity, String, Text
from sqlmodel import Field, SQLModel


class DsRules(SQLModel, table=True):
    """数据源规则表"""
    __tablename__ = "ds_rules"
    
    id: Optional[int] = Field(
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True)
    )
    enable: bool = Field(default=True)
    name: str = Field(max_length=128)
    description: Optional[str] = Field(max_length=512, default=None)
    permission_list: Optional[str] = Field(sa_column=Column(Text, default="[]"))
    user_list: Optional[str] = Field(sa_column=Column(Text, default="[]"))
    white_list_user: Optional[str] = Field(sa_column=Column(Text, default="[]"))
    create_time: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=False), nullable=True)
    )
    oid: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))


class DsPermission(SQLModel, table=True):
    """数据源权限表"""
    __tablename__ = "ds_permission"
    
    id: Optional[int] = Field(
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True)
    )
    enable: bool = Field(default=True)
    auth_target_type: Optional[str] = Field(max_length=128, default=None)
    auth_target_id: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))
    type: str = Field(max_length=64)  # 'row' or 'column'
    ds_id: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))
    table_id: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))
    expression_tree: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    permissions: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    white_list_user: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    create_time: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=False), nullable=True)
    )
    name: Optional[str] = Field(max_length=128, default=None)

