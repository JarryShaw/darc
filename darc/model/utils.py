# -*- coding: utf-8 -*-
# pylint: disable=unsubscriptable-object,ungrouped-imports
"""Miscellaneous Utilities
-----------------------------

The :mod:`darc.model.utils` module contains several miscellaneous
utility functions and data fields.

"""

import enum
import ipaddress
import json
import pickle  # nosec
from typing import TYPE_CHECKING

from peewee import BlobField, IntegerField
from peewee import IPField as _IPField
from peewee import Model, make_snake_case
from playhouse.mysql_ext import JSONField as _JSONField

if TYPE_CHECKING:
    from enum import IntEnum
    from ipaddress import IPv4Address, IPv6Address
    from typing import Any, Optional, Union

    IPAddress = Union[IPv4Address, IPv6Address]

__all__ = ['table_function',
           'JSONField', 'IPField',
           'IntEnumField', 'PickleField',
           'Proxy']


def table_function(model_class: Model) -> str:
    """Generate table name dynamically.

    The function strips ``Model`` from the class name and
    calls :func:`peewee.make_snake_case` to generate a
    proper table name.

    Args:
        model_class: Data model class.

    Returns:
        Generated table name.

    """
    name: str = model_class.__name__
    if name.endswith('Model'):
        name = name[:-5]  # strip ``Model`` suffix
    return make_snake_case(name)


class JSONField(_JSONField):
    """JSON data field."""

    def db_value(self, value: 'Any') -> 'Optional[str]':  # pylint: disable=inconsistent-return-statements
        """Dump the value for database storage.

        Args:
            value: Source JSON value.

        Returns:
            JSON serialised string data.

        """
        if value is not None:
            return json.dumps(value)
        return None

    def python_value(self, value: 'Optional[str]') -> 'Any':  # pylint: disable=inconsistent-return-statements
        """Load the value from database storage.

        Args:
            value: Serialised JSON string.

        Returns:
            Original JSON data.

        """
        if value is not None:
            return json.loads(value)
        return None


class IPField(_IPField):
    """IP data field."""

    def db_value(self, val: 'Optional[Union[str, IPAddress]]') -> 'Optional[int]':  # pylint: disable=inconsistent-return-statements
        """Dump the value for database storage.

        Args:
            value: Source IP address instance.

        Returns:
            Integral representation of the IP address.

        """
        if val is not None:
            if isinstance(val, str):
                val = ipaddress.ip_address(val)
            return int(val)  # type: ignore[arg-type]
        return None

    def python_value(self, val: 'Optional[int]') -> 'Optional[IPAddress]':  # pylint: disable=inconsistent-return-statements
        """Load the value from database storage.

        Args:
            value: Integral representation of the IP address.

        Returns:
            Original IP address instance.

        """
        if val is not None:
            return ipaddress.ip_address(val)
        return None


class IntEnumField(IntegerField):
    """:class:`enum.IntEnum` data field."""

    #: The original :class:`enum.IntEnum` class.
    choices: 'IntEnum'

    # def db_value(self, value: 'Optional[IntEnum]') -> 'Optional[str]':  # pylint: disable=inconsistent-return-statements
    #     """Dump the value for database storage.

    #     Args:
    #         val: Original enumeration object.

    #     Returns:
    #         Integral representation of the enumeration.

    #     """
    #     if value is not None:
    #         return value

    def python_value(self, value: 'Optional[int]') -> 'Optional[IntEnum]':  # pylint: disable=inconsistent-return-statements
        """Load the value from database storage.

        Args:
            value: Integral representation of the enumeration.

        Returns:
            Original enumeration object.

        """
        if value is not None:
            return self.choices(value)  # type: ignore
        return None


class PickleField(BlobField):
    """Pickled data field."""

    def db_value(self, value: 'Any') -> 'Optional[bytes]':  # pylint: disable=inconsistent-return-statements
        """Dump the value for database storage.

        Args:
            value: Source value.

        Returns:
            Picked bytestring data.

        """
        if value is not None:
            value = pickle.dumps(value)
        return super().db_value(value)

    def python_value(self, value: 'Optional[bytes]') -> 'Any':  # pylint: disable=inconsistent-return-statements
        """Load the value from database storage.

        Args:
            value: SPicked bytestring data.

        Returns:
            Original data.

        """
        value = super().python_value(value)
        if value is not None:
            return pickle.loads(value)  # nosec
        return None


class Proxy(enum.IntEnum):
    """Proxy types supported by :mod:`darc`.

    .. _tor2web: https://onion.sh/
    """

    #: No proxy.
    NULL = enum.auto()
    #: Tor proxy.
    TOR = enum.auto()
    #: I2P proxy.
    I2P = enum.auto()
    #: ZeroNet proxy.
    ZERONET = enum.auto()
    #: Freenet proxy.
    FREENET = enum.auto()
    #: Proxied Tor (`tor2web`_, no proxy).
    TOR2WEB = enum.auto()
