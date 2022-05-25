import logging
import unittest
unittest.TestLoader.sortTestMethodsUsing = None

from .ec2alarms import EC2AlarmErrorTargets, EC2AlarmError

class TestHelper:

    msg = "test raiseSimpleException"

    def raiseSimpleException(self):
        raise EC2AlarmError(self,EC2AlarmErrorTargets.PROPAGATE,self.msg, False)

    def raiseLoggingException(self):
        raise EC2AlarmError(self,EC2AlarmErrorTargets.LOGANDPROPAGATE,self.msg, False)

    def raiseTerminatingException(self):
        raise EC2AlarmError(self,EC2AlarmErrorTargets.PROPAGATE,self.msg,True)

class Test_EC2AlarmErrorTC(unittest.TestCase):

    def setUp(self):
        self.propagate:EC2AlarmErrorTargets = EC2AlarmErrorTargets.PROPAGATE
        self.log_and_propagate:EC2AlarmErrorTargets = EC2AlarmErrorTargets.LOGANDPROPAGATE
        self.testhelper = TestHelper()
        
    def test_EC2AlarmErrorTargets(self):
        self.assertEqual(EC2AlarmErrorTargets.PROPAGATE, self.propagate)
        self.assertEqual(EC2AlarmErrorTargets.LOGANDPROPAGATE, self.log_and_propagate)
        
    def test_EC2AlarmErrorSimpleException(self):
        self.assertRaises(EC2AlarmError, self.testhelper.raiseSimpleException)

    def test_EC2AlarmErrorSimpleExceptionObject(self):
        with self.assertRaises(EC2AlarmError) as cm_error:
            self.testhelper.raiseSimpleException()
        self.assertEqual(TestHelper, type(cm_error.exception.get_trigger()))
        self.assertEqual(self.testhelper.msg, cm_error.exception.get_message())
        self.assertEqual(None, cm_error.exception.get_logger())
    
    def test_EC2AlarmErrorLoggingException(self):
        with self.assertRaises(EC2AlarmError) as cm_error:
            self.testhelper.msg = "test raiseLoggingException"
            self.testhelper.raiseLoggingException()
        self.assertEqual(logging.Logger, type(cm_error.exception.get_logger()))
        self.assertIn("EC2AlarmLogger", logging.getLogger("EC2AlarmLogger").manager.loggerDict)
        self.assertTrue(cm_error.exception.get_logger().isEnabledFor(logging.INFO))
        with self.assertLogs(cm_error.exception.get_logger(),level=logging.INFO) as cm_logger:
                cm_error.exception.get_logger().info("unit testing logger")
        self.assertEqual("EC2AlarmLogger", cm_error.exception.get_logger().name)
        self.assertEqual(1,len(cm_logger.output))
        self.assertEqual("INFO:EC2AlarmLogger:unit testing logger",cm_logger.output[0])

    def test_EC2AlarmErrorTerminatingException(self):
        with self.assertRaises(SystemExit) as cm_exit:
                self.testhelper.msg = "test raiseTerminatingException"
                self.testhelper.raiseTerminatingException()
        self.assertEqual(SystemExit, type(cm_exit.exception))
    
    def tearDown(self):
        self.propagate = None
        self.log_and_propagate = None
        self.testhelper = None

if __name__ == "__main__":
    unittest.main()