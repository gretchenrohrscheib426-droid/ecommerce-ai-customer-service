"""Local API; startup never imports SQL, retrains models or rebuilds graph indexes."""

import asyncio
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from ..config import Settings
from ..health import status as dependency_status
from ..logging_config import configure_logging
from ..qa.schema import Question
from .schemas import StatusResponse


def wait_for_database(instance, timeout=40, pause=time.sleep):
    """Retry only transient startup connectivity; configuration failures still fail closed."""
    from neo4j.exceptions import ServiceUnavailable, SessionExpired

    deadline = time.monotonic() + timeout
    while True:
        try:
            instance.verify_connectivity()
            with instance.session(database="neo4j") as session:
                session.run("RETURN 1").consume()
            return
        except (ServiceUnavailable, SessionExpired):
            if time.monotonic() >= deadline:
                raise
            pause(0.5)


def create_app(service=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.service = service
        app.state.ready = False
        app.state.reason = "starting"
        app.state.gate = threading.BoundedSemaphore(2)
        scope = None
        try:
            if service is None:
                from ..db.neo4j import driver
                from ..retrieval.indexes import Embedder

                settings = Settings.load()
                configure_logging(settings.log_level)
                scope = driver(settings.root)
                instance = scope.__enter__()
                await asyncio.to_thread(wait_for_database, instance)
                with instance.session(database="system") as session:
                    access = session.run(
                        "SHOW DATABASES YIELD name,access WHERE name='neo4j' RETURN access"
                    ).single()["access"]
                if access != "read-only":
                    raise RuntimeError("Database must be in read-only serving mode")
                with instance.session(database="neo4j") as session:
                    indexes = [
                        r
                        for r in session.run(
                            "SHOW INDEXES YIELD type,state WHERE type IN ['FULLTEXT','VECTOR'] RETURN type,state"
                        )
                    ]
                    if len(indexes) != 10 or any(r["state"] != "ONLINE" for r in indexes):
                        raise RuntimeError("Ten ONLINE retrieval indexes required")
                    scopes = [r["scope"] for r in session.run("MATCH (n) RETURN DISTINCT n.dataset AS scope")]
                    if len(scopes) != 1:
                        raise RuntimeError("One owned dataset required")
                embedder = await asyncio.to_thread(Embedder, settings.root)
                from .service import build_service

                app.state.service = build_service(settings, instance, embedder, scopes[0])
            app.state.ready = True
            app.state.reason = "ready"
        except Exception as error:
            app.state.reason = type(error).__name__
        try:
            yield
        finally:
            if scope:
                scope.__exit__(None, None, None)

    app = FastAPI(title="电商图谱 · 本地复现", lifespan=lifespan, docs_url="/docs", redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    @app.middleware("http")
    async def bounds(request: Request, call_next):
        if request.method == "POST":
            origin = request.headers.get("origin")
            port = Settings.load().api_port
            if origin and origin not in {
                f"http://127.0.0.1:{port}",
                f"http://localhost:{port}",
                "http://testserver",
            }:
                return JSONResponse({"message": "Origin rejected"}, status_code=403)
            if len(await request.body()) > 8192:
                return JSONResponse({"message": "Request body too large"}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        )
        return response

    @app.get("/health/live")
    def live():
        return {"status": "up"}

    @app.get("/health")
    def health():
        return {"app": "ok", "ready": app.state.ready}

    @app.get("/api/status", response_model=StatusResponse)
    def status():
        return dependency_status(Settings.load().root, app.state.service)

    @app.get("/health/ready")
    def ready():
        if not app.state.ready:
            return JSONResponse({"status": "unavailable", "reason": app.state.reason}, status_code=503)
        try:
            if getattr(app.state.service, "driver", None):
                with app.state.service.driver.session(database="neo4j") as session:
                    session.run("RETURN 1").consume()
        except Exception:
            return JSONResponse({"status": "unavailable", "reason": "database"}, status_code=503)
        return {
            "status": "ready",
            "mode": "online" if getattr(app.state.service, "online", False) else "offline-local-templates",
            "annotation_services": "optional-not-probed",
            "raw_cypher": False,
        }

    @app.post("/api/chat")
    async def chat(question: Question):
        if not app.state.ready:
            return JSONResponse(
                {"message": "服务尚未就绪，请查看健康检查。", "status": "dependency_unavailable"},
                status_code=503,
            )

        def work():
            if not app.state.gate.acquire(blocking=False):
                return JSONResponse(
                    {"message": "当前请求较多，请稍后重试。", "status": "busy"}, status_code=429
                )
            try:
                return app.state.service.chat(question)
            finally:
                app.state.gate.release()

        try:
            return await asyncio.wait_for(asyncio.to_thread(work), timeout=45)
        except asyncio.TimeoutError:
            return JSONResponse({"message": "处理超时，请稍后重试。", "status": "timeout"}, status_code=504)
        except Exception:
            return JSONResponse(
                {"message": "查询依赖发生故障，本次未生成商品答案。", "status": "dependency_unavailable"},
                status_code=503,
            )

    static = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")

    return app


app = create_app()
