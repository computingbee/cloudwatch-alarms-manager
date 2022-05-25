import os
import logging
from enum import Enum, unique

@unique
class S3AlarmErrorTargets(Enum):
    CONSOLE = 1
    LOGGER = 2

class S3AlarmError(Exception):
    pass
    