
# -*- coding: utf-8 -*-


import logging
import ask_sdk_core.utils as ask_utils
import os
from ask_sdk_s3.adapter import S3Adapter
import requests
import boto3
from boto3.dynamodb.conditions import Key
import json
import datetime
import math
from ask_sdk_model.ui import AskForPermissionsConsentCard

s3_adapter = S3Adapter(bucket_name="my-alexa-bucket-test-aws")
client = boto3.resource('dynamodb')
table = client.Table("intern")

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

WHAT_CAN_I_DO         = ("You can ask me questions like What is my on-boarding status or if you have any other questions related to on-boarding. ")
WHAT_CAN_I_DO_REPOMPT = ("I can help you in assisting your on-boarding. You can ask me questions like, What is my onboarding status  ")
permissions = ["alexa::profile:email:read", "alexa::profile:given_name:read"]


ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])
                     
                             
def get_profile_details(access_token, apiName):
    #print access_token
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'content-type': 'application/json'
    };
    amazonProfileURL = 'https://api.amazonalexa.com/v2/accounts/~current/settings/Profile.'+apiName
    r = requests.get(url=amazonProfileURL, headers=headers)
    #print(r)
    if r.status_code == 200:
        return r.json()
    else:
        return False

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        #logger.info(handler_input.__dict__)
        req_envelope = handler_input.request_envelope
        response_builder = handler_input.response_builder
        if not (req_envelope.context.system.user.permissions and req_envelope.context.system.user.permissions.consent_token):
            response_builder.speak("Please enable email and name permissions in the Amazon Alexa app.")
            response_builder.set_card(AskForPermissionsConsentCard(permissions=permissions))
            return response_builder.response
        
        access_token = handler_input.request_envelope.context.system.api_access_token
        email = get_profile_details(access_token, "email")
        
        logger.info(email)
        givenName = get_profile_details(access_token, "givenName")
        
        logger.info(givenName)
        if not email or not givenName:
            handler_input.response_builder.speak("I am unable to retrieve your detials. Please give permission to access your name and email-id")
        else:
            
            attributes_manager = handler_input.attributes_manager
            user_attributes = {
                "name": givenName,
                "email": email
            }

            attributes_manager.persistent_attributes = user_attributes
            attributes_manager.save_persistent_attributes()
            
            
            joiningDate = "2020-08-02"
            joiningDate_obj = datetime.datetime.strptime(joiningDate, '%Y-%m-%d')
            
            
            backgrounfCheckDate_obj = joiningDate_obj - datetime.timedelta(60)
            bankAndSSN_obj = joiningDate_obj - datetime.timedelta(30)
            relocationDate_obj = joiningDate_obj - datetime.timedelta(14)
            
            
            backgroundCheckDocsDeadline      = backgrounfCheckDate_obj.strftime('%Y-%m-%d')
            bankAndSSNInfoSubmissionDeadline = bankAndSSN_obj.strftime('%Y-%m-%d')
            relocationInfoDeadLine            = relocationDate_obj.strftime('%Y-%m-%d')
            
            # Add item to db
            table.put_item(Item= {
                'email':                             email,
                'name':                              givenName,
                'recruiterName':                     "John",
                'joiningDate':                       joiningDate,
                'backgroundCheckDocsSubmitted':      False,
                'backgroundVerificationApproval':    False,
                'backgroundCheckDocsDeadline':       backgroundCheckDocsDeadline,
                'bankAndSSNInfoSubmitted':           False,
                'bankAndSSNInfoSubmissionDeadline':  bankAndSSNInfoSubmissionDeadline,
                'relocationInfoSubmitted':           False,
                'relocationInfoDeadLine':            relocationInfoDeadLine
            })
            
        speak_output = "Welcome to onboarding buddy. " + "I am here to help you with your pre-on-boarding process with Amazon. " + WHAT_CAN_I_DO
        reprompt_text = WHAT_CAN_I_DO
                
            
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )
        

class backGroundCheckHandler(AbstractRequestHandler):
    """Handler for launch after they have set their birthday"""

    def can_handle(self, handler_input):
        # extract persistent attributes and check if they are all present
        attr = handler_input.attributes_manager.persistent_attributes
        attributes_are_present = ("name" in attr and "email" in attr )
        return attributes_are_present and ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        name = attr['name']
        email = attr['email']
        
        fullResponse = table.get_item(Key={"email": email})['Item']
        # logger.info(fullResponse)
        # logger.info(type(fullResponse))
        
        speak_output = "Welcome back " + fullResponse['name']  +" ."+ WHAT_CAN_I_DO
        #logger.info("Status "+ str(fullResponse['backgroundCheckDocsSubmitted']))
        reprompt_text = WHAT_CAN_I_DO_REPOMPT
        # handler_input.response_builder.speak(speak_output)
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

        
class OnBoardingStatusIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("OnBoardingStatusIntent")(handler_input)

    def handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        name = attr['name']
        email = attr['email']
        
        fullResponse = table.get_item(Key={"email": email})['Item']
        
        
        if fullResponse['relocationInfoSubmitted'] == True:
            relocationInfoSubmissionDeadline_dateObj = datetime.datetime.strptime(fullResponse['relocationInfoDeadLine'], '%Y-%m-%d')
            relocationInfoDeadlineDate = ordinal(int(relocationInfoSubmissionDeadline_dateObj.strftime("%d")))
            relocationInfoDeadlineMonth = relocationInfoSubmissionDeadline_dateObj.strftime("%B")
            
            speak_output = "You are all set to go. Looking forward to meet you on day 1!"
            reprompt = "Is there anything else I can help you with?"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt)
                    .response
            )
        elif fullResponse['backgroundCheckDocsSubmitted'] == False:
            backgroundCheckDocsDeadline_dateObj = datetime.datetime.strptime(fullResponse['backgroundCheckDocsDeadline'], '%Y-%m-%d')
            backgroundCheckDocsDeadlineDate = ordinal(int(backgroundCheckDocsDeadline_dateObj.strftime("%d")))
            backgroundCheckDocsDeadlineDateMonth = backgroundCheckDocsDeadline_dateObj.strftime("%B")
            speak_output = "Please Submit  your background check documents by "+  backgroundCheckDocsDeadlineDateMonth + " "+ backgroundCheckDocsDeadlineDate
            reprompt = "Thanks for submitting your background check documents, there is approval pending from Amazon's side."
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt)
                    .response
            )
            
        elif fullResponse['backgroundCheckDocsSubmitted'] == True and  fullResponse['backgroundVerificationApproval'] == False:
            speak_output = "You have submitted your background check documents, there is approval pending from Amazon's side."
            reprompt = "Thanks for letting me know. You can ask me the updated status  "
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt)
                    .response
            )
        elif fullResponse['backgroundVerificationApproval'] == True and  fullResponse['bankAndSSNInfoSubmitted'] == False:
            bankAndSSNInfoSubmissionDeadline_dateObj = datetime.datetime.strptime(fullResponse['bankAndSSNInfoSubmissionDeadline'], '%Y-%m-%d')
            bankAndSSNDeadlineDate = ordinal(int(bankAndSSNInfoSubmissionDeadline_dateObj.strftime("%d")))
            bankAndSSNDeadlineMonth = bankAndSSNInfoSubmissionDeadline_dateObj.strftime("%B")
            
            speak_output = "Your background check verification was approved. Please submit  your bank and SSN info in the portal by "+ bankAndSSNDeadlineMonth  + " "+ bankAndSSNDeadlineDate 
            reprompt = "Thanks for letting me know. You can ask me the updated status."
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt)
                    .response
            )
        elif fullResponse['bankAndSSNInfoSubmitted'] == True and  fullResponse['relocationInfoSubmitted'] == False:
            relocationInfoSubmissionDeadline_dateObj = datetime.datetime.strptime(fullResponse['relocationInfoDeadLine'], '%Y-%m-%d')
            relocationInfoDeadlineDate = ordinal(int(relocationInfoSubmissionDeadline_dateObj.strftime("%d")))
            relocationInfoDeadlineMonth = relocationInfoSubmissionDeadline_dateObj.strftime("%B")
            
            speak_output = "Your bank and SSN info have been received. Please submit your relocation information in the portal by "+  relocationInfoDeadlineMonth + " "+ relocationInfoDeadlineDate 
            reprompt = "Thanks for letting me know. You can ask me the updated status  "
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt)
                    .response
            )
        elif fullResponse['relocationInfoSubmitted'] == True:
            relocationInfoSubmissionDeadline_dateObj = datetime.datetime.strptime(fullResponse['relocationInfoDeadLine'], '%Y-%m-%d')
            relocationInfoDeadlineDate = ordinal(int(relocationInfoSubmissionDeadline_dateObj.strftime("%d")))
            relocationInfoDeadlineMonth = relocationInfoSubmissionDeadline_dateObj.strftime("%B")
            
            speak_output = "Thanks for updating your relocation Information. You are all set to go. Looking forward to meet you on day 1!"
            reprompt = "Is there anything else I can help you with?"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt)
                    .response
            )
        else:
            speak_output = "oops noo"
            reprompt = "oops no"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(reprompt)
                    .response
            )
            

class BackgroundInfoSubmittedIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("BackgroundInfoSubmittedIntent")(handler_input)

    def handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        name = attr['name']
        email = attr['email']
        
        fullResponse = table.get_item(Key={"email": email})['Item']
        fullResponse['backgroundCheckDocsSubmitted'] = True
        
        table.put_item(Item= {
                'email':                             fullResponse['email'],
                'name':                              fullResponse['name'],
                'recruiterName':                     fullResponse['recruiterName'],
                'joiningDate':                       fullResponse['joiningDate'],
                'backgroundCheckDocsSubmitted':      fullResponse['backgroundCheckDocsSubmitted'],
                'backgroundVerificationApproval':    fullResponse['backgroundVerificationApproval'],
                'backgroundCheckDocsDeadline':       fullResponse['backgroundCheckDocsDeadline'],
                'bankAndSSNInfoSubmitted':           fullResponse['bankAndSSNInfoSubmitted'],
                'bankAndSSNInfoSubmissionDeadline':  fullResponse['bankAndSSNInfoSubmissionDeadline'],
                'relocationInfoSubmitted':           fullResponse['relocationInfoSubmitted'],
                'relocationInfoDeadLine':            fullResponse['relocationInfoDeadLine'],
            })
        # logger.info("updated background check")

        speak_output = "I have updated your background check information,, there is approval pending from Amazon's side."
    
        reprompt = "Is there anything else I can help you with?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )


class BackgroundInfoApprovedIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("BackgroundInfoApprovedIntent")(handler_input)

    def handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        name = attr['name']
        email = attr['email']
        
        fullResponse = table.get_item(Key={"email": email})['Item']
        fullResponse['backgroundVerificationApproval'] = True
        
        table.put_item(Item= {
                'email':                             fullResponse['email'],
                'name':                              fullResponse['name'],
                'recruiterName':                     fullResponse['recruiterName'],
                'joiningDate':                       fullResponse['joiningDate'],
                'backgroundCheckDocsSubmitted':      fullResponse['backgroundCheckDocsSubmitted'],
                'backgroundVerificationApproval':    fullResponse['backgroundVerificationApproval'],
                'backgroundCheckDocsDeadline':       fullResponse['backgroundCheckDocsDeadline'],
                'bankAndSSNInfoSubmitted':           fullResponse['bankAndSSNInfoSubmitted'],
                'bankAndSSNInfoSubmissionDeadline':  fullResponse['bankAndSSNInfoSubmissionDeadline'],
                'relocationInfoSubmitted':           fullResponse['relocationInfoSubmitted'],
                'relocationInfoDeadLine':            fullResponse['relocationInfoDeadLine'],
            })
        # logger.info("updated background check")

        bankAndSSNInfoSubmissionDeadline_dateObj = datetime.datetime.strptime(fullResponse['bankAndSSNInfoSubmissionDeadline'], '%Y-%m-%d')
        bankAndSSNDeadlineDate = ordinal(int(bankAndSSNInfoSubmissionDeadline_dateObj.strftime("%d")))
        bankAndSSNDeadlineMonth = bankAndSSNInfoSubmissionDeadline_dateObj.strftime("%B")
        
        speak_output = "Your background check verification was approved. Please submit  your bank and SSN info in the portal by "+  bankAndSSNDeadlineDate + " "+ bankAndSSNDeadlineMonth
        reprompt = "Thanks for letting me know. You can ask me the updated status  "
    
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )
            
class BankAndSSNInfoSubmittedIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("BankAndSSNInfoSubmittedIntent")(handler_input)

    def handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        name = attr['name']
        email = attr['email']
        
        fullResponse = table.get_item(Key={"email": email})['Item']
        fullResponse['bankAndSSNInfoSubmitted'] = True
        
        table.put_item(Item= {
                'email':                             fullResponse['email'],
                'name':                              fullResponse['name'],
                'recruiterName':                     fullResponse['recruiterName'],
                'joiningDate':                       fullResponse['joiningDate'],
                'backgroundCheckDocsSubmitted':      fullResponse['backgroundCheckDocsSubmitted'],
                'backgroundVerificationApproval':    fullResponse['backgroundVerificationApproval'],
                'backgroundCheckDocsDeadline':       fullResponse['backgroundCheckDocsDeadline'],
                'bankAndSSNInfoSubmitted':           fullResponse['bankAndSSNInfoSubmitted'],
                'bankAndSSNInfoSubmissionDeadline':  fullResponse['bankAndSSNInfoSubmissionDeadline'],
                'relocationInfoSubmitted':           fullResponse['relocationInfoSubmitted'],
                'relocationInfoDeadLine':            fullResponse['relocationInfoDeadLine'],
            })
        
        speak_output = "I have updated your status. Let me know, Is there is anything I can help you with?"
        reprompt = "Is there anything else I can help you with?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )
            

class RelocationInfoUpdateIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("RelocationInfoUpdateIntent")(handler_input)

    def handle(self, handler_input):
        attr = handler_input.attributes_manager.persistent_attributes
        name = attr['name']
        email = attr['email']
        
        fullResponse = table.get_item(Key={"email": email})['Item']
        fullResponse['relocationInfoSubmitted'] = True
        
        table.put_item(Item= {
                'email':                             fullResponse['email'],
                'name':                              fullResponse['name'],
                'recruiterName':                     fullResponse['recruiterName'],
                'joiningDate':                       fullResponse['joiningDate'],
                'backgroundCheckDocsSubmitted':      fullResponse['backgroundCheckDocsSubmitted'],
                'backgroundVerificationApproval':    fullResponse['backgroundVerificationApproval'],
                'backgroundCheckDocsDeadline':       fullResponse['backgroundCheckDocsDeadline'],
                'bankAndSSNInfoSubmitted':           fullResponse['bankAndSSNInfoSubmitted'],
                'bankAndSSNInfoSubmissionDeadline':  fullResponse['bankAndSSNInfoSubmissionDeadline'],
                'relocationInfoSubmitted':           fullResponse['relocationInfoSubmitted'],
                'relocationInfoDeadLine':            fullResponse['relocationInfoDeadLine'],
            })
        

        speak_output = "Thanks for updating your relocation Information. You are all set to go. Looking forward to meet you on day 1!"
        reprompt = "Is there anything else I can help you with?"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )
        


class RecruiterIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("RecruiterIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        month = str(slots["month"].value).lower()
        day = int(slots["day"].value)
        
        logger.info(day)
        dayString = "{0:0=2d}".format(day)
        
        # logger.info(month)
        # logger.info(day)
        
        month_dict ={}
        month_dict['january']       = '01'
        month_dict['february']      = '02'
        month_dict['march']         = '03'
        month_dict['april']         = '04'
        month_dict['may']           = '05'
        month_dict['june']          = '06'
        month_dict['july']          = '07'
        month_dict['august']        = '08'
        month_dict['septermber']    = '09'
        month_dict['october']       = '10'
        month_dict['november']      = '11'
        month_dict['december']      = '12'
        
        date = '2020-' + month_dict[month] +'-'+ dayString
        logger.info("date: "+date)
        
        resp = table.query(
        # Add the name of the index you want to use in your query.
            IndexName="joiningDate-index",
            KeyConditionExpression=Key('joiningDate').eq(date),
        )
        
        logger.info(resp)
        
        if not resp['Items']:
            speak_output = "There are no interns joining on " + month +" " +ordinal(int(day))
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .response
            )
          
        total_interns = len(resp['Items'])
        backgroundCheckCompleted = 0
        bankDetailsCompleted = 0
        relocationInfoCompleted = 0
        allSet = 0
              
        
        for item in resp['Items']:
            if item['backgroundCheckDocsSubmitted'] == True:
                backgroundCheckCompleted+=1
            if item['bankAndSSNInfoSubmitted'] == True:
                bankDetailsCompleted+=1
            if item['relocationInfoSubmitted'] == True:
                relocationInfoCompleted+=1
        
        logger.info(resp['Items'][0])
        recruiter_name = resp['Items'][0]['recruiterName']
        
        backgroundCheckCompletedPercentage = int(backgroundCheckCompleted * 100/total_interns)
        bankDetailsCompletedPercentage = int(bankDetailsCompleted * 100/total_interns)
        relocationInfoCompletedPercentage = int(relocationInfoCompleted * 100/total_interns)
        
        if backgroundCheckCompletedPercentage == 100:
            b = "All of them have completed their background check. "
        else:
             b = str(100 - backgroundCheckCompletedPercentage) +"% have their background check pending. "
             
        if bankDetailsCompletedPercentage == 100:
            ssn = "All of them have submiited their bank and SSN details. "
        else:
            ssn = str(100 - bankDetailsCompletedPercentage) +"% have to submit their bank and SSN details. "   

        if relocationInfoCompletedPercentage == 100:
            r = "All of them have submiited their relocation info. "
        else:
             r = str(relocationInfoCompletedPercentage) +"% are all set to join!"             
        
        
        
        if relocationInfoCompletedPercentage == 100:
            speak_output = "Hi " + recruiter_name +", There are a total of " +str(total_interns)+ " interns joining on " + month +" " +ordinal(int(day)) +". All of them are ALL SET TO JOIN!!!"
        else:
            speak_output = "Hi " + recruiter_name +", There are a total of " +str(total_interns)+ " interns joining on " + month +" " +ordinal(int(day)) +".  "+  b  + ssn +   r 
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )
        
class StartDateIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("StartDateIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "August second is your start date"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Is there anything else I can help you with?")
                .response
        )

        
class PrepareIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("PrepareIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "We encourage you to be familiar with the Leadership Principles, but there is no need to memorize them. All of what you will need to be successful in your role will be provided to you by your team and other internal resources. Just relax as much as you can and enjoy your time prior to starting!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )
        
class ChangeStartDateIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ChangeStartIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "To reduce potential issues with immigration and/or background checks, we recommend keeping your start dates as is; however, if there has been a change in your availability, please reach out to your recruiting team to request the change."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Is there anything else I can help you with?")
                .response
        )
        
        
class AmazonGearIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AmazonGearIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Yes! Each intern receives a credit to use in our Amazon gear store where you choose the Amazon gear you prefer – from hoodies and t-shirts to bags and water bottles."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Is there anything else I can help you with?")
                .response
        )
        
class MentorIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("MentorIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Yes. In addition to your manager, you will be assigned a mentor and an onboarding buddy, who you will meet during orientation."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Is there anything else I can help you with?")
                .response
        )
        
class InternEventIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("MentorIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Yes! We will host a variety of intern events. You will receive additional details about events once you start at Amazon."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Is there anything else I can help you with?")
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )
        

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = CustomSkillBuilder(persistence_adapter=s3_adapter)

sb.add_request_handler(backGroundCheckHandler())
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(OnBoardingStatusIntentHandler())
sb.add_request_handler(BackgroundInfoSubmittedIntentHandler())
sb.add_request_handler(BackgroundInfoApprovedIntentHandler())
sb.add_request_handler(BankAndSSNInfoSubmittedIntentHandler())
sb.add_request_handler(RelocationInfoUpdateIntentHandler())
sb.add_request_handler(RecruiterIntentHandler())

sb.add_request_handler(StartDateIntentHandler())
sb.add_request_handler(PrepareIntentHandler())
sb.add_request_handler(ChangeStartDateIntentHandler())
sb.add_request_handler(AmazonGearIntentHandler())
sb.add_request_handler(InternEventIntentHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()