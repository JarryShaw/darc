# -*- coding: utf-8 -*-
# pylint: disable=import-error

from typing import TYPE_CHECKING

from darc.error import WorkerBreak
from darc.process import register

if TYPE_CHECKING:
    from typing import List, Literal, NoReturn

    from darc.link import Link


def dummy_hook(node_type: 'Literal["crawler", "loader"]', link_pool: 'List[Link]') -> 'NoReturn':
    """A sample hook function that prints the processed links
    in the past round and informs the work to quit.

    Args:
        node_type (Literal['crawler', 'loader']): Type of worker node.
        link_pool (List[darc.link.Link]): List of processed links.

    Returns:
        NoReturn: The hook function will never return, though return
            values will be ignored anyway.

    Raises:
        darc.error.WorkerBreak: Inform the work to quit after this round.

    """
    if node_type == 'crawler':
        verb = 'crawled'
    elif node_type == 'loader':
        verb = 'loaded'
    else:
        raise ValueError('unknown type of worker node: %s' % node_type)

    for link in link_pool:
        print('We just %s the link: %s' % (verb, link.url))
    raise WorkerBreak


# register the hook function
register(dummy_hook)
