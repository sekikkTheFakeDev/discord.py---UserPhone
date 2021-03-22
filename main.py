import discord
from discord.ext import commands, tasks
import asyncio
import os
import random
import json

prefix = "$"

client = commands.Bot(command_prefix = prefix)

@client.event
async def on_ready():
  print("ALIVE!")
  pairs.start()
  time_system.start()

"""
this is for removing 5 "seconds" from time of user, and if it reaches the 0 it will close the connection between afk user and its pair
"""
@tasks.loop(seconds = 5)
async def time_system():
  try:
    with open("pairs.json", "r") as f:
      pairs = json.load(f)

    for user in pairs:
      
      timex = pairs[str(user)]["time"]
      timex -= 5
      pairs[str(user)]["time"] = timex
      if timex <= 0: #if time is 0 delete the users
        user2 = pairs[str(user)]["pid"]
        ch1 = pairs[str(user)]["chid"]
        ch2 = pairs[str(user)]["pchid"]
        del pairs[str(user)]
        del pairs[str(user2)]
        channel1 = client.get_channel(ch1)
        channel2 = client.get_channel(ch2)

        await channel1.send("One of the user was AFK so the connection was closed")
        await channel2.send("One of the user was AFK so the connection was closed")

      with open("pairs.json", "w") as f:
        json.dump(pairs, f)
  except:
    pass

"""
this is for finding pairs for users in queue
"""

@tasks.loop(seconds = 3)
async def pairs():
  try:
    with open("talk.json", "r") as f:
      talk = json.load(f)
    users = talk["users"]

    if len(users) == 1 : #if there is only one user in queue to pass
      return

    while len(users) > 1: #to find every user a pair
      users = talk["users"]
      if len(users) <= 1:
        break
      else:
        user1 = random.choice(users) 
        user2 = random.choice(users)

        ls = [user1, user2]

        while ls[0] == ls[1]: #to make sure the users are not the same
          ls.pop(-1)
          user2 = random.choice(users)
          ls.append(user2)
          if ls[0] != ls[1]:
            break

        index1 = users.index(user1)
        index2 = users.index(user2)

        users.pop(index1)
        users.pop(index2)

        talk["users"] = users

        with open("talk.json", "w") as f:
          json.dump(talk, f)

        user1 = ls[0]
        user2 = ls[1]

        ch1 = user1["channel"]
        ch2 = user2["channel"]

        channel1 = client.get_channel(ch1)
        channel2 = client.get_channel(ch2)

        id1 = user1["id"]
        id2 = user2["id"]

        usero = await client.fetch_user(id1)
        useroo = await client.fetch_user(id2)

        await asyncio.sleep(1)

        await channel1.send(f"You are currently talking to **{useroo.name}**")
        await channel2.send(f"You are currently talking to **{usero.name}**")
        
        with open("pairs.json", "r") as f: #make the users a pair "account"
          pairs = json.load(f)

        pairs[str(usero.id)] = {}
        pairs[str(usero.id)]["id"] = usero.id
        pairs[str(usero.id)]["pid"] = useroo.id
        pairs[str(usero.id)]["chid"] = channel1.id
        pairs[str(usero.id)]["pchid"] = channel2.id
        pairs[str(usero.id)]["time"] = 60

        pairs[str(useroo.id)] = {}
        pairs[str(useroo.id)]["id"] = useroo.id
        pairs[str(useroo.id)]["pid"] = usero.id
        pairs[str(useroo.id)]["chid"] = channel2.id
        pairs[str(useroo.id)]["pchid"] = channel1.id
        pairs[str(useroo.id)]["time"] = 60

        with open("pairs.json", "w") as f:
          json.dump(pairs, f)
  except:
    pass

"""
to check if user is already in the queue and this is used in the command below in @comands.check()
"""
async def check_talk(ctx):
  user = ctx.author
  
  with open("talk.json", "r") as f:
    talk = json.load(f)

  ls = talk["users"]

  obj = {"id": user.id, "channel": ctx.channel.id}

  if obj in ls:
    await ctx.send("You are already in the queue...")
    return False
  else:
    return True

"""
to put a user in a queue
"""

@client.command()
@commands.check(check_talk)
async def talk(ctx):
  user = ctx.author
  with open("talk.json", "r") as f:
    talk = json.load(f)

  ls = talk["users"]

  obj = {"id": user.id, "channel": ctx.channel.id}

  m = await ctx.send("Sometimes you will not be able to talk to people just because there are not many people using this command")

  await asyncio.sleep(2)

  await m.delete()

  talk["users"].append(obj)

  with open("talk.json", "w") as f: # put the user in the queue
    json.dump(talk, f)

  with open("pairs.json", "r") as f:
    pairs = json.load(f)

  t = 0
  for i in range(30):
    if str(user.id) in pairs: #wait 30 seconds and if there is no pair it will say that it didn't find a pair if t == 0
      t = 1
      break
    await asyncio.sleep(1)

  if t == 0:
    try:
      with open("talk.json", "r") as f:
        talk = json.load(f)

      users = talk["users"]

      i = users.index(obj)

      talk["users"].pop(i)

      with open("talk.json", "w") as f:
        json.dump(talk, f)

      await ctx.send("Didn't find you a pair")
    except:
      pass

#error handler just because of check
@talk.error
async def talk_handler(ctx, error):
  if isinstance(error, commands.CheckFailure):
    pass
  else:
    raise error

#chatting
@client.event
async def on_message(msg):

  with open("pairs.json", "r") as f:
    pairs = json.load(f)

    #if user tries to say end but doesn't have a pair
    if msg.content.startswith(f"{prefix}end"):
      if str(msg.author.id) not in pairs:
        await msg.channel.send("You are not connected")
        return

  #check if user has a pair
  if str(msg.author.id) in pairs:
    chid = pairs[str(msg.author.id)]["chid"]
    if msg.channel.id == chid:
      #if has a pair and says end
      if msg.content.startswith(f"{prefix}end"):

        userko = pairs[str(msg.author.id)]["pid"]
        channelko = pairs[str(msg.author.id)]["pchid"]

        del pairs[str(msg.author.id)] #delete the both of the users
        del pairs[str(userko)]

        with open("pairs.json", "w") as f:
          json.dump(pairs, f)

        ch = client.get_channel(channelko)

        await msg.channel.send(f"You ended the call")
        await ch.send(f"**{msg.author.name}** has ended the call")
        return

      pairs[str(msg.author.id)]["time"] = 60

      with open("pairs.json", "w") as f:
        json.dump(pairs, f)

      #sending the message

      pchid = pairs[str(msg.author.id)]["pchid"]
      uid = pairs[str(msg.author.id)]["id"]

      pchannel = client.get_channel(pchid)
      author = await client.fetch_user(uid)

      await asyncio.sleep(1)

      await pchannel.send(f"**{author.name}**: {msg.content}")
 

  await client.process_commands(msg)

client.run(TOKEN)
