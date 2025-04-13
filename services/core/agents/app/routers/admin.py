from fastapi import APIRouter

router = APIRouter(
    prefix="/admin",
    tags=["Admin - Overview"],
    # TODO: Add dependencies=[Depends(require_admin_user)] for security
)

# Example: Maybe an overview endpoint?
# @router.get("/overview")
# async def get_admin_overview():
#     return {"message": "Admin Overview"}

# Note: Specific resource routes (providers, models, etc.) are in sub-modules.