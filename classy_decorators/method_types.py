from __future__ import annotations

__all__ = [
    "get_function_type",
    "FunctionType",
    "ClassMethod",
    "ClassMethodDescriptor",
]

import enum
import inspect
from typing import Any, Callable, Protocol, TypeVar, Union, runtime_checkable

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)
C = TypeVar("C", bound=Callable)

FT = TypeVar("FT", bound=Callable[..., Any])
CMD_contra = TypeVar(
    "CMD_contra", classmethod, staticmethod, contravariant=True
)


@runtime_checkable
class ClassMethodDescriptor(Protocol[CMD_contra, FT]):
    __func__: FT

    def __get__(self, __origin: CMD_contra, *args, **kwargs):
        ...  # pragma: no cover


@runtime_checkable
class ClassMethod(ClassMethodDescriptor, Protocol[FT]):
    __call__: FT


class FunctionType(enum.Flag):
    FUNCTION = enum.auto()

    INSTANCEMETHOD_BOUND = enum.auto()
    INSTANCEMETHOD_UNBOUND = enum.auto()
    INSTANCEMETHOD = INSTANCEMETHOD_BOUND | INSTANCEMETHOD_UNBOUND

    CLASSMETHOD_BOUND = enum.auto()
    CLASSMETHOD_UNBOUND = enum.auto()
    CLASSMETHOD = CLASSMETHOD_BOUND | CLASSMETHOD_UNBOUND

    STATICMETHOD_BOUND = enum.auto()
    STATICMETHOD_UNBOUND = enum.auto()
    STATICMETHOD = STATICMETHOD_BOUND | STATICMETHOD_UNBOUND

    METHOD_BOUND = INSTANCEMETHOD_BOUND | CLASSMETHOD_BOUND | STATICMETHOD_BOUND
    METHOD_UNBOUND = (
        INSTANCEMETHOD_UNBOUND | CLASSMETHOD_UNBOUND | STATICMETHOD_UNBOUND
    )
    METHOD = METHOD_BOUND | METHOD_UNBOUND

    def __str__(self) -> str:
        if self is FunctionType.FUNCTION:
            return "function"

        tokens = []
        if self in FunctionType.METHOD_BOUND:
            tokens.append("bound")
        elif self in FunctionType.METHOD_UNBOUND:
            tokens.append("unbound")

        if self in FunctionType.CLASSMETHOD:
            tokens.append("classmethod")
        elif self in FunctionType.STATICMETHOD:
            tokens.append("staticmethod")
        else:
            tokens.append("method")

        return " ".join(tokens)

    def as_bound(self) -> FunctionType:
        if self is FunctionType.FUNCTION:
            raise TypeError("cannot bind functions")
        elif self in FunctionType.METHOD_BOUND:
            raise TypeError("already bound")

        elif self is FunctionType.INSTANCEMETHOD_UNBOUND:
            return FunctionType.INSTANCEMETHOD_BOUND
        elif self is FunctionType.CLASSMETHOD_UNBOUND:
            return FunctionType.CLASSMETHOD_BOUND
        elif self is FunctionType.STATICMETHOD_UNBOUND:
            return FunctionType.STATICMETHOD_BOUND
        else:  # pragma: no cover
            raise TypeError(f"unknown {repr(self)}")


def get_function_type(
    fn: Union[Callable, ClassMethodDescriptor]
) -> FunctionType:
    """If ignore_staticmethod is set, staticmethods are considered functions"""
    if isinstance(fn, classmethod):
        return FunctionType.CLASSMETHOD_UNBOUND
    elif isinstance(fn, staticmethod):
        return FunctionType.STATICMETHOD_UNBOUND
    elif not callable(fn):
        raise TypeError(type(fn))

    instance = getattr(fn, "__self__", None)
    if isinstance(instance, type):
        return FunctionType.CLASSMETHOD_BOUND
    elif instance is not None:
        return FunctionType.INSTANCEMETHOD_BOUND

    params = list(inspect.signature(fn).parameters)
    if params and params[0] == "self":
        return FunctionType.INSTANCEMETHOD_UNBOUND
    else:
        return FunctionType.FUNCTION
