# Classy Decorators

[![PyPI version](https://badge.fury.io/py/classy-decorators.svg)](https://badge.fury.io/py/classy-decorators)

Hassle-free creation of decorators for functions and methods, OO-style.

## Features

 - One decorator to rule them all; it works on functions, methods, 
 classmethods and staticmethods.
 - Easily define parameters with a dataclass-like annotated attribute syntax.
 - Runtime type-checking of decorator paremeters.
 - For decorators with all-default or no parameters, parentheses are optional: 
 `@spam() == @spam`
 - Inheritance is supported.
 - Any decorator parameters and instance attributes are accessible (as copies) 
 in bound methods as well; no need to worry about those pesky descriptors.
 - MyPy compatible and 100% test coverage.



## Dependencies

Python 3.8 or 3.9.


## Install

```bash
pip install classy-decorators
```

for better runtime type checking:

```bash
pip install classy-decorators[typeguard]
```


## Usage 

*The following code can also be found in the 
[examples](https://github.com/jorenham/classy-decorators/tree/master/examples).*

Create a decorator by subclassing `classy_decorators.Decorator`. 
You can override the the decorated function or method using the 
`__call_inner__` method (`__call__` is meant for internal use only and should 
not be used for this).

### Simple decorator

```python
from classy_decorators import Decorator

class Double(Decorator):
    def __call_inner__(self, *args, **kwargs) -> float:
        return super().__call_inner__(*args, **kwargs) * 2
```

To see it in action, let's decorate a function:

```python
@Double
def add(a, b):
    return a + b

assert add(7, 14) == 42
```

You can also decorate methods and classmethods:

```python
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
```

### Decorator parameters

Our `Double` decorator is pretty nice, but we can do better! So let's create a
decorator that is able to multiply results by any number instead of only by `2`:

```python
class Multiply(Decorator):
    factor: int

    def __call_inner__(self, *args, **kwargs) -> float:
        return super().__call_inner__(*args, **kwargs) * self.factor
```

By simply setting the type-annotated `factor` attribute, we can use it as 
decorator parameter. If you are familiar with 
[dataclasses](https://docs.python.org/3/library/dataclasses.html), you can see
that this is very similar to defining dataclass fields.


```python
@Multiply(2)
def add_and_double(a, b):
    return a + b

@Multiply(factor=3)
def add_and_triple(a, b):
    return a + b

assert add_and_double(8, 15) == 46
assert add_and_triple(8, 15) == 69
```


### Default parameters and inheritance

It's classy to be DRY, so let's combine our `Double` and `Multiply` decorators 
into one that multiplies by `2`, unless specified otherwise:

```python
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
```


### Advanced dataclass methods 

The `Decorator` base class provided, aside from `__call_inner__`, two other
interface methods you can override:

- `Decorator.__decorate__(self, **params)`, which is called just after a 
function method is decorated, with all decorator parameter values or defaults as
keyword arguments, i.e. `DoubleOrMultiply.__decorate__(self, factor: int = 2)`.
- `Decorator.__bind__(self, instance_or_class)`, which is called when a method 
(not for functions), is bound to an instance, or when a class/static method is 
bound to a class.

Additionally, these properties can be used for figuring out what's been 
decorated:

- `is_function`
- `is_method`; either an instance, class- or static method
- `is_instancemethod` 
- `is_classmethod`
- `is_staticmethod`

And for methods, `is_bound` and `is_unbound` are provided.

If you're looking for the original wrapped function, you can find it at 
`__func__`.

---

*Classy, eh?*
