from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from starlette.responses import RedirectResponse

from rivo_drome.container.default_container import DefaultContainer
from rivo_drome.controller.example_controller import ExampleController
from rivo_drome.controller.navidrome_proxy_controller import NavidromeProxyController
from rivo_drome.controller.search_controller import SearchController
from rivo_drome.controller.stream_controller import StreamController


default_container: DefaultContainer = DefaultContainer.getInstance()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Rimosso BaseEntity.metadata.create_all per evitare conflitti con Alembic.
    # Le tabelle devono essere create esclusivamente tramite `alembic upgrade head`.
    yield


app = FastAPI(
    title="Rivo-Drome",
    description="Proxy Subsonic con ricerca Deezer e streaming on-demand",
    version="1.0.0",
    lifespan=lifespan,
)

example_controller: ExampleController = default_container.get(ExampleController)

app.include_router(example_controller.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


search_controller: SearchController = default_container.get(SearchController)

app.include_router(search_controller.router)

stream_controller: StreamController = default_container.get(StreamController)

app.include_router(stream_controller.router)

navidrome_proxy_controller: NavidromeProxyController = default_container.get(NavidromeProxyController)

app.include_router(navidrome_proxy_controller.router)


if __name__ == "__main__":
    uvicorn.run(
        "rivo_drome.api:app",
        host=default_container.get_var("api_host"),
        port=default_container.get_var("api_port"),
        reload=False,
    )
