import time
import discord
import requests
import json
import threading
import asyncio
from discord.ext import commands

bot = commands.Bot(command_prefix = "green!")

@bot.event
async def on_ready():
    print('This is {0.user}, hello :D'.format(bot))

@bot.command()
async def test(ctx):
    await ctx.send("Yay! :D", tts = True)

last_sub_id = {}

async def latest(ctx, handle):

    global last_sub_id

    req = requests.get("https://codeforces.com/api/user.status?handle=" + handle + "&count=1")

    if req.status_code != 200:
        await ctx.send("Username not found.")
        return False

    l = json.loads(req.text)

    if l["status"] != "OK":
        await ctx.send("I can't get data from CF. Error: " + l["comment"])
        return False

    if len(l["result"]) == 0:
        last_sub_id[handle] = -1
        return

    sub = l["result"][0]

    if "verdict" not in sub:
        return

    if sub["verdict"] == "TESTING":
        return

    if handle not in last_sub_id:
        last_sub_id[handle] = sub["id"]
        return

    if last_sub_id[handle] == sub["id"]:
        return

    last_sub_id[handle] = sub["id"]

    if(sub["verdict"] == "OK"):
        await ctx.send(sub["author"]["members"][0]["handle"] +
            " got ACCEPTED on problem " +
            str(sub["problem"]["contestId"]) +
            sub["problem"]["index"] +
            " (" +
            sub["problem"]["name"] +
            ")!", tts = True)

    else:
        await ctx.send(sub["author"]["members"][0]["handle"] +
            " got " +
            sub["verdict"].replace("_", " ") +
            " on problem " +
            str(sub["problem"]["contestId"]) + 
            sub["problem"]["index"] +
            " (" +
            sub["problem"]["name"] +
            ")!", tts = True)

@bot.command()
async def track(ctx, *args):
    if len(last_sub_id) >= 5:
        await ctx.send("Woah hold on I can only track 5 ppl at a time, I'm not a good stalker yet.")
        return
    handle = args[0]
    await ctx.send("Now tracking " + handle + " :eyes:")
    while True:
        res = await latest(ctx, handle)
        if res == False:
            break
        await asyncio.sleep(10)

bot.run('ODc4Mjg1NDA1MzQwOTY2OTMy.YR-9Bg.QV4LuYM45e36FE-4F7uQKlB6rHo')
# client.run('ODc4Mjg1NDA1MzQwOTY2OTMy.YR-9Bg.QV4LuYM45e36FE-4F7uQKlB6rHo')
