from __future__ import annotations

__all__ = ["Decorator"]

import functools
from typing import (
    Any,
    Callable,
    Final,
    Generic,
    NoReturn,
    Optional,
    Type,
    TypeVar,
    Union,
    final,
)

from classy_decorators.method_types import (
    ClassMethod,
    ClassMethodDescriptor,
    FunctionType,
    get_function_type,
)

# type to which the decorated method is bound
T = TypeVar("T")
# return value
RT = TypeVar("RT")
# decorated function
FT = TypeVar("FT", bound=Callable[..., Any])
# classmethod descriptor
CMD = TypeVar("CMD", classmethod, staticmethod)


class Decorator(Generic[FT, T]):
    """
    Base class for writing decorators to use on functions, methods,
    classmethods or staticmethods.
    """

    __name__: Final[str]
    __qualname__: Final[str]
    __self__: Union[T, Type[T]]
    __func__: FT

    @final
    def __init__(
        self,
        function: Union[FT, ClassMethod[FT], ClassMethodDescriptor[Any, FT]],
        /,
        *args,
        _unbound_function_type: Optional[FunctionType] = None,
        _decorate: bool = True,
        **kwargs,
    ):
        """

        :param function: The decorated function, method, classmethod or
            staticmethod descriptor instance.
        :param args: Decorator args, passed to the bound decorator.
        :param _unbound_function_type: Optional unbound class/staticmethod
            function type, needed because the bound staticmethod function type
            cannot be reliably determined with `get_function_type(function)`
            (it would otherwise be classified as `FunctionType.Function`).
        :param _decorate: Whether to call __decorate__, set to False when
            instantiated from __get__.
        :param kwargs: Decorator kwargs, passed to the bound decorator.
        """
        self.__func_wrapped = function

        # verbose nested conditions for mypy-compatibility
        if isinstance(function, ClassMethodDescriptor):
            if callable(function):
                self.__func__ = function
            else:
                self.__func__ = function.__func__
        else:
            self.__func__ = function

        self.__unbound_function_type = _unbound_function_type

        # verbose variant for functools.update_wrapper for mypy-compatibilty
        self.__module__ = self.__func__.__module__
        self.__name__ = self.__func__.__name__
        self.__qualname__ = self.__func__.__qualname__
        self.__doc__ = self.__func__.__doc__
        self.__annotations__ = self.__func__.__annotations__
        if (_self := getattr(self.__func__, "__self__", None)) is not None:
            self.__self__ = _self
        self.__dict__.update(self.__func__.__dict__)

        self.owner: Optional[Type[T]] = None
        if self.is_method and self.is_bound:
            if self.is_classmethod:
                assert isinstance(self.__self__, type)
                self.owner = self.__self__

            elif self.is_instancemethod:
                assert not isinstance(self.__self__, type)
                self.owner = type(self.__self__)

        self._args, self._kwargs = args, kwargs

        if _decorate:
            self.__decorate__()

    def __set_name__(self, owner: Type[T], name: str):
        if self.owner is None:
            self.owner = owner

    def __get__(
        self: Decorator[FT, T], instance: Optional[T], owner: Type[T]
    ) -> Decorator[FT, T]:
        inner_get = getattr(self.__func_wrapped, "__get__")
        unbound_function_type = self.__unbound_function_type

        if (self.is_classmethod or self.is_staticmethod) and self.is_unbound:
            unbound_function_type = self.function_type

        res = type(self)(
            inner_get(instance, owner),  # noqa
            *self._args,
            _unbound_function_type=unbound_function_type,
            _decorate=False,
            **self._kwargs,
        )

        if self.is_method and self.is_unbound:
            if instance is None:
                res.__bind_class__(owner)
            else:
                res.__bind__(instance)

        return res

    def __call__(self, *args, **kwargs):
        if self.function_type in FunctionType.METHOD_UNBOUND:
            raise TypeError(f"'{self}' object is not callable")
        return self.__func__(*args, **kwargs)

    def __eq__(self, other) -> bool:
        if isinstance(other, Decorator):
            if self.function_type is not other.function_type:
                return False

            other_function = other.__func__
        elif callable(other):
            other_function = other
        else:
            return False

        return self.__func__ == other_function

    def __gt__(self, other: Decorator) -> bool:
        """
        a > b iff b is b is a bound method of (an unbound method) a, i.e.
        `Foo.foo > Foo().foo`
        """
        self.__typecheck_order_operator_param(other, ">")

        if self.is_function or other.is_function:
            # functions cannot be (un)bound
            return False

        if not self.is_unbound or not other.is_bound:
            return False

        if not self.function_type.as_bound() is other.function_type:
            return False

        if self.is_instancemethod:
            other_instance: Union[T, Any] = other.__self__
            self_bound = self.__get__(other_instance, type(other_instance))
            return self_bound.__func__ == other.__func__
        else:
            # unbound class/staticmethods are wrapper instances of
            #  class/staticmethod
            self_func = getattr(self.__func__, "__func__", self.__func__)
            other_func = getattr(other.__func__, "__func__", other.__func__)
            return self_func == other_func

    def __ge__(self, other) -> bool:
        self.__typecheck_order_operator_param(other, ">=")
        return self == other or self > other

    def __lt__(self, other) -> bool:
        self.__typecheck_order_operator_param(other, "<")
        return other > self

    def __le__(self, other) -> bool:
        self.__typecheck_order_operator_param(other, "<=")
        return self == other or self < other

    def __repr__(self):
        type_str = str(self.function_type)

        if (instance := getattr(self, "__self__", None)) is not None:
            type_str = f"{type_str} of {instance}"

        return f"<{type_str}>"

    __str__ = __repr__

    @final
    @functools.cached_property
    def is_function(self):
        return self.function_type is FunctionType.FUNCTION

    @final
    @functools.cached_property
    def is_method(self):
        return self.function_type in FunctionType.METHOD

    @final
    @functools.cached_property
    def is_instancemethod(self):
        return self.function_type in FunctionType.INSTANCEMETHOD

    @final
    @functools.cached_property
    def is_classmethod(self):
        return self.function_type in FunctionType.CLASSMETHOD

    @final
    @functools.cached_property
    def is_staticmethod(self):
        return self.function_type in FunctionType.STATICMETHOD

    @final
    @functools.cached_property
    def is_unbound(self):
        if not self.is_method:
            raise TypeError("not a method")
        return self.function_type in FunctionType.METHOD_UNBOUND

    @final
    @functools.cached_property
    def is_bound(self):
        if not self.is_method:
            raise TypeError("not a method")
        return self.function_type in FunctionType.METHOD_BOUND

    @final
    @functools.cached_property
    def function_type(self) -> FunctionType:
        if self.__unbound_function_type:
            return self.__unbound_function_type.as_bound()
        else:
            return get_function_type(self.__func_wrapped)

    @classmethod
    def __typecheck_order_operator_param(cls, other, operator: str):
        if not isinstance(other, cls):
            raise TypeError(
                f"'{operator}' not supported between instances of {cls} and "
                f"{type(other)}"
            )

    # The following methods are meant for overriding
    def __decorate__(self) -> NoReturn:
        ...  # pragma: no cover

    def __bind__(self, instance: T) -> NoReturn:
        ...  # pragma: no cover

    def __bind_class__(self, cls: Type[T]) -> NoReturn:
        ...  # pragma: no cover
