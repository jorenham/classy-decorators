from classy_decorators import Decorator


class MyDecorator(Decorator):
    def __decorate__(self):
        print(f"decorated {self.function_type} '{self.__name__}'")

    def __call__(self, *args, **kwargs):
        print(f"called {self.function_type} '{self.__name__}'")
        return super().__call__(*args, **kwargs)


# prints: decorated function 'spam'
@MyDecorator
def spam():
    pass


# prints: called function 'spam'
spam()
