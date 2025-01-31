from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from .checks.raster_context import LocalContext, ServerContext

__all__ = ["ctx", "model_checker_ctx"]


class Context:
    def __init__(self) -> None:
        self._model_checker_context: ContextVar[
            LocalContext | ServerContext | None
        ] = ContextVar("model_checker_context", default=None)
        self._epsg_ref_code: ContextVar[int | None] = ContextVar(
            "epsg_ref_code", default=None
        )
        self._epsg_ref_name: ContextVar[str | None] = ContextVar(
            "epsg_ref_name", default=None
        )

    @property
    def model_checker_context(self) -> LocalContext | ServerContext | None:
        return self._model_checker_context.get()

    @model_checker_context.setter
    def model_checker_context(self, value: LocalContext | ServerContext | None) -> None:
        self._model_checker_context.set(value)

    @property
    def epsg_ref_code(self) -> int | None:
        return self._epsg_ref_code.get()

    @epsg_ref_code.setter
    def epsg_ref_code(self, value: int | None) -> None:
        self._epsg_ref_code.set(value)

    @property
    def epsg_ref_name(self) -> str | None:
        return self._epsg_ref_name.get()

    @epsg_ref_name.setter
    def epsg_ref_name(self, value: str | None) -> None:
        self._epsg_ref_name.set(value)


ctx = Context()


@contextmanager
def model_checker_ctx(
    model_checker_context: LocalContext | ServerContext | None = None,
    epsg_ref_code: int | None = None,
    epsg_ref_name: str | None = None,
) -> Iterator[None]:
    print("INIT", model_checker_context, epsg_ref_code, epsg_ref_name)
    print("JOOO", ctx.model_checker_context)
    assert ctx.model_checker_context is None
    ctx.model_checker_context = model_checker_context
    ctx.epsg_ref_code = epsg_ref_code
    ctx.epsg_ref_name = epsg_ref_name
    try:
        yield
    finally:
        ctx.model_checker_context = None
        ctx.epsg_ref_code = None
        ctx.epsg_ref_name = None
