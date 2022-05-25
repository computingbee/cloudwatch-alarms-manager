import unittest
unittest.TestLoader.sortTestMethodsUsing = None

from .s3alarms import S3AlarmErrorTargets,S3Alarm

class TestHelper:

    msg = "simple exception test"

    def raiseSimpleException(self):
        pass

    def raiseLoggingException(self):
        pass

class Test_S3AlarmErrorTC(unittest.TestCase):

    def setUp(self):
        self.testhelper = TestHelper()
              
    def test_S3AlarmErrorSimpleException(self):
        pass

    def tearDown(self):
        self.testhelper = None

if __name__ == "__main__":
    unittest.main()