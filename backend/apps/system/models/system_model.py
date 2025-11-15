from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text as SAText
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import BigInteger, Field, Text, SQLModel
from common.core.models import SnowflakeBase
from common.core.schemas import BaseCreatorDTO


class CustomPromptTypeEnum(str, Enum):
    """自定义提示词类型枚举"""
    GENERATE_SQL = "GENERATE_SQL"
    ANALYSIS = "ANALYSIS"
    PREDICT_DATA = "PREDICT_DATA"


class AiModelBase:
    supplier: int = Field(nullable=False)
    name: str = Field(max_length=255, nullable=False)
    model_type: int = Field(nullable=False)
    base_model: str = Field(max_length = 255, nullable=False)
    default_model: bool = Field(default=False, nullable=False)

class AiModelDetail(SnowflakeBase, AiModelBase, table=True):
   __tablename__ = "ai_model"
   api_key: str | None = Field(nullable=True)
   api_domain: str = Field(nullable=False)
   protocol: int = Field(nullable=False, default = 1)
   config: str = Field(sa_type = Text())
   status: int = Field(nullable=False, default = 1)
   create_time: int = Field(default=0, sa_type=BigInteger())
   



class WorkspaceBase(SQLModel):
    name: str = Field(max_length=255, nullable=False)

class WorkspaceEditor(WorkspaceBase, BaseCreatorDTO):
    pass
    
class WorkspaceModel(SnowflakeBase, WorkspaceBase, table=True):
    __tablename__ = "sys_workspace"
    create_time: int = Field(default=0, sa_type=BigInteger())
    
class UserWsBaseModel(SQLModel):
    uid: int = Field(nullable=False, sa_type=BigInteger())
    oid: int = Field(nullable=False, sa_type=BigInteger())
    weight: int =  Field(default=0, nullable=False)
    
class UserWsModel(SnowflakeBase, UserWsBaseModel, table=True):
    __tablename__ = "sys_user_ws"
    

class AssistantBaseModel(SQLModel):
    name: str = Field(max_length=255, nullable=False)
    type: int = Field(nullable=False, default=0)
    domain: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(sa_type = Text(), nullable=True)
    configuration: Optional[str] = Field(sa_type = Text(), nullable=True)
    create_time: int = Field(default=0, sa_type=BigInteger())
    app_id: Optional[str] = Field(default=None, max_length=255,  nullable=True)
    app_secret: Optional[str] = Field(default=None, max_length=255, nullable=True)

class AssistantModel(SnowflakeBase, AssistantBaseModel, table=True):
    __tablename__ = "sys_assistant"
    

class AuthenticationBaseModel(SQLModel):
    name: str = Field(max_length=255, nullable=False)
    type: int = Field(nullable=False, default=0)
    config: Optional[str] = Field(sa_type = Text(), nullable=True)
    
    
class AuthenticationModel(SnowflakeBase, AuthenticationBaseModel, table=True):
    __tablename__ = "sys_authentication"
    create_time: Optional[int] = Field(default=0, sa_type=BigInteger())
    enable: bool = Field(default=False, nullable=False)
    valid: bool = Field(default=False, nullable=False)


class SysArg(SQLModel, table=True):
    """系统参数表 - 用于存储外观设置等系统配置"""
    __tablename__ = "sys_arg"

    id: Optional[int] = Field(
        sa_column=Column(BigInteger, primary_key=True, nullable=False, comment='ID')
    )
    pkey: str = Field(
        sa_column=Column(String(255), nullable=False, comment='pkey')
    )
    pval: Optional[str] = Field(
        sa_column=Column(String(255), nullable=True, comment='pval')
    )
    ptype: str = Field(
        sa_column=Column(String(255), nullable=False, server_default='str', comment='str or file')
    )
    sort_no: int = Field(
        sa_column=Column(Integer, nullable=False, server_default='1', comment='sort_no')
    )


class CustomPrompt(SQLModel, table=True):
    """自定义提示词表"""
    __tablename__ = "custom_prompt"

    id: Optional[int] = Field(
        sa_column=Column(BigInteger, primary_key=True, nullable=False)
    )
    oid: Optional[int] = Field(
        sa_column=Column(BigInteger, nullable=True)
    )
    type: Optional[CustomPromptTypeEnum] = Field(
        sa_column=Column(String(20), nullable=True)
    )
    create_time: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=False), nullable=True)
    )
    name: Optional[str] = Field(max_length=255, nullable=True)
    prompt: Optional[str] = Field(
        sa_column=Column(SAText, nullable=True)
    )
    specific_ds: Optional[bool] = Field(
        sa_column=Column(Boolean, nullable=True)
    )
    datasource_ids: Optional[str] = Field(
        sa_column=Column(JSONB, nullable=True)
    )