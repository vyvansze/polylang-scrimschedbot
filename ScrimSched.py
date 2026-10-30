import discord
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("BOT_TOKEN")

if token is None:
    raise RuntimeError("BOT_TOKEN is not set")

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content == 'Axlyte':
            await message.channel.send('You mean singaporean Aspire?')
        
        if message.content == '!faceit':
            await message.channel.send('https://www.faceit.com/en/team-home/23bb31a5-759f-4d53-921b-6be676bfc745/overview')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(token)