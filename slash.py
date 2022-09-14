import os
from dotenv import load_dotenv

import discord
from discord import app_commands

import random

from tools.useful_functions import log
#import logging

load_dotenv()
TOKEN = os.getenv("TOKEN")
NIZARI = int(os.getenv("NIZARI"))
BASE = int(os.getenv("BASE"))
FILENAME = os.getenv("FILENAME")

#logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
#log = logging.getLogger(__name__)

guilds = [discord.Object(id=BASE), discord.Object(id=NIZARI)]

class MCPClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            for guild in guilds:
                await tree.sync(guild=guild)
            self.synced = True
        log(f"NET: Logged in as {self.user}")

client = MCPClient()
tree = app_commands.CommandTree(client)

@tree.command(name="test", description="Testing slash commands", guilds=guilds)
async def test(interaction: discord.Interaction):
	log(f"CMD: {interaction.user.name} used {interaction.command.name}.")
	await interaction.response.send_message(f"This slash command worked")

@tree.command(name='roll', description="Roll dice", guilds=guilds)
async def roll_dice(interaction: discord.Interaction, dice: str="1d20"):
	dice = dice.lower()
	
	log(f"CMD: {interaction.user.name} used {interaction.command.name} {dice}.")
	
	part = get_mod(dice)
	
	arg = part[0]

	try:
		mod = int(part[2]) if part[2] != "" else 0
	except ValueError:
		await interaction.response.send_message("You fucked up... try again.")
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
			await interaction.response.send_message("Enter an integer.")
		else:
			send_str = f"You rolled {dice[0]}d{dice[1]}{part[1]}{part[2]}" + (f" {dlist}" if len(dlist) > 1 or addsub != 0 else "") + f", getting {total}."
			if len(send_str) < 2001:
				await interaction.response.send_message(send_str)
			else:
				await interaction.response.send_message(f"You rolled a shitload of dice, getting {total}.")


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

client.run(TOKEN)