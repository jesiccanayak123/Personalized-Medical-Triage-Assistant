"""Application entry point."""

import uvicorn

from app.application import get_app
from config.settings import settings

# Create the application
app = get_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug,
        log_level="info",
    )

