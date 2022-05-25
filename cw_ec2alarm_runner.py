import logging
import os
import json
from ec2alarms import EC2Alarm, EC2AlarmError

def cw_ec2alarm_handler(event, context):

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    if event is not None and event["source"] == "aws.ec2" and event["detail"]["state"] == "running" and \
        event["detail"]["instance-id"] is not None and event["region"] is not None:
        try:
            logger.info("Setting up CW alarms for EC2 instance " + event["detail"]["instance-id"] + "in region " + event["region"])
            ec2a = EC2Alarm(event["detail"]["instance-id"], event["region"])
            ec2a._setup_alarms()
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": 
                    json.dumps({
                        "message": "CW EC2 metric alarms created for instance " + event["detail"]["instance-id"],
                        "region":  os.environ["AWS_REGION"]
                    })
            }
        except EC2AlarmError:
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": 
                    json.dumps({
                        "message": "Error creating CW EC2 metric alarms created for instance " + event["detail"]["instance-id"],
                        "region":  os.environ["AWS_REGION"]
                    })
            }
    else:
        logger.setLevel(logging.ERROR)
        logger.error("CW event is missing EC2 instance id or region")
        return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": 
                    json.dumps({
                        "message": "Incorrect event info",
                        "region":  os.environ["AWS_REGION"]
                    })
            }