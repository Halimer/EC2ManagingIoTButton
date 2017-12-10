import boto3
import json
import boto3
from botocore.exceptions import ClientError

# AWS US Regions
us_aws_regions = {'us-east-1', 'us-east-2','us-west-1', 'us-west-2'}
dryRun = True
one_IOT_click_stop = False
two_IOT_click_start = True

def toggle_instances(ec2, instance_list, dry_run, current_status_name):
    was_successful = False
    try:
        if current_status_name == 'stopped':
            response = ec2.start_instances(InstanceIds=instance_list, DryRun=dry_run)
        else:
            if current_status_name == 'running':
                response = ec2.stop_instances(InstanceIds=instance_list, DryRun=dry_run)

    except ClientError as e:
        if dry_run and e.response['Error'].get('Code') == 'DryRunOperation':
            was_successful = True
        else:
            print(e)

    return was_successful


                
                
 def lambda_handler(event, context):
 	print(event)
 	print('Recieved EventType: ' + event['clickType'])
 	
 	click_type = event['clickType']
 	
 	for aws_region in us_aws_regions:
    print (aws_region)
    ec2 = boto3.client('ec2',region_name=aws_region)

    response = ec2.describe_instances(
    Filters=[
     #   {'Name': 'instance-state-name', 'Values': ['running']},
        {'Name': 'tag-value' , 'Values': ['Frugal']}])

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            key_name = instance['KeyName']
            status_code = instance['State']['Code']
            status_name = instance['State']['Name']
            availability_zone = instance['Placement']['AvailabilityZone']
            print('     {:30} {:10} {:3} {:15} '.format(instance_id, status_name, status_code, availability_zone))

            if (click_type == 'SINGLE'):
                response_value = toggle_instances(ec2, [instance_id], dryRun, status_name)
                print("     Shutting down Instances "+str(response_value))

            elif (click_type == 'DOUBLE'):
                response_value = toggle_instances(ec2, [instance_id], dryRun, status_name)
                print("     Starting up Instances "+str(response_value))
                
			else:
            	print("     Click type not set: " + click_type)