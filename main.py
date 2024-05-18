from typing import Final
import os
from dotenv import load_dotenv
import discord

import sqlite3

import google.generativeai as genai

#loads database for user levels
connection = sqlite3.connect("users.db")
db = connection.cursor()

# Loads bot token from the OS
load_dotenv()
TOKEN: str = os.getenv('DISCORD_TOKEN')

genai.configure(api_key=os.getenv("GOOGLE_TOKEN"))

# Sets up bot's permissions
intents: discord.Intents = discord.Intents.default()
intents.message_content = True #NOQA
client: discord.Client = discord.Client(intents=intents)

# Bot Startup
@client.event
async def on_ready() -> None:
    print(f"{client.user} is now running")

#Incoming messages
@client.event
async def on_message(message: discord.Message) -> None:
    if message.author != client.user:
        user_message: str = message.content
        channel: str = str(message.channel)
        username: str = str(message.author)
        server: str = str(message.guild)
        
        if db.execute("SELECT * FROM userLevels WHERE user = ? AND server = ?", [username, server]).fetchall():
            db.execute("UPDATE userLevels SET messagesSent = messagesSent + 1 WHERE user = ? AND server = ?", [username, server])
            connection.commit()
            if float(db.execute("SELECT messagesSent FROM userLevels WHERE user = ? AND server = ?", [username, server]).fetchall()[0][0]) % 100 == 0:
                db.execute("UPDATE userLevels SET level = level + 1 WHERE user = ? AND server = ?", [username, server])
                connection.commit()
            
        else:
            db.execute("INSERT INTO userLevels (user, messagesSent, level, server) VALUES (?, ?, ?, ?)", [username, 1, 1, server])
            connection.commit()

        if user_message[0] == "!":
            try:
                response: str = get_response(user_message[1:], username, server)
                await message.channel.send(response)
            except Exception as e:
                print(e)

        c_channel = discord.utils.get(message.guild.text_channels, name='🔢counting')
        messages = await c_channel.history(limit=2).flatten()
        if message.channel == c_channel and int(messages[1].content) + 1 != int(message.content):
            await message.delete()

#Main entry point
def main() -> None:
    client.run(token=TOKEN)


#set up genai
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_TOKEN"))
model = genai.GenerativeModel("gemini-pro")

#get response for the user given a command
def get_response(user_input: str, username: str, server: str) -> str:

    lowered: str = user_input.lower()
    splitMessage = lowered.split()
    if(splitMessage[0] == "add"):
        return str(float(splitMessage[1]) + float(splitMessage[2]))
    
    if(splitMessage[0] == "ask"):
       return  generate(user_input[3:])
    
    if(splitMessage[0] == "level"):
        return "Hi, " + username + ", you are server level " + str(db.execute("SELECT level FROM userLevels WHERE user = ? AND server = ?", [username, server]).fetchall()[0][0])
    
    if(splitMessage[0] == "xp"):
        return "You have " + str(db.execute("SELECT messagesSent FROM userLevels WHERE user = ? AND server = ?", [username, server]).fetchall()[0][0]) + " server XP"

    return "I don't know that command"

def generate(input: str) -> str:
    return model.generate_content("The following is a conversation between a user and a discord bot called \"DTYBot\", created by a user called DummiThiccYoda (but he is not the one asking the questions). USER: " + input + ", DTYbot: ").text


if __name__ == "__main__":
    main()