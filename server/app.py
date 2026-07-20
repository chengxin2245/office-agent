"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes import router
from server.sessions import session_manager


def create_app() -> FastAPI:
    app = FastAPI(title="Office Automation Agent")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.on_event("startup")
    async def startup():
        await session_manager.start_cleanup_loop()

    @app.on_event("shutdown")
    async def shutdown():
        await session_manager.shutdown()

    return app


app = create_app()
