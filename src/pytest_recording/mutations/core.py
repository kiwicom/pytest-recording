import attr

from .._compat import get_signature


@attr.s(slots=True)
class Mutation(object):
    func = attr.ib()
    context = attr.ib(factory=dict)
    _signature = attr.ib(init=False)

    @classmethod
    def from_function(cls, func):
        return cls(func)

    @property
    def signature(self):
        if not hasattr(self, "_signature"):
            self._signature = get_signature(self.func)
        return self._signature

    def __call__(self, **context):
        self.validate_call(**context)
        return self.__class__(self.func, context)

    def validate_call(self, **context):
        self.signature.bind(cassette={}, **context)

    def generate(self):
        yield self

    def apply(self, cassette):
        return self.func(cassette, **self.context)


mutation = Mutation.from_function


@attr.s(slots=True)
class MutationGroup(object):
    mutations = attr.ib()

    def generate(self):
        for mutation in self.mutations:
            # change to "yield from" after dropping Python 2
            for one in self.generate_one(mutation):
                yield one

    def generate_one(self, mutation):
        # change to "yield from" after dropping Python 2
        for one in mutation.generate():
            yield one
