# -*- coding: utf-8 -*-
"""Base Model
----------------

The :mod:`darc.model.abc` module contains abstract base class
of all data models for the :mod:`darc` project.

"""

import peewee
import playhouse.shortcuts

from darc.const import DB as database
from darc.const import DB_WEB as database_web
from darc.model.utils import table_function

__all__ = [
    'BaseMeta', 'BaseModel',
]


class BaseMeta:
    """Basic metadata for data models."""

    #: Reference database storage (c.f. :class:`~darc.const.DB`).
    database = database

    #: Generate table name dynamically (c.f. :func:`~darc.models.utils.table_function`).
    table_function = table_function


class BaseMetaWeb(BaseMeta):
    """Basic metadata for data models of data submission."""

    #: Reference database storage (c.f. :class:`~darc.const.DB`).
    database = database_web


class BaseModel(peewee.Model):
    """Base model with standard patterns.

    Notes:
        The model will implicitly have a :class:`~peewee.AutoField`
        attribute named as :attr:`id`.

    """

    #: Basic metadata for data models.
    Meta = BaseMeta

    def to_dict(self, keep_id: bool = False) -> None:
        """Convert record to :obj:`dict`.

        Args:
            keep_id: If keep the ID auto field.

        Returns:
            The data converted through :func:`playhouse.shortcuts.model_to_dict`.

        """
        data = playhouse.shortcuts.model_to_dict(self)
        if keep_id:
            return data

        if 'id' in data:
            del data['id']
        return data


class BaseModelWeb(BaseModel):
    """Base model with standard patterns for data submission.

    Notes:
        The model will implicitly have a :class:`~peewee.AutoField`
        attribute named as :attr:`id`.

    """

    #: Basic metadata for data models.
    Meta = BaseMetaWeb
