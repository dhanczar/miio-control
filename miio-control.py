from miio import device
import json 
import os
import argparse
import time
import configparser

#https://gemfury.com/aroundthecode/python:python-miio/-/content/yeelight.py
#https://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf

device_data = None
global_file_db = os.getcwd() + "\\" + 'devices.ini' 
global_result = None
global_action_exists = -1

def getDeviceData(device_id):
    config = configparser.ConfigParser()
    abspath = os.path.abspath(__file__)
    dir = os.path.dirname(abspath)  
    config.read(global_file_db)
    device_data = None #dict() 
    if device_id in config:
        values = config[device_id]
        if "active" in values and values["active"] == "1":
            device_data = dict()
            device_data["device_id"] = device_id
            device_data["device_ip"] = values["ip"]
            device_data["device_token"] = values["token"]

    if device_data == None:
        result_out = dict()
        result_out["cmd"] = "device"
        result_out["errno"] = "4"
        result_out["error"] = "No device "+device_id+" found, file " + global_file_db        
        global global_result, global_action_exists
        global_action_exists = 2
        global_result = result_out

    return device_data
    
def genResult(cmd, result_in):
    result_out = dict()
    result_out["cmd"] = cmd
    result_out["errno"] = "1"  
    result_out["data"] = result_in # ['ok']
    if result_in[0] == 'ok':
        result_out["errno"] = "0"      
    print(json.dumps(result_out))     


def deviceOn(device_data):
    dev = device.Device(device_data["device_ip"], device_data["device_token"])
    result_in = dev.raw_command("set_power", ["on"])

def deviceOff(device_data):
    dev = device.Device(device_data["device_ip"], device_data["device_token"])
    result_in = dev.raw_command("set_power", ["off"]) 

def deviceStatus(device_data):
    dev = device.Device(device_data["device_ip"], device_data["device_token"])
    result_out = dict()
    result_out["cmd"] = "status"
    result_out["errno"] = "1"
    properties = [
        "power",
        "bright",
        "ct",
        "rgb",
        "hue",
        "sat",
        "color_mode",
        "name",
        "lan_ctrl",
        "save_state"
    ]    
    result_in = dev.send("get_prop", properties)
    result_out["errno"] = "0"
    result_out['data'] = dict()
    result_out['data']["power"] = result_in[0]
    result_out['data']["bright"] = result_in[1]
    result_out['data']["temperature"] = result_in[2]
    result_out['data']["rgb"] = result_in[3]
    result_out['data']["hue"] = result_in[4]
    result_out['data']["sat"] = result_in[5]
    result_out['data']["color_mode"] = result_in[6]
    result_out['data']["name"] = result_in[7]
    result_out['data']["lan_ctrl"] = result_in[8]
    result_out['data']["save_state"] = result_in[9]
    return result_out

def deviceTemperature(device_data, temp=None):
    if temp != None:
        dev = device.Device(device_data["device_ip"], device_data["device_token"])
        temp_value = temp
        if temp_value < 2500:
            temp_value = 2500
        if temp_value > 4800:
            temp_value = 4800      
        
        result_in = dev.raw_command("set_ct_abx", [temp_value])
        time.sleep(1.0) 

def deviceTemperatureP(device_data, temp=None):
    if temp != None:
        dev = device.Device(device_data["device_ip"], device_data["device_token"])
        temp_value = temp   
        if temp_value < -100:
            temp_value = -100
        if temp_value > 100:
            temp_value = 100                 
        result_in = dev.raw_command("adjust_ct", [temp_value, 250])
        time.sleep(1.0) 

def deviceBrightP(device_data, bright=None):

    if bright != None:

        info = deviceStatus(device_data)
        # set mimum adjust (default if new value < 0 => lamp turn off)
        current_value = int(info['data']['bright'])
        if bright < 0 and current_value + bright < 1:
            bright = 1 - current_value

        if bright != 0:
            dev = device.Device(device_data["device_ip"], device_data["device_token"])
            bright_value = bright
            if bright > 100:
                bright_value = 100
            if bright < -100:
                bright_value = -100      
                
            result_in = dev.raw_command("adjust_bright", [bright_value, 500])
            time.sleep(1.0)   

def deviceBright(device_data, bright=None):
    dev = device.Device(device_data["device_ip"], device_data["device_token"])
    
    if bright != None:
        bright_value = bright
        if bright > 100:
            bright_value = 100
        if bright < 1:
            bright_value = 1      
                  
        result_in = dev.raw_command("set_bright", [bright_value])
        time.sleep(1.0) 
  
# =====================================================================================

parser = argparse.ArgumentParser(description='miio-control')
parser.add_argument('DEVICE_ID', type=str, help='Device ID (configuration in file devices.ini)')
group = parser.add_mutually_exclusive_group(required=False)
group.add_argument('-o', '--on', action="store_true", help='Turn on Device ID') #required=True
group.add_argument('-x', '--off', action="store_true", help='Turn off Device ID') #required=True
parser.add_argument('-b', '--bright', type=int, metavar="1-100", help='Brightness')
parser.add_argument('-B', '--Bright', type=int, metavar="-100-100", help='Brightness by percent (set brightness to 1 if adjust is too low)')
parser.add_argument('-k', '--temperature', type=int, metavar="2500-4800", help='Temperature')
parser.add_argument('-K', '--Temperature', type=int, metavar="-100-100", help='Temperature by percent')
parser.add_argument('-s', '--status', action="store_true", help='Device Status')
parser.add_argument('-f', '--file', help='File for device list (Default: devices.ini)')
#parser.add_argument('-d', '--dev', type=int, metavar="1,2", help='Dev #')

args = parser.parse_args()


if args.file != None:
    global_file_db = args.file

if args.status == True:
    device_data = getDeviceData(args.DEVICE_ID)
    if device_data != None:
        global_action_exists = 1

try:
    if args.on == True:
        device_data = getDeviceData(args.DEVICE_ID)
        if device_data != None:            
            deviceOn(device_data)
            deviceBright(device_data, args.bright)   
            global_action_exists = 1         
except AttributeError:
    global_result = dict()
    global_result['errno'] = "4"
    global_result['error'] = "No device found"
    global_action_exists = 2
    pass

try:
    if args.off == True:
        device_data = getDeviceData(args.DEVICE_ID)
        if device_data != None:
            deviceBright(device_data, args.bright)
            deviceOff(device_data)         
            global_action_exists = 1  
except AttributeError:
    global_result = dict()
    global_result['errno'] = "4"
    global_result['error'] = "No device found"
    global_action_exists = 2
    pass

try:
    if args.bright != None and args.on == False and args.off == False:
        device_data = getDeviceData(args.DEVICE_ID)
        if device_data != None:
            deviceBright(device_data, args.bright)
            global_action_exists = 1
except AttributeError:
    global_result = dict()
    global_result['errno'] = "4"
    global_result['error'] = "No device found"
    global_action_exists = 2
    pass

try:
    if args.Bright != None and args.on == False and args.off == False:
        device_data = getDeviceData(args.DEVICE_ID)
        if device_data != None:
            deviceBrightP(device_data, args.Bright)
            global_action_exists = 1
except AttributeError:
    global_result = dict()
    global_result['errno'] = "4"
    global_result['error'] = "No device found"
    global_action_exists = 2
    pass

try:
    if args.temperature != None and args.on == False and args.off == False:
        device_data = getDeviceData(args.DEVICE_ID)
        if device_data != None:
            deviceTemperature(device_data, args.temperature)
            global_action_exists = 1
except AttributeError:
    global_result = dict()
    global_result['errno'] = "4"
    global_result['error'] = "No device found"
    global_action_exists = 2
    pass

try:
    if args.Temperature != None and args.on == False and args.off == False:
        device_data = getDeviceData(args.DEVICE_ID)
        if device_data != None:
            deviceTemperatureP(device_data, args.Temperature)
            global_action_exists = 1
except AttributeError:
    global_result = dict()
    global_result['errno'] = "4"
    global_result['error'] = "No device found"
    global_action_exists = 2
    pass

if global_action_exists == 1:
    result = deviceStatus(device_data)
    print(json.dumps(result))
elif global_action_exists == 2:   
    print(json.dumps(global_result))
    pass
else:
    print("Error")
