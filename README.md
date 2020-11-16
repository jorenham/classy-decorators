# Classy Decorators

Hassle-free creation of decorators for functions and methods, OO-style.

## Dependencies

Python 3.8, 3.9

## Install

```bash
pip install classy-decorators
```

## Usage example

A custom decorator that prints the function type and name before the decorated 
callable is decorated, and before it is called.
The `__post_init__` is called after the `__init__` and should be used instead,
just like for dataclasses.

```python
from classy_decorators import Decorator

class PrintFunctionType(Decorator):
    def __post_init__(self):
        print("decorate", self.function_type, f"'{self.__qualname__}'")

    def __call__(self, *args, **kwargs):
        print("call", self.function_type, f"'{self.__qualname__}'")
        return super().__call__(*args, **kwargs)
```


Let's decorate a dummy function:

```jupyterpython
>>> @PrintFunctionType
... def spam(): 
...     pass
decorate function 'spam'
```

And call it:

```jupyterpython
>>> spam()
call function 'spam'
```

Methods can also be decorated:

```jupyterpython
>>> class Eggs:
...    @PrintFunctionType
...    def ham(self): 
...        pass
decorate unbound method 'Eggs.ham'
```

When instantiating the class, the method is bound to the instance and therefore
decorated again (now with `self.is_bound` instead of `self.is_unbound`):

```jupyterpython
>>> eggs = Eggs()
decorate bound method 'Eggs.ham'
```

```jupyterpython
>>> eggs.ham()
call bound method 'Eggs.ham'
```

Classmethods and staticmethods are also supported:

```jupyterpython
>>> class Eggs:
...    @PrintFunctionType
...    @classmethod
...    def ham(cls): 
...        pass
decorate unbound classmethod 'Eggs.ham'
```

```jupyterpython
>>> Eggs.ham()
call bound classmethod 'Eggs.ham'
```
