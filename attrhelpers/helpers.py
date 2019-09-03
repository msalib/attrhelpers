import collections
import enum
import inspect
import sys
import typing as T

import attr
import attr.validators

__all__ = ['type_validate']


# This whole thing is a lot more complex and confusing than it needs
# to be, and that's because the `typing` module is not well
# designed. Ideally, types in `typing` would be simple wrapper classes
# that record user intent. To use them, you'd have to call some sort of
# simplification or reduction function. Instead, types in `typing` do a
# bunch of complex metaclass work so as to perform
# simplifications/reductions as the objects are constructed. So:
#  `repr(typing.Optional[int])` -> `Union[int, None]`
# Information has been lost. Plus there isn't really a real API.


# static assert that we're py36+ since __args__ doesn't work in 3.5
if (sys.version_info.major, sys.version_info.minor) < (3, 6):
    raise ValueError('This code requires python 3.6+')


def _is_attr_dot_ib(value: T.Any) -> bool:
    return type(value) is attr._make._CountingAttr


class _nothing:
    blah = attr.ib()


if not _is_attr_dot_ib(_nothing.blah):
    raise ValueError(
        "attrs is not behaving like this code expects")


# These are just for reading clarity in this module; they do nothing
# for automated type checking.
TypingType = T.NewType('TypingType', T.Any)
Validator = T.NewType('Validator', T.Any)


def _type_is_NewType(type_: TypingType) -> bool:
    if callable(type_) and hasattr(type_, '__supertype__'):
        try:
            return (inspect.getfullargspec(type_) ==
                    inspect.getfullargspec(Validator))
        except Exception:
            pass
    return False


def _collapse_validators(
        vals: T.Sequence[Validator],
        reducer: Validator = attr.validators.and_) -> Validator:
    if not vals:
        raise ValueError
    if len(vals) == 1:
        return vals[0]
    else:
        return reducer(*vals)


_sequence_types = {T.List: list, T.Set: set, T.FrozenSet: frozenset,
                   T.Tuple: tuple, T.Deque: collections.deque,
                   T.Sequence: collections.abc.Sequence,
                   T.MutableSequence: collections.abc.MutableSequence,
                   T.AbstractSet: collections.abc.Set,
                   T.MutableSet: collections.abc.MutableSet,
                   T.Collection: collections.abc.Collection}


_mapping_types = {T.Dict: dict,
                  T.Mapping: collections.abc.Mapping,
                  T.MutableMapping: collections.abc.MutableMapping,
                  T.DefaultDict: collections.defaultdict,
                  T.ChainMap: collections.ChainMap}

if sys.version_info >= (3, 7, 0):
    _mapping_types[T.OrderedDict] = collections.OrderedDict


NoneType = type(None)


def _type_to_validator(type_: TypingType) -> T.Optional[Validator]:
    if _type_is_NewType(type_):
        return _type_to_validator(type_.__supertype__)

    origin = getattr(type_, '__origin__', None)
    args = getattr(type_, '__args__', None)
    if origin is T.Union:
        assert args
        if len(args) == 2 and args[-1] is NoneType:
            # Union[X, None] -> optional
            return attr.validators.optional(
                _type_to_validator(args[0]))
        else:
            # Union[*args] -> Or
            # FIXME: drop Or and take advantage of isinstance taking a tuple
            return _collapse_validators(
                list(map(_type_to_validator, args)),
                Or)

    elif origin in _sequence_types:
        # Sequence/List/Tuple/Set/FrozenSet -> deep_iterable
        iterable_type = _sequence_types[origin]
        iterable_validator = attr.validators.instance_of(iterable_type)
        if args:
            is_tuple = origin is T.Tuple
            if is_tuple and len(args) == 2 and args[-1] == ...:
                pass
            elif is_tuple:
                return _TupleValidator(
                    tuple(map(_type_to_validator, args)))
            else:
                assert len(args) == 1
            member_validator = _type_to_validator(args[0])
            return attr.validators.deep_iterable(
                member_validator, iterable_validator)
        else:
            return iterable_validator

    elif origin in _mapping_types:
        # Mapping/Dict -> deep_mapping
        mapping_type = _mapping_types[origin]
        iterable_validator = attr.validators.instance_of(mapping_type)
        if args:
            assert len(args) == 2
            key_validator = _type_to_validator(args[0])
            value_validator = _type_to_validator(args[1])
            return attr.validators.deep_mapping(
                key_validator, value_validator, iterable_validator)
        else:
            return iterable_validator

    elif callable(type_) or isinstance(enum.EnumMeta):
        # else -> instance_of
        return attr.validators.instance_of(type_)

    # FIXME: maybe add something fancy for T.Callable
    else:
        return None


@attr.s(frozen=True, slots=True)
class _Or:
    _validators: T.Sequence[Validator] = attr.ib()

    def __call__(self, instance, attr, value):
        exceptions = []
        for v in self._validators:
            try:
                v(instance, attr, value)
            except Exception as e:
                exceptions.append(e)
            else:
                return
        if len(exceptions) == 1:
            raise exceptions[0]
        elif len(exceptions) > 1:
            raise TypeError('no validators succeeded', exceptions)
        else:
            raise ValueError


def Or(*validators: Validator) -> Validator:
    return _Or(validators)


@attr.s(frozen=True, slots=True)
class _TupleValidator:
    _validators: T.Sequence[Validator] = attr.ib()

    def __call__(self, instance, attr, value):
        if not isinstance(value, tuple):
            raise TypeError(
                f"'{attr}' must be {type((1,))} "
                f"(got {repr(value)} that is a {type(value)}).")
        if len(value) != len(self._validators):
            raise ValueError

        for i, subvalue, validator in zip(
                range(len(value)), value, self._validators):
            validator(instance, f'{attr}[{i}]', subvalue)


def type_validate(cls: type) -> type:
    # only deal with the auto_attribs=False case
    if type(cls) is not type:
        raise ValueError(
            f'type_validate can only called on a class, not a {type(cls)}')
    if hasattr(cls, '__attrs_attrs__'):
        raise ValueError(
            'type_validate must be called before `attr.s`, not after')

    annotations = getattr(cls, '__annotations__', {})
    for name, value in cls.__dict__.items():
        annotation = annotations.get(name)
        if annotation is None:
            continue
        if _is_attr_dot_ib(value):
            new_validator = _type_to_validator(annotation)
            if new_validator is None:
                continue

            if value._validator is None:
                validators = []
            elif isinstance(value._validator, attr._make._AndValidator):
                validators = list(value._validator._validators)
            else:
                validators = [value._validator]

            validators.append(new_validator)
            value._validator = _collapse_validators(validators)
    return cls
