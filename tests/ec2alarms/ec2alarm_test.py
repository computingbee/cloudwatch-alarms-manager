import time
import pytest
import json
import types
import os

from .ec2alarms import EC2Alarm

class TestEC2Alarm:

    @pytest.fixture
    def loadCWEventFromJSON(self):
        return json.load(open(os.path.join("tests","ec2alarms","data","ec2eventrunning.json")))

    @pytest.fixture
    def initializeEC2Alarm(self,loadCWEventFromJSON):
        cwevent = loadCWEventFromJSON
        return EC2Alarm(cwevent["detail"]["instance-id"], cwevent["region"])

    @pytest.mark.dependency()
    def test_CWEventLoaded(self,loadCWEventFromJSON):
        cwevent = loadCWEventFromJSON
        assert type(cwevent) != None
        assert cwevent["region"] == "us-east-1"
        assert cwevent["detail"]["state"] == "running"

    @pytest.mark.dependency(depends=["CWEventLoaded"])
    def test_EC2AlarmInitialized(self,loadCWEventFromJSON,initializeEC2Alarm):
        cwevent = loadCWEventFromJSON
        ec2a = initializeEC2Alarm
        assert ec2a != None
        assert ec2a.ec2instanceid == cwevent["detail"]["instance-id"]
        assert ec2a._region == cwevent["region"]

    @pytest.mark.dependency(depends=["CWEventLoaded","EC2AlarmInitialized"])    
    def test_EC2AlarmGetAlarmDefinition(self,initializeEC2Alarm):
        ec2a = initializeEC2Alarm
        alarms = ("EC2_StatusCheckFailed_System","High_CPU_Utilization")
        for a in alarms:
            ad = ec2a._get_alarm_defintion(a)
            assert type(ad) != types.NoneType
            assert a == ad["Prefix"]

    @pytest.mark.dependency(depends=["EC2AlarmInitialized"])    
    def test_EC2AlarmSetInstanceName(self,initializeEC2Alarm):
        ec2a = initializeEC2Alarm
        ec2a._set_ec2_instance_name()
        ec2iname = "CWTEST01"
        assert ec2iname  == ec2a._ec2iname

    @pytest.mark.dependency(depends=["EC2AlarmInitialized","EC2AlarmSetInstanceName"]) 
    def test_EC2AlarmExpectedAlarms(self,initializeEC2Alarm):
        ec2a = initializeEC2Alarm
        ec2a._set_ec2_instance_name()
        alarms = ("EC2_StatusCheckFailed_System","High_CPU_Utilization","EC2_StatusCheckFailed_Instance",\
            "EC2_StatusCheckFailed","Windows_LogicalFreeSpace_C","Windows_Memory_Committed_Bytes_Usage")
        ec2i_expected_alarms = set()
        for a in alarms:
            ec2i_expected_alarms.add(ec2a._ec2iname + "_" + a)
        assert ec2i_expected_alarms == ec2a._get_desired_alarms()

    @pytest.mark.dependency(depends=["CWEventLoaded","EC2AlarmInitialized","EC2AlarmSetInstanceName","EC2AlarmExpectedAlarms"]) 
    def test_EC2AlarmCreateAlarms(self,initializeEC2Alarm):

        ec2a = initializeEC2Alarm
        ec2a._set_ec2_instance_name()
        desired_alarms_names = ec2a._get_desired_alarms()
        ec2a._create(list(desired_alarms_names))
        
        time.sleep(10)

        configured_alarms = ec2a._cwc.describe_alarms(AlarmNamePrefix=ec2a._ec2iname,AlarmTypes=['MetricAlarm'])
        configured_alarms_names = set() 
        for a in configured_alarms["MetricAlarms"]:
            configured_alarms_names.add(a["AlarmName"])

        assert desired_alarms_names == configured_alarms_names

    @pytest.mark.dependency(depends=["CWEventLoaded","EC2AlarmInitialized","EC2AlarmSetInstanceName","EC2AlarmCreateAlarms"]) 
    def test_EC2AlarmRemoveAlarms(self,initializeEC2Alarm):

        ec2a = initializeEC2Alarm
        ec2a._set_ec2_instance_name()
        desired_alarms_names = ec2a._get_desired_alarms()
        ec2a._remove(list(desired_alarms_names))
        
        time.sleep(10)

        configured_alarms = ec2a._cwc.describe_alarms(AlarmNamePrefix=ec2a._ec2iname,AlarmTypes=['MetricAlarm'])
        
        assert configured_alarms["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert len(configured_alarms["MetricAlarms"]) == 0

    @pytest.mark.dependency(depends=["CWEventLoaded","EC2AlarmInitialized","EC2AlarmSetInstanceName","EC2AlarmCreateAlarms","EC2AlarmRemoveAlarms"]) 
    def test_EC2AlarmSetupAlarms(self,initializeEC2Alarm):

        ec2a = initializeEC2Alarm
        ec2a._set_ec2_instance_name()
        desired_alarms_names = ec2a._get_desired_alarms()
        ec2a._setup_alarms()

        time.sleep(10)
     
        configured_alarms = ec2a._cwc.describe_alarms(AlarmNamePrefix=ec2a._ec2iname,AlarmTypes=['MetricAlarm'])
        configured_alarms_names = set() 
        for a in configured_alarms["MetricAlarms"]:
            configured_alarms_names.add(a["AlarmName"])

        assert desired_alarms_names == configured_alarms_names

        ec2a._remove(list(configured_alarms_names))

    



