from fastapi.openapi.utils import get_openapi

def custom_openapi(app) -> dict:
    """Return a custom OpenAPI schema for the FastAPI app."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Facial Profile Creator API",
        version="1.0.0",
        description="API for uploading images and generating facial profiles. Upload an image to `/create-profile` to receive a profile description. See the /docs endpoint for interactive usage.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema
