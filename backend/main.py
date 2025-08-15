import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.init_db import init_database
from app.api.v1.router import api_router

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire du cycle de vie de l'application
    Initialise la base de données au démarrage
    """
    logger.info("🚀 Démarrage de Visibility Tracker API...")
    
    try:
        # Initialiser la base de données
        init_database()
        logger.info("✅ Base de données initialisée avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
        raise
    
    yield
    
    logger.info("🛑 Arrêt de Visibility Tracker API")

# Création de l'instance FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## 🎯 Visibility Tracker API

    API pour analyser la visibilité des marques dans les réponses des LLM.

    ### Fonctionnalités principales :
    - **Projets** : Gestion des projets SEO avec mots-clés et concurrents
    - **Prompts** : Templates de prompts avec variables et tags
    - **Modèles IA** : Configuration des modèles OpenAI, Anthropic, etc.
    - **Analyses** : Exécution et suivi des analyses de visibilité
    - **Statistiques** : Métriques et rapports de performance

    ### Authentification :
    Actuellement en mode développement (pas d'authentification requise).

    ### Liens utiles :
    - [Documentation interactive](/docs)
    - [Schéma OpenAPI](/openapi.json)
    - [Health check](/)
    """,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG,
    lifespan=lifespan,
    # Support du root path pour le déploiement avec reverse proxy
    root_path=settings.ROOT_PATH
)

# Configuration CORS pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Middleware de gestion d'erreurs globales
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Gestionnaire d'exceptions HTTP personnalisé
    """
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url.path),
            "method": request.method
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Gestionnaire d'erreurs de validation Pydantic
    """
    logger.warning(f"Erreur de validation: {exc.errors()} - {request.method} {request.url}")
    
    # Nettoyer les erreurs pour la sérialisation JSON
    clean_errors = []
    for error in exc.errors():
        clean_error = {
            "type": error.get("type", "unknown"),
            "loc": error.get("loc", []),
            "msg": error.get("msg", "Erreur de validation"),
            "input": str(error.get("input", "")) if error.get("input") is not None else ""
        }
        clean_errors.append(clean_error)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "status_code": 422,
            "message": "Erreur de validation des données",
            "details": clean_errors,
            "path": str(request.url.path),
            "method": request.method
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Gestionnaire d'exceptions générales
    """
    logger.error(f"Erreur interne: {str(exc)} - {request.method} {request.url}", exc_info=True)
    
    if settings.DEBUG:
        # En mode debug, retourner les détails de l'erreur
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "status_code": 500,
                "message": "Erreur interne du serveur",
                "debug_info": str(exc),
                "path": str(request.url.path),
                "method": request.method
            }
        )
    else:
        # En production, masquer les détails
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "status_code": 500,
                "message": "Erreur interne du serveur",
                "path": str(request.url.path),
                "method": request.method
            }
        )

# Health check endpoint
@app.get("/", tags=["health"])
async def health_check():
    """
    Health check endpoint
    
    Retourne le statut de l'API et des informations de base.
    Utile pour les outils de monitoring et les tests de connectivité.
    """
    return {
        "status": "healthy",
        "message": "🎯 Visibility Tracker API is running!",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug_mode": settings.DEBUG,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "endpoints": {
            "projects": "/api/v1/projects/",
            "ai_models": "/api/v1/ai-models/",
            "prompts": "/api/v1/prompts/",
            "analyses": "/api/v1/analyses/"
        }
    }

# Endpoint d'informations détaillées
@app.get("/info", tags=["health"])
async def app_info():
    """
    Informations détaillées sur l'application
    
    Utile pour le debugging et la configuration
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "database_url": settings.DATABASE_URL,
        "cors_origins": settings.BACKEND_CORS_ORIGINS,
        "log_level": settings.LOG_LEVEL,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "default_max_tokens": settings.DEFAULT_MAX_TOKENS,
        "request_timeout": settings.REQUEST_TIMEOUT
    }

# Servir les fichiers statiques du frontend
from fastapi.staticfiles import StaticFiles

# Inclusion du routeur principal API v1
app.include_router(api_router, prefix="/api/v1")

# Servir les fichiers statiques (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route pour servir l'index.html à la racine et pour toutes les routes frontend
from fastapi.responses import FileResponse
import os

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """
    Servir le frontend SPA pour toutes les routes non-API
    """
    # Si c'est une route API, ne pas intercepter
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Si c'est un fichier statique, le servir
    static_file_path = f"static/{full_path}"
    if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
        return FileResponse(static_file_path)
    
    # Sinon, servir index.html pour le SPA
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

# Middleware de logging des requêtes (optionnel)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware pour logger les requêtes HTTP
    """
    # Logger la requête entrante
    logger.info(f"📥 {request.method} {request.url}")
    
    # Traiter la requête
    response = await call_next(request)
    
    # Logger la réponse
    logger.info(f"📤 {request.method} {request.url} - {response.status_code}")
    
    return response

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Démarrage en mode développement...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8021,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 