import time
import math
import discord
import requests
import json
import threading
import asyncio
import hashlib
import collections
import tabulate
import random
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

bot = commands.Bot(command_prefix = ["green!", "g!"], intents=discord.Intents.all())

@bot.command()
async def test(ctx):
    await ctx.send("Yay! :DD")

belt = {
    "some": ["BODY ONCE TOLD ME THE WORLD WAS GONNA ROLL ME"]
}

all_pairs = set()

@bot.event
async def on_message(ctx):
    msg = ctx.content.lower().replace(' ', '')
    chn = ctx.channel
    usr = ctx.author.id
    for catch in belt:
        if msg.endswith(catch) and ((usr, catch) not in all_pairs or random.randrange(0, 4) == 1) and usr != 878285405340966932:
            r = random.randrange(0, len(belt[catch]))
            all_pairs.add((usr, catch))
            await ctx.reply(belt[catch][r], mention_author=False)
    await bot.process_commands(ctx)

@bot.command(brief = "List all song catches you've found")
async def progress(ctx):
    s = ""
    x = 0
    usr = ctx.author.id
    for catch in belt:
        if (usr, catch) in all_pairs:
            s += catch
            s += " "
            x += 1
    t = "Song triggers found (" + str(x) + "): " + s
    await ctx.send(t)

@bot.command(brief = "Update the leaderboard")
async def leaderboard(ctx):
    ip10_api_key = "placeholder"
    ip10_api_secret = "placeholder"
    s = f"contest.status?apiKey={ip10_api_key}&contestId=409027&time={math.floor(time.time())}"
    h = hashlib.new("sha512")
    h.update(f"691337/{s}#{ip10_api_secret}".encode("utf-8"))
    req = requests.get(f"https://codeforces.com/api/{s}&apiSig=691337{h.hexdigest()}")

    if req.status_code != 200:
        await ctx.send("Some error has happened. Code " + str(req.status_code))
        return False

    submissions = json.loads(req.text)
    # EDIT SCORES HERE
    scores = collections.OrderedDict({
        "A": 9,
        "B": 10,
        "C": 11,
        "D": 12,
        "E": 13,
        "F1": 7,
        "F2": 7,
        "G": 15,
        "H": 16
    })
    board = {}
    time_list = {}
    n = len(scores)

    probs = []
    for prob in scores:
        probs.append(prob)

    for sub in submissions["result"]:
        user = sub["author"]["members"][0]["handle"]
        if user not in board:
            board[user] = {}
            for problem in scores:
                board[user][problem] = 0
            time_list[user] = 0
        if sub["verdict"] == "OK":
            problem = sub["problem"]["index"]
            board[user][problem] = scores[problem]
            time_list[user] = max(time_list[user], sub["creationTimeSeconds"])

    sorts = []
    for user in board:
        tot_score = 0
        for prob in board[user]:
            tot_score += board[user][prob]
        sorts.append([tot_score, -time_list[user], user])
    sorts = sorted(sorts, reverse=True)


    leader_board = []
    leader_board.append(["", "Username"])
    for prob in probs:
        if prob[0] == leader_board[0][-1][0]:
            leader_board[0].pop()
        leader_board[0].append(prob[0])
    leader_board[0].append("Total")

    for stuff in sorts:
        if len(leader_board) >= 16:
            break
        user = stuff[2]
        leader_board.append([str(len(leader_board))])
        leader_board[-1].append(user)
        for i in range(n):
            prob = probs[i]
            same = False
            if i > 0:
                if probs[i][0] == probs[i-1][0]:
                    same = True
            if same:
                leader_board[-1][-1] += board[user][prob]
            else:
                leader_board[-1].append(board[user][prob])
        leader_board[-1].append(str(stuff[0]))

    keepchars = ''.join(c for c in map(chr, range(256)))
    image = Image.new(mode = "RGB", size = (770, 620))
    draw = ImageDraw.Draw(image)
    table = tabulate.tabulate(leader_board, headers='firstrow', tablefmt='fancy_grid')
    test_table = ''.join(ch for ch in table if (ch in keepchars))
    draw.text((0, 0), test_table, font=ImageFont.truetype("Monocraft.otf", 16))
    image.show()
    image.save("leaderboard.png")
    await ctx.send(file=discord.File("leaderboard.png"))

handles_track = {}
handles_contest = {}
last_sub_id = {}

async def latest(ctx, handle, contest=False):

    global last_sub_id

    req = requests.get("https://codeforces.com/api/user.status?handle=" + handle + "&count=1")

    if req.status_code != 200:
        await ctx.send("Some error has happened. Code " + str(req.status_code))
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

    print("New sub");

    if(sub["verdict"] == "OK"):
        if contest == True:
            await ctx.message.author.send("Accepted! :DD " + 
                str(sub["problem"]["contestId"]) +
                sub["problem"]["index"] + ", " +
                str(sub["timeConsumedMillis"]) + "ms, " + 
                str(sub["memoryConsumedBytes"]/1000) + "KB", tts = True)
        if handle in handles_track:
            await ctx.send(sub["author"]["members"][0]["handle"] +
                " got ACCEPTED on problem " +
                str(sub["problem"]["contestId"]) +
                sub["problem"]["index"] +
                " (" +
                sub["problem"]["name"] +
                ")! <:ginkobingo:859811367556612126>")

    else:
        if contest == True:
            await ctx.message.author.send((sub["verdict"].replace("_", " ")).capitalize() +
                " on test " + str(sub["passedTestCount"]+1) + ": " +
                str(sub["problem"]["contestId"]) +
                sub["problem"]["index"] + ", " +
                str(sub["timeConsumedMillis"]) + "ms, " + 
                str(sub["memoryConsumedBytes"]//1000) + "KB", tts = True)
        if handle in handles_track:
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

@bot.command(brief = "Track someone on CF", description = "Alerts the channel whenever a submission has finished judging on Codeforces.\nBy default, stops tracking after one hour, but this can be changed.\nUse in DM to enable SERIOUS MODE! Great for virtuals/contests, it features less delay, less clutter, and more useful info.")
async def track(ctx, handle, track_time = 60):

    handle = str(handle)
    handle = handle.lower()

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
    if track_time >= 360:
        await ctx.send("Track time is very long! Note that after a restart, all tracks will be lost.")
    
    # mark handle with end time
    start_time = time.time()
    end_time = start_time + 60 * track_time
    handles_track[handle] = end_time

    # send
    await ctx.send("Now tracking " + handle + " :eyes:")

    # loop until either untrack or time end
    while (handle in handles_track) and (time.time() < end_time):
        res = await latest(ctx, handle)
        if res == False:
            handles_track.discard(handle)
            break;
        await asyncio.sleep(15)

    # check if time too long
    if time.time() >= end_time:
        await ctx.send(str(track_time) + " minutes have passed, now untracking " + handle)
        handles_track.pop(handle)

@bot.command(brief = "Stop tracking someone")
async def untrack(ctx, handle):
    handle = str(handle)
    handle = handle.lower()
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

@bot.command(brief = "Serious tracking for contests/virtuals")
async def contest(ctx, handle, track_time = 60):

    handle = str(handle)
    handle = handle.lower()

    # error handling
    if not isinstance(track_time, int):
        await ctx.send("Track length must be an integer oops")
        return
    if len(handles_contest) >= LIMIT:
        await ctx.send("Woah hold on I can only track " + str(LIMIT) + " ppl at a time, I'm not a good stalker yet.")
        return
    if handle in handles_contest:
        await ctx.send("Already tracking " + handle)
        return
    res = await latest(ctx, handle)
    if res == False:
        return

    # too long
    if track_time >= 360:
        await ctx.send("Track time is very long! Note that after a restart, all tracks will be lost.")
    
    # mark handle with end time
    start_time = time.time()
    end_time = start_time + 60 * track_time
    handles_contest[handle] = end_time

    # send
    await ctx.message.author.send(":thumbsup: Will DM you once a submission has been judged. Thanks for using Green! :D")

    # loop until either untrack or time end
    while (handle in handles_contest) and (time.time() < end_time):
        res = await latest(ctx, handle, True)
        if res == False:
            handles_contest.discard(handle)
            break;
        await asyncio.sleep(4)

    # check if time too long
    if time.time() >= end_time:
        await ctx.send(str(track_time) + " minutes have passed, now untracking " + handle)
        handles_contest.pop(handle)

@bot.command(brief = "Stop tracking someone in contest mode")
async def uncontest(ctx, handle):
    handle = str(handle)
    handle = handle.lower()
    if handle not in handles_contest:
        await ctx.send(handle + " not being tracked right now")
        return
    handles_contest.pop(handle)
    await ctx.send("Stopped tracking " + handle)

@bot.command(brief = "Get the url to an NUS mod", description = "Because people like saying they are probably going to SU the PP6969 mod (Baterisna, 2021)")
async def nus(ctx, mod):
    await ctx.send("https://nusmods.com/modules/" + mod.upper())

@bot.event
async def on_ready():
    print('This is {0.user}, hello :D'.format(bot))

# put your token here :D
bot.run()
# client.run()
