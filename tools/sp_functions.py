#sp_functions.py

import os
from dotenv import load_dotenv 

import random

load_dotenv()
SPLIST = os.getenv("SPLIST")
SPTOGGLE = os.getenv("SPTOGGLE")


def load_sp_toggle():
	with open(SPTOGGLE) as file:
		flag = file.read()
		return True if flag == "True" else False

def save_sp_toggle(toggle):
	with open(SPTOGGLE, 'w') as file:
		file.write(str(toggle))

def get_sp():
	with open(SPLIST) as file:
		splist = [line.rstrip('\n') for line in file]
	ri = random.randint(0, len(splist)-1)
	return splist[ri]

def add_sp(arg):
	with open(SPLIST, 'a') as file:
		file.write(arg)

def check_name(arg):
	names = arg.split(" ")
	if len(names) != 2:
		return False
	else:
		if names[0].startswith("S") and names[1].startswith("P"):
			return True
	return False

def check_splist(arg):
	with open(SPLIST) as file:
		splist = [line.rstrip('\n') for line in file]
	if arg in splist:
		return True
	return False

def get_size_splist():
	with open(SPLIST) as file:
		num = 0
		for line in file:
			num += 1
	return num
