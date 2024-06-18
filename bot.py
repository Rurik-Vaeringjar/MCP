#bot.py
#269954014127325194
import os
from dotenv import load_dotenv

import setproctitle

import discord
from discord.ext import commands

from datetime import datetime, timezone, timedelta
import json
import random

from tools.useful_functions import log, log_nl

from warframe import WarframeCog
#from ffxiv import FFXIV
#from valheim import Valheim
from sp import Sp

setproctitle.setproctitle("Master Control Program")

load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD = os.getenv("GUILD")
FILENAME = os.getenv("FILENAME")

intents = discord.Intents.default()
intents.members = True
cmd = '.'
bot = commands.Bot(command_prefix=cmd, intents=intents)

startup = True

################################################################################################################### EVENTS
@bot.event
async def on_ready():
	global startup
	if startup:
		for guild in bot.guilds:
			if guild:
				log(f"SRV: {bot.user} has connected to {guild.name} (id: {guild.id})")
		startup = False

@bot.event
async def on_connect():
	if startup:
		log(f"NET: {bot.user} has connected to Discord")

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):
		return
	raise error

@bot.event
async def on_member_join(member):
	if member.guild.name == GUILD:

		role = discord.utils.get(member.guild.roles, name="Open Mic Knight")
		await member.add_roles(role)

		log(f"SRV: {member.name} joined {member.guild.name}. Automatically assigned {role}")
	else:
		log(f"SRV: {member.name} joined {member.guild.name}.")

# ----------------------------------------------------------------------------------------------------------------- ON_MESSAGE
@bot.event
async def on_message(message):
	#ignore bot's own messages
	if message.author == bot.user:
		return

	#delete = False

	msg = message.content
	
	if msg.startswith(f"{cmd}roll") or msg.startswith(f"{cmd}help") or msg.startswith(f"{cmd}datetime") or msg.startswith(f"{cmd}dt"):
		log(f"CMD: {message.author.name} called " + message.content)
	elif msg.startswith(cmd):
		log(f"CMD: {message.author.name} called " + message.content)
	#	delete = True
	
	#process all the bot and cog commands
	#needed because on_message() was overwritten
	await bot.process_commands(message)

	#Adds the secret toggle command to the help file when certain users call help
	if msg == f"{cmd}help" and (message.author.id == 160515564308135937 or message.author.id == 269954014127325194):
		await message.channel.send("```\nSecret:\n  toggle\tToggles name switching on and off\n  randsp\tChooses a random name and sets sp to it\n```", delete_after=3.0)
	
	#if delete:
	#	await message.delete()

################################################################################################################### COGS
bot.add_cog(Sp(bot))
bot.add_cog(WarframeCog(bot))
#bot.add_cog(FFXIV(bot))
#bot.add_cog(Valheim(bot))

################################################################################################################### COMMANDS
@bot.command(name='roll', help='Roll dice (ex: 5d4+5)')
async def roll_dice(ctx, arg="1d20"):
	arg = arg.lower()
	
	stat = False
	if arg == "stat":
		stat = True
		arg = "4d6"
		

	part = get_mod(arg)
	
	arg = part[0]
	
	try:
		mod = int(part[2]) if part[2] != "" else 0
	except ValueError:
		await ctx.send("You fucked up... try again.")
	else:
		addsub = 1 if part[1] == "+" else -1 if part[1] == "-" else 0
		
		try:
			dice = cut_into_ints(arg)
			total = mod * addsub
			
			dlist = []
			append = True
			if dice[0] > 1000:
				append = False
			for i in range(dice[0]):
				roll = random.randint(1, dice[1])
				if append:
					dlist.append(roll)
				total += roll
		except ValueError:
			await ctx.send("Enter an integer.")
		else:
			if stat:
				dlist.sort(reverse=True)
				total -= dlist[-1]
			send_str = f"You rolled {dice[0]}d{dice[1]}{part[1]}{part[2]}" + (f" {dlist}" if len(dlist) > 1 or addsub != 0 else "") + f", getting {total}."
			if len(send_str) < 2001:
				await ctx.send(send_str)
			else:
				await ctx.send(f"You rolled a shitload of dice, getting {total}.")

def get_mod(arg: str) -> tuple:
	if "+" in arg:
		return arg.partition("+")
	elif "-" in arg:
		return arg.partition("-")
	else:
		return (arg, "", "")

def cut_into_ints(arg: str) -> tuple:
	if "d" in arg:
		part = arg.partition("d")
		return (int(part[0] if (part[0] != "" and int(part[0]) < 628318531) else "1"), int(part[2]))
	else:
		return (1, int(arg))

@bot.command(name='test', hidden=True)
async def test_post(ctx):
	await ctx.send("Status: 200", delete_after=3.0)
	await ctx.message.delete()

#Chronomancy, the magic of time.
@bot.command(name='datetime', hidden=True)
async def date_and_time(ctx, *args):
	
	if "tznone" in args:
		dt = datetime.now(tz=None)
	else:
		dt = datetime.now(tz=timezone.utc)
	
	msg = dt

	if args:
		if "timeleft" in args:
			i = args.index("timeleft")
			msg = time_remaining(args[i+1])

		if "convert" in args:
			i = args.index("convert")
			dt = get_datetime(args[i+1])
			msg = dt

	await ctx.send(msg)

@bot.command(name='dt', hidden=True)
async def d_and_t(ctx, *args):
	await date_and_time(ctx, *args)

def time_remaining(timestr: str) -> str:
	expiry = get_datetime(timestr)
	now = datetime.now(tz=timezone.utc)
	delta = expiry - now
	return convert_time(delta.total_seconds())

def get_datetime(timestr: str):
	part = timestr.partition("-")
	year = int(part[0])
	part = part[2].partition("-")
	month = int(part[0])
	part = part[2].partition("T")
	day = int(part[0])
	part = part[2].partition(":")
	hour = int(part[0])
	part = part[2].partition(":")
	minute = int(part[0])
	part = part[2].partition(".")
	second = int(part[0])
	
	dt = datetime(	year=year,
					month=month,
					day=day,
					hour=hour,
					minute=minute,
					second=second,
					tzinfo=timezone.utc)
	return dt

def convert_time(seconds):
	hours = 0
	minutes = 0
	while seconds >= 3600:
		hours += 1
		seconds -= 3600
	while seconds >= 60:
		minutes +=1
		seconds -= 60

	timestr = ""
	if hours > 0:
		timestr = f"{hours}h "
	if minutes > 0:
		timestr += f"{minutes}m "
	timestr += f"{int(seconds)}s"
	
	return timestr

@bot.command(name='memberlist', hidden=True)
async def member_list(ctx):
	if ctx.author.id == 269954014127325194:
		i = 0
		async for member in ctx.guild.fetch_members(limit=None):
			i += 1
			print(f"name: {member.name}\t\t\tnick: {member.nick}\t\t\t(id: {member.id})")
		print(f"{i} total on {ctx.guild.name}")

bot.run(TOKEN)