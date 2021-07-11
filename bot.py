import discord
import os
import dotenv
import asyncio
import math

# get secret token from .env file
dotenv.load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

time_dict = {'s': 1, 'm': 60, 'h': 3600}
bound_channels = {"im-gonna-do-a-question-for-an-hour", "spam"}
admin_roles = {"super admin", "artem", "nice person"}
msg_dict = {"mute": "muted", "blind": "blinded"}
admin_commands = {"admin": admin_roles, "channel": bound_channels}
admin_commands_txt = {"admin": "as an admin role", "channel": "as a bound channel"}
max_time = 86400
fail_text = "Could not execute command, try using ;help :slight_smile:"


# would really love to avoid having to do this
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents = intents)

@client.event
async def on_ready():
    print("Connected")
    await client.change_presence(activity = discord.Game(name=";help"))

@client.event
async def on_message(message):
    author = message.author
    channel = message.channel

    # help command
    if not (author.bot or author.system) and message.content == ';help':
        await author.send("""*User Commands (only work in work/spam channels):*
**;mute [time][s/m/h]**
Mutes you for a specified amount of time.
Only works in the work channel.\n
**;blind [time][s/m/h]**
Blinds you for a specified amount of time.
Only works in the work channel.\n
*Admin only commands:*
**;clear [@user1] [@user2] ...**
Unmutes and unblinds specified users.\n
**;admin [add/remove] [role name]**
Adds or removes the specified role as an admin role for this bot.\n
**;admin display**
Displays the current admin roles.\n
**;channel [add/remove] [channel name]**
Adds or removes the specified channel as a usable channel for the mute and blind commands\n
**;channel display**
Displays the current bound channels.\n
**;maxtime [set] [time][s/m/h]**
Sets the maximum mute/blind time.\n
**;maxtime display**
Displays the current maximum mute/blind time.""")
        return

    if type(channel).__name__ == "TextChannel" and type(author).__name__ == "Member":
        global max_time
        is_admin = set([r.name for r in author.roles]).intersection(admin_roles) or author.permissions_in(channel).administrator

        # other commands
        if (channel.name in bound_channels or is_admin) and not (author.bot or author.system):
            text = message.content
            if text[0] == ";":
                try:
                    #get role to add
                    roleDict = {"mute": discord.utils.get(message.guild.roles, name="muted"), "blind": discord.utils.get(message.guild.roles, name="blind")}
                    words = text[1:].split(" ")

                    # mute/blind command
                    if words[0] in roleDict.keys():
                        new_role = roleDict[words[0]]
                        time = getTimeVal(words[1])
                        if time != -1:
                            time = min(time, max_time)
                            await author.add_roles(new_role)
                            await channel.send(msg_dict[words[0]].title() + " " + author.name + " for " + getTimeStr(time))
                            await asyncio.sleep(time)

                            # fuckery needed to get updated roles after wait
                            if new_role in discord.utils.get(message.guild.members, id = author.id).roles:
                                await author.remove_roles(new_role)
                                await channel.send(author.name + " is back!")
                            return
                        else:
                            await channel.send(fail_text)

                    # admin-only commands
                    if is_admin:
                        if words[0] == "clear":
                            savedUsers = message.mentions
                            for u in savedUsers:
                                await u.remove_roles(roleDict["mute"])
                                await u.remove_roles(roleDict["blind"])
                            await channel.send(author.name + " force cleared " + "".join([(u.name + ", ") for u in savedUsers[:-1]]) + (" and " if len(savedUsers) > 1 else "") + savedUsers[-1].name)
                            return

                        if words[0] in admin_commands.keys():
                            if words[1] == "add":
                                admin_commands[words[0]].add(words[2])
                                await channel.send("Added " + words[2] + " " + admin_commands_txt[words[0]])
                            elif words[1] == "remove":
                                admin_commands[words[0]].remove(words[2])
                                await channel.send("Removed " + words[2] + " " + admin_commands_txt[words[0]])
                            elif words[1] == "display":
                                await channel.send(admin_commands[words[0]])
                            return

                        if words[0] == "maxtime":
                            if words[1] == "display":
                                await channel.send("Maximum time is " + getTimeStr(max_time))
                            elif words[1] == "set":
                                new_time = getTimeVal(words[2])
                                if new_time != -1:
                                    max_time = new_time
                                    await channel.send("Set max time to " + getTimeStr(new_time))
                                else:
                                    await channel.send(fail_text)
                except:
                    await channel.send(fail_text)

# converts time string into numerical value (-1 if it fails)
def getTimeVal(timeStr):
    # need to improve this to read eg 1h30m or 1h 30m
    if len(timeStr) > 1:
        base = timeStr[:-1]
        if base.isdigit():
            multi = timeStr[-1]
            time = time_dict.get(multi, 60) * int(base)
            return time
    return -1

# converts number of seconds into time string
def getTimeStr(time):
    secs = time % 60
    mins = math.floor(time/60) % 60
    hrs = math.floor(time/3600)
    return str(hrs) + "h " + str(mins) + "m " + str(secs) + "s"

client.run(TOKEN)