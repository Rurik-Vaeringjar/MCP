import discord
from discord.ext import commands

from lib.pymuninn.pymuninn import *

from tools.useful_functions import concat, log

class Valheim(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None

	@commands.command(name='item', help="Stats about the specified item, only food right now")
	async def get_item(self, ctx, *args):
		arg="Carrot"
		if args:
			arg = concat(args)
		try:
			item = muninn.get_item_info(arg)
		except OdinError as e:
			log(f"ERR: Muninn API failure: {e}")
			await ctx.send(f"Muninn API failure: {e}", delete_after=10.0)
		else:
			description = f"*{item['description']}*"
			embed = discord.Embed(title=item['name'], description=description, url=item['wikiaUrl'])
			embed.set_thumbnail(url=item['wikiaThumbnail'])

			if item['type'] == 'food':
				duration = int(int(item['duration'])/60)
				healing = f"{item['healing']}/tick"
				embed.add_field(name="Health", value=item['health'], inline=True)
				embed.add_field(name="Stamina", value=item['stamina'], inline=True)
				embed.add_field(name="Duration", value=f"{duration}m", inline=True)
				embed.add_field(name="Healing", value=healing, inline=True)
				embed.add_field(name="Weight", value=item['weight'], inline=True)
				embed.add_field(name="Max Stack", value=item['stack'], inline=True)

			embed.add_field(name="_ _", value="_ _", inline=False)
			if 'craftable' in item.keys():
				source_str = f"{item['craftable']['source']}"
				if item['craftable']['lvl']:
					if item['craftable']['lvl'] > 1:
						source_str += f" (level {item['craftable']['lvl']})"
				mats_str = ""
				for mat in item['craftable']['mats']:
					mats_str += f"- *{mat['mat']} x{mat['qty']}*\n"
				
				embed.add_field(name=source_str, value=mats_str, inline=False)
			elif 'sources' in item.keys():
				source_str = ""
				for source in item['sources']:
					source_str += " - *"
					if source['source']:
						source_str += f"{source['source']}"
						if source['location']:
							source_str += " in the "
					if source['location']:
						source_str += f"{source['location']}"
					source_str += "*\n"
				embed.add_field(name="Sources", value=source_str, inline=False)
					
			await ctx.send(embed=embed, delete_after=60.0)

	@commands.command(name='items', hidden=True)
	async def get_items(self, ctx, *args):
		await self.get_item(ctx, *args)

	@commands.command(name='mob', hidden=True)
	async def get_creature(self, ctx, *args):
		arg="Boar"
		if args:
			arg = concat(args)
		try:
			mob = muninn.get_mob_info(arg)
		except OdinError as e:
			log(f"ERR: Muninn API failure: {e}")
			await ctx.send(f"Muninn API failure: {e}", delete_after=10.0)
		else:
			embed = discord.Embed(title=mob['name'], url=mob['wikiaUrl'])
			embed.set_thumbnail(url=mob['wikiaThumbnail'])
			
			#embed.add_field(name="STATS", value="_ _", inline=False)
			embed.add_field(name="Health", value=f"*{mob['health']}*", inline=True)
			embed.add_field(name="_ _", value="_ _", inline=False)


			embed.add_field(name="RESISTANCES ---", value="_ _", inline=False)
			if mob['resist']:
				resist = mob['resist'].replace(",", "\n")
				embed.add_field(name="Resistant", value=f"*{resist}*", inline=True)
			if mob['veryresist']:
				veryresist = mob['veryresist'].replace(",", "\n")
				embed.add_field(name="V.Resistant", value=f"*{veryresist}*", inline=True)
			if mob['immune']:
				immune = mob['immune'].replace(",", "\n")
				embed.add_field(name="Immune", value=f"*{immune}*", inline=True)
			if mob['weak']:
				weak = mob['weak'].replace(",", "\n")
				embed.add_field(name="Weak", value=f"*{weak}*", inline=True)
			if mob['veryweak']:
				veryweak = mob['veryweak'].replace(",", "\n")
				embed.add_field(name="V.Weak", value=f"*{veryweak}*", inline=True)
			
			if mob['stagger']:
				stagger = int(float(mob['stagger'])*100)
				if stagger < 100:
					name_str = "Stagger limit"
					value_str = f"{stagger}%"
				else:
					name_str = "Stagger"
					value_str = "immune"

			
			embed.add_field(name=name_str, value=f"*{value_str}*", inline=False)

			await ctx.send(embed=embed, delete_after=60.0)