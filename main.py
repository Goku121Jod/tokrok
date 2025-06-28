import discord
from discord.ext import commands
import json
import re
import os

# Load config
with open("config.json") as f:
    config = json.load(f)

TOKEN = config["TOKEN"]
PREFIX = config["PREFIX"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

BALANCE_FILE = "balances.json"
FAKE_LTC_RATE = 85.0  # $85 per LTC

# Helper: Load balances
def load_balances():
    if not os.path.exists(BALANCE_FILE):
        return {}
    with open(BALANCE_FILE, "r") as f:
        return json.load(f)

# Helper: Save balances
def save_balances(balances):
    with open(BALANCE_FILE, "w") as f:
        json.dump(balances, f, indent=4)

# Helper: Get or init user balance
def get_user_balance(balances, user_id):
    if str(user_id) not in balances:
        balances[str(user_id)] = {"ltc": 5.0}  # Default 5 LTC
    return balances[str(user_id)]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def tip(ctx, member: discord.Member, amount_str: str, coin: str):
    if member == ctx.author:
        await ctx.send("You can't tip yourself.")
        return

    match = re.match(r"(\d+(?:\.\d+)?)\$", amount_str)
    if not match:
        await ctx.send("Please use the format like `10$`.")
        return

    usd = float(match.group(1))
    ltc_amount = round(usd / FAKE_LTC_RATE, 4)

    balances = load_balances()
    sender = get_user_balance(balances, ctx.author.id)
    receiver = get_user_balance(balances, member.id)

    if sender["ltc"] < ltc_amount:
        await ctx.reply(f"❌ You don't have enough LTC. Your balance: {sender['ltc']} LTC.")
        return

    # Transfer
    sender["ltc"] -= ltc_amount
    receiver["ltc"] += ltc_amount
    save_balances(balances)

    response = f"{ctx.author.mention} sent {member.mention} {ltc_amount} LTC (≈ ${usd:.2f})."
    await ctx.reply(response)

@bot.command(aliases=["bals"])
async def bal(ctx, coin: str = None):
    balances = load_balances()
    user_bal = get_user_balance(balances, ctx.author.id)

    if coin is None:
        await ctx.reply(f"💰 Your balances:\nLTC: {user_bal['ltc']} LTC")
    elif coin.lower() == "ltc":
        await ctx.reply(f"💰 LTC balance: {user_bal['ltc']} LTC")
    else:
        await ctx.reply("❌ Unsupported coin. Try `ltc`.")

bot.run(TOKEN)
              
