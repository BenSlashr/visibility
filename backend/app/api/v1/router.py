from fastapi import APIRouter

from .endpoints import projects, ai_models, prompts, analyses, sources, serp

api_router = APIRouter()

# Inclusion des routers d'endpoints avec leurs préfixes
api_router.include_router(
    projects.router, 
    prefix="/projects", 
    tags=["projects"]
)

api_router.include_router(
    ai_models.router, 
    prefix="/ai-models", 
    tags=["ai-models"]
)

api_router.include_router(
    prompts.router, 
    prefix="/prompts", 
    tags=["prompts"]
)

api_router.include_router(
    analyses.router, 
    prefix="/analyses", 
    tags=["analyses"]
) 

api_router.include_router(
    sources.router,
    prefix="/sources",
    tags=["sources"]
)

api_router.include_router(
    serp.router,
    prefix="/serp",
    tags=["serp", "seo"]
)