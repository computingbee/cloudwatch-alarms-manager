import os
import re
import boto3
import json

from .ec2alarmerror import EC2AlarmError, EC2AlarmErrorTargets

class EC2Alarm:
    """ 
    Creates missing or new CloudWatch metric alarms for an EC2 instance
    
    Attributes:
        __ec2instanceid -- instance id of the running instance
        _region -- AWS _region where instance is running
    """

    ec2instanceid = None

    _ec2r = None
    _cwc = None
    _s3c = None

    __S3__BUCKET__NAME = "<bucket-name_here>"
    __S3__BUCKET__PRFX = "cw/ec2alarmdefinitions.json"

    __ec2i = None

    __alarm_definitions = None

    _ec2iname = ''
    _region = ''

    def __init__(self, ec2instanceid:str, region:str):
        
        self.ec2instanceid = ec2instanceid
        self._region = region

        # initialize boto3 api
        self._ec2r = boto3.resource('ec2',self._region)
        if self._ec2r is None:
            raise EC2AlarmError(trigger=self, target=EC2AlarmErrorTargets.LOGANDPROPAGATE, \
                message=f'Unable to initialize boto3.resource(ec2,{self._region})', terminate=True)

        self.__ec2i = self._ec2r.Instance(self.ec2instanceid)
        if self.__ec2i is None:
            raise EC2AlarmError(trigger=self, target=EC2AlarmErrorTargets.LOGANDPROPAGATE, \
                message=f'Unable to find ec2 instance {self.ec2instanceid}', terminate=True)
        
        self._cwc = boto3.client('cloudwatch', self._region)
        if self._cwc is None:
            raise EC2AlarmError(trigger=self, target=EC2AlarmErrorTargets.LOGANDPROPAGATE, \
                message=f'Unable to initialize boto3.client(cloudwatch, {self._region})', terminate=True)

        #load desired alarms from s3 bucket
        self._s3c = boto3.client("s3")
        if self._s3c is None:
            raise EC2AlarmError(trigger=self, target=EC2AlarmErrorTargets.LOGANDPROPAGATE, \
                message=f'Unable to initialize boto3.client(s3)', terminate=True)

        s3_response = self._s3c.list_objects_v2(Bucket=self.__S3__BUCKET__NAME, Prefix=self.__S3__BUCKET__PRFX)
        s3_files = s3_response["Contents"]
        for s3_file in s3_files:
            file_content = \
                self._s3c.get_object(Bucket=self.__S3__BUCKET__NAME, Key=s3_file["Key"])["Body"].read()

        self.__alarm_definitions = json.loads(file_content)

        if self.__alarm_definitions is None:
            raise EC2AlarmError(trigger=self, target=EC2AlarmErrorTargets.LOGANDPROPAGATE, \
                message=f'Unable to load alarm definitions from s3 bucket', terminate=True)

    def _get_alarm_defintion(self, ad_name_prefix):
        """
        Helper function that returns defintion for alarm name from json objects loaded in memory

            ad_name_prefix: name of the alarm
        """
        alarm_def = None
        for ad in self.__alarm_definitions["Alarms"]:
            if ad_name_prefix == ad["Prefix"]:
                alarm_def = ad
                break
        return alarm_def

    def _set_ec2_instance_name(self):
        """
        Makes EC2 instance name available object wide.
        """
        self._ec2iname = self.ec2instanceid # defaults to instance id
        for t in self.__ec2i.tags:
            if t["Key"] == "Name":
                self._ec2iname = t["Value"]
                break

    def _get_desired_alarms(self):
        
        __ec2i_alarm_names_to_create = set()
        
        for a in self.__alarm_definitions["Alarms"]:
            if (a["Type"] == "Linux"):
                if self.__ec2i.platform_details is not None and re.search("windows", self.__ec2i.platform_details, re.IGNORECASE):
                    continue
            if (a["Type"] == "Windows"):
                if self.__ec2i.platform_details is not None and re.search("linux", self.__ec2i.platform_details, re.IGNORECASE):
                    continue
            __ec2i_alarm_names_to_create.add(self._ec2iname + "_" + a["Prefix"])
        
        return __ec2i_alarm_names_to_create

    def _create(self,ec2i_alarms_to_create: list):
        """
            Helper function that will create CW alarms in the given list for EC2 instance that
            triggered the event. One alarm is created at a time.

            ec2i_alarms_to_create: Alarm names to create 
        """
        cw_alarms_creation_failures = ()
        
        for ec2ia_name in ec2i_alarms_to_create:
            ad_name_prefix = ec2ia_name.replace(self._ec2iname + "_", '')
            alarm_def = self._get_alarm_defintion(ad_name_prefix)

            cw_alarm_creation_result = {}
            response = None
            try:
                response = self._cwc.put_metric_alarm(
                                AlarmName = ec2ia_name,
                                Namespace = "AWS/EC2",
                                MetricName = alarm_def["Condition"]["MetricName"],
                                ComparisonOperator = alarm_def["Condition"]["ComparisonOperator"],
                                Period = alarm_def["Condition"]["Period"],
                                EvaluationPeriods = alarm_def["Condition"]["EvaluationPeriods"],
                                Threshold = alarm_def["Condition"]["Threshold"],
                                AlarmDescription = "Alarm when server " + self._ec2iname + " " + alarm_def["Description"] + ".",
                                Dimensions = [{"Name": "InstanceId", "Value": self.ec2instanceid }],
                                AlarmActions = alarm_def["AlarmActions"],
                                Statistic = alarm_def["Condition"]["Statistic"]
                            )
                cw_alarm_creation_result = {"AlarmName": ec2ia_name, "HttpResponse": response}
            except:
                cw_alarm_creation_result = {"AlarmName": ec2ia_name, "HttpResponse": response}
            finally:
                if response is None or response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                    cw_alarms_creation_failures = cw_alarms_creation_failures + cw_alarm_creation_result

            if len(cw_alarms_creation_failures) > 0:
                for acf in cw_alarms_creation_failures: # raise non-terminating errors 
                   raise EC2AlarmError(trigger=self, target=EC2AlarmErrorTargets.LOGANDPROPAGATE, \
                        message=\
                            f'Failed to create alarm {acf["AlarmName"]}.{os.linesep}Response:{os.linesep}{acf["HttpResponse"]}')  
    
    def _remove(self,ec2i_alarms_to_remove: list):
        """
            Helper function that will remove CW alarms in the given list for EC2 instance that
            triggered the event. Either all alarms are removed or none.

            ec2i_alarms_to_remove: Alarm names to create 
        """
        response = None
        try:
            response = self._cwc.delete_alarms(AlarmNames=ec2i_alarms_to_remove)
        except:
            raise EC2AlarmError(trigger=self, target=EC2AlarmErrorTargets.LOGANDPROPAGATE, \
                        message=\
                            f'Failed to remove alarms {ec2i_alarms_to_remove}.{os.linesep}Response:{os.linesep}{response["ResponseMetadata"]}',\
                                terminate=True)
        if response is None or response["ResponseMetadata"]["HTTPStatusCode"] != 200:
             raise EC2AlarmError(trigger=self, target=EC2AlarmErrorTargets.LOGANDPROPAGATE, \
                        message=\
                            f'Failed to remove alarms {ec2i_alarms_to_remove}.{os.linesep}Response:{os.linesep}{response["ResponseMetadata"]}',\
                                terminate=True)  

    def _get_bad_alarms(self, ec2i_common_alarm_names_to_fix: set, cw_ec2i_configured_alarms):

        _ec2i_bad_alarm_names_to_fix = set()

        for cwa_name in ec2i_common_alarm_names_to_fix:
            ad_name_prefix = cwa_name.replace(self._ec2iname + "_", '')
            alarm_def = self._get_alarm_defintion(ad_name_prefix)

            #find cw alarm
            cw_alarm = None
            for cwa in cw_ec2i_configured_alarms["MetricAlarms"]:
                if cwa_name ==  cwa["AlarmName"]:
                    cw_alarm = cwa
                    break
            #now compare cw alarm settings to alarm definitions to find misconfigured alarms
            if alarm_def is not None and cw_alarm is not None:
                if not (
                    cw_alarm["Namespace"] == self.__alarm_definitions["Namespace"] and \
                    cw_alarm["ComparisonOperator"] == alarm_def["Condition"]["ComparisonOperator"] and \
                    cw_alarm["MetricName"] == alarm_def["Condition"]["MetricName"] and \
                    cw_alarm["Threshold"] == alarm_def["Condition"]["Threshold"] and \
                    cw_alarm["AlarmActions"] == alarm_def["AlarmActions"] and \
                    cw_alarm["Period"] == alarm_def["Condition"]["Period"] and \
                    cw_alarm["EvaluationPeriods"] == alarm_def["Condition"]["EvaluationPeriods"] 
                ):
                    _ec2i_bad_alarm_names_to_fix.add(cwa_name)

        return _ec2i_bad_alarm_names_to_fix

    def _setup_alarms(self):
        """
            Main function that will fetch all current CW metric alarms from AWS for EC2 instance
            that triggered the event. It will then create any missing alarms and remove incorrect alarms.
        """
        self._set_ec2_instance_name()

        ec2i_alarm_names_to_create = self._get_desired_alarms()

        #current alarms
        cw_ec2i_configured_alarms = self._cwc.describe_alarms(AlarmNamePrefix=self._ec2iname,AlarmTypes=['MetricAlarm'])

        if cw_ec2i_configured_alarms["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise EC2AlarmError(trigger=self, target=EC2AlarmErrorTargets.LOGANDPROPAGATE, \
                message="AWS API error calling describe_alarms for EC2 instance (Name: " + self._ec2iname + \
                    ", Id: " + self.ec2instanceid + ")", terminate=True)

        ec2i_missing_alarm_names_to_create = set()
        ec2i_common_alarm_names_to_fix = set()
        ec2i_bad_alarm_names_to_delete = set()
        ec2i_bad_alarm_names_to_fix = set()

        if cw_ec2i_configured_alarms is None or \
            (type(cw_ec2i_configured_alarms["MetricAlarms"]) is list and \
                len(cw_ec2i_configured_alarms["MetricAlarms"]) == 0):
            ec2i_missing_alarm_names_to_create = ec2i_alarm_names_to_create
        else:
            #extract alarm names from CW alarms
            cw_ec2i_configured_alarm_names = set() 
            for a in cw_ec2i_configured_alarms["MetricAlarms"]:
                cw_ec2i_configured_alarm_names.add(a["AlarmName"])
            
            #check alarms to be created, deleted or fixed
            ec2i_missing_alarm_names_to_create = ec2i_alarm_names_to_create - cw_ec2i_configured_alarm_names
            ec2i_bad_alarm_names_to_delete = cw_ec2i_configured_alarm_names - ec2i_alarm_names_to_create
            
            ec2i_common_alarm_names_to_fix = ec2i_alarm_names_to_create & cw_ec2i_configured_alarm_names
            if len(ec2i_common_alarm_names_to_fix) > 0:
                ec2i_bad_alarm_names_to_fix = self._get_bad_alarms(ec2i_common_alarm_names_to_fix,cw_ec2i_configured_alarms)
                
        # setup alarms as necessary
        if len(ec2i_bad_alarm_names_to_delete) > 0:
            self._remove(list(ec2i_bad_alarm_names_to_delete))

        if len(ec2i_missing_alarm_names_to_create) > 0:
            self._create(list(ec2i_missing_alarm_names_to_create))
        
        if len(ec2i_bad_alarm_names_to_fix) > 0:
            remove_result = self._remove(list(ec2i_bad_alarm_names_to_fix))
            if (remove_result[1] == None):
                self._create(list(ec2i_bad_alarm_names_to_fix))