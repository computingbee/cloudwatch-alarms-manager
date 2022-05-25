import sys
import logging
from enum import Enum, unique

@unique
class EC2AlarmErrorTargets(Enum):
    PROPAGATE = 1
    LOGANDPROPAGATE = 2

class EC2AlarmError(Exception):
    """
    Error raised for API errros or internal errors

    Attributes:
        trigger -- object that caused the error condition
        message -- error explanation
        target  -- propogate to parent exception and optionally send to logger
        terminate -- indicates terminating exception, will exit program
    """

    __trigger = None
    __message = ''
    __terminate = False
    __logger = None

    def __init__(self, trigger, \
        target:EC2AlarmErrorTargets=EC2AlarmErrorTargets.PROPAGATE, message="Unexpected EC2 alarm error", terminate:bool = False):
        
        self.__trigger = trigger
        self.__message = message
        self.__terminate = terminate

        err_message = "Trigger: " + type(self.get_trigger()).__name__ + ", Error Message: " + self.get_message()

        if target is EC2AlarmErrorTargets.LOGANDPROPAGATE:
            logging.basicConfig(format='%(levelname)s:%(asctime)s:%(message)s',datefmt='%m-%d-%Y %I:%M:%S %p')
            self.__logger = logging.getLogger("EC2AlarmLogger")
            self.get_logger().setLevel(logging.INFO)
            self.get_logger().info(err_message) 
        
        super().__init__(err_message)

        if self.get_terminate():
            sys.exit(500)

    def __str__(self):
        return f'{self.get_message()}'

    def get_trigger(self):
        return self.__trigger

    def get_message(self):
        return self.__message

    def get_logger(self):
        return self.__logger

    def get_terminate(self):
        return self.__terminate
        