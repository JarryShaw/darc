# -*- coding: utf-8 -*-
"""Typing declrations."""
# pylint: disable=unused-wildcard-import

import argparse
import datetime
import enum
import ipaddress
import queue
import subprocess
import types
from typing import *

import peewee
import requests_futures.sessions
import stem
import stem.control
import stem.process
import stem.util.term
from typing_extensions import *

import requests
import selenium.common.exceptions
import selenium.webdriver
import selenium.webdriver.common.proxy

# argparse.ArgumentParser
ArgumentParser = argparse.ArgumentParser

Datetime = datetime.datetime

# requests.Response
Response = requests.Response

# requests.Session
Session = requests.Session

# requests_futures.sessions.FuturesSession
FuturesSession = requests_futures.sessions.FuturesSession

# queue.Queue
Queue = queue.Queue

# subprocess.Popen
Popen = subprocess.Popen

# stem.control.Controller
Controller = stem.control.Controller

# stem.util.term.Color
Color = stem.util.term.Color

# selenium.webdriver.Chrome
Driver = selenium.webdriver.Chrome

# selenium.webdriver.ChromeOptions
Options = selenium.webdriver.ChromeOptions

# selenium.webdriver.DesiredCapabilities
DesiredCapabilities = selenium.webdriver.DesiredCapabilities

# types.ModuleType
ModuleType = types.ModuleType

# types.FrameType
FrameType = types.FrameType

# Dict[str, Tuple[Callable, Callable]]
LinkMap = Dict[str, Tuple[Callable[[], Session], Callable[[], Driver]]]

# enum.IntEnum
IntEnum = enum.IntEnum

# Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]

# peewee.Database
Database = peewee.Database

# Dict[str, str]
Cookies = Dict[str, str]

# Dict[str, str]
Headers = Dict[str, str]
