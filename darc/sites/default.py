# -*- coding: utf-8 -*-
"""Default Hooks
===================

The :mod:`darc.sites.default` module is the fallback for sites
customisation.

"""

import time

import darc.typing as typing
from darc.const import SE_WAIT
from darc.link import Link
from darc.sites._abc import BaseSite


class DefaultSite(BaseSite):
    """Default hooks."""

    @staticmethod
    def crawler(timestamp: typing.Datetime, session: typing.Session, link: Link) -> typing.Response:  # pylint: disable=unused-argument
        """Default crawler hook.

        Args:
            timestamp: Timestamp of the worker node reference.
            session (requests.Session): Session object with proxy settings.
            link: Link object to be crawled.

        Returns:
            requests.Response: The final response object with crawled data.

        See Also:
            * :func:`darc.crawl.crawler`

        """
        response = session.get(link.url, allow_redirects=True)
        return response

    @staticmethod
    def loader(timestamp: typing.Datetime, driver: typing.Driver, link: Link) -> typing.Driver:  # pylint: disable=unused-argument
        """Default loader hook.

        When loading, if :data:`~darc.const.SE_WAIT` is a valid time lapse,
        the function will sleep for such time to wait for the page to finish
        loading contents.

        Args:
            timestamp: Timestamp of the worker node reference.
            driver (selenium.webdriver.Chrome): Web driver object with proxy settings.
            link: Link object to be loaded.

        Returns:
            selenium.webdriver.Chrome: The web driver object with loaded data.

        Note:
            Internally, :mod:`selenium` will wait for the browser to finish
            loading the pages before return (i.e. the web API event
            |event|_). However, some extra scripts may take more time
            running after the event.

            .. |event| replace:: ``DOMContentLoaded``
            .. _event: https://developer.mozilla.org/en-US/docs/Web/API/Window/DOMContentLoaded_event

        See Also:
            * :func:`darc.crawl.loader`
            * :data:`darc.const.SE_WAIT`

        """
        driver.get(link.url)

        # wait for page to finish loading
        if SE_WAIT is not None:
            time.sleep(SE_WAIT)

        return driver
