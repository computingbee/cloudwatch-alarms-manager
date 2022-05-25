### CloudWatch EC2 Alarms Module

*This module is used to setup CW alarms for EC2 instnaces.
Following CW alarms are created for a given instance. The 
alarm is only created if one is not already present. Alarm
name is prefixed with EC2 name tag. if name tag is not present
or empty, instance id is used.*

[ec2alarmdefinitions.json](../data/ec2alarmsdefinitions.json) contains definitions of alarms listed below.

* **Instance**
1. EC2_StatusCheckFailed_System
      * Condition: StatusCheckFailed_System > 0 for 1 datapoints within 5 minutes
      * Action: SNS/CWNotifications
      * Example: XYZPBX01_EC2_StatusCheckFailed_System

2. EC2_StatusCheckFailed_Instance
    * Condition: StatusCheckFailed_Instance > 0 for 1 datapoints within 5 minutes
    * Action: SNS/CWNotifications
    * Example: XYZPBX01_EC2_StatusCheckFailed_Instance

3. EC2_StatusCheckFailed
    * Condition: StatusCheckFailed > 0 for 1 datapoints within 5 minutes
    * Action: SNS/CWNotifications
    * Example: XYZPBX01_EC2_StatusCheckFailed

* **CPU**
1. High_CPU_Utilization
    * Condition: CPUUtilization > 90 for 5 datapoints within 1 hour and 40 minutes
    * Action: SNS/CWNotifications
    * Example: XYZPBX01_Linux_High_CPU_Utilization, XYZWMGM01_Windows_High_CPU_Utilization 

* **Linux**
1. RootVol_SpaceUtilization
    * Condition: disk_used_percent > 95 for 1 datapoints within 5 minutes
    * Action: SNS/CWNotifications
    * Example: XYZPBX01_RootVol_SpaceUtilization

2. Linux_High_MemoryUsage
    * Condition: mem_used_percent > 90 for 5 datapoints within 1 hour and 40 minutes
    * Action: SNS/CWNotifications
    * Example: XYZPBX01_Linux_High_MemoryUsage

* **Windows**
1. Windows_LogicalFreeSpace_C
    * Condition: LogicalDisk % Free Space <= 10 for 1 datapoints within 5 minutes
    * Action: SNS/CWNotifications
    * Example: XYZWMGM01_Windows_LogicalFreeSpace_C

2. Windows_Memory_Committed_Bytes_Usage
    * Condition: Memory % Committed Bytes In Use > 90 for 1 datapoints within 5 minutes	
    * Action: SNS/CWNotifications
    * Example: XYZWMGM01_Windows_Memory_Committed_Bytes_Usage