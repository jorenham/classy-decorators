from examples.multiply import Multiply


class DoubleOrMultiply(Multiply):
    factor = 2


@DoubleOrMultiply
def add_and_double(a, b):
    return a + b


@DoubleOrMultiply(factor=3)
def add_and_triple(a, b):
    return a + b


assert add_and_double(7, 14) == 42
assert add_and_triple(8, 15) == 69
