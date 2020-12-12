# Depth Capture Kit
The purpose of this document is to walk through what is included in the box and how to set everything up.

## Kit Contents
Ensure everything is accounted for before starting assembly
- Raspberry Pi 4 Computer
- Raspberry Pi 4 Case with 3.5in touch display
- Intel Realsense camera
- Type-c power supply for the Raspberry Pi 4
- Tripod
- Microphone
- MicroSD card

# Assembly
Follow the 3.5in screen/ case assembly instruction to put the raspberry pi 4 and the screen together. Make sure that there only 7 pins showing off of the raspberry pi to one side as shown in the diagrams.

Make sure to set up the intel realsense camera as well as the microphone with the mounting hardware provided.

# First time setup
- [] Once the case/touch screen is installed, install the microSD on bottom of the raspberry pi.
- [] Plug in ethernet (**strongly recommended**) if available
- [] Plug in the power cable
- [] Follow the prompts to set up wifi is the ethernet cable is not an option
- [] Connect to the raspberry pi to add a streamkey into the device

# Troubleshooting
The section below is for trouble shooting some common issues with the raspberry pi.

## Black screen
Ensure that the raspberry pi is getting power. This can be checked by the red led light near the type-c port. There will be a little cutout in the case to see the leds.

## Blank screen
Tap to ensure that the raspberry pi did not simply go to sleep

If the screen is still powered on, but is not asleep. It could be that the raspberry pi is powered off, but the screen is still on. Unplug the power from the raspberry pi and plug it back in, it should start right back up and have a display after a few mins.

## Wifi saying its not connected after already setting it up
This could be because the raspberry pi is too far away from the router. Meaning that it doesn't have a strong enough connection, if possible move the raspberry pi closer to the router or move the router closer to the raspberry pi.

## Connected to ethernet, but its still using wifi
This could be happening because the raspberry pi is using both and choosing to stream with the wifi. To delete the wifi information stored type this into the terminal:
```
sudo rm -rf /etc/NetworkManager/system-connections/*
```