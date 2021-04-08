# -*- coding: utf-8 -*-
"""URL Records
-----------------

The :mod:`darc.model.web.url` module defines the data model
representing URLs, specifically from ``requests`` and
``selenium`` submission.

.. seealso::

   Please refer to :func:`darc.submit.submit_requests` and
   :func:`darc.submit.submit_selenium` for more information.

"""

from typing import TYPE_CHECKING

from peewee import BooleanField, CharField, DateTimeField, ForeignKeyField, TextField

from darc._typing import SPHINX_BUILD
from darc.model.abc import BaseMetaWeb as BaseMeta
from darc.model.abc import BaseModelWeb as BaseModel
from darc.model.utils import IntEnumField, Proxy
from darc.model.web.hostname import HostnameModel

if TYPE_CHECKING:
    from typing import List, TypeVar

    from darc._compat import datetime

    if not SPHINX_BUILD:
        from darc.model.web.requests import RequestsModel  # pylint: disable=unused-import
        from darc.model.web.selenium import SeleniumModel  # pylint: disable=unused-import
    else:
        RequestsModel = TypeVar('RequestsModel', bound='darc.model.web.requests.RequestsModel')  # type: ignore[name-defined,unreachable,misc] # pylint: disable=line-too-long
        SeleniumModel = TypeVar('SeleniumModel', bound='darc.model.web.selenium.SeleniumModel')  # type: ignore[name-defined,unreachable,misc] # pylint: disable=line-too-long

__all__ = ['URLModel', 'URLThroughModel']


class URLModel(BaseModel):
    """Data model for a requested URL.

    Important:
        The *alive* of a URL is toggled if :func:`~darc.crawl.crawler`
        successfully requested such URL and the status code is
        :attr:`~flask.Response.ok`.

    """

    #: ``requests`` submission record, back reference from
    #: :attr:`RequestsModel.url <darc.models.web.requests.RequestsModel.url>`.
    requests: 'List[RequestsModel]'

    #: ``selenium`` submission record, back reference from
    #: :attr:`SeleniumModel.url <darc.models.web.selenium.SeleniumModel.url>`.
    selenium: 'List[SeleniumModel]'

    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: str = TextField()
    #: Sha256 hash value (c.f. :attr:`Link.name <darc.link.Link.name>`).
    hash: str = CharField(max_length=256, unique=True)

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    hostname: 'HostnameModel' = ForeignKeyField(HostnameModel, backref='urls')
    #: Proxy type (c.f. :attr:`link.proxy <darc.link.Link.proxy>`).
    proxy: 'Proxy' = IntEnumField(choices=Proxy)

    #: Timestamp of first submission.
    discovery: 'datetime' = DateTimeField()
    #: Timestamp of last submission.
    last_seen: 'datetime' = DateTimeField()

    #: If the hostname is still active.
    alive: bool = BooleanField()
    #: The hostname is active/inactive since this timestamp.
    since: 'datetime' = DateTimeField()

    @classmethod
    def get_by_url(cls, url: str) -> 'URLModel':
        """Select by URL.

        Args:
            url: URL to select.

        Returns:
            Selected URL model.

        """
        return cls.get(cls.url == url)

    @property
    def parents(self) -> 'List[URLModel]':
        """Back reference to where the URL was identified."""
        return (URLModel
                .select()
                .join(URLThroughModel, on=URLThroughModel.parent)
                .where(URLThroughModel.child == self)
                .order_by(URLModel.url))

    @property
    def childrent(self) -> 'List[URLModel]':
        """Back reference to which URLs were identified from the URL."""
        return (URLModel
                .select()
                .join(URLThroughModel, on=URLThroughModel.child)
                .where(URLThroughModel.parent == self)
                .order_by(URLModel.url))


class URLThroughModel(BaseModel):
    """Data model for the map of URL extration chain."""

    #: Back reference to where the URL was identified.
    parent: 'List[URLModel]' = ForeignKeyField(URLModel, backref='parents')
    #: Back reference to which URLs were identified from the URL.
    child: 'List[URLModel]' = ForeignKeyField(URLModel, backref='children')

    class Meta(BaseMeta):
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('parent', 'child'), True),
        )
