"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
"""

from __future__ import print_function
import json
import urllib
import boto3
import os
from botocore.exceptions import ClientError


# --------------- Global Variables  ----------------------
DRYRUN = False
DEBUGGING = True
us_aws_regions = {'us-east-1', 'us-east-2','us-west-1', 'us-west-2'}


# --------------- Debugging ----------------------
# Logic: If DEBUGGING is True print
# Varialbles: Output Text
# Action: Print
# Returns: Null
# --------------------------------------------------
def debugging(output_text):
	if DEBUGGING:
		print(output_text)


# --------------- Helper Sart and stop intances ----------------------
# Logic: iterrates through regions and instances building a list per region
#				then shutting down or starting up based on action
# Varialbles: 
#						Action: can be Shutdown or Startup
# 					Instance_state: running or stopped (other types not as useful)
# Returns: Alexa card of how many instances have been actioned
# ----------------------------------------------------------------------

def start_stop_ec2_instances(action,instance_state):
	
	
	total_instances_actioned = 0
	
	debugging('Instance state is: ' + instance_state)
	for aws_region in us_aws_regions:
		debugging(aws_region)
		
		count_of_instances_to_action = 0		
		
		ec2 = boto3.client('ec2',region_name=aws_region)
		#Getting Running Instances Should also add a Tag Filter
		raw_response = ec2.describe_instances(
		Filters=[
			{'Name': 'instance-state-name', 'Values': [instance_state]},
			{'Name': 'tag-value' , 'Values': ['Frugal']}])
	
		reservations = raw_response['Reservations']
		#print(reservations)

		
		debugging("Lengthing of res: " + str(len(reservations)))
		for raw_instance in reservations:
			instances_to_action = []
			for instance in raw_instance['Instances']:
				debugging(instance['InstanceId'])
				instances_to_action.append(instance['InstanceId'])
				
				# Count of all instances that will be actioned
				count_of_instances_to_action = count_of_instances_to_action + 1 
				
			debugging(instances_to_action)
			debugging("Count of Instances to action: " + str(count_of_instances_to_action))
			
			try:
				if count_of_instances_to_action > 0 and action == 'shutdown':
					# ec2 = boto3.client('ec2', region_name=aws_region)
					debugging("Shutdown")
					total_instances_actioned = total_instances_actioned + count_of_instances_to_action
					response = ec2.stop_instances(InstanceIds=instances_to_action,DryRun=DRYRUN)
					debugging("Instances shutdown")
				elif count_of_instances_to_action > 0 and action == 'started':
					total_instances_actioned = total_instances_actioned + count_of_instances_to_action
					response = ec2.start_instances(InstanceIds=instances_to_action,DryRun=DRYRUN)
					debugging("Instances started")
				else:
					print("Nothing to do!")
			except ClientError as e:
				if DRYRUN and e.response['Error'].get('Code') == 'DryRunOperation':
					was_successful = True
				else:
					print(e)
	 
	debugging("Instances to action: " + str(count_of_instances_to_action))
	
	
	## Determining if there are instances
	## For now I am not using this function because I am testing
	## Need to update code for production
	
	session_attributes = {}
	card_title = "Instances Actioned"
	speech_output = "I have " + action + " " + str(total_instances_actioned) + " instances."
	# If the user either does not reply to the welcome message or says something
	# that is not understood, they will be prompted again with this text.
	reprompt_text = "Please tell me whether, " \
									"You want to shutdown my instances, " \
									"or, You want to startup my instances."
	should_end_session = True
	return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, should_end_session))


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
	return {
		'outputSpeech': {
			'type': 'PlainText',
			'text': output
			},
			'card': {
				'type': 'Simple',
				'title': "SessionSpeechlet - " + title,
				'content': "SessionSpeechlet - " + output
				},
				'reprompt': {
					'outputSpeech': {
						'type': 'PlainText',
						'text': reprompt_text
						}
						},
						'shouldEndSession': should_end_session
						}


def build_response(session_attributes, speechlet_response):
	return {
		'version': '1.0',
		'sessionAttributes': session_attributes,
		'response': speechlet_response
		}


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
	""" If we wanted to initialize the session to have some attributes we could
		add those here
	"""

	session_attributes = {}
	card_title = "Welcome"
	speech_output = "Welcome to Frugal. " \
									"Please tell me whether, " \
									"You want to shutdown my instances, " \
									"or, You want to startup my instances."
	# If the user either does not reply to the welcome message or says something
	# that is not understood, they will be prompted again with this text.
	reprompt_text = "Please tell me whether, " \
									"You want to shutdown my instances, " \
									"or, You want to startup my instances."
	should_end_session = False
	return build_response(session_attributes, build_speechlet_response(
		card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
	card_title = "Session Ended"
	speech_output = "Thank you for saving money with Frugal"
	# Setting this to true ends the session and exits the skill.
	should_end_session = True
	return build_response({}, build_speechlet_response(
		card_title, speech_output, None, should_end_session))



# --------------- Events ------------------

def on_session_started(session_started_request, session):
	""" Called when the session starts """

	print("on_session_started requestId=" + session_started_request['requestId']
		+ ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
	""" Called when the user launches the skill without specifying what they
	want
	"""

	print("on_launch requestId=" + launch_request['requestId'] +
		", sessionId=" + session['sessionId'])
	# Dispatch to your skill's launch
	return get_welcome_response()


def on_intent(intent_request, session):
	""" Called when the user specifies an intent for this skill """

	print("on_intent requestId=" + intent_request['requestId'] +
		", sessionId=" + session['sessionId'])

	intent = intent_request['intent']
	intent_name = intent_request['intent']['name']

	# Dispatch to your skill's intent handlers
	if intent_name == "ShutdownIntent":
		print("Shutdown")
		return start_stop_ec2_instances("shutdown",'running')
	elif intent_name == "StartupIntent":
		print("Sartup")
		return start_stop_ec2_instances('started','stopped')
	elif intent_name == "AMAZON.HelpIntent":
		return get_welcome_response()
	elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
		return handle_session_end_request()
	else:
		raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
	""" Called when the user ends the session.
	Is not called when the skill returns should_end_session=true
	"""
	print("on_session_ended requestId=" + session_ended_request['requestId'] +
		", sessionId=" + session['sessionId'])
	# add cleanup logic here


# --------------- Main handler ------------------


def lambda_handler(event, context):
	""" Route the incoming request based on type (LaunchRequest, IntentRequest,
	etc.) The JSON body of the request is provided in the event parameter.
	"""
	print("event.session.application.applicationId=" +
		event['session']['application']['applicationId'])

	"""
	Uncomment this if statement and populate with your skill's application ID to
	prevent someone else from configuring a skill that sends requests to this
	function.	
	"""
	# if (event['session']['application']['applicationId'] !=
	#         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
	#     raise ValueError("Invalid Application ID")

	if event['session']['new']:
		on_session_started({'requestId': event['request']['requestId']},
				event['session'])

	if event['request']['type'] == "LaunchRequest":
		return on_launch(event['request'], event['session'])
	elif event['request']['type'] == "IntentRequest":
		print("intent")    
		return on_intent(event['request'], event['session'])
	elif event['request']['type'] == "SessionEndedRequest":
		return on_session_ended(event['request'], event['session'])
		
