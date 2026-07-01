from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from starlette.responses import RedirectResponse

from rivo_drome.container.default_container import DefaultContainer
from rivo_drome.controller.example_controller import ExampleController


app = FastAPI(
    title="Example API",
    description="Minimal boilerplate API",
    version="1.0.0",
)

default_container: DefaultContainer = DefaultContainer.getInstance()
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


if __name__ == "__main__":
    uvicorn.run(
        "namespace.api:app",
        host=default_container.get_var("api_host"),
        port=default_container.get_var("api_port"),
        reload=False,
    )
