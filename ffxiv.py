#ffxiv.py
import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

import mariadb
import sys
import json

import time

from tools.useful_functions import log, overwrite, read, iexists

load_dotenv()
USER = os.getenv('USER')
PWD = os.getenv('PASSWORD')
ENTRYFEE = os.getenv('ENTRYFEE')
LOTTOTAX = os.getenv('LOTTOTAX')

################################################################################################################### FUNCTIONS
def get_eorzean_time():
	epoch = int(time.time())
	eo_seconds_total = int(epoch * 20.5714285714)
	eo_minutes_total = int(eo_seconds_total / 60)
	eo_hours_total = int(eo_minutes_total / 60)

	minute = eo_minutes_total % 60
	hour = eo_hours_total % 24
	return hour, minute	

def get_connection():
	try:
		con = mariadb.connect(
			user=USER,
			password=PWD,
			host='localhost',
			port=3306,
			database='ffxiv',
			autocommit=True)
	except mariadb.Error as e:
		log(f"ERR: Unable to connect to MariaDB: {e}")
		return None
	else:
		return con

################################################################################################################### FFXIV COG
class FFXIV(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

	# ------------------------------------------------------------------------------------------------------------- ETIME
	@commands.command(name='etime', hidden=True)
	async def eorzean_time(self, ctx):
		hour, minute = get_eorzean_time()

		await ctx.send(f"Current Eorzean time is {hour}:{str(minute).zfill(2)}?", delete_after=10.0)

	# ------------------------------------------------------------------------------------------------------------- OGNODES
	# DEPRECIATED
	@commands.command(name='ognodes', hidden=True)
	async def og_nodes(self, ctx, arg=None):
		con = get_connection()
		cur = con.cursor()
		if cur:
			cur.execute("SELECT name, time, end, zone, x, y, route, type FROM nodes_old")
			msg=""
			hour, minute = get_eorzean_time()
			for (name, time, end, zone, x, y, route, node_type) in cur:
				
				if (hour >= time and hour < end) and (not arg or arg==node_type):
					x = "?" if not x else x
					y = "?" if not y else y
					temp=f"{name} at {zone} ({x},{y}). Fastest teleport is from {route}.\n"
					if len(msg) + len(temp) > 2000:
						await ctx.send(msg)
						msg = ""
					msg+=temp
			await ctx.send(msg if msg else "No known nodes currently available")
		con.close()
	
	# ------------------------------------------------------------------------------------------------------------- NODES
	# Syntax for json object in database
	# {"name": "", "lvl": , "star": "", "per": , "gth": }
	@commands.command(name='nodes', help="This function doesn't...", hidden=True)
	async def current_nodes(self, ctx, arg=None):
		con = get_connection()
		cur = con.cursor()
		hour, minute = get_eorzean_time()
		try:	
			qry = "SELECT time, end, zone, x, y, route, type, "
			qry += "slot1, slot2, slot3, slot4, slot5, slot6, slot7, slot8 "
			qry += "FROM nodes WHERE (time<=?) AND (end>?)"
			data = (hour,hour)
			cur.execute(qry, data)
		except mariadb.Error as e:
			log(f"ERR: MariaDB Error: {e}")
			await ctx.send("Database error...", delete_after=5.0)
		else:
			msg=""
			for (time, end, zone, x, y, route, node_type,
				 slot1, slot2, slot3, slot4, slot5, slot6, slot7, slot8) in cur:
				slots = [slot1, slot2, slot3, slot4, slot5, slot6, slot7, slot8]
				x = "?" if not x else x
				y = "?" if not y else y
				temp=f"{zone} ({x},{y}). Fastest teleport is from {route}.\n"
				for i, slot in enumerate(slots):
					if slot:
						jslot = json.loads(slot)
						jslot['star'] = jslot['star'].replace("*", "\*") 
						temp+=f"- Slot {i+1}: {jslot['name']}\tlevel: {jslot['lvl']}{jslot['star']}\n"
				if len(msg) + len(temp) > 2000:
					await ctx.send(msg, delete_after=30.0)	
					msg = ""
				msg+=temp
			await ctx.send(msg if msg else "No known nodes currently available", delete_after=30.0)
		con.close()

	# ------------------------------------------------------------------------------------------------------------- LOTTERY
	@commands.command(name='lottery', help="", hidden=True)
	async def fc_lottery(self, ctx, *args):
		con = get_connection()
		cur = con.cursor()

		msg = ""
		if args:
			role = discord.utils.get(ctx.guild.roles, name="Consul")
			if role in ctx.author.roles:
				#SETFEE -------------------------------------------------------------------------------------------
				if args[0] == 'setfee':
					if iexists(args, 1): #if there is a second argument
						overwrite(ENTRYFEE, args[1])
						msg = "Setting entry fee to {:,} gil".format(int(args[1]))
					else:
						fee = int(read(ENTRYFEE))
						msg = "You did not specify a new entry fee, current entry fee is {:,} gil".format(int(args[1]))
				#SETTAX -------------------------------------------------------------------------------------------
				elif args[0] == 'settax':
					if iexists(args, 1): #if there is a second argument
						overwrite(LOTTOTAX, args[1])
						msg = f"Setting lotto tax to {args[1]}%"
					else:
						tax = read(LOTTOTAX)
						msg = f"You did not specify a new lottery tax, current lottery tax is {tax}%"
				#ADD ----------------------------------------------------------------------------------------------
				elif args[0] == 'add':
					if iexists(args, 1): #if there is a second argument (name)
						if iexists(args, 2): #if there is a third argument (tickets)
							new_tickets = int(args[2])
						else:
							new_tickets = 1
						try:
							qry = "INSERT INTO lottery_entrants (name, tickets) VALUES (?,?) "
							qry += "ON DUPLICATE KEY UPDATE tickets=tickets+?"
							data = (args[1], new_tickets, new_tickets)
							cur.execute(qry, data)
						except mariadb.Error as e:
							log(f"ERR: Query failure: {e}")
							msg = "Error occurred"
						else:
							msg = f"{args[1]}\'s +{new_tickets} ticket" 
							msg += "s " if new_tickets>1 else " "
							msg += "successfully added to lottery"
					else:
						msg = "You need to specify someone to add to the lottery"
				#REMOVE --------------------------------------------------------------------------------------------
				elif args[0] == 'rm':
					try:
						cur.execute("DELETE FROM lottery_entrants WHERE (name=?)", (args[1],))
					except mariadb.Error as e:
						log(f"ERR: Query failure: {e}")
						msg = f"Error occurred: {e}"
					else:
						msg = f"{args[1]} removed from lottery."
				#NUKE ----------------------------------------------------------------------------------------------
				elif args[0] == 'nuke':
					try:
						cur.execute("DELETE FROM lottery_entrants")
					except mariadb.Error as e:
						log(f"ERR: Query failure: {e}")
						msg = f"Error occurred: {e}"
					else:
						msg = f"Lottery deleted, all entrants removed from database"
				#CHOOSE --------------------------------------------------------------------------------------------
				#elif args[0] == 'choose':
				#	try:
				#		cur.execute()
			else:
				if (args[0] == 'setfee' or args[0] == 'add' or args[0] == 'nuke' or args[0] == 'rm'):
 					msg = f"You lack the requisite permissions to use the \'{args[0]}\' command"
			if args[0] == 'tax':
				tax = read(LOTTOTAX)
				msg = f"The current lottery tax is {tax}%"
		else:
			fee = int(read(ENTRYFEE))
			msg = "The current entry fee is {:,} gil per ticket".format(fee)

		await ctx.send(msg, delete_after=5.0)
		con.close()
	@commands.command(name='lotto', hidden=True)
	async def fc_lotto(self, ctx, *args):
		await self.fc_lottery(ctx, *args)

	@commands.command(name='count', hidden=True)
	async def count_nodes(self, ctx):
		con = get_connection()
		cur = con.cursor()
		try:
			cur.execute("SELECT COUNT(*) FROM nodes")
			#for each, in cur:
			#	num = each
			num, = cur.fetchone()
		except mariadb.Error as e:
			print(f"ERR: Query failure: {e}")
		else:
			await ctx.send(num, delete_after=5.0)
		con.close()	