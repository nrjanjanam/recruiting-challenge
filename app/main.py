# Main entrypoint for FastAPI app
from fastapi import FastAPI
import uvicorn
from app.routers.register import register_routers
from app.services.logging_config import setup_logging
from app.services.openapi_schema import custom_openapi
from app.services.port_utils import get_available_port
from app.config import settings

app = FastAPI()

# Setup logging
logger = setup_logging()

# Custom OpenAPI schema for enhanced documentation
app.openapi = lambda: custom_openapi(app)

# Include routers
register_routers(app)

# Use config for port/host
port = settings.PORT
host = settings.HOST

if __name__ == "__main__":
    logger.info("Starting FastAPI server with Loguru logging!")
    logger.info(f"Using port {port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=settings.RELOAD)
