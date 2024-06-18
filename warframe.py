import discord
from discord.ext import commands

from lib.forklotus.forklotus import *

from tools.useful_functions import *

from pprint import pprint

################################################################################################################### FUNCTIONS
def completion_bar(percent: float) -> str:
	len_ = int(round(percent/5.0, 0))

	bar = ""
	for i in range(len_):
		bar += "▒" #"█"
	for i in range(20-len_):
		bar += "░"

	return bar

#def disposition_str(disposition: int) -> str:
#	str_ = ""
#	for i in range(1,6):
#		if i <= disposition:
#			str_ += "●"
#		else:
#			str_ += "○"
#	return str_

def wf_emoji(emoji: str=None) -> str:
	if emoji == "naramon":
		return "<:naramon:928445850437419139>"
	elif emoji == "vazarin":
		return "<:vazarin:928445875196399646>"
	elif emoji == "madurai":
		return "<:madurai:928445892405628988>"
	elif emoji == "mastery":
		return "<:mastery:928445904078393344>"
	elif emoji == "aura":
		return "<:aura:931064772831621122>"
	return "<:clem:931758276784316416>"

################################################################################################################### WARFRAME COG
class WarframeCog(commands.Cog, name='Warframe'):
	def __init__(self, bot):
		self.bot = bot
		self._last_member = None
		self.url = "https://warframe.fandom.com/wiki/"

	# ------------------------------------------------------------------------------------------------------------- ITEM LINKING
	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author == self.bot.user:
			return
		
		if (message.channel.name == "bot-spam" or message.channel.name == "warframe-general") and "[" in message.content and "]" in message.content:
			try:
				msg = add_links(message.content, self.url)
			except Exception:
				log("ERR: add_link failure")
				await message.channel.send("Something went very wrong with the embed, sorry", delete_after=5.0)
			else:	
				embed = discord.Embed(description=msg)
				name = message.author.nick if (message.author.nick != None) else message.author.name
				embed.set_author(name=name, icon_url=message.author.avatar_url)
				await message.delete()
				await message.channel.send(embed=embed)

	@commands.command(name='masterysymbol', hidden=True)
	async def mastery_symbol(self, ctx):
		msg = wf_emoji("mastery")
		await ctx.send(msg)

	# ============================================================================================================= WORLDSTATE COMMANDS
	# ------------------------------------------------------------------------------------------------------------- FISSURES
	@commands.command(name='fissures', help="Active fissures and void storms")
	async def show_fissures(self, ctx):
		try:
			pc_wf = wf_api('pc')
			fissures = Fissures(pc_wf.get_fissure_info())
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:	
			fissure_list = [[],[],[],[],[]]
			for fissure in fissures.list:
				fissure_list[fissure.tierNum-1].append(fissure)
	
			embeds = [	discord.Embed(title="Void Fissures", url=fissures.wikiaUrl),
			 			discord.Embed(title="Steelpath Fissures", url=fissures.wikiaUrl),
						discord.Embed(title="Void Storms", url=fissures.wikiaUrl)]
			#embeds[0].set_author(name="Void Fissures", icon_url="https://static.wikia.nocookie.net/warframe/images/5/57/VoidTearIcon_b.png")
			#embeds[1].set_author(name="Void Storms", icon_url="https://static.wikia.nocookie.net/warframe/images/5/57/VoidTearIcon_b.png")
			
			missions = [["", "", "", "", ""], ["", "", "", "", ""], ["", "", "", ""]]
			enemies = [["", "", "", "", ""], ["", "", "", "", ""], ["", "", "", ""]]
			eta = [["", "", "", "", ""], ["", "", "", "", ""], ["", "", "", ""]]
			locations = [["", "", "", "", ""], ["", "", "", "", ""], ["", "", "", ""]]

			for i, fissures in enumerate(fissure_list):
				for fissure in fissures:
					if not "-" in fissure.eta:
						index = 0
						if fissure.isHard:
							index = 1
						if fissure.isStorm:
							index = 2
						missions[index][i] += f"{fissure.enemy} {fissure.missionType}\n"
						eta[index][i] += f"{fissure.eta}\n"
						locations[index][i] += f"{fissure.location}\n"
				for j in range(3):
					if i == 4 and j == 1:
						break
					embeds[j].add_field(name=fissure_list[i][0].tier, value=missions[j][i], inline=True)
					embeds[j].add_field(name="_ _", value=locations[j][i], inline=True)
					embeds[j].add_field(name="_ _", value=eta[j][i], inline=True)

			await ctx.send(embed=embeds[0], delete_after=120.0)
			await ctx.send(embed=embeds[1], delete_after=120.0)
			await ctx.send(embed=embeds[2], delete_after=120.0)
		await ctx.message.delete()

	@commands.command(name='fissure', hidden=True)
	async def show_fissure(self, ctx):
		await self.show_fissures(ctx)

	

	# ------------------------------------------------------------------------------------------------------------- INVASIONS
	@commands.command(name='invasions', help="Active invasion progress")
	async def show_invasions(self, ctx):
		try: 
			pc_wf = wf_api('pc')
			invasions = Invasions(pc_wf.get_invasion_info())
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			#def sort_by_planet(inv):
			#	return inv.planet
			#def sort_by_vsInfestation(inv):
			#	return inv.vsInfestation

			#invasions.list.sort(key=sort_by_planet)
			#invasion_objects.sort(key=sort_by_vsInfestation)
			
			invasion_list = [[], []]
			for invasion in invasions.list:
				if invasion.vsInfestation:
					invasion_list[0].append(invasion)
				else:
					invasion_list[1].append(invasion)

			for invasions in invasion_list:
				msg = ""
				for invasion in invasions:
					if invasion.completion > 0 and invasion.completion < 100:
						msg += f"**{invasion.desc}** @ {invasion.location}\n"

						if not invasion.vsInfestation:
							reward = add_links(f"[{invasion.attackerReward.type}]", self.url)
							msg += f"{invasion.attackingFaction} giving {reward}"
							msg += (f" x{invasion.attackerReward.count}" if invasion.attackerReward.count > 1 else "") + " vs "

						reward = add_links(f"[{invasion.defenderReward.type}]", self.url)
						msg += f"{invasion.defendingFaction} giving {reward}"
						msg += f" x{invasion.defenderReward.count}" if invasion.defenderReward.count > 1 else ""
					
						msg += "\n" + completion_bar(invasion.completion) + " {:.1f}%\n\n".format(round(invasion.completion, 1))
					
				embed = discord.Embed(description=msg) #, color=discord.Color.from_rgb(180, 0, 180))
				await ctx.send(embed=embed, delete_after=60.0)
		await ctx.message.delete()
	
	@commands.command(name='invasion', hidden=True)
	async def show_invasion(self, ctx):
		await self.show_invasions(ctx)

	# ------------------------------------------------------------------------------------------------------------- SORTIE
	@commands.command(name='sortie', help="Sortie missions and mods")
	async def show_sortie(self, ctx):
		try:
			pc_wf = wf_api('pc')
			sortie = Sortie(pc_wf.get_sortie_info())
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			embed = discord.Embed(title=f"{sortie.boss}", url=sortie.wikiaUrl)
			embed.set_thumbnail(url=sortie.wikiaThumbnail)
			for variant in sortie.variants:
				embed.add_field(name=f"{variant.missionType} - {variant.mission}", value=variant.modifier, inline=False)
			embed.set_footer(text=f"{sortie.eta} remaining", icon_url="https://cdn.discordapp.com/emojis/931758276784316416.png")
			await ctx.send(embed=embed, delete_after=30.0)
		await ctx.message.delete()
	
	# ------------------------------------------------------------------------------------------------------------- CETUS
	@commands.command(name="cetus", help="Day/night cycle")
	async def cetus_cycle(self, ctx):
		try:
			pc_wf = wf_api('pc')
			cetus = CetusInfo(pc_wf.get_cetus_info())
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			approx_time = get_time(cetus.timeLeft)

			msg = "```" + ("fix" if cetus.isDay else "ini") + "\n[It is " + ("Day" if cetus.isDay else "Night") + f" on Cetus for another {cetus.timeLeft}]\n```"
			msg += "```" + ("ini" if cetus.isDay else "css") +"\n[It will be " + ("Night" if cetus.isDay else "Day") + f" at approximately {approx_time}]\n```"
			embed = discord.Embed(description=msg, title="Plains of Eidolon", url=cetus.wikiaUrl)
			await ctx.send(embed=embed, delete_after=30.0)
		await ctx.message.delete()

	# ------------------------------------------------------------------------------------------------------------- VALLIS
	@commands.command(name='vallis', help="Warm/cold cycle")
	async def vallis_cycle(self, ctx):
		try:
			pc_wf = wf_api('pc')
			vallis = VallisInfo(pc_wf.get_vallis_info())
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			approx_time = get_time(vallis.timeLeft)

			msg = "```" + ("css" if vallis.isWarm else "ini") + "\n[It is " + ("Warm" if vallis.isWarm else "Cold") + f" on Vallis for another {vallis.timeLeft}]\n```"
			msg += "```" + ("ini" if vallis.isWarm else "css") + "\n[It will be " + ("Cold" if vallis.isWarm else "Warm") + f" at approximately {approx_time}]\n```"
			embed = discord.Embed(description=msg, title="Orb Vallis", url=vallis.wikiaUrl)
			await ctx.send(embed=embed, delete_after=30.0)
		await ctx.message.delete()
	
	# ------------------------------------------------------------------------------------------------------------- DEIMOS
	@commands.command(name='deimos', help="Fass/Vome cycle")
	async def deimos_cycle(self, ctx):
		try:
			pc_wf = wf_api('pc')
			deimos = DeimosInfo(pc_wf.get_deimos_info())
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			approx_time = get_time(deimos.timeLeft)

			msg = "```" + ("css" if deimos.isFass else "ini") + "\n[" + ("Fass" if deimos.isFass else "Vome") + f" is active on Deimos for another {deimos.timeLeft}]\n```"
			msg += "```" + ("ini" if deimos.isFass else "css") + "\n[" + ("Vome" if deimos.isFass else "Fass") + f" will be active at approximately {approx_time}]\n```"
			embed = discord.Embed(description=msg, title="Cambion Drift", url=deimos.wikiaUrl)
			await ctx.send(embed=embed, delete_after=30.0)
		await ctx.message.delete()

	# ------------------------------------------------------------------------------------------------------------- BARO
	@commands.command(name='baro', help="Time till or inventory")
	async def baro_info(self, ctx):
		try:
			pc_wf = wf_api('pc')
			baro = VoidTrader(pc_wf.get_void_trader_info())
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
				#msg = f"Will arrive at the {baro.relay} on {baro.planet} in {baro.startString}."
		
			embed = discord.Embed(title=baro.character, url=baro.wikiaUrl)
			msg = f"Departing in {baro.endString}" if baro.active else f"Arriving in {baro.startString}" 
			embed.add_field(name=f"{baro.relay}, {baro.planet}", value=msg, inline=False)
			if baro.active:
				if baro.inventory:
					item_str = ""
					ducats_str = ""
					credits_str = ""
					for item in baro.inventory:
							item_str += f"{item.name}\n"#add_links(f"[{item.name}]\n", self.url)
							ducats_str += f"{item.ducats}\n"
							credits_str += f"{item.credits:,}\n"
					embed.add_field(name="Inventory", value=item_str, inline=True)
					embed.add_field(name="Ducats", value=ducats_str, inline=True)
					embed.add_field(name="Credits", value=credits_str, inline=True)
			embed.set_thumbnail(url=baro.wikiaThumbnail)

			#msg = f"id={baro.id}\nactivation={baro.activation}\nexpiry={baro.expiry}\ncharacter={baro.character}\nlocation={baro.location}\n"
			#msg += f"psId={baro.psId}\nactive={baro.active}\nstartString={baro.startString}\nendString={baro.endString}\ninventory={baro.inventory}"
			await ctx.send(embed=embed, delete_after=90.0)
		await ctx.message.delete()
	
	# ------------------------------------------------------------------------------------------------------------- STEELPATH
	@commands.command(name='steelpath', help="Weekly rewards")
	async def steelpath_info(self, ctx):
		try:
			pc_wf = wf_api('pc')
			steelpath = SteelPath(pc_wf.get_steelpath_info())
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			atCurrent = False
			first_name_str = ""
			last_name_str = ""
			first_cost_str = ""
			last_cost_str = ""
			for reward in steelpath.rotation:
				if reward.name == steelpath.currentReward.name:
					atCurrent = True
				elif atCurrent:
					first_name_str += f"{reward.name}\n"
					first_cost_str += f"{reward.cost}\n"
				else:
					last_name_str += f"{reward.name}\n"
					last_cost_str += f"{reward.cost}\n"
			name_str = first_name_str + last_name_str
			cost_str = first_cost_str + last_cost_str	
			
			#msg = f"time remaining: {steelpath.remaining}"
			embed = discord.Embed(title="Steel Path Rotation", url=steelpath.wikiaUrl)
			embed.set_thumbnail(url=steelpath.wikiaThumbnail)
			msg = f"{steelpath.currentReward.name}\n       {steelpath.remaining}" # <--Those are not spaces
			embed.add_field(name="Current Reward", value=msg, inline=True)
			embed.add_field(name="Cost", value=steelpath.currentReward.cost, inline=True)
			embed.add_field(name="_ _", value="_ _", inline=True)
			
			embed.add_field(name="Next Rewards", value=name_str, inline=True)
			embed.add_field(name="Cost", value=cost_str, inline=True)
			embed.add_field(name="_ _", value="_ _", inline=True)
			await ctx.send(embed=embed, delete_after=30.0)
		await ctx.message.delete()

	# ------------------------------------------------------------------------------------------------------------- ARBITRATION
	@commands.command(name='arbitration', help="Info about current arbi")
	async def arbitration_info(self, ctx):
		try:
			pc_wf = wf_api('pc')
			arbi = Arbitration(pc_wf.get_arbitration_info())
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			embed = discord.Embed(title="Arbitration", url=arbi.wikiaUrl)
			embed.set_thumbnail(url=arbi.wikiaThumbnail)

			embed.add_field(name=f"{arbi.location}", value=f"{arbi.enemy} - {arbi.type}", inline=False)
			embed.set_footer(text=f"{arbi.timeLeft} remaining", icon_url="https://cdn.discordapp.com/emojis/931758276784316416.png")

			await ctx.send(embed=embed, delete_after=30.0)
		await ctx.message.delete()

	@commands.command(name='arbi', hidden=True)
	async def arbi_info(self, ctx):
		await self.arbitration_info(ctx)


	# ============================================================================================================= SEARCHABLE
	# ------------------------------------------------------------------------------------------------------------- RIVEN
	@commands.command(name='riven', help="Price info")
	async def riven_price(self, ctx, *args):
		arg = "Braton"
		if args:
			arg = concat(args)
			arg = capitalize_words(arg)	
		
		try:		
			pc_wf = wf_api('pc')
			riven_raw = pc_wf.get_specific_riven_info(arg)
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			key = capitalize_words(arg)
		
			if key not in riven_raw.keys():
				await ctx.send(f"Riven information for {key} does not exist", delete_after=3.0)
				return

			riven = [riven_raw[key]['unrolled'], riven_raw[key]['rerolled']]

			embed = discord.Embed()

			embed.set_author(name=f"{key} Riven")

			msg = f"Median: {riven[0]['median']}\nAverage: {riven[0]['avg']} ± {riven[0]['stddev']}\n"
			msg += f"Min: {riven[0]['min']}, Max: {riven[0]['max']}"
			embed.add_field(name="Unrolled", value=msg, inline=True)

			embed.add_field(name="_ _", value="_ _", inline=True)
			
			msg = f"Median: {riven[1]['median']}\nAverage: {riven[1]['avg']} ± {riven[1]['stddev']}\n"
			msg += f"Min: {riven[1]['min']}, Max: {riven[1]['max']}"
			embed.add_field(name="Rolled", value=msg, inline=True)

			await ctx.send(embed=embed, delete_after=60.0)
		await ctx.message.delete()

	# ------------------------------------------------------------------------------------------------------------- WARFRAME
	@commands.command(name='frame', help="Info about specified frame")
	async def warframe_info(self, ctx, *args):
		arg = 'Excalibur'
		if args:
			arg = concat(args)
		try:
			pc_wf = wf_api('pc')
			warframe = Warframe(pc_wf.get_warframe_info_sr(arg))
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			description = f"*{warframe.description}*"
			url = self.url + warframe.name.replace(" ", "_")
			embed = discord.Embed(title=warframe.name, description=description, url=url)

			embed.set_thumbnail(url=warframe.wikiaThumbnail)

			mastery = "-"
			if warframe.masteryReq > 0:
				mastery = f"{warframe.masteryReq}" + wf_emoji("mastery")
			embed.add_field(name="MR", value=mastery, inline=True)
			aura = wf_emoji(warframe.aura) if warframe.aura else "-"
			embed.add_field(name="Aura", value=aura, inline=True)
			polarities = ""
			for polarity in warframe.polarities:
				polarities += wf_emoji(polarity)
			embed.add_field(name="Polarities", value=polarities, inline=True)

			embed.add_field(name="Health", value=warframe.health, inline=True)
			embed.add_field(name="Armor", value=warframe.armor, inline=True)
			embed.add_field(name="Shield", value=warframe.shield, inline=True)

			embed.add_field(name="_ _", value="_ _", inline=False)
			embed.add_field(name="Passive", value=f"*{warframe.passiveDescription}*", inline=False)
			embed.add_field(name="_ _", value="_ _", inline=False)
			embed.add_field(name="ABILITIES", value="_ _", inline=False)
			for i, ability in enumerate(warframe.abilities):
				embed.add_field(name=ability.name, value=f"*{ability.description}*", inline=False)

			await ctx.send(embed=embed, delete_after=90.0)
		await ctx.message.delete()

	# ------------------------------------------------------------------------------------------------------------- WEAPON
	@commands.command(name='weapon', help="Info about specified weapon", hidden=True)
	async def weapon_info(self, ctx, *args):
		arg = "braton"
		if args:
			arg = concat(args)
			arg = arg.lower()
		try:
			pc_wf = wf_api('pc')
			weapon = Weapon(pc_wf.get_weapon_info_sr(arg))
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			embed = discord.Embed(title=weapon.name, url=weapon.wikiaUrl, description=f"*{weapon.description}*")
			embed.add_field(name=weapon.dispositionString, value="_ _", inline=False)
			embed.set_thumbnail(url=weapon.wikiaThumbnail)
			await ctx.send(embed=embed, delete_after=30.0)
		
		await ctx.message.delete()

	# ------------------------------------------------------------------------------------------------------------- DROPS
	@commands.command(name='drop', help="Something about drop information", hidden=True)
	async def drop_table(self, ctx, *args):
		arg = "ammo drum"
		if args:
			arg = concat(args)
			arg = arg.lower()
		try:
			pc_wf = wf_api('pc')
			drop_info = pc_wf.get_drop_info(arg)
			drops = [DropInfo(drop) for drop in drop_info]
		except LotusError as e:
			log(f"ERR: Lotus API failure: {e}")
			await ctx.send(f"Lotus API failure: {e}", delete_after=5.0)
		else:
			embed = discord.Embed()
			if drops:
				embed.set_author(name=f"{drops[0].item} from mobs")
				place = ""
				chance = ""
				for drop in drops:
					if drop.isMob:
						place += f"{drop.place}\n"
						chance += f"{drop.chance}%\n"
			
				embed.add_field(name="Mob", value=place, inline=True)
				embed.add_field(name="Chance", value=chance, inline=True)
				await ctx.send(embed=embed, delete_after=60.0)
			else:
				print(drops)
				pprint(drop_info)
				await ctx.send(f"Couldn't find drop information for {arg}", delete_after=3.0)

		await ctx.message.delete()

	@commands.command(name="drops", hidden=True)
	async def drops(self, ctx, *args):
		await self.drop_table(ctx, *args)