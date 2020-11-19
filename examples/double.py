from classy_decorators import Decorator


class Double(Decorator):
    def __call_inner__(self, *args, **kwargs) -> float:
        return super().__call_inner__(*args, **kwargs) * 2


@Double
def add(a, b):
    return a + b


assert add(7, 14) == 42


class AddConstant:
    default_constant = 319

    def __init__(self, constant=default_constant):
        self.constant = constant

    @Double
    def add_to(self, value):
        return value + self.constant

    @Double
    @classmethod
    def add_default(cls, value):
        return value + cls.default_constant


assert AddConstant(7).add_to(14) == 42
assert AddConstant.add_default(14) == 666
