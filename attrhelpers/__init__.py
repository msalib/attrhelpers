"""
Type-based validators for attrs classes

Typically, when you define an attrs class, you'll specify a type
annotation for communicating types to human readers and automated type
checkers. But then you'll also duplicate the type information in a
validator to ensure that the code will perform runtime type checks. To
avoid that duplication, you have two options. You can use this module
as stand-in for attrs like so:

```
import attrhelpers as attr

@attr.s(auto_attribs=True, frozen=True)
class X:
    a: Optional[int]
    b: Sequence[float]
    c: str = attr.ib(default='hi')
```

Or you can use a lower level approach and import the `type_validate`
decorator from this module. Use it before `attr.s`; it will create
attrs validators based on the type annotations you supply. For
example, this:

```
import attr
from attrhelpers import type_validate

@attr.s(frozen=True)
@type_validate
class X:
    a: Optional[int] = attr.ib()
    b: Sequence[float] = attr.ib()
    c: str = attr.ib(default='hi')
```

Both code snippets above are equivalent to:

```
@attr.s(frozen=True)
class X:
    a: Optional[int] = attr.ib(validator=optional(instance_of(int)))
    b: Sequence[float] = attr.ib(validator=deep_iterable(
        instance_of(float),
        instance_of(collections.abc.Sequence)))
    c: str = attr.ib(default='hi', valiator=instance_of(str))
```

Note that `type_validate` WILL NOT WORK with `attr.s(auto_attribs)`;
you must use `attr.ib` for each attribute in the class body.
"""

import attr
from .helpers import type_validate

__all__ = ['type_validate', 's', 'ib']


def s(cls: type, *args, **kwargs) -> type:
    inner = type_validate(cls)
    return attr.s(inner, *args, **kwargs)


ib = attr.ib
