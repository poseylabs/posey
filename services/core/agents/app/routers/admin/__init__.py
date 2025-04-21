from fastapi import APIRouter

from .llm_providers import router as llm_providers_router
from .llm_models import router as llm_models_router
from .minion_configs import router as minion_configs_router
from .managed_minions import router as managed_minions_router

router = APIRouter(prefix="/admin")
router.include_router(llm_providers_router)
router.include_router(llm_models_router)
router.include_router(minion_configs_router)
router.include_router(managed_minions_router)

__all__ = ["router"] 