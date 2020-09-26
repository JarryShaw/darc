# -*- coding: utf-8 -*-
"""Typing declrations."""
# pylint: disable=all

import argparse
import datetime
import enum
import ipaddress
import queue
import subprocess  # nosec
import types
from typing import *
import typing

import peewee
import requests
import requests_futures.sessions
import selenium.webdriver
import stem
import stem.control
import stem.process
import stem.util.term
from typing_extensions import *  # type: ignore

T = typing.TypeVar('T')

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

# types.MethodType
MethodType = types.MethodType

# Dict[str, Tuple[Callable, Callable]]
LinkMap = Dict[str, Tuple[Callable[[bool], Session], Callable[[], Driver]]]  # type: ignore

# enum.IntEnum
IntEnum = enum.IntEnum

# Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]

# peewee.Database
Database = peewee.Database

# List[Dict[str, Any]]
Cookies = List[Dict[str, Any]]

# Dict[str, str]
Headers = Dict[str, str]
