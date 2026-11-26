from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException


class Problem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str


def problem(
    request: Request,
    status: int,
    detail: str,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = Problem(
        title=HTTPStatus(status).phrase, status=status, detail=detail, instance=request.url.path
    )
    return JSONResponse(
        body.model_dump(),
        status_code=status,
        headers=headers,
        media_type="application/problem+json",
    )


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    code: {
        "description": HTTPStatus(code).phrase,
        "content": {"application/problem+json": {"schema": Problem.model_json_schema()}},
    }
    for code in (401, 404, 422, 500, 501, 503)
}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return problem(request, exc.status_code, str(exc.detail), exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Ne pas renvoyer les valeurs saisies, qui peuvent contenir des secrets.
        fields = [".".join(map(str, error["loc"])) for error in exc.errors()]
        return problem(request, 422, "Paramètres invalides : " + ", ".join(fields))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return problem(request, 500, "Erreur interne du serveur")
