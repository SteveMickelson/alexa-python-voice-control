# -*- coding: utf-8 -*-

import logging
import gettext
import requests  # To make HTTP requests
from pyngrok import ngrok  # Import ngrok
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractRequestInterceptor, AbstractExceptionHandler
import ask_sdk_core.utils as ask_utils
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from alexa import data

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Set ngrok authtoken for authentication
ngrok.set_auth_token("2orstFkoh7ZyLE6njr4pxdIv2DA_4spvTnfdEpXTCcJm7KpZn")  # Replace with your actual ngrok authtoken

# Start ngrok tunnel on port 5000 (assuming Flask or FastAPI is running there)
# You can change this port to match your local server port
public_url = ngrok.connect(5000).public_url
logger.info(f"Public ngrok URL: {public_url}")

# CommandIntentHandler that sends commands to the local server via the ngrok URL
class CommandIntentHandler(AbstractRequestHandler):
    """Handler for Command Intent to send commands to an external Python application and get a response."""

    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("CommandIntent")(handler_input)

    def handle(self, handler_input):
        # Get the command slot value from the user's input
        command = handler_input.request_envelope.request.intent.slots["command"].value
        logger.info(f"Received command: {command}")

        # Use the ngrok URL as the endpoint for the local server
        url = f"{public_url}/command"
        headers = {'Content-Type': 'application/json'}
        payload = {'command': command}

        try:
            # Send the POST request to the local server via ngrok
            response = requests.post(url, headers=headers, json=payload)

            # Check the response from the server
            if response.status_code == 200:
                # Assuming the server response contains a JSON object with a "response_text" field
                app_response_text = response.json().get("response_text", "Command completed successfully.")
                speak_output = app_response_text
            else:
                speak_output = "There was an error processing your command on the server."

        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to server: {e}")
            speak_output = "I'm sorry, I couldn't reach the server to process your command."

        # Respond to Alexa with the server's response
        return handler_input.response_builder.speak(speak_output).response


# Original Amazon Handlers (e.g., LaunchRequestHandler, HelpIntentHandler, etc.)
class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        _ = handler_input.attributes_manager.request_attributes["_"]
        speak_output = _(data.WELCOME_MESSAGE)

        return handler_input.response_builder.speak(speak_output).ask(speak_output).response


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        _ = handler_input.attributes_manager.request_attributes["_"]
        speak_output = _(data.HELLO_MSG)

        return handler_input.response_builder.speak(speak_output).response

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "You have reached Steve my master's HelpIntentHandler."
        return handler_input.response_builder.speak(speak_output).ask(speak_output).response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Handler for Cancel and Stop Intents."""
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = "Goodbye!"
        return handler_input.response_builder.speak(speak_output).set_should_end_session(True).response

class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "I'm sorry, I don't know how to help with that. Please try again."
        return handler_input.response_builder.speak(speak_output).ask(speak_output).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session Ended Request."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # Any cleanup logic goes here.
        logger.info("Session ended.")
        return handler_input.response_builder.response

class IntentReflectorHandler(AbstractRequestHandler):
    """Handler for reflecting the intent name back to the user. Useful for debugging."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = f"You just triggered {intent_name}."
        return handler_input.response_builder.speak(speak_output).response


# (Continue defining other handlers as in your original code...)

# Set up the SkillBuilder
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(CommandIntentHandler())  # Register the new CommandIntent handler
sb.add_request_handler(IntentReflectorHandler())  # Keep as the last handler
sb.add_global_request_interceptor(LocalizationInterceptor())
sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()
