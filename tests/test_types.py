import pytest

from classy_decorators.function_types import FunctionType, get_function_type


class Spam:
    def method(self):
        ...

    @classmethod
    def classmethod(cls):
        ...

    @staticmethod
    def staticmethod():
        ...


def eggs():
    ...


ham = lambda: ...  # noqa


expected_types = [
    (Spam.method, FunctionType.INSTANCEMETHOD_UNBOUND),
    (Spam().method, FunctionType.INSTANCEMETHOD_BOUND),
    (Spam.classmethod, FunctionType.CLASSMETHOD_BOUND),
    (Spam().classmethod, FunctionType.CLASSMETHOD_BOUND),
    (Spam.staticmethod, FunctionType.FUNCTION),
    (Spam().staticmethod, FunctionType.FUNCTION),
    (eggs, FunctionType.FUNCTION),
    (ham, FunctionType.FUNCTION),
]


@pytest.mark.parametrize("fn,tp", expected_types)
def test_function_type(fn, tp: FunctionType):
    assert get_function_type(fn) is tp


@pytest.mark.parametrize(
    "tp_bound,tp_unbound,tp",
    [
        (
            FunctionType.INSTANCEMETHOD_BOUND,
            FunctionType.INSTANCEMETHOD_UNBOUND,
            FunctionType.INSTANCEMETHOD,
        ),
        (
            FunctionType.CLASSMETHOD_BOUND,
            FunctionType.CLASSMETHOD_UNBOUND,
            FunctionType.CLASSMETHOD,
        ),
        (
            FunctionType.STATICMETHOD_BOUND,
            FunctionType.STATICMETHOD_UNBOUND,
            FunctionType.STATICMETHOD,
        ),
    ],
)
def test_function_type_method_variant(
    tp_bound: FunctionType, tp_unbound: FunctionType, tp: FunctionType
):
    assert tp_bound is not tp_unbound
    assert tp_bound in tp
    assert tp_unbound in tp


@pytest.mark.parametrize(
    "tp_bound",
    [
        FunctionType.INSTANCEMETHOD_BOUND,
        FunctionType.CLASSMETHOD_BOUND,
        FunctionType.STATICMETHOD_BOUND,
    ],
)
@pytest.mark.parametrize(
    "tp_unbound",
    [
        FunctionType.INSTANCEMETHOD_UNBOUND,
        FunctionType.CLASSMETHOD_UNBOUND,
        FunctionType.STATICMETHOD_UNBOUND,
    ],
)
def test_function_type_method_state(
    tp_bound: FunctionType,
    tp_unbound: FunctionType,
):
    assert tp_bound is not tp_unbound

    assert tp_bound in FunctionType.METHOD
    assert tp_bound in FunctionType.METHOD_BOUND

    assert tp_unbound in FunctionType.METHOD
    assert tp_unbound in FunctionType.METHOD_UNBOUND


@pytest.mark.parametrize(
    "tp",
    [
        FunctionType.FUNCTION,
        FunctionType.INSTANCEMETHOD_BOUND,
    ],
)
def test_as_bound_error(tp):
    with pytest.raises(TypeError):
        tp.as_bound()


def test_funtion_type_error():
    with pytest.raises(TypeError):
        get_function_type("nope")  # noqa
