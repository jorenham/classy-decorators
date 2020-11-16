from __future__ import annotations

__all__ = ["Decorator"]

import functools
from typing import Any, Callable, Generic, Optional, Type, TypeVar, Union

from classy_decorators.method_types import FunctionType, get_function_type

T = TypeVar("T")
FT = TypeVar("FT", bound=Callable[..., Any])


class Decorator(Generic[FT, T]):
    __name__: str
    __qualname__: str
    __self__: Union[T, Type[T]]

    def __init__(
        self,
        function: FT,
        /,
        *args,
        _unbound_function_type: Optional[FunctionType] = None,
        **kwargs,
    ):
        self.__func__: FT = function
        self.__unbound_function_type = _unbound_function_type

        functools.update_wrapper(
            self,
            self.__func__,
            assigned=("__self__", *functools.WRAPPER_ASSIGNMENTS),
        )

        self.owner: Optional[Type[T]] = None
        if self.is_method and self.is_bound:
            if self.is_classmethod:
                assert isinstance(self.__self__, type)
                self.owner = self.__self__

            elif self.is_instancemethod:
                assert not isinstance(self.__self__, type)
                self.owner = type(self.__self__)

        self._args, self._kwargs = args, kwargs

    def __set_name__(self, owner: Type[T], name: str):
        if self.owner is None:
            self.owner = owner

    def __get__(
        self: Decorator[FT, T], instance: T, owner: Type[T]
    ) -> Decorator[FT, T]:
        inner_get = getattr(self.__func__, "__get__")
        unbound_function_type = self.__unbound_function_type
        if (self.is_classmethod or self.is_staticmethod) and self.is_unbound:
            unbound_function_type = self.function_type

        return type(self)(
            inner_get(instance, owner),  # noqa
            *self._args,
            _unbound_function_type=unbound_function_type,
            **self._kwargs,
        )

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
            # class/staticmethod
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

    @functools.cached_property
    def is_function(self):
        return self.function_type is FunctionType.FUNCTION

    @functools.cached_property
    def is_method(self):
        return self.function_type in FunctionType.METHOD

    @functools.cached_property
    def is_instancemethod(self):
        return self.function_type in FunctionType.INSTANCEMETHOD

    @functools.cached_property
    def is_classmethod(self):
        return self.function_type in FunctionType.CLASSMETHOD

    @functools.cached_property
    def is_staticmethod(self):
        return self.function_type in FunctionType.STATICMETHOD

    @functools.cached_property
    def is_unbound(self):
        if not self.is_method:
            raise TypeError("not a method")
        return self.function_type in FunctionType.METHOD_UNBOUND

    @functools.cached_property
    def is_bound(self):
        if not self.is_method:
            raise TypeError("not a method")
        return self.function_type in FunctionType.METHOD_BOUND

    @functools.cached_property
    def function_type(self) -> FunctionType:
        if self.__unbound_function_type:
            return self.__unbound_function_type.as_bound()
        else:
            return get_function_type(self.__func__)

    @classmethod
    def __typecheck_order_operator_param(cls, other, operator: str):
        if not isinstance(other, cls):
            raise TypeError(
                f"'{operator}' not supported between instances of {cls} and "
                f"{type(other)}"
            )
