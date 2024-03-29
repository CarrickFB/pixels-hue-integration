from flask import Flask, request
import requests
import json
import threading
import time
import logging
import random

app = Flask(__name__)

# The IP of your Hue Bridge. Can be found in the Hue 
# app by going to Settings > My Hue system > The more info Icon on your bridge
HUE_BRIDGE_IP = "<IP_ADDRESS>"

# Your HUE username. If this is the first time using the HUE API, you'll need to get a username
# from the CLIP API Tester by following the guide here: https://developers.meethue.com/develop/get-started-2/
HUE_USERNAME =  "<HUE_USERNAME>"

# Group name of the set of lights you want to affect. If you don't know your group names, Uncomment ln165 and the Call the endpoint.
# this will call print_all_group_names() and it should log out your available groups in the shell. As an example, I used "Living Room"
HUE_GROUP_NAME = "<HUE_GROUP_NAME>"

# How long you want the effect to last. It's not an exact science and will probably run for about 2 seconds longer, so bear
# That in mind
EFFECT_TIME = 5  


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Prints the names of all configured Philips hue groups on your Bridge
def print_all_group_names():
    try:
        # Get all groups
        groups_url = f"http://{HUE_BRIDGE_IP}/api/{HUE_USERNAME}/groups"
        groups_response = requests.get(groups_url)
        groups_response.raise_for_status()
        groups_data = groups_response.json()

        # Print out all group names
        logger.info("Available groups:")
        for id, group_info in groups_data.items():
            logger.info(f"Group ID: {id}, Name: {group_info['name']}")

    except Exception as e:
        logger.error("Error printing group names: %s", e)

# Gets the initial state of all lights in the defined group using the HUE api
def get_initial_lights_state(group_name):
    try:
        # Get all groups
        groups_url = f"http://{HUE_BRIDGE_IP}/api/{HUE_USERNAME}/groups"
        groups_response = requests.get(groups_url)
        groups_response.raise_for_status()
        groups_data = groups_response.json()

        # Find the group ID by group name
        group_id = None
        for id, group_info in groups_data.items():
            if group_info["name"] == group_name:
                group_id = id
                break

        if not group_id:
            logger.error("Group '%s' not found", group_name)
            return {}

        # Get lights in the group
        group_lights_url = f"http://{HUE_BRIDGE_IP}/api/{HUE_USERNAME}/groups/{group_id}"
        group_lights_response = requests.get(group_lights_url)
        group_lights_response.raise_for_status()
        group_lights_data = group_lights_response.json()

        initial_state = {}
        for light_id in group_lights_data["lights"]:
            # Get light state
            light_url = f"http://{HUE_BRIDGE_IP}/api/{HUE_USERNAME}/lights/{light_id}"
            light_response = requests.get(light_url)
            light_response.raise_for_status()
            light_info = light_response.json()

            light_state = light_info.get("state")
            if light_state:
                light_state["alert"] = "none"  # Set alert to none
                initial_state[light_id] = light_state

        return initial_state

    except Exception as e:
        logger.error("Error getting lights state: %s", e)
        return {}
    
# Restores the lights to their initial state before the effects were called using the HUE api
def restore_group_lights_state(group_name, initial_state):
    try:
        

        # Get the IDs of all lights in the group
        group_lights_url = f"http://{HUE_BRIDGE_IP}/api/{HUE_USERNAME}/groups/{group_name}"
        group_lights_response = requests.get(group_lights_url)
        group_lights_response.raise_for_status()
        group_lights_data = group_lights_response.json()

        group_light_ids = group_lights_data["lights"]

        # Set the initial state for all lights in the group
        for light_id in group_light_ids:
            set_hue_light_state(light_id, **initial_state.get(light_id, {}))

        logger.info("Lights in group '%s' restored to initial state", group_name)
        return True

    except Exception as e:
        logger.error("Error restoring lights in group '%s': %s", group_name, e)
        return False

# Sets the state of a single light using the HUE api
def set_hue_light_state(light, **kwargs):
    try:
        url = f"http://{HUE_BRIDGE_IP}/api/{HUE_USERNAME}/lights/{light}/state"
        requests.put(url, json=kwargs)
    except Exception as e:
        logger.error("Error setting light state: %s", e)

# Main webhook handler. This defines the actions when the webhook is hit and holds the conditional that determines which functions to call based
# On the dice result. It also has some logging
def handle_webhook(payload):
    try:
        logger.info("Handling webhook")
        data = json.loads(payload)
        logger.info(f"Received payload: {data}")
        face_value = data.get("faceValue")
        
        lights = get_initial_lights_state(HUE_GROUP_NAME)
        initial_state = get_initial_lights_state(HUE_GROUP_NAME)
        
        logger.info(f"Face value: {face_value}")

        if face_value == 20:
            logger.info("Natural 20!!!!")
            nat_20_rainbow_fade(lights)
        elif face_value == 1:
            logger.info("Natural 1...")
            nat_1_red_strobe(lights)

  
        else:
            logger.info("Invalid face value: %s", face_value)
 
        # Restore previous light states
        restore_group_lights_state(HUE_GROUP_NAME, initial_state)
    except Exception as e:
        logger.error("Error handling webhook: %s", e)
        
# Function takes in an array of lights and starts a unique thread for each calling fade_light_rainbow, allowing them
# to execute individually rather than as a part of the same loop
def nat_20_rainbow_fade(lights):
    try:
        logger.info("Fading rainbow lights")
        start_time = time.time()
        threads = []

        for light in lights:
            # Create a new thread for each light
            thread = threading.Thread(target=fade_light_rainbow, args=(light, start_time))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        logger.info("Rainbow fading complete")
    except Exception as e:
        logger.error("Error during rainbow fade effect: %s", e)

# Function for individual thread to control fade lighting. This contains the actual effects
def fade_light_rainbow(light, start_time):
    while time.time() - start_time < EFFECT_TIME:
        try:
            # Random hue value for random colors
            random_hue = random.randint(0, 65535)
            set_hue_light_state(light, hue=random_hue, bri=255, sat=254, transition_time=0.6)
            time.sleep(0.7)
        except Exception as e:
            logger.error("Error fading light: %s", e)

# The light effect for a NAT 1, It uses the HUE api to strobe flash your lights red for the duration of the EFFECT_TIME
# Alter this if you want to change the lighting effect
def nat_1_red_strobe(lights):
    try:
        logger.info("Flashing red strobe lights")
        logger.info("Lights variable in nat_1_red_strobe function: %s", lights)  # Print lights variable

        # Command to make lights flash red in a strobe effect
        for light in lights:
            set_hue_light_state(light, alert="lselect", hue=65535, sat=254, bri=254)
        time.sleep(EFFECT_TIME+2)


        logger.info("Red strobe effect complete")
    except Exception as e:
        logger.error("Error during red strobe effect: %s", e)
        
# The endpoint itself. This can now accept either a JSON payload or query parameters matching the format
# specified in the Pixels app.
@app.route("/critroll", methods=["POST"])
def webhook():
    try:
        payload = request.json
        if payload:
            # If JSON payload is present, process it
            threading.Thread(target=handle_webhook, args=(json.dumps(payload),)).start()
            logger.info("Webhook hit with JSON Payload: %s", payload)
            return "Webhook received", 200
        else:
            # If no JSON payload, extract query parameters
            pixelName = request.args.get("value1")
            actionValue = request.args.get("value2")
            faceValue = int(request.args.get("value3"))
            profileName = request.args.get("value4")

            # Create a dictionary containing the query parameters
            query_params = {
                "pixelName": pixelName,
                "actionValue": actionValue,
                "faceValue": faceValue,
                "profileName": profileName
            }

            # Use the values as needed
            threading.Thread(target=handle_webhook, args=(json.dumps(query_params),)).start()
            logger.info("Webhook hit with query parameters: value1=%s, value2=%s, value3=%s, value4=%s",
                        pixelName, actionValue, faceValue, profileName)
            return "Webhook received", 200
    except Exception as e:
        logger.error("Error processing webhook request: %s", e)
        return "Error processing webhook request", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
