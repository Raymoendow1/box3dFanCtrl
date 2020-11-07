# coding=utf-8
from __future__ import absolute_import
from os import error

from flask.templating import render_template_string
import octoprint.util
import octoprint.plugin
from octoprint.events import Events
from octoprint.server.util.flask import restricted_access
from flask import jsonify, request, make_response, Response, render_template
from subprocess import Popen, PIPE
import json
import requests
import sys
import glob
import os
import pigpio # GPIO control, make sure sudo pigpiod was called before
import math
import time

class Box3dfanctrlPlugin(octoprint.plugin.BlueprintPlugin,
						 octoprint.plugin.StartupPlugin,
						 octoprint.plugin.SettingsPlugin,
						 octoprint.plugin.AssetPlugin,
						 octoprint.plugin.TemplatePlugin,
						 octoprint.plugin.EventHandlerPlugin):

	pin = {"red":27, "green" :22, "blue":10, "lock":17, "lockStat":18,"ldr":13, "dir": 26 }
	pi = pigpio.pi()
	adc= None
	color = { "white":["red","green","blue"]}

	@staticmethod
	def to_int(value):
		try:
			val = int(value)
			return val
		except:
			return 0

	##~~ StartupPlugin mixin
	def on_after_startup(self):
		self._logger.info("box3d Industrial plugin is life.")
		# self.pi = pigpio.pi()
		self.init_temp()
		self.init_lock()
		self.init_lights()
		self.set_fanspeed(100)

	##~~ SettingsPlugin mixin
	def get_settings_defaults(self):
		return dict(
			slidVal=20, FanConfig=True, box3d_temp="25", box3d_tartemp="60"
			, fan_speed="100", fan_speed_min="5", fan_speed_max="900000" 		# temp crl vars
			, LightColorRed=False, LightColorGreen=False, LightColorBlue=False  # Light vars
			, fil_trsprt_s=True, fil_ldr_v="1000", fil_extr_v="50"
			, fil_dw="100", fil_noz="200"										# filament loader vars
			, UserNickName="box3d", UserPassword="Industrial", login=False		# log in
			
		)


################################## LOG-IN CTRL #######################################
	@octoprint.plugin.BlueprintPlugin.route("/login", methods=["POST"])
	def LogIn (self):
		self.login = True if request.values["login_state"] == 'true' else False
		self._logger.info("Log state: %s" % self.login)
		return jsonify(success=True)


########################## FAN AND TEMPERATURE CTRL ##################################

	def init_temp(self):
		baud = 2000000 # 2MHz SPI-clock, room between 4MHz or 1MHz
		spi_channel = 0x2
		spi_flags = 0x162
		self.adc = self.pi.spi_open(spi_channel, baud, spi_flags)

	def get_adc(self):
		(bytes, data) = self.pi.spi_read(self.adc, 2)
		
		# 2 bytes (16 bits) totall
		# 4 leading zeroes and 4 trailing zeroes
		adc_val = (data[0]<<4)|(data[1]>>4)
		return adc_val

	def calc_temp(self, adc_val):
		boefficient=3950
		seriesressistor=1000 	# 1kOhm
		thermistornominal=10000 # 10kOhm in 25C
		temperaturenominal=25
		adc_resolution= 8 		# in bits

		resis= seriesressistor * ((math.pow(2, adc_resolution)-1)/adc_val)
		temp = 1/(math.log(resis/thermistornominal)/boefficient+1.0/(temperaturenominal+273.15))-273.15
		temp = round(temp)
		return temp


	def get_temp(self):
		# # start with adc-reading
		adc_val = self.get_adc()
		# # calculate temperature
		temperature = self.calc_temp(adc_val)
		return temperature

	## weird flask things happening here
	# update the actual_temp value
	@octoprint.plugin.BlueprintPlugin.route("/getTemperature", methods=["GET"])
	def get_temperature(self):

		old_temp 	= self.to_int(request.values["box3d_temp"])
		fanval 		= self.to_int(request.values["FanSpd"])
		auto_crl 	= True if request.values["FanCrl"] == 'true' else False
		target_temp = self.to_int(request.values["TargTemp"])
		fanSpeedMax = self._settings.get_int(["fan_speed_max"])
		fanSpeedMin = self._settings.get_int(["fan_speed_min"])

		# Measure de temperature with SPI
		actual_temp = self.get_temp() #old_temp # temp reading

		if (auto_crl is True):
			if (actual_temp > target_temp):
				# Stuur fans aan
				fanval = fanSpeedMax
			else:
				# Minimale waarde fans
				fanval = fanSpeedMin
		self.set_fanspeed(fanval)
		
		# self._logger.info("target_temp=%d | old_temp=%d | auto_crl=%d",target_temp, old_temp,auto_crl)
		self._plugin_manager.send_plugin_message(self._identifier, dict(comptemp=actual_temp, fan=fanval))
		return jsonify(success=True)

	# Is auto-temp control enabled?
	# Zo niet gebruik de ingestelde waarde 
	@octoprint.plugin.BlueprintPlugin.route('/setFAN', methods=["POST"])
	def set_fan (self):
		fanVal = self.to_int(request.values["FanSpd"])
		self._logger.info("Fanval = %d", fanVal)
		self.set_fanspeed(fanVal) # PWM control
		return jsonify(success=True)

	def set_fanspeed(self, pwm_val):
			# set pwm to pwm_val
			fanval=1000000-pwm_val
			self.pi.hardware_PWM(12, 25000, fanval)


##################################		LIGHT CTRL		#######################################

	def init_lights(self):
		for i in ( "red", "green", "blue"):
			self.pi.set_mode(self.pin[i], pigpio.OUTPUT)

	def set_blink(self, colors):
		for color in colors:
			self.pi.set_PWM_dutycycle(self.pin[color], 128)
			self.pi.set_PWM_frequency(self.pin[color], 5)
	
	def clr_blink(self, colors):
		for color in colors:
			self.pi.set_PWM_dutycycle(self.pin[color], 0)
			self.pi.set_PWM_frequency(self.pin[color], 0)

	def set_lights(self, colors):
		for color in colors:
			if(color == "white"):
				self.pi.write(self.pin["red"], 1)
				self.pi.write(self.pin["green"], 1)
				self.pi.write(self.pin["blue"], 1)
				break
			self.pi.write(self.pin[color], 1)

	def clr_lights(self, colors):
		for color in colors:
			self.pi.write(self.pin[color], 0)

	@octoprint.plugin.BlueprintPlugin.route('/KillBlink', methods=["POST"])
	def kill_blink(self):
		self.clr_blink(("red", "green", "blue"))
		return jsonify(success=True)
		
	## weird flask things happening here
	# get the new RGB-light value from the Tab-menu
	@octoprint.plugin.BlueprintPlugin.route("/toggleLight", methods=["POST"])
	def toggle_lights(self):
		color = request.values["color"]
		lightState = True if request.values["state"] == 'true' else False 
		if (lightState == True):
			self.set_lights([color])
		elif(lightState==False):
			self.clr_lights([color])
		return jsonify(success=True)

	def on_event(self, event, payload):
		if(event == Events.CONNECTING):
			self.set_blink(self.color["white"]) # White blinking
		elif(event == Events.CONNECTED): 
			self.set_lights(self.color["white"]) # White on
		elif(event == Events.DISCONNECTED):
			self.set_lights(["green"])# Green on
			self.clr_lights(["red", "blue"]) 
		# elif(event == (Events.PRINT_STARTED or Events.PRINT_RESUMED)):
		# 	self.set_lights(["red", "green", "blue"]) # White on
		elif(event == Events.UPLOAD):
			self.set_lights(["blue"]) # Blue on
			self.clr_lights(["red", "green"])
		elif(event == "PrinterStateChanged"):
			self._logger.info("Printer state changed to {}".format(payload['state_string']))
			# if (payload['state_string'] == "Operational"):
			# 	self.set_lights(self.color["white"])
			if(payload['state_string'] == "Printing"):
				self.clr_blink(self.color["white"]) 
				self.set_lights(self.color["white"]) 	  # white
			elif(payload['state_string'] == "Pausing"):
				self.set_lights(["red"])  				  # Red
				self.clr_lights(["green", "blue"]) 
			elif(payload['state_string'] == "Cancelling"):
				self.set_blink(["red"])  			# Red blinking
				self.clr_blink(["blue", "green"]) 


###################### 			LOCK CTRL				##################################

	def init_lock(self):
		self.pi.set_mode(self.pin["lock"], pigpio.OUTPUT)
		self.pi.write(self.pin["lock"], pigpio.LOW)
		self.pi.set_mode(self.pin["lockStat"], pigpio.INPUT)
		self.pi.write(self.pin["lockStat"], pigpio.HIGH)

	def set_unlock(self):
		self.pi.write(self.pin["lock"],pigpio.HIGH)
		time.sleep(1.5)
		self.pi.write(self.pin["lock"],pigpio.LOW)


	def set_lock(self):
		self.pi.write(self.pin["lock"],pigpio.LOW)

	@octoprint.plugin.BlueprintPlugin.route('/unlock', methods=["POST"])
	def unlock(self):
		temp = self.to_int(request.values["temperature"])
		self._logger.info("temp val(for lock)= %d" % temp)
		self.set_unlock()
		return jsonify(success=True)
		
	@octoprint.plugin.BlueprintPlugin.route('/lock', methods=["POST"])
	def lock(self):
		self.set_lock()
		return jsonify(success=True)


############## 					FILAMENT CTRL					 #########################
##
# Loading filament bestaat uit 2 componenten: 
# 	1. De filamentlader-stappenmotor
# 	2. De 3d printer-extruder
# INLADEN: De volgorde van inladen is eerst de filamentlader-stappenmotor te late draaien
# 	daarna de 3D printer-extruder stappenmotor
# UITLADEN: Eerst de extruder, daarna de filamentlader-stappenmotor
# NOTE: zorg dat users de aantal meters aanpasbaar kunnen maken, zodat het in een programma
# 	gestroomlijnt ingeladen kan worden
##
	@octoprint.plugin.BlueprintPlugin.route('/LoadFilament', methods=["POST"])
	def filament(self):
		if(not(self._printer.is_closed_or_error() or self._printer.is_ready())):
			return jsonify(succes=False)
		self._logger.info("Printer ready for filamentchange!")
		drv_wheel =self.to_int(self._settings.get(["fil_dw"]))
		fil_noz	  =self.to_int(self._settings.get(["fil_noz"]))
		dst_extr  =self.to_int(self._settings.get(["fil_extr_v"])) # distance between extruder-3d printer and hot-end
		dst_loader=self.to_int(self._settings.get(["fil_ldr_v"])) # distance between box3d filament input and extruder-3d printer
		dir = True if request.values["fil_transport_state"] == 'filament_load' else False # true= loading, false=unloading
		steps  = 200 # number of steps in the motor for full rotation
		rot_fr = 50 # frequency of rotation
		fil_feedRate = (drv_wheel*math.pi)/(steps/rot_fr) #200 steps, 50 Hz = 200/50 = 1x round in 4 sec
		sec = float(dst_loader/fil_feedRate)
		self._logger.info("Wait time calculated: {} s".format(sec))


		# Heat nozzel to desired temperature
		self.send_gcode_command("M104 S{}".format(fil_noz))
		# time.sleep(10)

		# Load filament
		if (dir==True): 
			self.pi.write(self.pin["dir"],pigpio.HIGH)
			self.pi.hardware_PWM(self.pin["ldr"], rot_fr, 500000) #50% Duty Cycle
			# wait for filament to reach the 3D-printer
			time.sleep(sec) 
			# Load filament in the printer
			# self.send_gcode_command("G1 E{} F500".format(dst_extr)) # gecommend
		
		# Unload filament 
		else: 
			# move printer-extruder out first
			# self.send_gcode_command("G1 E-{} F500".format(dst_extr)) #gecommend
			# then filament-steppermotor
			self.pi.hardware_PWM(self.pin["ldr"], rot_fr, 500000)
			time.sleep(sec+1) # system unloads longer to make sure everything is out

		# Maak volgorde afhankelijk van in- en uitladen
		# load_filament_loader(meters)
		# load_filament_extruder(meters) # <== dit is Gcode: G91 - G21 - G1 E-100 F1000 (zie to_do.klad)

		self.pi.hardware_PWM(self.pin["ldr"], 0, 0)
		self.pi.write(self.pin["dir"],pigpio.LOW)
		return jsonify(success=True) # Spin steppermotor
	

	def send_gcode_command(self, command):
			for line in command.split('\n'):
				if line:
					self._printer.commands(line.strip())
					self._logger.info("Sending GCODE command: %s", line.strip())
					time.sleep(0.2)

	def shell_command(self, command):
		# self._logger.info(command + " function activated")
		try:
			# stdout = (Popen(command, shell=True, stdout=PIPE).stdout).read()
			self._plugin_manager.send_plugin_message(self._identifier,
				dict(is_msg=True, msg="Shell script executed", msg_type="success")) #msg=stdout
		except Exception as ex:
			# self.log_error(ex)
			self._logger.info(ex)
			self._plugin_manager.send_plugin_message(self._identifier,
				dict(is_msg=True, msg="Could not execute shell script", msg_type="error"))


	def on_settings_save(self, data):
		# old_slidVal 		= self._settings.get_int	(['slidVal'])
		# Old saved value
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		# New saved value
		# new_slidVal 		= self._settings.get_int	(['slidVal'])
		login = self._settings.get_boolean	(['login'])
		self._logger.info("New login state: %s" % login)

	##~~ TemplatePlugin mixin
	def get_template_configs(self):
		return [
	   		dict(type="navbar", custom_bindings=False),
	   		dict(type="settings", custom_bindings=False)
	   		,dict(type="tab", custom_bindings=False)
		]


	##~~ AssetPlugin mixin
	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/box3dFanCtrl.js"],
			css=["css/box3dFanCtrl.css"],
			less=["less/box3dFanCtrl.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
		# for details.
		return dict(
			box3dFanCtrl=dict(
				displayName="box3d",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="Raymoendow1",
				repo="box3dFanCtrl",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/Raymoendow1/box3dFanCtrl/archive/{target_version}.zip"
			)
		)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "box3d"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
#__plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = Box3dfanctrlPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

