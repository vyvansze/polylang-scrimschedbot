
import discord
import os
from google import genai
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

token = os.getenv("BOT_TOKEN")
ai_token = os.getenv("AI_TOKEN")

if not token:
    raise RuntimeError("BOT_TOKEN is not set")

if not ai_token:
    raise RuntimeError("AI_TOKEN is not set")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
gemini_client = genai.Client(api_key=ai_token)


@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content == "Axlyte":
        await message.channel.send("You mean singaporean Aspire?")

    if message.content == "!faceit":
        await message.channel.send(
            "https://www.faceit.com/en/team-home/23bb31a5-759f-4d53-921b-6be676bfc745/overview"
        )

    if message.content == "Mac Donald:":
        await message.channel.send(
            "Jacob:",
            file=discord.File("jacob.gif")
        )

    await bot.process_commands(message)


class MessageModal(discord.ui.Modal, title="Enter Your Message"):
    def __init__(self, view):
        super().__init__()
        self.scrim_view = view

        self.message_input = discord.ui.TextInput(
            label="Your message",
            placeholder="Enter the message you want to send...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.add_item(self.message_input)

    async def on_submit(self, interaction: discord.Interaction):
        self.scrim_view.user_message = self.message_input.value

        await interaction.response.send_message(
            "Your message has been saved!",
            ephemeral=True
        )


class ConfigSelect(discord.ui.Select):
    def __init__(self, attribute, placeholder, options, row):
        super().__init__(
            placeholder=placeholder,
            options=[
                discord.SelectOption(label=option, value=option)
                for option in options
            ],
            row=row
        )
        self.attribute = attribute

    async def callback(self, interaction: discord.Interaction):
        setattr(self.view, self.attribute, self.values[0])

        await interaction.response.send_message(
            f"Selected: **{self.values[0]}**",
            ephemeral=True
        )


class ScrimView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=300)

        self.owner_id = owner_id
        self.user_message = None
        self.target_language = None
        self.tone = None
        self.reason = None

        self.add_item(ConfigSelect(
            "target_language",
            "Select target language",
            ["English", "Filipino", "Japanese", "Chinese"],
            0
        ))

        self.add_item(ConfigSelect(
            "tone",
            "Select message tone",
            ["Formal", "Apology", "Firm"],
            1
        ))

        self.add_item(ConfigSelect(
            "reason",
            "Select reason for scrim cancellation",
            [
                "Scheduling conflict",
                "Insufficient players",
                "Technical difficulties",
                "Team emergency",
                "Other commitments"
            ],
            2
        ))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This menu belongs to another user.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Enter Message",
        style=discord.ButtonStyle.primary,
        emoji="✏️",
        row=3
    )
    async def enter_message(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(MessageModal(self))

    @discord.ui.button(
        label="Generate",
        style=discord.ButtonStyle.green,
        emoji="✅",
        row=3
    )
    async def generate(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not all([
            self.user_message,
            self.target_language,
            self.tone,
            self.reason
        ]):
            await interaction.response.send_message(
                "Please enter your message and complete all selections first!",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        prompt = f"""
You are an AI assistant specializing in esports scrim management.

Your task is to rewrite messages between esports teams.

Original message: {self.user_message}
Target language: {self.target_language}
Tone: {self.tone}
Cancellation reason: {self.reason}

Instructions:
- Automatically detect the original message's language.
- Rewrite it naturally in the selected target language.
- Maintain the selected tone.
- Preserve all important information.
- Do not invent dates, times, or agreements.
- Use the cancellation reason only when relevant.
- If the message is not about cancellation, preserve its original intent.

Return the result in exactly these three sections:

**Generated Message:**
The rewritten message in the target language.

**Romanized Version:**
Write the generated message using Latin characters.
For English or languages already written in the Latin alphabet,
write "Not applicable."

**Direct English Translation:**
Translate the generated message directly into English.
Preserve its original meaning and wording as closely as possible.

Return no additional sections.
"""

        try:
            response = await gemini_client.aio.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            ai_response = response.text

            if not ai_response:
                raise ValueError("Gemini returned an empty response.")

            await interaction.followup.send(
                f"**Generated Message:**\n{ai_response}",
                ephemeral=True
            )

        except Exception as e:
            print(f"Gemini API Error: {e}")

            await interaction.followup.send(
                "Something went wrong while generating your message.",
                ephemeral=True
            )


@bot.command()
async def menu(ctx):
    await ctx.send(
        "**Scrim Message Generator**\n"
        "Enter your message and configure how you want the AI to rewrite it.",
        view=ScrimView(ctx.author.id)
    )


bot.run(token)
