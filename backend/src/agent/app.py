# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
import fastapi.exceptions
from fastapi.middleware.cors import CORSMiddleware

# Define the FastAPI app for agent-specific routes
agent_fastapi_app = FastAPI(
    title="Deepest Research Agent API",
    version="0.1.0",
    # The comment below advised against adding CORS here,
    # but it's necessary for the dev server to allow frontend requests.
    # Füge hier ggf. weitere FastAPI-Parameter hinzu, aber KEINE CORS-Middleware
)

# Define allowed origins for CORS
origins = [
    "http://localhost:5173",  # React frontend development server
    "http://127.0.0.1:5173", # Also common for localhost
]

# Add CORS middleware
agent_fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (Definition deiner Routen für agent_fastapi_app, falls vorhanden) ...
# agent_fastapi_app.include_router(...)

# Stelle sicher, dass die Variable 'app' auf deine FastAPI-Instanz zeigt,
# damit langgraph dev sie finden kann.
app = agent_fastapi_app

def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir
    static_files_path = build_path / "assets"  # Vite uses 'assets' subdir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    build_dir = pathlib.Path(build_dir)

    react = FastAPI(openapi_url="")
    react.mount(
        "/assets", StaticFiles(directory=static_files_path), name="static_assets"
    )

    @react.get("/{path:path}")
    async def handle_catch_all(request: Request, path: str):
        fp = build_path / path
        if not fp.exists() or not fp.is_file():
            fp = build_path / "index.html"
        return fastapi.responses.FileResponse(fp)

    return react


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
)
