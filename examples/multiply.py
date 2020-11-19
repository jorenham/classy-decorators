from classy_decorators import Decorator


class Multiply(Decorator):
    factor: int

    def __call_inner__(self, *args, **kwargs) -> float:
        return super().__call_inner__(*args, **kwargs) * self.factor


@Multiply(2)
def add_and_double(a, b):
    return a + b


@Multiply(factor=3)
def add_and_triple(a, b):
    return a + b


assert add_and_double(8, 15) == 46
assert add_and_triple(8, 15) == 69
