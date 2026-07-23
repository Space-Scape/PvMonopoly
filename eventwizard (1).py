import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
import gspread
from google.oauth2.service_account import Credentials
import asyncio
import re
from discord.ui import Modal, TextInput, View, Button
from discord import ButtonStyle
from typing import Optional
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
import collections
import traceback

# ---------------------------
# 🔹 Google Sheets Setup
# ---------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials_dict = {
    "type": os.getenv('EVENT_TYPE'),
    "project_id": os.getenv('EVENT_PROJECT_ID'),
    "private_key_id": os.getenv('EVENT_PRIVATE_KEY_ID'),
    "private_key": os.getenv('EVENT_PRIVATE_KEY').replace("\\n", "\n"),
    "client_email": os.getenv('EVENT_CLIENT_EMAIL'),
    "client_id": os.getenv('EVENT_CLIENT_ID'),
    "auth_uri": os.getenv('EVENT_AUTH_URI'),
    "token_uri": os.getenv('EVENT_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('EVENT_AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": os.getenv('EVENT_CLIENT_X509_CERT_URL'),
    "universe_domain": os.getenv('EVENT_UNIVERSE_DOMAIN')
}

creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
sheet_client = gspread.authorize(creds)

# Drop Submission Sheet
sheet_id = "1VjoOx_GdzD0dNP-SnbMDjhKV8M054QQ9JgRbLQeSe-M"
sheet = sheet_client.open_by_key(sheet_id).sheet1

# RSN Tracker Sheet
rsn_sheet = sheet_client.open_by_key("1ZwJiuVMp-3p8UH0NCVYTV9_UVI26jl5kWu2nvdspl9k").worksheet("Tracker")

# Events Sheet
EVENTS_SHEET_ID = "1ycltDSLJeKTLAHzVeYZ6JKwIV5A7md8Lh7IetvVljEc"
events_sheet = sheet_client.open_by_key(EVENTS_SHEET_ID).worksheet("Event Inputs")


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

current_schedule_message_id = None
last_known_sheet_data = None


REQUIRED_ROLE_NAME = "Event Staff"
REGISTERED_ROLE_NAME = "Registered"

# Event Shit
EVENT_SCHEDULE_CHANNEL_ID = 1272646577432825977
STAFF_ROLE_ID = 1272635396991221824
ADMINISTRATOR_ROLE_ID = 1272961765034164318

# Timezone Shit
CST = ZoneInfo("America/Chicago")
TIMEZONE_DATA = {
    "PST": ("America/Los_Angeles", "🇺🇸"), "MST": ("America/Denver", "🇺🇸"),
    "CST": ("America/Chicago", "🇺🇸"), "EST": ("America/New_York", "🇺🇸"),
    "AST": ("America/Halifax", "🇨🇦"), "BRT": ("Brazil", "🇧🇷"),
    "ART": ("Argentina", "🇦🇷"), "GMT": ("Europe/London", "🇬🇧"),
    "CET": ("Europe/Paris", "🇫🇷"), "EET": ("Europe/Helsinki", "🇫🇮"),
    "AWST": ("Australia/Perth", "🇦🇺"), "ACST": ("Australia/Adelaide", "🇦🇺"),
    "AEST": ("Australia/Sydney", "🇦🇺"),
}
INTERNATIONAL_TIMEZONES = {"GMT", "CET", "EET", "BRT", "ART", "AWST", "ACST", "AEST"}

def _fmt_no_leading_zero(hour_12: str) -> str:
    return hour_12.lstrip("0") if hour_12.startswith("0") else hour_12

async def find_manual_event_posts_for_times(channel: discord.TextChannel, times_cst: list[datetime]) -> list[discord.Message]:
    patterns = set()
    for dt in times_cst:
        dt_cst = dt.astimezone(CST)
        weekday_long = dt_cst.strftime("%A")
        month_long = dt_cst.strftime("%B")
        day_str = str(dt_cst.day)
        year = dt_cst.strftime("%Y")
        time_12 = _fmt_no_leading_zero(dt_cst.strftime("%I:%M %p"))
        fmt1 = f"{weekday_long}, {month_long} {day_str}, {year} {time_12}"
        fmt2 = f"{month_long} {day_str}, {year} {time_12}"
        patterns.update([fmt1, fmt2])

    matches = []
    async for msg in channel.history(limit=400):
        text = (msg.content or "").strip()
        if any(p in text for p in patterns):
            matches.append(msg)
    matches.sort(key=lambda m: m.created_at, reverse=False)
    return matches

async def post_todays_event_links(channel: discord.TextChannel):
    """Posts today's links with @Events mention and includes manual events from text posts."""
    if not channel:
        print("❌ post_todays_event_links: No channel provided.")
        return
    async for msg in channel.history(limit=50):
        if msg.author == bot.user and msg.id != current_schedule_message_id:
            try:
                await msg.delete()
            except Exception:
                pass

    today = datetime.now(CST).date()
    guild_events = channel.guild.scheduled_events

    todays_discord_events = [event for event in guild_events if event.start_time.astimezone(CST).date() == today]

    events_role = discord.utils.get(channel.guild.roles, name="Events")
    role_mention = events_role.mention if events_role else "@Events"

    times_to_match = [e.start_time for e in todays_discord_events]
    if not times_to_match:
        for h in (0, 12, 15, 18, 20):
            times_to_match.append(datetime.combine(today, time(hour=h, minute=0, tzinfo=CST)))

    manual_posts = await find_manual_event_posts_for_times(channel, times_to_match)

    if not todays_discord_events and not manual_posts:
        print("ℹ️ No Discord calendar events or manual posts found for today.")
        return

    header = "Today's Event:" if (len(todays_discord_events) + len(manual_posts)) == 1 else "Today's Events:"
    
    await channel.send(
        f"""{role_mention}\n{header}""",
        allowed_mentions=discord.AllowedMentions(roles=True)
    )

    for event in sorted(todays_discord_events, key=lambda e: e.start_time):
        await channel.send(event.url)

    for msg in manual_posts:
        try:
            await channel.send(msg.jump_url)
        except Exception:
            snippet = (msg.content or "").splitlines()[0][:100]
            await channel.send(f"(manual) {snippet}…")

async def update_schedule_message(channel: discord.TextChannel, force_new=False):
    """Posts or edits the weekly schedule message."""
    global current_schedule_message_id
    if not channel: return

    embed = await generate_schedule_embed()
    
    if force_new and current_schedule_message_id:
        try:
            old_message = await channel.fetch_message(current_schedule_message_id)
            await old_message.delete()
            print("🗑️ Deleted old schedule message.")
        except discord.NotFound:
            pass
        current_schedule_message_id = None

    if current_schedule_message_id:
        try:
            message = await channel.fetch_message(current_schedule_message_id)
            await message.edit(embed=embed)
            print("✅ Edited existing schedule message.")
        except discord.NotFound:
            current_schedule_message_id = None
    
    if not current_schedule_message_id:
        new_message = await channel.send(embed=embed)
        current_schedule_message_id = new_message.id
        print("✅ Posted new schedule message.")

def get_all_event_records():
    """Fetches all event records, adding a row number for identification."""
    try:
        all_values = events_sheet.get_all_values()
        if len(all_values) < 5: return []
        
        headers = all_values[3]
        data_rows = all_values[4:]
        
        records = []
        for i, row in enumerate(data_rows):
            record = {headers[j]: (row[j] if j < len(row) else "") for j in range(len(headers))}
            record['row_number'] = i + 5
            
            if any(val for key, val in record.items() if key != 'row_number'):
                records.append(record)
        return records
    except Exception as e:
        print(f"Error fetching and parsing event sheet data: {e}")
        return []

class AddEventModal(Modal):
    def __init__(self, event_type_str: str, is_international: bool = False, existing_data: Optional[dict] = None):
        super().__init__(title="Create/Edit Event")
        self.is_international = is_international
        self.existing_data = existing_data

        date_format_str = "D/M/YYYY" if is_international else "M/D/YYYY"
        date_placeholder = f"e.g., {'29/9/2025' if is_international else '9/29/2025'}"
        
        default_type = existing_data.get("Type of Event", event_type_str) if existing_data else event_type_str
        default_desc = existing_data.get("Event Description", "") if existing_data else ""
        default_owner = existing_data.get("Event Owner", "") if existing_data else ""
        default_comments = existing_data.get("Comments", "") if existing_data else ""
        
        default_dates = ""
        if existing_data:
            start_str = existing_data.get("Start Date", "")
            end_str = existing_data.get("End Date", "")
            if start_str and not is_international:
                try: start_str = datetime.strptime(start_str, "%d/%m/%Y").strftime("%m/%d/%Y")
                except ValueError: pass
            if end_str and not is_international:
                try: end_str = datetime.strptime(end_str, "%d/%m/%Y").strftime("%m/%d/%Y")
                except ValueError: pass

            if start_str and end_str and start_str != end_str:
                default_dates = f"{start_str} - {end_str}"
            else:
                default_dates = start_str

        self.field1 = TextInput(label="Type of Event", default=default_type)
        self.field2 = TextInput(label="Event Description", placeholder="e.g., Learner ToB", default=default_desc)
        self.field3 = TextInput(label="Event Owner (Optional)", placeholder="Leave blank to default to you", default=default_owner, required=False)
        self.field4 = TextInput(label=f"Date(s) ({date_format_str})", placeholder=f"{date_placeholder} or {date_placeholder} - {date_placeholder}", default=default_dates)
        self.field5 = TextInput(label="Comments (Optional)", style=discord.TextStyle.paragraph, default=default_comments, required=False)

        for item in [self.field1, self.field2, self.field3, self.field4, self.field5]: self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        dates_str = self.field4.value
        start_date_str, end_date_str = (dates_str.split(' - ', 1) + [None])[:2] if ' - ' in dates_str else (dates_str, dates_str)
        start_date_str = start_date_str.strip()
        end_date_str = end_date_str.strip() if end_date_str else start_date_str

        expected_format = "%d/%m/%Y" if self.is_international else "%m/%d/%Y"
        try:
            start_date_obj = datetime.strptime(start_date_str, expected_format)
            end_date_obj = datetime.strptime(end_date_str, expected_format)
        except ValueError:
            await interaction.followup.send(f"❌ **Invalid Date.** Use **{expected_format.upper()}** format.", ephemeral=True)
            return

        start_date_for_sheet = start_date_obj.strftime("%m/%d/%Y")
        end_date_for_sheet = end_date_obj.strftime("%m/%d/%Y")

        event_owner = self.field3.value.strip()
        if not event_owner:
            try:
                cell = rsn_sheet.find(str(interaction.user.id))
                event_owner = rsn_sheet.cell(cell.row, 4).value if cell else re.sub(r'^\W+', '', interaction.user.display_name)
            except Exception:
                event_owner = re.sub(r'^\W+', '', interaction.user.display_name)

        event_data = [
            self.field1.value, self.field2.value, event_owner, "", "",
            start_date_for_sheet, end_date_for_sheet, "", "", "", self.field5.value or ""
        ]

        try:
            action_verb = "created"
            if self.existing_data:
                row_num = self.existing_data['row_number']
                events_sheet.update(range_name=f"B{row_num}:L{row_num}", values=[event_data], value_input_option='USER_ENTERED')
                action_verb = "edited"
            else:
                next_row = len(events_sheet.col_values(2)) + 1
                events_sheet.update(range_name=f"B{next_row}:L{next_row}", values=[event_data], value_input_option='USER_ENTERED')

            confirm_embed = discord.Embed(title=f"✅ Event {action_verb.capitalize()}!", color=discord.Color.green())
            confirm_embed.add_field(name="Description", value=self.field2.value, inline=False)
            await interaction.followup.send(embed=confirm_embed, ephemeral=True)
        except Exception as e:
            print(f"Error processing event: {e}")
            await interaction.followup.send(f"❌ An error occurred while saving the event: {e}", ephemeral=True)

@tree.command(name="addevent", description="Add a new event to the schedule.")
@app_commands.checks.has_role(REQUIRED_ROLE_NAME)
@app_commands.describe(event_type="The type of event.")
@app_commands.choices(event_type=[
    app_commands.Choice(name=t, value=t) for t in ["BOTW", "SOTW", "Pet Roulette", "Sanguine Sunday", "Mass Event", "Bounty", "Large Event", "Castle Wars", "Wildy Altar", "Discord games", "Hide and seek", "Workshop", "Other Event"]
])
async def addevent(interaction: discord.Interaction, event_type: str):
    user_roles = {r.name for r in interaction.user.roles}
    is_international = bool(user_roles.intersection(INTERNATIONAL_TIMEZONES))
    await interaction.response.send_modal(AddEventModal(event_type, is_international))

@tree.command(name="editevent", description="Edit an existing event by its ID (row number).")
@app_commands.checks.has_role(REQUIRED_ROLE_NAME)
@app_commands.describe(event_id="The ID (row number) of the event to edit.")
async def editevent(interaction: discord.Interaction, event_id: int):
    try:
        if event_id < 5: raise ValueError("Invalid ID")
        
        row_data = events_sheet.row_values(event_id)
        if not any(row_data): raise ValueError("No event found")

        headers = events_sheet.row_values(4)
        event_dict = {headers[i]: (row_data[i] if i < len(row_data) else "") for i in range(len(headers))}
        event_dict['row_number'] = event_id

        user_roles = {r.name for r in interaction.user.roles}
        is_international = bool(user_roles.intersection(INTERNATIONAL_TIMEZONES))
        
        await interaction.response.send_modal(AddEventModal("", is_international, existing_data=event_dict))
    except (IndexError, ValueError, gspread.exceptions.APIError):
        await interaction.response.send_message(f"❌ Could not find event with ID `{event_id}`. Please check the sheet.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

class DeleteConfirmationView(View):
    def __init__(self, event_id: int):
        super().__init__(timeout=60)
        self.event_id = event_id

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        try:
            events_sheet.delete_rows(self.event_id)
            await interaction.response.edit_message(content=f"✅ Event ID `{self.event_id}` has been deleted.", view=None)
        except Exception as e:
            await interaction.response.edit_message(content=f"❌ An error occurred during deletion: {e}", view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content="Deletion canceled.", view=None)

@tree.command(name="deleteevent", description="Delete an event by its ID (row number).")
@app_commands.checks.has_role(REQUIRED_ROLE_NAME)
@app_commands.describe(event_id="The ID (row number) of the event to delete.")
async def deleteevent(interaction: discord.Interaction, event_id: int):
    try:
        if event_id < 5: raise ValueError("Invalid ID")
        row_data = events_sheet.row_values(event_id)
        if not any(row_data): raise ValueError("No event found")

        desc, owner, start_date = row_data[1], row_data[2], row_data[5]
        embed = discord.Embed(title="⚠️ Confirm Deletion", description="Are you sure you want to delete this event? This action cannot be undone.", color=discord.Color.red())
        embed.add_field(name="ID", value=f"`{event_id}`").add_field(name="Description", value=desc).add_field(name="Host", value=owner).add_field(name="Date", value=start_date)
        await interaction.response.send_message(embed=embed, view=DeleteConfirmationView(event_id), ephemeral=True)
    except (IndexError, ValueError, gspread.exceptions.APIError):
        await interaction.response.send_message(f"❌ Could not find an event with ID `{event_id}`.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)

@tree.command(name="schedule", description="Manually posts/updates the weekly event schedule.")
@app_commands.checks.has_role(REQUIRED_ROLE_NAME)
async def schedule(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
    if channel:
        await update_schedule_message(channel, force_new=True)
        await post_todays_event_links(channel)
        await interaction.followup.send(f"✅ Schedule has been posted in {channel.mention}!", ephemeral=True)
    else:
        await interaction.followup.send("⚠️ Event schedule channel not found.", ephemeral=True)

async def generate_schedule_embed():
    """Fetches event data and generates the weekly schedule embed."""
    try:
        all_events = get_all_event_records()
    except Exception as e:
        print(f"Could not fetch event records: {e}")
        return discord.Embed(title="Error", description="Could not fetch event data from the spreadsheet.", color=discord.Color.red())

    now, today = datetime.now(CST), datetime.now(CST).date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    daily_events = {start_of_week + timedelta(days=i): [] for i in range(7)}
    week_long_events = []

    for event in all_events:
        try:
            start_date = datetime.strptime(event["Start Date"], "%m/%d/%Y").date()
            end_date = datetime.strptime(event["End Date"], "%m/%d/%Y").date() if event.get("End Date") else start_date
            
            if (end_date - start_date).days >= 6 and start_date <= end_of_week and end_date >= start_of_week:
                week_long_events.append(event)
            else:
                d = start_date
                while d <= end_date:
                    if start_of_week <= d <= end_of_week:
                        daily_events[d].append(event)
                    d += timedelta(days=1)
        except (ValueError, KeyError):
            continue
    
    embed = discord.Embed(title=f"📅 Weekly Clan Schedule ({start_of_week:%b %d} - {end_of_week:%b %d})", color=discord.Color.gold())

    if week_long_events:
        value = "\n".join([f"• ||{e['row_number']}|| **{e['Event Description']}**・Hosted by {e['Event Owner']}" for e in week_long_events])
        embed.add_field(name="# Week-Long Events", value=value, inline=False)

    for i in range(7):
        current_date = start_of_week + timedelta(days=i)
        day_name = current_date.strftime("%A")
        
        day_lines = []
        day_events_for_day = sorted(daily_events.get(current_date, []), key=lambda x: x['Event Description'])
        
        if day_events_for_day:
            grouped_events = collections.defaultdict(lambda: {'hosts': [], 'ids': [], 'original_type': '', 'original_desc': ''})
            for event in day_events_for_day:
                e_type = event.get('Type of Event', '')
                desc = event.get('Event Description', 'No Description')
                key = (e_type.lower(), desc.lower())
                
                grouped_events[key]['hosts'].append(event.get('Event Owner', 'N/A'))
                grouped_events[key]['ids'].append(str(event.get('row_number', 'N/A')))

                if not grouped_events[key]['original_desc']:
                    grouped_events[key]['original_type'] = e_type
                    grouped_events[key]['original_desc'] = desc

            for key, data in grouped_events.items():
                e_type = data['original_type']
                desc = data['original_desc']

                if len(data['hosts']) > 1:
                    hosts_str = ' & '.join(sorted(list(set(data['hosts']))))
                else:
                    hosts_str = data['hosts'][0] if data['hosts'] else 'N/A'

                ids_str = ", ".join(sorted(list(set(data['ids']))))
                
                line_base = f"**{e_type}**: {desc}" if e_type and e_type.lower() != desc.lower() else f"**{desc}**"
                line = f"• ||{ids_str}|| {line_base}・Hosted by {hosts_str}"
                day_lines.append(line)

        embed.add_field(name=day_name, value="\n".join(day_lines) if day_lines else "- No events planned.", inline=False)

    embed.set_footer(text=f"Last Updated: {now:%m/%d/%Y %I:%M %p CST}")
    return embed

@tasks.loop(minutes=10)
async def check_sheet_for_updates():
    """Periodically checks the sheet for changes and posts a NEW schedule if changed."""
    global last_known_sheet_data
    try:
        channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
        if not channel:
            return

        current_data = get_all_event_records()
        
        if last_known_sheet_data is None:
            last_known_sheet_data = current_data
            return

        if current_data != last_known_sheet_data:
            print("📝 Sheet change detected, posting fresh schedule...")
            await update_schedule_message(channel, force_new=True)
            last_known_sheet_data = current_data
            
            await post_todays_event_links(channel)

    except Exception as e:
        print(f"Error in check_sheet_for_updates: {e}")

@tasks.loop(time=time(hour=0, minute=0, tzinfo=CST))
async def weekly_schedule_post():
    """Posts a fresh schedule embed only on Mondays at 12:00 AM CST."""
    if datetime.now(CST).weekday() == 0:
        channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
        if channel:
            print("📅 It's Monday! Posting weekly schedule...")
            await update_schedule_message(channel, force_new=True)
    else:
        print(f"ℹ️ Skipping daily post (Today is {datetime.now(CST).strftime('%A')})")

@tasks.loop(time=time(hour=0, minute=1, tzinfo=CST))
async def daily_event_link_post():
    """Posts links for the current day's events every day at 12:01 AM CST."""
    channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
    if channel:
        await post_todays_event_links(channel)

@bot.event
async def on_ready():
    global last_known_sheet_data, current_schedule_message_id
    print(f"✅ Logged in as {bot.user}")
    
    if not check_sheet_for_updates.is_running():
        check_sheet_for_updates.start()
    if not weekly_schedule_post.is_running():
        weekly_schedule_post.start()
    if not daily_event_link_post.is_running():
        daily_event_link_post.start()
    
    if "bingo_cog" not in bot.extensions:
        try:
            await bot.load_extension("bingo_cog")
            print("✅ Loaded extension: bingo_cog")
        except Exception as e:
            print(f"❌ Failed to load extension: bingo_cog - {e}")
            traceback.print_exc()
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Command sync failed: {e}")

    channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
    if channel:
        print(f"Searching for existing schedule message in {channel.name}...")
        try:
            async for message in channel.history(limit=50):
                if message.author == bot.user and message.embeds and message.embeds[0].title and "Weekly Clan Schedule" in message.embeds[0].title:
                    current_schedule_message_id = message.id
                    print(f"✅ Found existing schedule message: {message.id}")
                    break
            if not current_schedule_message_id:
                print("ℹ️ No existing schedule message found. A new one will be posted by the daily task or on the next sheet update.")
                
        except Exception as e:
            print(f"❌ Error searching for existing schedule message: {e}")

        last_known_sheet_data = get_all_event_records()
    else:
        print(f"⚠️ Could not find EVENT_SCHEDULE_CHANNEL_ID ({EVENT_SCHEDULE_CHANNEL_ID}) on startup.")


bot.run(os.getenv("BOT_TOKEN"))


