import json
import random

from .._compat import Iterable
from .core import mutation, Mutation


class ChangeStatusCode(Mutation):
    def generate(self):
        # "code" will always be in the context, because it is validated before
        if isinstance(self.context["code"], Iterable):
            for status_code in self.context["code"]:
                yield Mutation(self.func, {"code": status_code})
        else:
            yield self


@ChangeStatusCode.from_function
def status_code(cassette, code):
    cassette["status"]["code"] = code


@mutation
def empty_body(cassette):
    """Make the body empty."""
    cassette["body"]["string"] = b""


@mutation
def malform_body(cassette):
    """Add chars to the body to make it not decodable."""
    cassette["body"]["string"] = b"xX" + cassette["body"]["string"] + b"Xx"


@mutation
def reduce_body(cassette):
    data = json.loads(cassette["body"]["string"])
    # it could be a list or other json type
    # take out random key
    key = random.choice(list(data.keys()))
    del data[key]
    cassette["body"]["string"] = json.dumps(data)


# TODO.
# XML - Add / remove XML tags.
# JSON - add keys, remove keys, replace values
# JSON - shrink lists, extend lists
