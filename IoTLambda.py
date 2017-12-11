from __future__ import print_function

import json
import urllib
import boto3
from botocore.exceptions import ClientError
import os

# Include a TOPIC ARN in your environment variable for SNS
TOPIC = os.environ.get("TOPIC", None)
SUBJECT = os.environ.get("SUBJECT", None)

# AWS Regions excluding China and Gov
us_aws_regions = {'us-east-1', 'us-east-2','us-west-1', 'us-west-2'}
dryRun = False

# Single Click from IOT Button will shut down
# Double Click from IOT Button will start up

def toggle_instances(ec2, instance_list, dry_run, current_status_name,clickType):
    was_successful = False
    #print("In toggle instances")
    try:
        if (clickType == 'SINGLE'):
            if current_status_name == 'running':
                response = ec2.stop_instances(InstanceIds=instance_list, DryRun=dry_run)
                print("     Shutting down Instances "+str(response))
                return ("Shutting down instances")
                
        elif (clickType == 'DOUBLE'):
            if current_status_name == 'stopped':
                response = ec2.start_instances(InstanceIds=instance_list, DryRun=dry_run)
                print("     Startup up Instances "+str(response))    
                return ("Startup up instances")
        else:
            print(" Click type not defined: " + clickType)
            return("Not Defined") 

    except ClientError as e:
        if dry_run and e.response['Error'].get('Code') == 'DryRunOperation':
            was_successful = True
        else:
            print(e)
 
    return was_successful

def start_stop_ec2_regions(clickType):
    response_value = "none";
    instances = 0
    
    for aws_region in us_aws_regions:
        #print (aws_region)
        ec2 = boto3.client('ec2',region_name=aws_region)
    
        response = ec2.describe_instances(
            Filters=[ {'Name': 'tag-value' , 'Values': ['Frugal']}])
        
        instances = len(response['Reservations']) + instances
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                key_name = instance['KeyName']
                status_code = instance['State']['Code']
                status_name = instance['State']['Name']
                availability_zone = instance['Placement']['AvailabilityZone']
                print('     {:30} {:10} {:3} {:15} '.format(instance_id, status_name, status_code, availability_zone))
            
                response_value = toggle_instances(ec2, [instance_id], dryRun, status_name, clickType)

    return (instances)
    
def send_to_sns(topic,subject,body,responseRet):
    # Example:
    #   {
    #       "topic": "arn:aws:sns:REGION:123456789012:MySNSTopic",
    #       "subject": "This is the subject of the message.",
    #       "message": "This is the body of the message."
    #   }

    sns = boto3.client('sns')
    print ("in send_to_sns: "+topic+", subject: "+subject+", response: "+responseRet)
    sns.publish(
        TopicArn=topic,
        Subject=subject,
        Message=json.dumps(body, indent=2) +"\n\n "+responseRet
    )

    return ('Sent a message to an Amazon SNS topic.')

#
#The following JSON template shows what is sent as the payload:
#
#    "serialNumber": "GXXXXXXXXXXXXXXXXX",
#    "batteryVoltage": "xxmV",
#    "clickType": "SINGLE" | "DOUBLE" | "LONG"
#
# A "LONG" clickType is sent if the first press lasts longer than 1.5 seconds.
# "SINGLE" and "DOUBLE" clickType payloads are sent for short clicks.
#
# For more documentation, follow the link below.
# http://docs.aws.amazon.com/iot/latest/developerguide/iot-lambda-rule.html
# 
def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    numberOfInstances = start_stop_ec2_regions(event['clickType'])
    
    if (event['clickType'] == 'SINGLE'):
      body = str(numberOfInstances) + " instances have been shutdown."
    elif (event['clickType'] == 'DOUBLE'):
      body = str(numberOfInstances) + " instances have been started."
    else:
       body = "Long click not yet supported." 
    
    send_to_sns(TOPIC, SUBJECT, body, str(event))
    
    return 'Completed'
