import collections
import enum
import functools
import typing as T

import attr
import pytest

from .helpers import _type_to_validator, type_validate, _TupleValidator, Or


i = attr.validators.instance_of
o = attr.validators.optional
di = attr.validators.deep_iterable
dm = attr.validators.deep_mapping


@pytest.mark.parametrize(
    'input,expected',
    [(float, i(float)),
     (str, i(str)),
     (list, i(list)),
     (T.Union[int, float, str], Or(i(int), i(float), i(str))),
     (T.Optional[int], o(i(int))),
     (T.Optional[str], o(i(str))),
     (T.Tuple[T.Optional[int], ...], di(o(i(int)), i(tuple))),
     (T.Tuple[float, T.Optional[int]], _TupleValidator((i(float), o(i(int))))),
     (T.Sequence[int], di(i(int), i(collections.abc.Sequence))),
     (T.Sequence[T.Optional[int]], di(o(i(int)), i(collections.abc.Sequence))),
     (T.Dict[int, float], dm(i(int), i(float), i(dict))),
     (T.Dict[int, T.Optional[float]], dm(i(int), o(i(float)), i(dict)))])
def test_type_to_validator(input, expected):
    assert expected == _type_to_validator(input)


@attr.s(frozen=True)
@type_validate
class X:
    a: T.Optional[int] = attr.ib()
    b: T.Sequence[float] = attr.ib()
    c: str = attr.ib(default='hi')


@pytest.mark.parametrize(
    'a,b,c,should_raise',
    [(1, [2.2], 'hi', False),
     (None, [2.2], 'hi', False),
     (1, [2], 'hi', True),
     (1, [2], 4, True)])
def test_simple(a, b, c, should_raise):
    if should_raise:
        with pytest.raises(Exception):
            X(a, b, c)
    else:
        X(a, b, c)


def test_wrong_order_raises():
    with pytest.raises(ValueError):
        @type_validate
        @attr.s
        class X:
            a: T.Optional[int] = attr.ib()


def test_Or():
    U = functools.partial(Or(i(int), i(float)), None, None)
    U(1)
    U(1.1)
    with pytest.raises(Exception):
        U(None)
    with pytest.raises(Exception):
        U('hi')


def test_enum():

    class Answer(enum.Enum):
        YES = 1
        NO = 2
        MAYBE = 3

    @attr.s
    @type_validate
    class EnumHaver:
        a: Answer = attr.ib()

    for a in Answer:
        EnumHaver(a)

    with pytest.raises(Exception):
        EnumHaver(1)
    with pytest.raises(Exception):
        EnumHaver('YES')
