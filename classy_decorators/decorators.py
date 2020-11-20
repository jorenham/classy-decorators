from __future__ import annotations

__all__ = ["Decorator"]

import functools
import types
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Final,
    FrozenSet,
    Generic,
    NoReturn,
    Optional,
    Protocol,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
    final,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

try:
    import typeguard
except ImportError:
    typeguard = NotImplemented
    _TYPEGUARD = False
else:
    _TYPEGUARD = True

from classy_decorators.function_types import (
    ClassMethod,
    ClassMethodDescriptor,
    FunctionType,
    get_function_type,
    is_decoratable,
)

# type to which the decorated method is bound
T = TypeVar("T")
# decorator param type
PT = TypeVar("PT")
# return value
RT = TypeVar("RT")
# decorated function
FT = TypeVar("FT", bound=Callable[..., Any])
_FT = TypeVar("_FT", bound=Callable[..., Any])
# classmethod descriptor
CMD = TypeVar("CMD", classmethod, staticmethod)

MaybeFT = TypeVar("MaybeFT", covariant=True)
Decoratable = Union[FT, ClassMethod[FT], ClassMethodDescriptor[Any, FT]]


class _MissingType:
    pass


Missing = _MissingType()


class Param(Generic[PT]):
    # based on dataclassed.Field.__set_name__
    __slots__ = ("name", "type", "default")

    name: Union[str, _MissingType]
    type: Union[Type[PT], _MissingType]
    default: Union[PT, _MissingType]

    def __init__(self, *, default: Union[PT, _MissingType] = Missing):
        self.name = Missing
        self.type = Missing
        self.default = default

    def __repr__(self):
        return (
            "Field("
            f"name={self.name!r},"
            f"type={self.type!r},"
            f"default={self.default!r},"
            ")"
        )

    def is_of_type(self, arg) -> Optional[bool]:
        """
        Checks if arg is of the param type.
        Uses typeguard if installed, otherwise a simple typechecking of the
        origin type is done and returns None if the type could not be checked.
        """
        if self.type is Missing:  # pragma: no cover
            raise TypeError("decorator param has no type")
        if self.name is Missing:  # pragma: no cover
            raise TypeError("decorator param has no name")

        if _TYPEGUARD:
            try:
                typeguard.check_type(cast(str, self.name), arg, self.type)
            except TypeError:
                return False
            else:
                return True
        else:
            return _isinstance_typing(arg, cast(Type[PT], self.type))

    def check_type(self, arg):
        if self.name is Missing:  # pragma: no cover
            raise TypeError("decorator param has no name")

        if self.is_of_type(arg) is False:
            raise TypeError(
                f"type of decorator parameter '{self.name}' must be "
                f"'{self.type}'; got '{type(arg)}' instead"
            )


class BaseDecoratorType(Protocol[MaybeFT]):
    __init__: Callable
    __call__: Callable


class DecoratorType(BaseDecoratorType[FT]):
    __func__: FT
    __func_wrapped: Decoratable[FT]

    @overload
    def __init__(
        self,
        decoratable: Decoratable[FT],
        /,
        _unbound_function_type: Optional[FunctionType],
        _param_values: Dict[str, Any],
        _decorate: bool,
    ) -> None:
        ...  # pragma: no cover

    @overload
    def __init__(self, decoratable: Decoratable[FT], /) -> None:
        ...  # pragma: no cover

    def __init__(
        self,
        decoratable: Decoratable[FT],
        /,
        _unbound_function_type: Optional[FunctionType] = None,
        _param_values: Optional[Dict[str, Any]] = None,
        _decorate: bool = True,
        **__kwargs,
    ) -> None:
        ...  # pragma: no cover

    def __call__(self, *args, **kwargs) -> Any:
        ...  # pragma: no cover


class PartialDecoratorType(BaseDecoratorType[None]):
    def __call__(self, __decoratable: Decoratable[FT], /) -> DecoratorType[FT]:
        ...  # pragma: no cover


D = TypeVar("D", bound=BaseDecoratorType, covariant=True)


class Decorator(Generic[D, MaybeFT]):
    """
    Base class for writing decorators to use on functions, methods,
    classmethods or staticmethods.
    """

    __decorator_params__: ClassVar[Dict[str, Param]]

    @final
    def __init__(
        self,
        *args,
        _unbound_function_type=None,
        _param_values=None,
        _decorate=True,
        **kwargs,
    ):
        self.__unbound_function_type = _unbound_function_type
        self.__param_values: Dict[str, Any] = _param_values or {}

        if _param_values is None and (
            kwargs
            or len(args) != 1
            or self._required_params
            or not is_decoratable(args[0])
        ):
            # postpone __decorate__ call until wrapped
            _decorate = False

            for arg, (name, param) in zip(
                args, self.__decorator_params__.items()
            ):
                param.check_type(arg)
                self.__param_values[name] = arg

            for name, arg in kwargs.items():
                if name not in self.__decorator_params__:
                    raise ValueError(
                        f"'{name}' is an invalid decorator param for "
                        f"'{type(self).__name__}'"
                    )
                if name in self.__param_values:
                    raise ValueError(
                        f"multiple values provided for decorator param "
                        f"'{name}'"
                    )

                param = self.__decorator_params__[name]
                param.check_type(arg)
                self.__param_values[name] = arg

        elif len(args) != 1 or kwargs:  # pragma: no cover
            raise ValueError(f"'{type(self).__name__}' must have one argument")

        else:
            self.__set_function(args[0])

        kwargs = {}
        for name, param in self.__decorator_params__.items():
            if name not in self.__param_values and param.default is Missing:
                raise ValueError(f"decorator param '{name}' is required")

            value = self.__param_values.get(name, param.default)
            kwargs[name] = value
            setattr(self, name, value)

        if _decorate:
            self.__decorate__(**kwargs)

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)

        # based on dataclasses._process_class
        params: Dict[str, Param] = {}

        for b in cls.__mro__[-1:0:-1]:
            base_params = getattr(b, "__decorator_params__", None)
            if base_params:
                for param in base_params.values():
                    params[param.name] = param

        cls_annotations = get_type_hints(cls)
        ccls = cls.mro()[1]  # the current class
        for _name, param_type in cls_annotations.items():
            if not _specialattr(_name) and not _privateattr(ccls, _name):
                param = _get_param(cls, _name, param_type)
                params[param.name] = param

        for name, value in cls.__dict__.items():
            if (
                not _specialattr(name)
                and not _privateattr(ccls, name)
                and name not in cls_annotations
            ):
                raise TypeError(
                    f"{name!r} is a decorator param but has no type annotation"
                )

        cls.__decorator_params__ = params

    def __get__(
        self: Decorator[DecoratorType[FT], FT],
        instance: Optional[T],
        owner: Type[T],
    ) -> Decorator[DecoratorType[FT], FT]:
        inner_get = getattr(self.__func_wrapped, "__get__")(instance, owner)
        if self.__func_wrapped == inner_get:
            return self

        res = self._as_bound(inner_get)

        if self.is_method and self.is_unbound:
            res.__bind__(instance or owner)

        return res

    @final
    def __call__(self, *args, **kwargs):
        if not hasattr(self, "__func__"):
            if len(args) != 1 or kwargs:
                raise ValueError(
                    f"'{type(self).__name__}' decorator must have one argument"
                )
            if not is_decoratable(args[0]):
                raise TypeError(f"cannot decorate '{args[0]}'")

            function: Union[Callable, classmethod, staticmethod] = args[0]
            return self._as_bound(function)

        if self.function_type in FunctionType.METHOD_UNBOUND:
            raise TypeError(f"'{self}' object is not callable")

        return self.__call_inner__(*args, **kwargs)

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

    def __gt__(self: Decorator, other: Decorator) -> bool:
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
            other_instance = other.__self__
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

    @final
    @functools.cached_property
    def _required_params(self) -> FrozenSet[str]:
        res: Set[str] = set()
        for name, param in self.__decorator_params__.items():
            if param.default is Missing:
                res.add(name)

        return frozenset(res)

    @classmethod
    def __typecheck_order_operator_param(cls, other, operator: str):
        if not isinstance(other, cls):
            raise TypeError(
                f"'{operator}' not supported between instances of {cls} and "
                f"{type(other)}"
            )

    def _as_bound(
        self: Decorator[BaseDecoratorType[MaybeFT], MaybeFT],
        decoratable: Decoratable[FT],
    ) -> Decorator[DecoratorType[FT], FT]:
        unbound_function_type = self.__unbound_function_type
        partial = not hasattr(self, "__func__")
        if (
            not unbound_function_type
            and not partial
            and (self.is_classmethod or self.is_staticmethod)
            and self.is_unbound
        ):
            unbound_function_type = self.function_type

        param_values = {}
        for name, param in self.__decorator_params__.items():
            if hasattr(self, name):
                param_values[name] = getattr(self, name)

        res = type(self)(
            decoratable,
            _unbound_function_type=unbound_function_type,
            _param_values=param_values,
            _decorate=partial,
        )

        # persistant attributes
        for name, value in self.__dict__.items():
            if (
                not _specialattr(name)
                and not _privateattr(type(self), name)
                and not hasattr(res, name)
            ):
                setattr(res, name, value)

        return cast(Decorator[DecoratorType[FT], FT], res)

    def __set_function(self, function):
        self.__func_wrapped = function

        # verbose nested conditions for mypy-compatibility
        if isinstance(function, ClassMethodDescriptor):
            if callable(function):
                self.__func__ = function
            else:
                self.__func__ = function.__func__
        else:
            self.__func__ = function

        # verbose variant for functools.update_wrapper for mypy-compatibilty
        self.__module__ = self.__func__.__module__
        self.__name__ = self.__func__.__name__
        self.__qualname__ = self.__func__.__qualname__
        self.__doc__ = self.__func__.__doc__
        self.__annotations__ = self.__func__.__annotations__
        if (_self := getattr(self.__func__, "__self__", None)) is not None:
            self.__self__ = _self
        self.__dict__.update(self.__func__.__dict__)

        if self.is_method and self.is_bound:
            if self.is_classmethod:
                assert isinstance(self.__self__, type)

            elif self.is_instancemethod:
                assert not isinstance(self.__self__, type)

    # The following methods are meant for overriding
    def __decorate__(self, **kwargs) -> NoReturn:
        ...  # pragma: no cover

    def __bind__(self, instance_or_class: Union[T, Type[T]]) -> NoReturn:
        ...  # pragma: no cover

    def __call_inner__(self, *args, **kwargs) -> Any:
        return self.__func__(*args, **kwargs)


def _get_param(cls: Type[Decorator], name: str, tp: Type[PT]) -> Param[PT]:
    # based on decorators._get_field

    default = getattr(cls, name, Missing)
    if isinstance(default, Param):  # pragma: no cover
        # TODO fix this
        param = default
    else:
        if isinstance(default, types.MemberDescriptorType):  # pragma: no cover
            # This is a param in __slots__, so it has no default value.
            default = Missing
        param = Param(default=default)

    param.name = name
    param.type = tp

    if default is not Missing and param.is_of_type(default) is False:
        raise TypeError(
            f"type of decorator parameter default '{param.name}' must be "
            f"'{param.type}'; got '{type(default)}' instead"
        )

    return param


def _specialattr(name: str) -> bool:
    return name[:2] == name[-2:] == "__"


def _privateattr(cls: type, name: str) -> bool:
    return name.startswith(f"_{cls.__name__}__")


def _isinstance_typing(  # noqa: C901
    arg: Union[T, Any], tp: Optional[Type[T]]
) -> Optional[bool]:
    if tp is Any:
        return True
    if tp is None:
        return arg is None

    try:
        return isinstance(arg, tp)
    except TypeError:
        pass

    if isinstance(tp, TypeVar):
        if tp.__constraints__:
            return any(type(arg) is c for c in tp.__constraints__)
        elif tp.__bound__:
            return isinstance(arg, tp.__bound__)
        else:
            # resolving TypeVars; no thank you
            return None

    origin = get_origin(tp)
    tp_args = get_args(tp)
    if origin is Union:
        indeterminate = False
        for _tp in tp_args:
            res = _isinstance_typing(arg, _tp)
            if res is None:
                indeterminate = True
            elif res is True:
                return True

        if not indeterminate:
            return False

    elif (origin is ClassVar or origin is Final) and tp_args:
        return _isinstance_typing(arg, tp_args[0])
    elif origin is type:
        if not isinstance(arg, type):
            return False
        if isinstance(tp_args[0], type):
            return arg is tp_args[0]
        else:
            # TODO: recurse
            return None
    elif origin is not None:
        return _isinstance_typing(arg, origin)

    return None  # pragma: no cover
