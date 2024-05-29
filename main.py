from typing import Final
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

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
        
        #Update user's Xp and Level when they send a message
        if db.execute("SELECT * FROM userLevels WHERE user = ? AND server = ?", [username, server]).fetchall():
            db.execute("UPDATE userLevels SET messagesSent = messagesSent + 1 WHERE user = ? AND server = ?", [username, server])
            connection.commit()
            if float(db.execute("SELECT messagesSent FROM userLevels WHERE user = ? AND server = ?", [username, server]).fetchall()[0][0]) % 100 == 0:
                db.execute("UPDATE userLevels SET level = level + 1 WHERE user = ? AND server = ?", [username, server])
                connection.commit() 
        else:
            db.execute("INSERT INTO userLevels (user, messagesSent, level, server) VALUES (?, ?, ?, ?)", [username, 1, 1, server])
            connection.commit()

        #If user attempts to run command, get proper response
        if user_message[0] == "!":
            try:
                response: str = get_response(user_message[1:], username, server)
                await message.channel.send(response)
            except Exception as e:
                print(e)

        #counting channel moderation
        c_channel = discord.utils.get(message.guild.text_channels, name='🔢counting')
        messages = [message async for message in c_channel.history(limit=2)]
        try:
            if message.channel == c_channel and int(messages[1].content) + 1 != int(message.content):
                await message.delete()
        except:
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

    #add command
    if(splitMessage[0] == "add"):
        return str(float(splitMessage[1]) + float(splitMessage[2]))
    
    #subtract command
    if(splitMessage[0] == "subtract"):
        return str(float(splitMessage[1]) - float(splitMessage[2]))
    
    #multiply command
    if(splitMessage[0] == "multiply"):
        return str(float(splitMessage[1]) * float(splitMessage[2]))
    
    #divide command
    if(splitMessage[0] == "divide"):
        return str(float(splitMessage[1]) / float(splitMessage[2]))
    
    #square root command
    if(splitMessage[0] == "sqrt"):
        return str(float(splitMessage[1]) ** 0.5)
    
    #square command
    if(splitMessage[0] == "square"):
        return str(float(splitMessage[1]) ** 2)
    
    #cube command
    if(splitMessage[0] == "cube"):
        return str(float(splitMessage[1]) ** 3)
    
    #ask command
    if(splitMessage[0] == "ask"):
       return  generate(user_input[3:])
    
    #level command
    if(splitMessage[0] == "level"):
        return "Hi, " + username + ", you are server level " + str(db.execute("SELECT level FROM userLevels WHERE user = ? AND server = ?", [username, server]).fetchall()[0][0])
    
    #xp command
    if(splitMessage[0] == "xp"):
        return "You have " + str(db.execute("SELECT messagesSent FROM userLevels WHERE user = ? AND server = ?", [username, server]).fetchall()[0][0]) + " server XP"

    return "I don't know that command"

def gamble(user_input, username: str, server: str) -> str:
    if not db.execute("SELECT * FROM userMoney WHERE user = ? AND server = ?", [username, server]).fetchall():
            db.execute("INSERT INTO userMoney (user, server, money, loans, bankrupt) VALUES (?, ?, ?, ?, ?)", [username, server, 1000, 0, 0])
            connection.commit()

    if(user_input.len() == 0):
        return "Grambling Commands:\n!gamble info: returns number of coins you current have, the number of loans you have active, and the number of times you've gone bankrupt\n!gamble loan: gives you 1,000 coins, adds a loan to your account\n!gamble payback: pays off a loan\n"
    elif(user_input[0] == "info"):
        info = db.execute("SELECT * FROM userMoney WHERE user = ? AND server = ?", [username, server]).fetchall()[0]
        return "You have " + str(info[2]) + " coins," + str(info[3]) + " loans, and " + str(info[4]) + " times gone bankrupt"
    elif(user_input[0] == "loan"):
        db.execute("UPDATE userMoney SET money = money + 1000 WHERE user = ? AND server = ?", [username, server])
        db.execute("UPDATE userMoney SET loans = loans + 1 WHERE user = ? AND server = ?", [username, server])
        connection.commit()
        return "You now have a loan of 1,000 coins"


def generate(input: str) -> str:
    return model.generate_content("The following is a conversation between a user and a discord bot called \"DTYBot\", created by a user called DummiThiccYoda (but he is not the one asking the questions). USER: " + input + "\n DTYbot: ").text


if __name__ == "__main__":
    main()