"""
See ../docs/ec2alarms.md for more details on this package
"""
__version__ = '1.0.0'
__author__  = 'Haris Buchal <hb@computingbee.com>'

from .s3alarm import S3Alarm
from .s3alarmerror import S3AlarmError, S3AlarmErrorTargets
