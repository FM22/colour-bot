import discord
import os
import dotenv

# get secret token from .env file
dotenv.load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bound_channels = {"bot-commands"}
admin_cmd_prefix = "c"
admin_roles = {"admin"}
admin_commands = {"admin": admin_roles, "channel": bound_channels}
admin_commands_txt = {"admin": "as an admin role", "channel": "as a bound channel"}
fail_text = "Could not execute command, try using ;help"

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
    server = message.guild

    # help command
    if not (author.bot or author.system) and message.content == ';help':
        await author.send("""*User Commands:*
**;colour [hexcode]**
Sets your colour on the server to the specified hexcode. Only works in #bot-commands.\n
*Admin only commands:*
**;colour [@user] [hexcode]**
Sets the specified user's colour to the specified hexcode.\n
**;admin [add/remove] [role name]**
Adds or removes the specified role as an admin role for this bot.\n
**;admin display**
Displays the current admin roles.\n
**;channel [add/remove] [channel name]**
Adds or removes the specified channel as a usable channel for user commands\n
**;channel display**
Displays the current bound channels.""")
        return

    if type(channel).__name__ == "TextChannel" and type(author).__name__ == "Member":
        is_admin = set([r.name for r in author.roles]).intersection(admin_roles) or author.permissions_in(channel).administrator

        # other commands
        if (channel.name in bound_channels or is_admin) and not (author.bot or author.system):
            text = message.content
            if text[0] == ";":
                try:
                    #get role to add
                    words = text[1:].split(" ")
                    
                    # colour-setting command
                    if words[0] == 'colour':
                        if len(words) == 3:
                            # admin version
                            if is_admin and len(message.mentions) == 1 and words[1][0] == '<':
                                target = message.mentions[0]
                                if await set_colour(target, words[2]):
                                    await channel.send("Set colour of " + target.name + " to " + words[2])
                                else:
                                    await channel.send(fail_text)
                            else:
                                await channel.send(fail_text)
                        elif len(words) == 2:
                            # non-admin version
                            if await set_colour(author, words[1]):
                                await channel.send("Set colour of " + author.name + " to " + words[1])
                            else:
                                await channel.send(fail_text)
                        else:
                            await channel.send(fail_text)

                    # admin-only commands
                    if is_admin:
                        if words[0] == admin_cmd_prefix and words[1] in admin_commands.keys():
                            if words[2] == "add":
                                admin_commands[words[1]].add(words[3])
                                await channel.send("Added " + words[3] + " " + admin_commands_txt[words[1]])
                            elif words[2] == "remove":
                                admin_commands[words[1]].remove(words[3])
                                await channel.send("Removed " + words[3] + " " + admin_commands_txt[words[1]])
                            elif words[2] == "display":
                                await channel.send(admin_commands[words[1]])
                            return
                except Exception as e:
                    print(e)
                    await channel.send(fail_text)

async def set_colour(user, hexcode):
    # try to convert hexcode
    try:
        if hexcode[0] == '#':
            hexcode = hexcode[1:]#
        c_int = int(hexcode, 16)

        # range check
        if not (c_int >= 0 and c_int <= 16777215):
            print("failed rangecheck")
            return False

        # set colour
        c = discord.Colour(int(hexcode, 16))
        txt = str(c) # hex code (std formatting)
    except Exception as e:
        print(e)
        return False
    
    # enumerate all colour roles
    found_role = False
    for r in user.guild.roles:
        if r.name[0] == '#':
            if r.name == txt:
                role = r
                found_role = True
            elif user in r.members: # remove old colour role(s)
                await user.remove_roles(r)
            
            # delete unused roles
            if len(r.members) == 0:
                await r.delete()

    # create colour role if it doesn't exist
    if not found_role:
        role = await user.guild.create_role(name=txt, colour=c)

    # set user colour
    await user.add_roles(role)
    return True

client.run(TOKEN)