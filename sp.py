#sp.py
import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

import mariadb

from random import randint, getrandbits

from tools.useful_functions import log, capitalize_words, concat
from tools.sp_functions import load_sp_toggle, save_sp_toggle, check_name

load_dotenv()
USER = os.getenv('USER')
PWD = os.getenv('PASSWORD')

################################################################################################################### FUNCTIONS
def get_connection():
	try:
		con = mariadb.connect(
			user=USER,
			password=PWD,
			host='localhost',
			port=3306,
			database='sp',
			autocommit=True)
	except mariadb.Error as e:
		log(f"ERR: Unable to connect to MariaDB: {e}")
		return None
	else:
		return con

def get_sp(cur) -> str:
	#get random number in range
	total = get_total(cur)-1
	randi = randint(0, total)

	#select nth row
	try:
		cur.execute("SELECT name FROM sp_list LIMIT ?,?", (randi,1))
	except mariadb.Error as e:
		log(f"ERR: Query failure: {e}")
		name = None
	else:
		name, = cur.fetchone()

	return name

def get_total(cur) -> int:
	try:
		cur.execute("SELECT COUNT(*) FROM sp_list")
	except mariadb.Error as e:
		log(f"ERR: Query failure: {e}")
		total = None
	else:
		total, = cur.fetchone()
	return total

def check_splist(cur, arg) -> bool:
	try:
		cur.execute("SELECT name FROM sp_list WHERE name=?", (arg,))
	except mariadb.Error as e:
		log(f"ERR: Query failure: {e}")
		return None
	else:
		if (arg,) in cur:
			return True
	return False

################################################################################################################### SP COG
class Sp(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None
		self.sp_toggle = load_sp_toggle()

	@commands.Cog.listener()
	async def on_message(self, message):
		if self.sp_toggle and message.author.id == 160515564308135937:
			trigger = bool(getrandbits(1))
			if trigger:
				con = get_connection()
				cur = con.cursor()
				nick = get_sp(cur)
				con.close()
				if nick != message.author.nick:
					await message.author.edit(nick=nick)
					log(f"UPD: Sp changed to {nick}.")

	@commands.command(name='randsp', hidden=True)
	async def rand_sp(self, ctx):
		if ctx.author.id == 160515564308135937 or ctx.author.id == 269954014127325194:
			con = get_connection()
			cur = con.cursor()
			nick = get_sp(cur)
			con.close()
		
			if nick:
				sp = ctx.guild.get_member(160515564308135937)
				
				if sp:
					await sp.edit(nick=nick)
					await ctx.send(f"Sp changed to {nick}", delete_after=3.0)
					log(f"UPD: Sp changed to {nick}.")
		else:
			await ctx.send("You don't have permission to do that", delete_after=3.0)


	@commands.command(name='toggle', hidden=True)
	async def toggle(self, ctx):
		if ctx.author.id == 160515564308135937 or ctx.author.id == 269954014127325194:
			
			self.sp_toggle = not self.sp_toggle
			save_sp_toggle(self.sp_toggle)
		
			log(f"UPD: Toggle set to {self.sp_toggle}")
			await ctx.send(f"toggle is now {self.sp_toggle}", delete_after=2.0)

	@commands.command(name='check', help="Checks the splist")
	async def check(self, ctx, *args):
		if not args:
			arg = "size"
		else:
			arg = concat(args)

		con = get_connection()
		cur = con.cursor()
		sp = False
		if arg == "size":
			total = get_total(cur)
			await ctx.send(f"{total} names in splist", delete_after=2.0)
		else:
			name = capitalize_words(arg)

			sp = check_splist(cur, name)
			await ctx.send(f"{name} **is** in splist" if sp else f"{name} **is not** in splist", delete_after=2.0)
		con.close()

	@commands.command(name='who', help="Find out who put a name in the sp list")
	async def who_done_it(self, ctx, *args):
		if not args:
			sp = ctx.guild.get_member(160515564308135937)
			if sp:
				nick = sp.nick
		else:
			arg = concat(args)
			nick = capitalize_words(arg)
		
		con = get_connection()
		cur = con.cursor()
		cur.execute("SELECT contributor FROM sp_list WHERE name=?", (nick,))
		contributor, = cur.fetchone()
		if not contributor:
			contributor = "An unknown contributor"
		con.close()
		await ctx.send(f"{contributor} put {nick} in the sp list.", delete_after=5.0)		

	@commands.command(name='add', help="Add another name to the pile")
	async def add(self, ctx, *args):
		if not args:
			await ctx.send("You've added nothing of value to the Sp list...", delete_after=3.0)
			return
		else:
			con = get_connection()
			cur = con.cursor()

			name = concat(args)
			name = capitalize_words(name)
			if check_name(name):
				if not check_splist(cur, name):
					try:
						cur.execute("INSERT INTO sp_list (name, contributor) VALUES (?, ?)", (name, ctx.message.author.name))
					except mariadb.Error as e:
						await ctx.send("Something went wrong while trying to save to the splist", delete_after=3.0)
						log(f"ERR: Query failure in Sp.add: {e}")
					else:
						log(f"UPD: {name} added to splist")
						await ctx.send(f"{name} successfully added to the splist", delete_after=3.0)
				else:
					await ctx.send(f"{name} is already in the splist", delete_after=2.0)
			else:
				await ctx.send(f"{name} is not valid", delete_after=2.0)
			
			con.close()