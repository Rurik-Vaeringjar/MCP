import os
from dotenv import load_dotenv

from datetime import datetime

load_dotenv()
LOG = os.getenv("LOG")

FTIME = "%Y/%m/%d %H:%M:%S  "

def iexists(t, i):
	try:
		t[i]
	except IndexError:
		return False
	return True

def overwrite(filename, value):
	with open(filename, 'w') as file:
		file.write(value)

def read(filename):
	with open(filename) as file:
		return file.read()

def log(entry):
	timestamp = datetime.now()
	timestampstr = timestamp.strftime(FTIME)
	log = timestampstr + entry
	with open(LOG, 'a') as file:
		file.write(log+"\n")
	print(log)

def log_nl():
	with open(LOG, 'a') as file:
		file.write("\n")

# Used to recursively add wiki hyperlinks to an embed in discord
def add_links(msg, url):
	first_part = msg.partition('[')
	second_part = first_part[2].partition(']')
	
	link = capitalize_words(second_part[0])
	link = link.replace(" ", "_")

	link = f"({url}{link})"

	ass = second_part[2]
	if "[" in ass and "]" in ass:
		ass = add_links(ass, url)
	
	return first_part[0]+first_part[1]+second_part[0]+second_part[1]+link+ass

def concat(args, sep=" "):
	return sep.join(args)

def capitalize_words(str_:str):
	words = str_.split(" ")
	restr = ""
	for word in words:
		word = word.capitalize()
		restr += f"{word} "
	restr = restr[0:len(restr)-1]

	return restr

#There is absolutely a better way to do this, change it
#It at least works as intended, slow as it is.
def get_time(time_left):
	time = datetime.now()
	hour = int(time.strftime("%H"))
	minute = int(time.strftime("%M"))
	second = int(time.strftime("%S"))
	
	tl_hour = 0
	if "h " in time_left:
		part = time_left.partition("h ")
		tl_hour = int(part[0])
		time_left = part[2]

	tl_min = 0
	if "m " in time_left:
		part = time_left.partition("m ")
		tl_min = int(part[0])
		time_left = part[2]

	tl_sec = int(time_left.partition("s")[0])

	hour = hour + tl_hour
	minute = minute + tl_min
	second = second + tl_sec
	if second > 59:
		minute += 1
	if minute > 59:
		minute -= 60
		hour += 1 
		if hour > 23:
			hour -= 24
	return f"{hour}:"+ ("0" if minute < 10 else "") + str(minute)

def format_time(time):
	part = time.partition('T')
	part = part[2].partition('.')
	proper_time = ""
	for i in range(len(part[0])-3):
		proper_time = proper_time + part[0][i]
	
	#Converting to EST
	part = proper_time.partition(':')
	hour = int(part[0])-4
	if hour < 0:
		hour = 24 + hour
	proper_time = str(hour)+part[1]+part[2]

	return proper_time

def get_time_left(time):
	nowtime = datetime.now()
	hour = int(nowtime.strftime("%H"))
	minute = int(nowtime.strftime("%M"))
	second = int(nowtime.strftime("%S"))
	
	part = time.partition(':')
	exp_hour = int(part[0])
	exp_minute = int(part[2])

	if second != 00:
		second = 60 - second
		minute += 1
	minute = exp_minute - minute
	if minute < 0:
		minute = 60 + minute
		hour += 1
	if hour <= exp_hour:
		hour = exp_hour - hour
	else:
		hour = exp_hour+24-hour
	
	time_left = ""
	if hour>0:
		time_left = time_left + f"{hour}h "
	if minute>0:
		time_left = time_left + f"{minute}m "
	time_left = time_left + f"{second}s"

	return time_left

def get_location(loc):
	part = loc.partition(" (")
	node = part[0]
	part = part[2].partition(")")
	planet = part[0]

	return [node, planet]