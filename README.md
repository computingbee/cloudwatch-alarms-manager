# AWS CloudWatch Alarms Manager

Automates setting up and tearing down of CloudWatch metric alarms for EC2 
instances and S3 buckets.

  - Python 3.9
  - AWS Lambda
  - CloudWatch
  - CI/CD via GitHub Actions (appleboy/lambda-actions)
  
## Development & Deployment
The code is split into individual python modules for each AWS resource 
type, i.e. ec2alarms module for EC2. Alarm definitions are stored under 
[ec2alarmdefinitions.json](../data/ec2alarmsdefinitions.json) for unit 
testing and should be copied to respective s3 bucket that lambda function 
can access.
	
Each module has its own corresponding Lambda function handler. For example 
cw_ec2alarm_runner.py for EC2 alarms. Custom package manager lambda_packager.py 
is used for building zip file package for Lambda in the bin folder which is 
deployed using GitHub actions.

### Unit Testing
Unit tests are also divided into python modules and test modules are under tests
folder. Unit tests are designed to be run locally on your machine against a 
test AWS resource that is configured under an in an event such as 
test\<alarm-name>\data\ec2eventrunning.json. Tests are written using pytest
and unittest modules.

### Logging
Uses a custom error handler class to propgate messages to CloudWatch Logs for 
debugging.