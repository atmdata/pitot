from __future__ import annotations

import functools
import inspect
import logging
from typing import Any, Callable

import numpy as np
import pint

from . import Q_, u

_log = logging.getLogger(__name__)


STRATOSPHERE_TEMP = Q_(216.65, u.K)  # until altitude = 22km
SPECIFIC_GAS_CONSTANT = Q_(287.05287, u.J / u.kg / u.K)

ReturnQuantity = Callable[..., pint.Quantity[Any]]


def default_units(**unit_kw: str | pint.Unit) -> Callable[..., ReturnQuantity]:
    def wrapper(fun: ReturnQuantity) -> ReturnQuantity:
        msg = "Input argument '{arg}' will be considered as '{unit}'"

        @functools.wraps(fun)
        def decorated_func(*args: Any, **kwargs: Any) -> pint.Quantity[Any]:
            bind_args = inspect.signature(fun).bind(*args, **kwargs)
            new_args = dict(bind_args.arguments)
            for arg, value in new_args.items():
                unit = unit_kw.get(arg, None)
                if unit is not None and not isinstance(arg, pint.Quantity):
                    _log.warning(msg.format(arg=arg, unit=unit))
                    new_args[arg] = Q_(value, unit)

            return fun(**new_args)

        return decorated_func

    return wrapper


@default_units(h=u.meter)
def temperature(h: Any) -> pint.Quantity[Any]:
    temp = np.maximum(
        Q_(288.15, u.K) - Q_(0.0065, u.K / u.meter) * h,
        STRATOSPHERE_TEMP,
    )
    return temp  # type: ignore


@default_units(h=u.meter)
def density(h: Any) -> pint.Quantity[Any]:
    temp = temperature(h)
    density_troposphere = (
        Q_(1.225, u.kg / u.meter ** 3) * (temp / Q_(288.15, u.K)) ** 4.256848
    )
    delta = np.maximum(0, h - Q_(11000, u.meter))
    density = density_troposphere * np.exp(-delta / Q_(6341.5522, u.meter))
    return density  # type: ignore


@default_units(h=u.meter)
def pressure(h: Any) -> pint.Quantity[Any]:
    temp = temperature(h)
    den = density(h)
    press = den * temp * SPECIFIC_GAS_CONSTANT
    return press  # type: ignore
