"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import json
import urllib
import boto3
from botocore.exceptions import ClientError
# --------------- Helpers Sart and stop intances ----------------------

us_aws_regions = {'us-east-1', 'us-east-2','us-west-1', 'us-west-2'}
dryRun = False

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


def start_stop_ec2_instances(action,instance_state):
	total_instances_actioned = 0
	
	for aws_region in us_aws_regions:
		print(aws_region)
		
		instances_to_action = 0		
		
		ec2 = boto3.client('ec2',region_name=aws_region)
		#Getting Running Instances Should also add a Tag Filter
		raw_response = ec2.describe_instances(
		Filters=[
			{'Name': 'instance-state-name', 'Values': [instance_state]},
			{'Name': 'tag-value' , 'Values': ['Alexa']}])
	
		reservations = raw_response['Reservations']
		#print(raw_instances['Reservations'])

		
		print(len(reservations))
		for raw_instance in reservations:
			instances_to_stop = []
			for instance in raw_instance['Instances']:
				print(instance['InstanceId'])
				instances_to_stop.append(instance['InstanceId'])
				instances_to_action = instances_to_action + 1 
				total_instances_actioned = total_instances_actioned + 1
			
			print(instances_to_stop)
		
		print("Instances to action: " + str(instances_to_action))
	
	
		## Determining if there are instances to 
		if instances_to_action == 1000:
			ec2 = boto3.client('ec2', region_name=aws_region)
			response = ec2.stop_instances(InstanceIds=region_instances,DryRun=True)	
	
	
	print("Total Instances actioned: " + str(total_instances_actioned))

    session_attributes = {}
    card_title = "Action Taken"
    speech_output = "I have shutdown " + str(total_instances_actioned) + " instances."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me whether, " \
                    "You want to shutdown my instances, " \
                    "or, You want to startup my instances."
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


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


def create_favorite_color_attributes(favorite_color):
    return {"favoriteColor": favorite_color}


def set_color_in_session(intent, session):
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'Color' in intent['slots']:
        favorite_color = intent['slots']['Color']['value']
        session_attributes = create_favorite_color_attributes(favorite_color)
        speech_output = "I now know your favorite color is " + \
                        favorite_color + \
                        ". You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
        reprompt_text = "You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your favorite color is. " \
                        "You can tell me your favorite color by saying, " \
                        "my favorite color is red."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_color_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
        favorite_color = session['attributes']['favoriteColor']
        speech_output = "Your favorite color is " + favorite_color + \
                        ". Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "You can say, my favorite color is red."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


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
        return start_stop_ec2_regions("SINGLE")
    elif intent_name == "StartupIntent":
        print("Sartup")
        return start_stop_ec2_regions("DOUBLE")
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
