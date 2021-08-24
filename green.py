import time
import discord
import requests
import json
import threading
import asyncio
from discord.ext import commands

bot = commands.Bot(command_prefix = "green!")

handles_track = {}

@bot.command()
async def test(ctx):
    await ctx.send("Yay! :D", tts = True)

last_sub_id = {}

async def latest(ctx, handle, contest=False):

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

    # no verdict
    if "verdict" not in sub:
        return

    # if currently testing don't add
    if sub["verdict"] == "TESTING":
        return

    # if new, don't report
    if handle not in last_sub_id:
        last_sub_id[handle] = sub["id"]
        return

    # if same, don't report
    if last_sub_id[handle] == sub["id"]:
        return

    last_sub_id[handle] = sub["id"]

    if(sub["verdict"] == "OK"):
        if contest == True:
            await ctx.send("Accepted! :D " + 
                str(sub["problem"]["contestId"]) +
                sub["problem"]["index"] + ", " +
                str(sub["timeConsumedMillis"]) + "ms, " + 
                str(sub["memoryConsumedBytes"]/1000) + "KB", tts = True)
        else:
            await ctx.send(sub["author"]["members"][0]["handle"] +
                " got ACCEPTED on problem " +
                str(sub["problem"]["contestId"]) +
                sub["problem"]["index"] +
                " (" +
                sub["problem"]["name"] +
                ")!")

    else:
        if contest == True:
                await ctx.send((sub["verdict"].replace("_", " ")).capitalize() +
                " on test " + str(sub["passedTestCount"]+1) + ": " +
                str(sub["problem"]["contestId"]) +
                sub["problem"]["index"] + ", " +
                str(sub["timeConsumedMillis"]) + "ms, " + 
                str(sub["memoryConsumedBytes"]//1000) + "KB", tts = True)
        else:
            await ctx.send(sub["author"]["members"][0]["handle"] +
                " got " +
                sub["verdict"].replace("_", " ") +
                " on problem " +
                str(sub["problem"]["contestId"]) + 
                sub["problem"]["index"] +
                " (" +
                sub["problem"]["name"] +
                ")!")

TRACK_TIME = 7200
LIMIT = 7

@bot.command(brief = "Track someone on CF", description = "Alerts you whenever a submission has finished judging on Codeforces.\nBy default, stops tracking after one hour, but this can be changed.\nUse in DM to enable SERIOUS MODE! Great for virtuals/contests, it features less delay, less clutter, and more useful info.")
async def track(ctx, handle, track_time = 60):

    # error handling
    if not isinstance(track_time, int):
        await ctx.send("Track length must be an integer oops")
        return
    if len(handles_track) >= LIMIT:
        await ctx.send("Woah hold on I can only track " + str(LIMIT) + " ppl at a time, I'm not a good stalker yet.")
        return
    if handle in handles_track:
        await ctx.send("Already tracking " + handle)
        return
    res = await latest(ctx, handle)
    if res == False:
        return

    # too long
    if track_time >= 720:
        await ctx.send("Track time is very long! Note that after a restart, all tracks will be lost.")
    
    # mark handle with end time
    start_time = time.time()
    end_time = start_time + 60 * track_time
    handles_track[handle] = end_time

    # send
    await ctx.send("Now tracking " + handle + " :eyes:")

    contest = False

    if isinstance(ctx.channel, discord.channel.DMChannel):
        contest = True

    # loop until either untrack or time end
    while (handle in handles_track) and (time.time() < end_time):
        res = await latest(ctx, handle)
        if res == False:
            handles_track.discard(handle)
            break
        if isinstance(ctx.channel, discord.channel.DMChannel):
            await asyncio.sleep(4)
        else:
            await asyncio.sleep(15)

    # check if time too long
    if time.time() >= end_time:
        await ctx.send(str(track_time) + " minutes have passed, now untracking " + handle)
        handles_track.pop(handle)

@bot.command(brief = "Stop tracking someone")
async def untrack(ctx, handle):
    if handle not in handles_track:
        await ctx.send(handle + " not being tracked right now")
        return
    handles_track.pop(handle)
    await ctx.send("Stopped tracking " + handle)

@bot.command(brief = "List of usernames being tracked")
async def tracklist(ctx):
    if len(handles_track) == 0:
        await ctx.send("Not tracking anyone right now")
        return
    s = "People currently being tracked:"
    for handle in handles_track:
        left_time = handles_track[handle] - time.time()
        s = s + "\n" + handle + ": " + str(int(left_time // 60)) + "m" + str(int(left_time % 60)) + "s left"
    await ctx.send(s)

@bot.event
async def on_ready():
    print('This is {0.user}, hello :D'.format(bot))

bot.run('ODc4Mjg1NDA1MzQwOTY2OTMy.YR-9Bg.QV4LuYM45e36FE-4F7uQKlB6rHo')
# client.run('ODc4Mjg1NDA1MzQwOTY2OTMy.YR-9Bg.QV4LuYM45e36FE-4F7uQKlB6rHo')
