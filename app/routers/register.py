from .profile_create import router as create_profile_router
from .profile_verify import router as verify_profile_router
from .profile_create_5poses import router as create_profile_5poses_router
from .quality_check import router as quality_check_router
from .health import router as health_router
from .chromadb_manage import router as chromadb_manage_router
from app.services.port_utils import get_available_port
from app.routers.root import router as root_router

def register_routers(app):
    # Routers are already versioned with prefix, so just include them
    app.include_router(root_router)
    app.include_router(create_profile_router)
    app.include_router(verify_profile_router)
    app.include_router(create_profile_5poses_router)
    app.include_router(quality_check_router)
    app.include_router(health_router)
    app.include_router(chromadb_manage_router)
