# -*- coding: utf-8 -*-
"""Miscellaneous Utilities
-----------------------------

The :mod:`darc.model.utils` module contains several miscellaneous
utility functions and data fields.

"""

import ipaddress
import json
import pickle

import peewee
import playhouse.mysql_ext
import playhouse.shortcuts

import darc.typing as typing

__all__ = ['table_function',
           'JSONField', 'IPField',
           'IntEnumField', 'PickleField']


def table_function(model_class: peewee.Model) -> str:
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
    return peewee.make_snake_case(name)


class JSONField(playhouse.mysql_ext.JSONField):
    """JSON data field."""

    def db_value(self, value: typing.Any) -> typing.Optional[str]:  # pylint: disable=inconsistent-return-statements
        """Dump the value for database storage.

        Args:
            value: Source JSON value.

        Returns:
            JSON serialised string data.

        """
        if value is not None:
            return json.dumps(value)

    def python_value(self, value: typing.Optional[str]) -> typing.Any:  # pylint: disable=inconsistent-return-statements
        """Load the value from database storage.

        Args:
            value: Serialised JSON string.

        Returns:
            Original JSON data.

        """
        if value is not None:
            return json.loads(value)


class IPField(peewee.IPField):
    """IP data field."""

    def db_value(self, val: typing.Optional[typing.IPAddress]) -> typing.Optional[int]:  # pylint: disable=inconsistent-return-statements
        """Dump the value for database storage.

        Args:
            val: Source IP address instance.

        Returns:
            Integral representation of the IP address.

        """
        if val is not None:
            return int(val)

    def python_value(self, val: typing.Optional[int]) -> typing.Optional[typing.IPAddress]:  # pylint: disable=inconsistent-return-statements
        """Load the value from database storage.

        Args:
            val: Integral representation of the IP address.

        Returns:
            Original IP address instance.

        """
        if val is not None:
            return ipaddress.ip_address(val)


class IntEnumField(peewee.IntegerField):
    """:class:`enum.IntEnum` data field."""

    #: The original :class:`enum.IntEnum` class.
    choices: typing.IntEnum

    # def db_value(self, value: typing.Optional[typing.IntEnum]) -> typing.Optional[str]:  # pylint: disable=inconsistent-return-statements
    #     """Dump the value for database storage.

    #     Args:
    #         val: Original enumeration object.

    #     Returns:
    #         Integral representation of the enumeration.

    #     """
    #     if value is not None:
    #         return value

    def python_value(self, value: typing.Optional[int]) -> typing.Optional[typing.IntEnum]:  # pylint: disable=inconsistent-return-statements
        """Load the value from database storage.

        Args:
            value: Integral representation of the enumeration.

        Returns:
            Original enumeration object.

        """
        if value is not None:
            return self.choices(value)


class PickleField(peewee.BlobField):
    """Pickled data field."""

    def db_value(self, value: typing.Any) -> typing.Optional[bytes]:  # pylint: disable=inconsistent-return-statements
        """Dump the value for database storage.

        Args:
            value: Source value.

        Returns:
            Picked bytestring data.

        """
        if value is not None:
            value = pickle.dumps(value)
        return super().db_value(value)

    def python_value(self, value: typing.Optional[bytes]) -> typing.Any:  # pylint: disable=inconsistent-return-statements
        """Load the value from database storage.

        Args:
            value: SPicked bytestring data.

        Returns:
            Original data.

        """
        value = super().python_value(value)
        if value is not None:
            return pickle.loads(value)
