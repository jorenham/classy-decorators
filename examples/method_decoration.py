from classy_decorators import Decorator


class MyDecorator(Decorator):
    def __decorate__(self):
        print(f"decorated {self.function_type} '{self.__name__}'")

    def __call__(self, *args, **kwargs):
        print(f"called {self.function_type} '{self.__name__}'")
        return super().__call__(*args, **kwargs)


class Spam:
    # prints: decorated unbound method 'eggs'
    @MyDecorator
    def eggs(self):
        pass

    # prints: decorated unbound classmethod 'ham'
    @MyDecorator
    @classmethod
    def ham(cls):
        pass

    # prints: decorated unbound staticmethod 'bacon'
    @MyDecorator
    @staticmethod
    def bacon():
        pass


# prints: called bound method 'eggs'
Spam().eggs()

# prints: called bound classmethod 'ham'
Spam.ham()

# prints: called bound staticmethod 'bacon'
Spam.bacon()
