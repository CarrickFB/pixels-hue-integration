# Pixels Dice Philips HUE Webhook integration

### Intro ###

This little script uses a Flask server to create a webhook listener that you can hit with your pixels die, and will 
Send commands to your HUE bridge to play a lighting effect on a NAT 1 or NAT 20. It's a pet project
and I'm not a Python dev, so it's far from perfect! If my explanations of anything are incorrect please forgive me!

However feel free to take, edit and improve it as you wish so long as you continue
to share it with other users/devs. 

Hope you enjoy it! 
<3 -Carrick FB

### Tech Info and Setup ###

Requirements: 
- Python
- A Pixels Die (https://gamewithpixels.com/)
- Philips Hue Lighting (with access to the API)

The server will run on localhost of the device you run this script on through port 5000.
This will only run locally to your network, so all relevant devices will need to be connected to the same network and I'd caution against making
it public facing without incorporating some form of security.

NOTE: This will only work properly if the lights are ON! If they are off, the Nat 1 effect will strobe but won't turn them red and the other
won't do anything

### How to run ###

Ensure you have python installed, Open a shell and head to the directory where the script it located. Use the following command to run it:
```python3 run_pixels_hue_webhook_server.py```

In the pixels app, set the webhook target URL to be: ```http://<LOCAL_DEVICE_IP>:5000/critroll``` and ensure you are sending the payload as JSON by
toggling it in the webhook setting.

If you hit test, and everything's working correctly, You should start seeing logs come through to your shell. If your lights fail to change, but 
you're recieving logs, it may be you haven't configured your HUE IP or username correctly.
If you're failing to hit the endpoint, you may need to use port forwarding to open up the relevant port from your local device to other local devices
On your network. I used a rasberry pi hardwired to my router, so needed to do that. 

The lighting effects are sent in ```nat_20_rainbow_fade``` and ```nat_1_red_strobe```, and they are called via the webhook_handler conditional.
If you want to add or edit any effects, those are the places to look