# -*- coding: utf-8 -*-
# pylint: disable=ungrouped-imports

import os
from typing import TYPE_CHECKING

import peewee
import playhouse.mysql_ext
import playhouse.shortcuts

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any, Dict, List

# database client
DB = playhouse.db_url.connect(os.getenv('DB_URL', 'mysql://127.0.0.1'))


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
    name = model_class.__name__  # type: str
    if name.endswith('Model'):
        name = name[:-5]  # strip ``Model`` suffix
    return peewee.make_snake_case(name)


class BaseMeta:
    """Basic metadata for data models."""

    #: Reference database storage (c.f. :class:`~darc.const.DB`).
    database = DB

    #: Generate table name dynamically (c.f. :func:`~darc.model.table_function`).
    table_function = table_function


class BaseModel(peewee.Model):
    """Base model with standard patterns.

    Notes:
        The model will implicitly have a :class:`~peewee.AutoField`
        attribute named as :attr:`id`.

    """

    #: Basic metadata for data models.
    Meta = BaseMeta

    def to_dict(self, keep_id: bool = False) -> 'Dict[str, Any]':
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


class HostnameModel(BaseModel):
    """Data model for a hostname record."""

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    hostname: str = peewee.TextField()
    #: Proxy type (c.f. :attr:`link.proxy <darc.link.Link.proxy>`).
    proxy: str = peewee.CharField(max_length=8)

    #: Timestamp of first ``new_host`` submission.
    discovery: 'datetime' = peewee.DateTimeField()
    #: Timestamp of last related submission.
    last_seen: 'datetime' = peewee.DateTimeField()


class RobotsModel(BaseModel):
    """Data model for ``robots.txt`` data."""

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    host: 'HostnameModel' = peewee.ForeignKeyField(HostnameModel, backref='robots')
    #: Timestamp of the submission.
    timestamp: 'datetime' = peewee.DateTimeField()

    #: Document data as :obj:`bytes`.
    data: bytes = peewee.BlobField()
    #: Path to the document.
    path: str = peewee.CharField()


class SitemapModel(BaseModel):
    """Data model for ``sitemap.xml`` data."""

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    host: 'HostnameModel' = peewee.ForeignKeyField(HostnameModel, backref='sitemaps')
    #: Timestamp of the submission.
    timestamp: 'datetime' = peewee.DateTimeField()

    #: Document data as :obj:`bytes`.
    data: bytes = peewee.BlobField()
    #: Path to the document.
    path: str = peewee.CharField()


class HostsModel(BaseModel):
    """Data model for ``hosts.txt`` data."""

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    host: 'HostnameModel' = peewee.ForeignKeyField(HostnameModel, backref='hosts')
    #: Timestamp of the submission.
    timestamp: 'datetime' = peewee.DateTimeField()

    #: Document data as :obj:`bytes`.
    data: bytes = peewee.BlobField()
    #: Path to the document.
    path: str = peewee.CharField()


class URLModel(BaseModel):
    """Data model for a requested URL."""

    #: Timestamp of last related submission.
    last_seen: 'datetime' = peewee.DateTimeField()
    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: str = peewee.TextField()

    #: Hostname (c.f. :attr:`link.host <darc.link.Link.host>`).
    host: HostnameModel = peewee.ForeignKeyField(HostnameModel, backref='urls')
    #: Proxy type (c.f. :attr:`link.proxy <darc.link.Link.proxy>`).
    proxy: str = peewee.CharField(max_length=8)

    #: Base path (c.f. :attr:`link.base <darc.link.Link.base>`).
    base: str = peewee.CharField()
    #: Link hash (c.f. :attr:`link.name <darc.link.Link.name>`).
    name: str = peewee.FixedCharField(max_length=64)

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
    parent: 'List[URLModel]' = peewee.ForeignKeyField(URLModel, backref='parents')
    #: Back reference to which URLs were identified from the URL.
    child: 'List[URLModel]' = peewee.ForeignKeyField(URLModel, backref='children')

    class Meta(BaseMeta):
        indexes = (
            # Specify a unique multi-column index on from/to-url.
            (('parent', 'child'), True),
        )


class RequestsDocumentModel(BaseModel):
    """Data model for documents from ``requests`` submission."""

    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: 'URLModel' = peewee.ForeignKeyField(URLModel, backref='requests')

    #: Document data as :obj:`bytes`.
    data: bytes = peewee.BlobField()
    #: Path to the document.
    path: str = peewee.CharField()


class SeleniumDocumentModel(BaseModel):
    """Data model for documents from ``selenium`` submission."""

    #: Original URL (c.f. :attr:`link.url <darc.link.Link.url>`).
    url: 'URLModel' = peewee.ForeignKeyField(URLModel, backref='selenium')

    #: Document data as :obj:`bytes`.
    data: bytes = peewee.BlobField()
    #: Path to the document.
    path: str = peewee.CharField()
