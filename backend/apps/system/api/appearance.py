import json
import mimetypes
import os

from fastapi import APIRouter, HTTPException, Path, Request
from fastapi.responses import StreamingResponse
from sqlbot_xpack.config.model import SysArgModel
from sqlbot_xpack.file_utils import SQLBotFileUtils
from sqlmodel import select

from apps.system.schemas.permission import SqlbotPermission, require_permissions
from common.core.deps import SessionDep

router = APIRouter(
    tags=["system/appearance"],
    prefix="/system/appearance",
    include_in_schema=False,
)

APPEARANCE_PREFIX = "appearance."
ALLOWED_FILE_FLAGS = {
    "web",
    "login",
    "bg",
    "navigate",
    "mobileLogin",
    "mobileLoginBg",
}
ALLOWED_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".svg", ".gif"]
MAX_IMAGE_SIZE = 10 * 1024 * 1024


@router.get("/ui")
async def get_ui_config(session: SessionDep) -> list[dict]:
    args = session.exec(
        select(SysArgModel)
        .where(SysArgModel.pkey.startswith(APPEARANCE_PREFIX))
        .order_by(SysArgModel.sort_no)
    ).all()
    return [
        {
            "pkey": arg.pkey.removeprefix(APPEARANCE_PREFIX),
            "pval": arg.pval,
            "ptype": arg.ptype,
            "sort": arg.sort_no,
        }
        for arg in args
    ]


@router.post("")
@require_permissions(permission=SqlbotPermission(role=["admin"]))
async def save_appearance(session: SessionDep, request: Request):
    form_data = await request.form()
    json_text = form_data.get("data")
    if not isinstance(json_text, str):
        raise HTTPException(status_code=400, detail="Missing appearance data")

    try:
        config_items = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid appearance data") from exc

    if not isinstance(config_items, list):
        raise HTTPException(status_code=400, detail="Appearance data must be a list")

    file_mapping: dict[str, str] = {}
    for file in form_data.getlist("files"):
        if not file.filename:
            continue

        file_name, flag_name = SQLBotFileUtils.split_filename_and_flag(file.filename)
        if flag_name not in ALLOWED_FILE_FLAGS:
            raise HTTPException(
                status_code=400,
                detail=f"The file [{file_name}] is not allowed to be uploaded",
            )

        SQLBotFileUtils.check_file(
            file=file,
            file_types=ALLOWED_IMAGE_TYPES,
            limit_file_size=MAX_IMAGE_SIZE,
        )
        file.filename = file_name
        file_mapping[flag_name] = await SQLBotFileUtils.upload(file)

    old_file_ids: list[str] = []
    for item in config_items:
        if not isinstance(item, dict) or not item.get("pkey"):
            continue

        key = str(item["pkey"])
        full_key = f"{APPEARANCE_PREFIX}{key}"
        value = file_mapping.get(key, item.get("pval"))
        value_type = "file" if key in file_mapping else item.get("ptype", "str")

        existing = session.exec(
            select(SysArgModel).where(SysArgModel.pkey == full_key)
        ).first()
        if existing:
            if existing.ptype == "file" and existing.pval and existing.pval != value:
                old_file_ids.append(existing.pval)
            existing.pval = str(value) if value is not None else None
            existing.ptype = value_type
            existing.sort_no = item.get("sort", existing.sort_no)
            session.add(existing)
        else:
            session.add(
                SysArgModel(
                    pkey=full_key,
                    pval=str(value) if value is not None else None,
                    ptype=value_type,
                    sort_no=item.get("sort", 1),
                )
            )

    session.commit()

    for file_id in old_file_ids:
        try:
            SQLBotFileUtils.delete_file(file_id)
        except Exception:
            pass


@router.get("/picture/{file_id}")
async def get_picture(file_id: str = Path(description="file_id")):
    file_path = SQLBotFileUtils.get_file_path(file_id=file_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    media_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    def iterfile():
        with open(file_path, mode="rb") as image_file:
            yield from image_file

    return StreamingResponse(iterfile(), media_type=media_type)
