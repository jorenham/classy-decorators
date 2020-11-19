from typing import Optional

import pytest

from classy_decorators import Decorator
from classy_decorators.function_types import FunctionType


class MyDecorator(Decorator):
    decorated: Optional[str] = None

    def __call_inner__(self, *args, **kwargs):
        super().__call_inner__(*args, **kwargs)
        return self.function_type

    def __bind__(self, instance):
        self.bound_to = instance

    def __decorate__(self, **kwargs):
        self.decorated = self.__qualname__


class Spam:
    @MyDecorator
    def method(self):
        ...

    @MyDecorator
    def method_alt(self):
        ...

    @MyDecorator  # noqa
    @classmethod
    def classmethod(cls):
        ...

    @MyDecorator  # noqa
    @staticmethod
    def staticmethod():
        ...


@MyDecorator
def eggs():
    ...


ham_inner = lambda: ...  # noqa
ham = MyDecorator(ham_inner)


@pytest.mark.parametrize(
    "fn", [Spam.method, Spam.classmethod, Spam.staticmethod, eggs, ham]
)
def test_decorate(fn):
    assert fn.decorated == fn.__qualname__


@pytest.mark.parametrize("method", [Spam.classmethod, Spam.staticmethod])
def test_bind_class(method):
    assert method.bound_to is Spam


def test_bind_instance():
    instance = Spam()
    assert instance.method.bound_to is instance


@pytest.mark.parametrize("fn", [eggs, ham])
def test_bind_function(fn):
    assert not hasattr(fn, "bound_to")


@pytest.mark.parametrize(
    "fn,tp",
    [
        (Spam().method, FunctionType.INSTANCEMETHOD_BOUND),
        (Spam.classmethod, FunctionType.CLASSMETHOD_BOUND),
        (Spam().classmethod, FunctionType.CLASSMETHOD_BOUND),
        (Spam.staticmethod, FunctionType.STATICMETHOD_BOUND),
        (Spam().staticmethod, FunctionType.STATICMETHOD_BOUND),
        (eggs, FunctionType.FUNCTION),
        (ham, FunctionType.FUNCTION),
    ],
)
def test_decorated_returns_type(fn, tp):
    assert fn() is tp


@pytest.mark.parametrize(
    "method,variant_attr,bind_attr",
    [
        (Spam.method, "is_instancemethod", "is_unbound"),
        (Spam().method, "is_instancemethod", "is_bound"),
        (Spam.__dict__["classmethod"], "is_classmethod", "is_unbound"),
        (Spam.classmethod, "is_classmethod", "is_bound"),
        (Spam().classmethod, "is_classmethod", "is_bound"),
        (Spam.__dict__["staticmethod"], "is_staticmethod", "is_unbound"),
        (Spam.staticmethod, "is_staticmethod", "is_bound"),
        (Spam().staticmethod, "is_staticmethod", "is_bound"),
    ],
)
def test_types_methods(method, variant_attr, bind_attr):
    assert method.is_method
    assert getattr(method, variant_attr)
    assert getattr(method, bind_attr)


def test_types_function():
    assert ham.is_function
    with pytest.raises(TypeError):
        _ = ham.is_unbound
    with pytest.raises(TypeError):
        _ = ham.is_bound


@pytest.mark.parametrize(
    "fn",
    [
        Spam.method,
        Spam.__dict__["classmethod"],
        Spam.__dict__["staticmethod"],
    ],
)
def test_unbound_call_raise(fn):
    with pytest.raises(TypeError):
        fn()


def test_decorated_eq():
    assert Spam.method == Spam.method
    assert Spam.method != Spam().method
    assert Spam().method != Spam().method

    assert Spam.classmethod == Spam.classmethod
    assert Spam.classmethod == Spam().classmethod
    assert Spam().classmethod == Spam().classmethod

    assert Spam.staticmethod == Spam.staticmethod
    assert Spam.staticmethod == Spam().staticmethod
    assert Spam().staticmethod == Spam().staticmethod

    assert eggs == eggs
    assert ham == ham_inner


def test_decorated_neq():
    assert Spam.method != Spam.method_alt
    assert Spam.classmethod != Spam.staticmethod
    assert Spam.staticmethod != eggs
    assert eggs != ham
    assert ham != Spam.method
    assert ham != "ham"


def test_decorated_order():
    assert Spam.method >= Spam().method
    assert Spam.method > Spam().method
    assert Spam().method <= Spam.method
    assert Spam().method < Spam.method

    assert Spam.__dict__["classmethod"] > Spam.classmethod
    assert Spam.__dict__["staticmethod"] > Spam.staticmethod


def test_decorated_order_incorrect():
    assert not Spam.method_alt > Spam().method
    assert not Spam.method > Spam().method_alt
    assert not Spam.method > Spam.method
    assert not Spam().method > Spam().method
    assert not Spam.method > ham
    assert not Spam.method > Spam.staticmethod

    with pytest.raises(TypeError):
        _ = Spam.method > "a"


def test_repr():
    obj = Spam()

    assert str(Spam.method) == "<unbound method>"
    assert str(obj.method) == f"<bound method of {obj}>"

    assert str(Spam.classmethod) == f"<bound classmethod of {Spam}>"
    assert str(obj.classmethod) == f"<bound classmethod of {Spam}>"

    assert str(Spam.staticmethod) == "<bound staticmethod>"
    assert str(obj.staticmethod) == "<bound staticmethod>"

    assert str(ham) == "<function>"
