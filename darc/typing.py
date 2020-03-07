# -*- coding: utf-8 -*-
"""Typing declrations."""
# pylint: disable=unused-wildcard-import

import argparse
import datetime
import queue
import subprocess
import types
import typing
from typing import *

import requests
import requests_futures.sessions
import selenium.common.exceptions
import selenium.webdriver
import selenium.webdriver.common.proxy
import stem
import stem.control
import stem.process
import stem.util.term
from typing_extensions import *

# argparse.ArgumentParser
ArgumentParser = typing.NewType('ArgumentParser', argparse.ArgumentParser)

Datetime = typing.NewType('Datetime', datetime.datetime)

# requests.Response
Response = typing.NewType('Response', requests.Response)

# requests.Session
Session = typing.NewType('Session', requests.Session)

# requests_futures.sessions.FuturesSession
FuturesSession = typing.NewType('FuturesSession', requests_futures.sessions.FuturesSession)

# queue.Queue
Queue = typing.NewType('Queue', queue.Queue)

# subprocess.Popen
Popen = typing.NewType('Popen', subprocess.Popen)

# stem.control.Controller
Controller = typing.NewType('Controller', stem.control.Controller)

# stem.util.term.Color
Color = typing.NewType('Color', stem.util.term.Color)

# selenium.webdriver.Chrome
Driver = typing.NewType('Driver', selenium.webdriver.Chrome)

# selenium.webdriver.ChromeOptions
Options = typing.NewType('Options', selenium.webdriver.ChromeOptions)

# selenium.webdriver.DesiredCapabilities
DesiredCapabilities = typing.NewType('DesiredCapabilities', selenium.webdriver.DesiredCapabilities)

# types.ModuleType
ModuleType = typing.NewType('ModuleType', types.ModuleType)

# types.FrameType
FrameType = typing.NewType('FrameType', types.FrameType)

# Dict[str, Tuple[Callable, Callable]]
LinkMap = typing.Dict[str, typing.Tuple[typing.Callable[[], Session], typing.Callable[[], Driver]]]
