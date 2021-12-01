#	NDI-Classify
#	A program for recognizing objects in NDI sources
#	Office Hours Global Community Project
#	Created and maintained by Andy Carluccio - Washington, D.C.
#	
#	This program loads tensorflow models (from sources such as Teachable Machine)
#	Then, it allows you to select a set of NDI Sources from your network
#	It then runs the model on those sources, scoring the classes
#	Finally, it reports the score of each class for each source via Open Sound Control (OSC)


#System Import, allow us to see NDI library path
import sys
sys.path.insert(0, './ndi')

#pyNDI Import
import finder
import receiver
import lib

#openCV Utils
import cv2
import imutils

#Machine Learning Libraries
from keras.models import load_model
from PIL import Image, ImageOps
import numpy as np

#Supress Tensorflow logging
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import tensorflow as tf
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

#OSC variables & libraries
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client 
from pythonosc import osc_bundle
from pythonosc import osc_bundle_builder

#Argument management
import argparse

#Greeting
print("Welcome to NDI-Classify")
print("Created by Andy Carluccio")
print("This program loads Tensorflow Models and runs them on NDI Sources")
print("The results are sent to OSC with the following schema:")
print("/ndiClassify/source/SOURCE_ID class_1_weight, class_2_weight, ...")
print("Where the SOURCE_ID identifies the NDI source and the weights are the confidence predictions")
print()

#Create NDI Finder Object and Source List
find = finder.create_ndi_finder()
NDIsources = find.get_sources()

# Load the model
model_name = "keras_model.h5"
#use_default_model = str(input("Use adjacent default model named keras_model.h5 (Windows Only)? [y/n] \n"))
#if(use_default_model == "n"):
#	model_name = str(input("Enter Model Full Path and Name"))
#	os.path.expanduser(model_name)

model_name = str(input("Drag model here and hit ENTER" + '\n'))
path = os.path.join(model_name)
fixed_path = (path.replace(os.sep, '/')).replace('"',"")
rel_path = os.path.relpath(fixed_path, start = os.curdir)
rel_path = rel_path.rstrip()
print("Attempting to load model from:")
print(rel_path)
print()

model = tf.keras.models.load_model(rel_path)
print("Success!")
print()

# Create the array of the right shape to feed into the keras model
# The 'length' or number of images you can put into the array is
# determined by the first position in the shape tuple, in this case 1.
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

#NDI Receivers
receivers = []

#OSC Setup
print("Would you like to [1] Input network parameters or [2] use default: 127.0.0.1:1234 (sending)")
	
send_ip = "127.0.0.1"
send_port = 1234

selection = int(input())
if(selection == 1):
	print("Input network parameters")
	send_ip = str(input("Send ip?: "))
	send_port = int(input("Send port?: "))
else:
	print("Using default network settings")

client = udp_client.SimpleUDPClient(send_ip,send_port)
sys.stdout.write("Opened Client on: ")
sys.stdout.write(send_ip)
sys.stdout.write(":")
sys.stdout.write(str(send_port))
sys.stdout.write('\n')

print()

# Connect to NDI Sources
if(len(NDIsources) > 0):
	print(str(len(NDIsources)) + " NDI Sources Detected...")

	#Print Each Source Name
	for x in range(len(NDIsources)):
		print(str(x) + ". "+NDIsources[x].name + " @ "+str(NDIsources[x].address))

	#Ask user which NDI sources they want to use	
	awaitUserInput = True;

	while(awaitUserInput):
		print("")
		try:
			selections = str(input("Please choose a NDI Source Numbers to connect to as a comma-separated list of values (example: 1,3,4,...): \n"))
			keys = selections.split(",")

			#Fill the array of receivers
			for key in keys:
				if(int(key) < len(NDIsources) and int(key) >= 0):
					awaitUserInput = False
					ndi_source = NDIsources[int(key)]
					receivers.append(receiver.create_receiver(ndi_source))
				else:
					print("Input Not A Number OR Number not in NDI Range. Please pick a number between 0 and "+ str(len(NDIsources)-1))		
		except:
			print("Input Not A Number OR Number not in NDI Range. Please pick a number between 0 and "+ str(len(NDIsources)-1))	
else:
	print("No NDI Sources Detected - Please Try Again")


print()
print("Running NDI-Classify...")

#Main Program Loop
while(1):
	k = 0

	#Loop over all receivers and classify them
	for rec in receivers:
		frame = rec.read()
		size = [str(frame.shape[0]),str(frame.shape[1]), frame.shape[2]]
		frame = imutils.resize(frame, width=500)
		
		#SHOW IMAGE
		#cv2.putText(frame, recieveSource.name,(0,15),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
		#cv2.putText(frame, "Size:"+ size[1] + "x" +size[0],(0,35),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
		#mode = ""
		#if(size[2] == 4):
		#	mode = "RGB Alpha"
		#if(size[2] == 3):
		#	mode = "RGB"	
		#cv2.putText(frame, "Mode:"+ mode,(0,55),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
	
		#cv2.imshow("image", frame)
		#k = cv2.waitKey(30) & 0xff
		#if k == 27:
		#	break

		#Convert from openCV to Pillow (PIL) Image
		img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		image = Image.fromarray(img)
	
		#resize the image to a 224x224 with the same strategy as in TM2:
		#resizing the image to be at least 224x224 and then cropping from the center
		size = (224, 224)
		image = ImageOps.fit(image, size, Image.ANTIALIAS)

		#turn the image into a numpy array
		image_array = np.asarray(image)

		# Normalize the image
		normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1

		# Load the image into the array
		data[0] = normalized_image_array

		# run the inference
		prediction = model.predict(data)

		#Send the model to OSC 
		osc_address = "/ndiClassify/source/"+str(k)
		bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
		msg = osc_message_builder.OscMessageBuilder(address=osc_address)

		for x in range (0,len(prediction[0])):
			msg.add_arg(float(prediction[0][x]))
			bundle.add_content(msg.build())

		bundle = bundle.build()
		client.send(bundle)

		#print(prediction)

		k+=1


print("User Quit")
cv2.destroyAllWindows()