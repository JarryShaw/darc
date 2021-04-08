# -*- coding: utf-8 -*-
# pylint: disable=import-error,unused-argument,ungrouped-imports

import sys
import time
from typing import TYPE_CHECKING

from darc.__main__ import main
from darc.const import SE_WAIT
from darc.sites import BaseSite, register

if TYPE_CHECKING:
    from datetime import datetime
    from typing import List

    from requests import Response, Session
    from selenium.webdriver import Chrome

    from darc.link import Link


class MySite(BaseSite):
    """This is a site customisation class for demonstration purpose.
    You may implement a module as well should you prefer."""

    #: List[str]: Hostnames the sites customisation is designed for.
    hostname = ['mysite.com', 'www.mysite.com']  # type: List[str]

    @staticmethod
    def crawler(timestamp: 'datetime', session: 'Session', link: 'Link') -> 'Response':
        """Crawler hook for my site.

        Args:
            timestamp (datetime.datetime): Timestamp of the worker node reference.
            session (requests.Session): Session object with proxy settings.
            link (darc.link.Link): Link object to be crawled.

        Returns:
            requests.Response: The final response object with crawled data.

        """
        # inject cookies
        session.cookies.set('SessionID', 'fake-session-id-value')

        response = session.get(link.url, allow_redirects=True)
        return response

    @staticmethod
    def loader(timestamp: 'datetime', driver: 'Chrome', link: 'Link') -> 'Chrome':
        """Loader hook for my site.

        Args:
            timestamp (datetime.datetime): Timestamp of the worker node reference.
            driver (selenium.webdriver.Chrome): Web driver object with proxy settings.
            link (darc.link.Link): Link object to be loaded.

        Returns:
            selenium.webdriver.Chrome: The web driver object with loaded data.

        """
        # land on login page
        driver.get('https://%s/login' % link.host)

        # animate login attempt
        form = driver.find_element_by_id('login-form')
        form.find_element_by_id('username').send_keys('admin')
        form.find_element_by_id('password').send_keys('p@ssd')
        form.click()

        driver.get(link.url)

        # wait for page to finish loading
        if SE_WAIT is not None:
            time.sleep(SE_WAIT)

        return driver


# register sites
register(MySite)


if __name__ == "__main__":
    sys.exit(main())
