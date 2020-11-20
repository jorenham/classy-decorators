import importlib
import sys
from importlib.abc import MetaPathFinder
from typing import Optional

import pytest

from classy_decorators import decorators


class MyDecorator(decorators.Decorator):
    spam: str
    ham: Optional[str] = None
    eggs: int = 6

    def __call_inner__(self, *args, **kwargs):
        super().__call_inner__(*args, **kwargs)
        return self.function_type

    def __bind__(self, instance):
        self.bound_to = instance

    def __decorate__(self, **kwargs):
        self.decorated = self.__qualname__


class SubDecorator(MyDecorator):
    spam = "defaultspam"
    bacon: float


def test_kwargs():
    kwargs = dict(spam="spam", eggs=4)

    class Spam:
        @MyDecorator(**kwargs)
        def method(self):
            ...

        @MyDecorator(**kwargs)  # noqa
        @classmethod
        def classmethod(cls):
            ...

        @MyDecorator(**kwargs)  # noqa
        @staticmethod
        def staticmethod():
            ...

    @MyDecorator(**kwargs)
    def eggs():
        ...

    instance = Spam()
    assert instance.method.spam == kwargs["spam"]
    assert instance.method.eggs == kwargs["eggs"]
    assert instance.method.ham is None

    for fn in (Spam.method, Spam.classmethod, Spam.staticmethod, eggs):
        assert fn.spam == kwargs["spam"]
        assert fn.eggs == kwargs["eggs"]
        assert fn.ham is None


def test_args():
    args = ["spam"]

    class Spam:
        @MyDecorator(*args)
        def method(self):
            ...

        @MyDecorator(*args)  # noqa
        @classmethod
        def classmethod(cls):
            ...

        @MyDecorator(*args)  # noqa
        @staticmethod
        def staticmethod():
            ...

    @MyDecorator(*args)
    def eggs():
        ...

    instance = Spam()
    assert instance.method.spam == args[0]

    for fn in (Spam.method, Spam.classmethod, Spam.staticmethod, eggs):
        assert fn.spam == args[0]


def test_inheritance():
    @SubDecorator(bacon=6.66)
    def subspam():
        ...

    assert subspam.spam == "defaultspam"
    assert subspam.ham is None
    assert subspam.bacon == 6.66


def test_missing():
    with pytest.raises(TypeError):

        @MyDecorator
        def eggs():
            ...

    with pytest.raises(ValueError):

        @MyDecorator(eggs=1)
        def bacon():
            ...


def test_wrong_param():
    with pytest.raises(ValueError):

        @MyDecorator(foo="bar")
        def eggs():
            ...


def test_double_param():
    with pytest.raises(ValueError):

        @MyDecorator("spam", spam="doublespam")
        def eggs():
            ...


def test_double_call_error():
    dec = MyDecorator(spam="spam")
    with pytest.raises(ValueError):

        @dec()
        def eggs():
            ...


def test_wrap_with_kwargs_error():
    dec = MyDecorator("spam")

    def eggs():
        ...

    with pytest.raises(ValueError):
        dec(eggs, ham="extraham")


def test_no_annotation():
    with pytest.raises(TypeError):

        class BadDecorator(decorators.Decorator):
            nope = "nope"


def test_decorate_partial_type_error():
    dec = MyDecorator("spam")
    with pytest.raises(TypeError):
        dec(None)


def test_type_error_default():
    with pytest.raises(TypeError):

        class _Decorator(decorators.Decorator):
            spam: str = 6


def test_type_error_param():
    with pytest.raises(TypeError):
        MyDecorator(spam=6)


def test_no_typeguard():
    # mock import error for typeguard
    class ImportRaiser(MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname == "typeguard":
                raise ImportError

    sys.meta_path.insert(0, ImportRaiser())
    del sys.modules["typeguard"]
    importlib.reload(decorators)

    assert not decorators._TYPEGUARD

    with pytest.raises(TypeError):

        class _Decorator(decorators.Decorator):
            spam: str = 6

    with pytest.raises(TypeError):
        MyDecorator(spam=6)
