import os
import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone
import json
import asyncio
import random
from discord.ui import Modal, TextInput
from discord import app_commands, ui, Interaction, Member, TextStyle
from typing import List, Optional
from discord import ui, Interaction, Member
from typing import Optional
from discord import SelectOption, Attachment
from discord import ui, Interaction, SelectOption, TextStyle, Attachment, Member

# ========== CONFIG ==========
SPREADSHEET_ID = "1OVC8HImUpoh2keU-h2v_b2gFDa4zyfWsaJxBWRoSJ08"
TEAM_ROLES = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5"]
COMMAND_CHANNEL_ID = 1401523115808526438
REVIEW_CHANNEL_ID = 1401510165764771950
LOG_CHANNEL_ID = 1401514384001601607
REQUIRED_ROLE_NAME = "Event Staff"
EVENT_CAPTAIN_ROLE_NAME = "Event Captain"

# ========== DISCORD SETUP ==========
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ========== GOOGLE SHEETS SETUP ==========
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

credentials_dict = {
    "type": os.getenv("type"),
    "project_id": os.getenv("project_id"),
    "private_key_id": os.getenv("private_key_id"),
    "private_key": os.getenv("private_key").replace("\\n", "\n"),
    "client_email": os.getenv("client_email"),
    "client_id": os.getenv("client_id"),
    "auth_uri": os.getenv("auth_uri"),
    "token_uri": os.getenv("token_uri"),
    "auth_provider_x509_cert_url": os.getenv("auth_provider_x509_cert_url"),
    "client_x509_cert_url": os.getenv("client_x509_cert_url"),
    "universe_domain": os.getenv("universe_domain")
}

creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client_g = gspread.authorize(creds)
sheet = client_g.open_by_key(SPREADSHEET_ID)
command_log = sheet.worksheet("Command Log")
team_data_sheet = sheet.worksheet("TeamData")
chest_sheet = sheet.worksheet("ChestCards")
chance_sheet = sheet.worksheet("ChanceCards")
CHEST_TILES = [2, 17, 33]
CHANCE_TILES = [7, 22, 36]
drop_log_sheet = sheet.worksheet("DropLog")

# ---------------------------
# 🔹 Boss-Drop Mapping
# ---------------------------

boss_drops = {
    "Araxxor": ["Noxious pommel", "Noxious point", "Noxious blade", "Araxyte fang", "Araxyte head", "Jar of venom", "Nid"],
    "Barrows": ["Ahrim's hood", "Ahrim's robetop", "Ahrim's robeskirt", "Ahrim's staff", "Karil's coif", "Karil's leathertop", "Karil's leatherskirt", "Karil's crossbow", "Dharok's helm", "Dharok's platebody", "Dharok's platelegs", "Dharok's greataxe", "Guthan's helm", "Guthan's platebody", "Guthan's chainskirt", "Guthan's warspear", "Torag's helm", "Torag's platebody", "Torag's platelegs", "Torag's hammers", "Verac's helm", "Verac's brassard", "Verac's plateskirt", "Verac's flail"],
    "Callisto": ["Callisto cub", "Tyrannical ring", "Dragon pickaxe", "Dragon 2h sword", "Claws of callisto", "Voidwaker hilt"],
    "Cerberus": ["Hellpuppy", "Eternal crystal", "Pegasian crystal", "Primordial crystal", "Jar of souls", "Smouldering stone"],
    "Chaos Fanatic": ["Pet chaos elemental", "Odium shard 1", "Malediction shard 1"],
    "Chambers of Xeric": ["Dexterous prayer scroll", "Arcane prayer scroll", "Twisted buckler", "Dragon hunter crossbow", "Dinh's bulwark", "Ancestral hat", "Ancestral robe top", "Ancestral robe bottom", "Dragon claws", "Elder maul", "Kodai insignia", "Twisted bow", "Olmlet", "Twisted ancestral colour kit", "Metamorphic dust"],
    "Colosseum": ["Dizana's quiver (uncharged)", "Sunfire fanatic cuirass", "Sunfire fanatic chausses", "Sunfire fanatic helm", "Echo crystal", "Tonalztics of ralos (uncharged)"],
    "Commander Zilyana": ["Pet zilyana", "Armadyl crossbow", "Saradomin hilt", "Saradomin sword", "Saradomin's light"],
    "Crazy Archaeologist": ["Odium shard 2", "Malediction shard 2", "Fedora"],
    "Doom of Mokhaiotl": ["Dom", "Avernic treads", "Eye of ayak (uncharged)", "Mokhaiotl cloth"],
    "Duke Sucellus": ["Baron", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Magus vestige", "Eye of the duke", "Ice quartz"],
    "Gauntlet": ["Youngllef", "Crystal weapon seed", "Crystal armour seed", "Enhanced crystal weapon seed"],
    "General Graardor": ["Pet general graardor", "Bandos hilt", "Bandos chestplate", "Bandos tassets", "Bandos boots"],
    "Hueycoatl": ["Huberte", "Dragon hunter wand", "Hueycoatl hide", "Tome of earth (empty)"],
    "Kree'arra": ["Pet kree'arra", "Armadyl helmet", "Armadyl chestplate", "Armadyl chainskirt", "Armadyl hilt"],
    "K'ril Tsutsaroth": ["Pet K'ril Tsutsaroth", "Zamorakian spear", "Staff of the dead", "Zamorak hilt", "Steam battlestaff"],
    "Moons of Peril": ["Eclipse atlatl", "Eclipse moon helm", "Eclipse moon chestplate", "Eclipse moon tassets", "Dual macuahuitl", "Blood moon helm", "Blood moon chestplate", "Blood moon tassets", "Blue moon spear", "Blue moon helm", "Blue moon chestplate", "Blue moon tassets"],
    "Nightmare": ["Little nightmare", "Nightmare staff", "Inquisitor's great helm", "Inquisitor's hauberk", "Inquisitor's plateskirt", "Inquisitor's mace", "Eldritch orb", "Harmonised orb", "Volatile orb", "Parasitic egg", "Jar of dreams", "Slepey tablet"],
    "Nex": ["Nexling", "Ancient hilt", "Nihil horn", "Zaryte vambraces", "Torva full helm (damaged)", "Torva platebody (damaged)", "Torva platelegs (damaged)"],
    "Phantom Muspah": ["Muphin", "Venator shard", "Ancient icon"],
    "Scorpia": ["Scorpia's Offspring", "Malediction shard 3", "Odium shard 3"],
    "The Leviathan": ["Lil'viathan", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Venator vestige", "Leviathan's lure", "Smoke quartz"],
    "The Whisperer": ["Wisp", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Bellator vestige", "Siren's staff", "Shadow quartz"],
    "Theatre of Blood": ["Lil' zik", "Avernic defender hilt", "Ghrazi rapier", "Sanguinesti staff (uncharged)", "Justiciar faceguard", "Justiciar chestguard", "Justiciar legguards", "Scythe of vitur (uncharged)", "Holy ornament kit", "Sanguine ornament kit", "Sanguine dust"],
    "Tombs of Amascut": ["Tumeken's Guardian", "Masori mask", "Masori body", "Masori chaps", "Lightbearer", "Osmumten's fang", "Elidinis' ward", "Tumeken's shadow (uncharged)", "Cursed phalanx"],
    "Vardorvis": ["Butch", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Ultor vestige", "Executioner's axe head", "Blood quartz"],
    "Venenatis": ["Venenatis spiderling", "Fangs of venenatis", "Dragon 2h sword", "Dragon pickaxe", "Voidwaker gem", "Treasonous ring"],
    "Vet'ion": ["Vet'ion jr.", "Skull of vet'ion", "Dragon 2h sword", "Dragon pickaxe", "Voidwaker blade", "Ring of the gods", "Skeleton champion scroll"],
    "Yama": ["Soulflame horn", "Oathplate helm", "Oathplate chest", "Oathplate legs", "Oathplate shards", "Dossier"],
    "Zulrah": ["Pet snakeling", "Tanzanite mutagen", "Magma mutagen", "Jar of swamp", "Tanzanite fang", "Magic fang", "Serpentine visage", "Uncut onyx"]
}

# ========= Helper Functions =========
def log_command(player_name, command, args_dict):
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        args_json = json.dumps(args_dict)
        command_log.append_row([player_name, command, args_json, timestamp, "no"])
        print(f"✅ Logged {command} for {player_name}: {args_json}")
    except Exception as e:
        print(f"❌ Error logging command: {e}")

def get_team(member: discord.Member) -> Optional[str]:
    for role in member.roles:
        if role.name in TEAM_ROLES:
            return role.name
    return None

def has_event_captain_role(member: discord.Member) -> bool:
    return any(role.name == EVENT_CAPTAIN_ROLE_NAME for role in member.roles)

def has_event_staff_role(member: discord.Member) -> bool:
    return any(role.name == REQUIRED_ROLE_NAME for role in member.roles)

def increment_rolls_available(team_name: str):
    try:
        records = team_data_sheet.get_all_records()
        for idx, record in enumerate(records, start=2):
            if record.get("Team") == team_name:
                headers = team_data_sheet.row_values(1)
                if "Rolls Available" not in headers:
                    print("❌ 'Rolls Available' column not found.")
                    return
                col_index = headers.index("Rolls Available") + 1
                current_rolls = team_data_sheet.cell(idx, col_index).value
                current_rolls_int = int(current_rolls) if current_rolls and current_rolls.isdigit() else 0
                team_data_sheet.update_cell(idx, col_index, current_rolls_int + 1)
                print(f"✅ Incremented rolls for {team_name} to {current_rolls_int + 1}")
                return
    except Exception as e:
        print(f"❌ Error incrementing rolls: {e}")

def decrement_rolls_available(team_name: str):
    try:
        records = team_data_sheet.get_all_records()
        for idx, record in enumerate(records, start=2):
            if record.get("Team") == team_name:
                headers = team_data_sheet.row_values(1)
                if "Rolls Available" not in headers:
                    print("❌ 'Rolls Available' column not found.")
                    return
                col_index = headers.index("Rolls Available") + 1
                current_rolls = team_data_sheet.cell(idx, col_index).value
                current_rolls_int = int(current_rolls) if current_rolls and current_rolls.isdigit() else 0
                new_val = max(0, current_rolls_int - 1)
                team_data_sheet.update_cell(idx, col_index, new_val)
                print(f"✅ Decremented rolls for {team_name}: {current_rolls_int} → {new_val}")
                return
    except Exception as e:
        print(f"❌ Error decrementing rolls: {e}")


# ======= Modal (for rejection) =======
class RejectModal(ui.Modal, title="Reject Drop Submission"):
    reason = ui.TextInput(
        label="Reason for rejection",
        style=discord.TextStyle.paragraph,
        placeholder="Explain why the drop is rejected...",
        required=True,
        max_length=1000
    )

    def __init__(self, review_message: discord.Message, submitter: discord.Member):
        super().__init__()
        self.review_message = review_message
        self.submitter = submitter

    async def on_submit(self, interaction: discord.Interaction):
        try:
            log_chan = interaction.client.get_channel(LOG_CHANNEL_ID)
            if log_chan:
                await log_chan.send(
                    f"❌ Drop submission rejected for {self.submitter.mention} by {interaction.user.mention}.\n"
                    f"**Reason:** {self.reason.value}"
                )
            else:
                print(f"❌ RejectModal: Log channel {LOG_CHANNEL_ID} not found.")

            embed = self.review_message.embeds[0]
            embed.color = discord.Color.red()

            # Prevent duplicate "[Rejected]" tags
            if "[Rejected]" not in embed.title:
                embed.title += " [Rejected]"

            # Add or update the rejection reason field
            existing_field = next((i for i, field in enumerate(embed.fields) if field.name == "Rejection Reason"), None)
            if existing_field is not None:
                embed.set_field_at(existing_field, name="Rejection Reason", value=self.reason.value, inline=False)
            else:
                embed.add_field(name="Rejection Reason", value=self.reason.value, inline=False)

            await self.review_message.edit(embed=embed, view=None)
            await interaction.response.send_message("✅ Rejection noted.", ephemeral=True)

        except Exception as e:
            print(f"❌ Error in RejectModal: {e}")
            await interaction.response.send_message(f"Error processing rejection: {e}", ephemeral=True)


# ======= Unified Drop Logging =======
def log_drop_to_sheet(submitted_for: str, team: str, boss: str, drop: str, verified_by: str, screenshot: str):
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        drop_log_sheet.append_row([
            submitted_for,   # Submitted For
            team,            # Team
            boss,            # Boss
            drop,            # Drop Received
            verified_by,     # Verified By
            screenshot,      # Screenshot URL
            timestamp        # Timestamp
        ])
        print(f"✅ Logged drop for {submitted_for} ({boss} - {drop})")
    except Exception as e:
        print(f"❌ Error writing to DropLog sheet: {e}")


# ======= DropReviewButtons view (approve/reject) =======
class DropReviewButtons(ui.View):
    def __init__(self, submitted_user, drop, image_url, submitting_user, team_mention, boss):
        super().__init__(timeout=None)
        self.submitted_user = submitted_user
        self.drop = drop
        self.image_url = image_url
        self.submitting_user = submitting_user
        self.team_mention = team_mention
        self.boss = boss
        self.message = None
        self.current_reviewer = None

        # Disable approve/reject buttons until someone starts reviewing
        self.approve_button.disabled = True
        self.reject_button.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not has_event_staff_role(interaction.user):
            await interaction.response.send_message("You do not have permission to use these buttons.", ephemeral=True)
            return False

        if self.current_reviewer and interaction.user != self.current_reviewer:
            await interaction.response.send_message(
                f"This submission is currently being reviewed by {self.current_reviewer.mention}. Please wait.",
                ephemeral=True,
            )
            return False

        return True

    @ui.button(label="Review", style=discord.ButtonStyle.primary, custom_id="review_drop")
    async def review_button(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_reviewer == interaction.user:
            # Stop reviewing
            self.current_reviewer = None
            button.label = "Review"
            self.approve_button.disabled = True
            self.reject_button.disabled = True
            content = "Stopped reviewing."
        else:
            # Start reviewing
            self.current_reviewer = interaction.user
            button.label = f"Reviewing: {interaction.user.display_name}"
            self.approve_button.disabled = False
            self.reject_button.disabled = False
            content = "You are now reviewing this submission."

        embed = self.message.embeds[0]
        embed.set_field_at(
            0,
            name="Review Status",
            value=(f"Currently being reviewed by {interaction.user.mention}"
                   if self.current_reviewer else "Not currently being reviewed"),
            inline=False,
        )

        await self.message.edit(embed=embed, view=self)
        await interaction.response.send_message(content, ephemeral=True)

    @ui.button(label="Approve Drop", style=discord.ButtonStyle.success, custom_id="approve_drop")
    async def approve_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.current_reviewer:
            await interaction.response.send_message("You must start reviewing before approving.", ephemeral=True)
            return

        try:
            embed = self.message.embeds[0]
            embed.color = discord.Color.green()
            if "[Approved]" not in embed.title:
                embed.title += " [Approved]"
            embed.set_field_at(0, name="Reviewed By", value=interaction.user.mention, inline=False)

            # Instead of editing the message, delete it
            await self.message.delete()

            # Send the approval info to the log channel only
            log_chan = bot.get_channel(LOG_CHANNEL_ID)
            if log_chan:
                mention = self.team_mention or self.submitted_user.mention or self.submitting_user.mention
                await log_chan.send(content=f"{mention} Drop submission approved by {interaction.user.mention}.", embed=embed)
                print(f"✅ Sent approval to DropLog ({log_chan.name})")
            else:
                print(f"❌ DropLog channel {LOG_CHANNEL_ID} not found")

            # Log to spreadsheet
            team_name = get_team(self.submitted_user) or "*No team*"
            log_drop_to_sheet(
                submitted_for=str(self.submitted_user),
                team=team_name,
                boss=self.boss,
                drop=self.drop,
                verified_by=interaction.user.name,
                screenshot=self.image_url
            )

            # 🔹 Only increment if player is on correct tile for this boss
            if team_name and team_name != "*No team*":
                try:
                    records = team_data_sheet.get_all_records()
                    current_tile = None
                    for record in records:
                        if record.get("Team") == team_name:
                            current_tile = int(record.get("Position", 0))
                            break

                    # Map tiles to bosses
                    tile_boss_map = {
                        1: ["Zulrah"],
                        3: ["General Graardor", "K'ril Tsutsaroth", "Kree'arra", "Commander Zilyana"],
                        4: ["Vet'ion", "Venenatis", "Callisto"],
                        5: ["The Whisperer"],
                        6: ["Tombs of Amascut"],
                        8: ["Theatre of Blood"],
                        9: ["Chambers of Xeric"],
                        10: ["Gauntlet", "Nex"],
                        11: ["Barrows"],
                        13: ["Moons of Peril"],
                        14: ["Nightmare"],
                        15: ["The Leviathan"],
                        16: ["Yama"],
                        18: ["Scorpia", "Chaos Fanatic", "Crazy Archaeologist"],
                        19: ["Cerberus"],
                        21: ["Tombs of Amascut"],
                        23: ["Theatre of Blood"],
                        24: ["Chambers of Xeric"],
                        25: ["Vardorvis"],
                        26: ["Hueycoatl"],
                        27: ["Colosseum"],
                        29: ["Doom of Mokhaiotl"],
                        31: ["Tombs of Amascut"],
                        32: ["Theatre of Blood"],
                        34: ["Chambers of Xeric"],
                        35: ["Duke Sucellus"],
                        37: ["Phantom Muspah"],
                        39: ["Araxxor"]
                    }

                    bosses_for_tile = tile_boss_map.get(current_tile, [])
                    if self.boss in bosses_for_tile:
                        increment_rolls_available(team_name)
                        print(f"✅ Roll granted: Team {team_name} on tile {current_tile} ({self.boss})")
                    else:
                        print(f"ℹ️ No roll granted: Team {team_name} on tile {current_tile}, drop boss {self.boss} not valid here.")
                except Exception as e:
                    print(f"❌ Error checking tile before granting roll: {e}")


            await interaction.response.send_message("✅ Drop approved and logged.", ephemeral=True)

        except Exception as e:
            print(f"❌ Error in approve_button: {e}")
            await interaction.response.send_message(f"Error approving drop: {e}", ephemeral=True)

    @ui.button(label="Reject Drop", style=discord.ButtonStyle.danger, custom_id="reject_drop")
    async def reject_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.current_reviewer:
            await interaction.response.send_message("You must start reviewing before rejecting.", ephemeral=True)
            return

        await interaction.response.send_modal(RejectModal(self.message, self.submitted_user))


# ======= Helper to get team from member roles =======
def get_team(member: discord.Member) -> Optional[str]:
    for role in member.roles:
        if role.name.startswith("Team "):
            return role.name
    return None


# ======= Your existing commands untouched (patched to log team) =======
@bot.tree.command(name="roll", description="Roll a dice (1-6)")
async def roll(interaction: discord.Interaction):
    team_name = get_team(interaction.user) or "*No team*"

    # 🔹 Check Rolls Available from the sheet
    records = team_data_sheet.get_all_records()
    rolls_available = 0
    for record in records:
        if record.get("Team") == team_name:
            rolls_available = int(record.get("Rolls Available", 0) or 0)
            break

    if rolls_available <= 0:
        await interaction.response.send_message(
            "❌ Your team has no rolls available right now.",
            ephemeral=True
        )
        return

    # ✅ Only roll if rolls are available
    result = random.randint(1, 1)
    await interaction.response.send_message(f"🎲 You rolled a {result}.")
    log_command(
        interaction.user.name,
        "/roll",
        {
            "team": team_name,
            "roll": result
        }
    )



@bot.tree.command(name="customize", description="Tell the spreadsheet you want to customize your team")
async def customize(interaction: discord.Interaction):
    if interaction.channel_id != COMMAND_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ You can only use this command in the designated command channel.", ephemeral=True
        )
        return

    team_name = get_team(interaction.user) or "*No team*"
    log_command(
        interaction.user.name,
        "/customize",
        {
            "team": team_name
        }
    )
    await interaction.response.send_message(
        "✅ Your customization request has been logged to the spreadsheet.", ephemeral=True
    )


# ======= BossSelect Modal + View =======
class BossSelectModal(ui.Modal, title="Select Boss"):
    def __init__(self, submitting_user: discord.Member, submitted_for: discord.Member, screenshot_url: str):
        super().__init__()
        self.submitting_user = submitting_user
        self.submitted_for = submitted_for
        self.screenshot_url = screenshot_url

        self.bosses = list(boss_drops.keys())
        self.page_size = 25
        self.current_page = 0

        self.boss_dropdown = ui.Select(
            placeholder="Select the boss",
            options=self.get_boss_options(),
            min_values=1,
            max_values=1,
        )
        self.boss_dropdown.callback = self.boss_selected
        self.add_item(self.boss_dropdown)

        self.prev_button = ui.Button(label="Previous", style=discord.ButtonStyle.secondary)
        self.next_button = ui.Button(label="Next", style=discord.ButtonStyle.secondary)
        self.prev_button.callback = self.prev_page
        self.next_button.callback = self.next_page
        self.add_item(self.prev_button)
        self.add_item(self.next_button)

        self.update_nav_buttons()

    def get_boss_options(self):
        start = self.current_page * self.page_size
        end = start + self.page_size
        return [discord.SelectOption(label=boss) for boss in self.bosses[start:end]]

    def update_nav_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = (self.current_page + 1) * self.page_size >= len(self.bosses)

    async def prev_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.boss_dropdown.options = self.get_boss_options()
            self.update_nav_buttons()
            await interaction.response.edit_modal(self)

    async def next_page(self, interaction: discord.Interaction):
        if (self.current_page + 1) * self.page_size < len(self.bosses):
            self.current_page += 1
            self.boss_dropdown.options = self.get_boss_options()
            self.update_nav_buttons()
            await interaction.response.edit_modal(self)

    async def boss_selected(self, interaction: discord.Interaction):
        selected_boss = self.boss_dropdown.values[0]
        await interaction.response.send_message(
            content=f"Selected boss: **{selected_boss}**. Now select the drop:",
            view=DropSelectView(
                submitting_user=self.submitting_user,
                submitted_for=self.submitted_for,
                screenshot_url=self.screenshot_url,
                boss=selected_boss
            ),
            ephemeral=True
        )


class BossSelectView(ui.View):
    def __init__(self, submitting_user: discord.Member, submitted_for: discord.Member, screenshot_url: str):
        super().__init__(timeout=180)
        self.submitting_user = submitting_user
        self.submitted_for = submitted_for
        self.screenshot_url = screenshot_url

        self.bosses = list(boss_drops.keys())
        self.page_size = 25
        self.current_page = 0

        self.boss_dropdown = ui.Select(
            placeholder="Select the boss",
            options=self.get_boss_options(),
            min_values=1,
            max_values=1,
        )
        self.boss_dropdown.callback = self.boss_selected
        self.add_item(self.boss_dropdown)

        self.prev_button = ui.Button(label="Previous", style=discord.ButtonStyle.secondary)
        self.next_button = ui.Button(label="Next", style=discord.ButtonStyle.secondary)
        self.prev_button.callback = self.prev_page
        self.next_button.callback = self.next_page
        self.add_item(self.prev_button)
        self.add_item(self.next_button)

        self.update_nav_buttons()

    def get_boss_options(self):
        start = self.current_page * self.page_size
        end = start + self.page_size
        return [discord.SelectOption(label=boss) for boss in self.bosses[start:end]]

    def update_nav_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = (self.current_page + 1) * self.page_size >= len(self.bosses)

    async def prev_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.boss_dropdown.options = self.get_boss_options()
            self.update_nav_buttons()
            await interaction.response.edit_message(view=self)

    async def next_page(self, interaction: discord.Interaction):
        if (self.current_page + 1) * self.page_size < len(self.bosses):
            self.current_page += 1
            self.boss_dropdown.options = self.get_boss_options()
            self.update_nav_buttons()
            await interaction.response.edit_message(view=self)

    async def boss_selected(self, interaction: discord.Interaction):
        selected_boss = self.boss_dropdown.values[0]
        await interaction.response.edit_message(
            content=f"Selected boss: **{selected_boss}**. Now select the drop:",
            embed=None,
            view=DropSelectView(
                submitting_user=self.submitting_user,
                submitted_for=self.submitted_for,
                screenshot_url=self.screenshot_url,
                boss=selected_boss,
            ),
        )


# ======= DropSelect + DropSelectView =======
class DropSelect(ui.Select):
    def __init__(self, submitting_user: discord.Member, submitted_for: discord.Member, screenshot_url: str, boss: str):
        self.submitting_user = submitting_user
        self.submitted_for = submitted_for
        self.screenshot_url = screenshot_url
        self.boss = boss

        options = [discord.SelectOption(label=drop) for drop in boss_drops[boss]]
        super().__init__(placeholder=f"Select the drop from {boss}", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected_drop = self.values[0]

        embed = discord.Embed(title=f"{self.boss} Drop Submission", colour=discord.Colour.blurple())
        embed.add_field(name="Submitted For", value=f"{self.submitted_for.mention} ({self.submitted_for.id})", inline=False)
        embed.add_field(name="Drop Received", value=selected_drop, inline=False)
        embed.add_field(name="Submitted By", value=f"{self.submitting_user.mention} ({self.submitting_user.id})", inline=False)
        embed.set_image(url=self.screenshot_url)

        review_channel = bot.get_channel(REVIEW_CHANNEL_ID)
        if not review_channel:
            print(f"❌ Review channel {REVIEW_CHANNEL_ID} not found")
            await interaction.response.send_message("❌ Review channel not found.", ephemeral=True)
            return

        team_role = get_team(self.submitted_for)
        team_mention = (
            next((role.mention for role in self.submitted_for.roles if role.name == team_role), "*No team*")
            if team_role else "*No team*"
        )

        view = DropReviewButtons(
            submitted_user=self.submitted_for,
            drop=selected_drop,
            image_url=self.screenshot_url,
            submitting_user=self.submitting_user,
            team_mention=team_mention,
            boss=self.boss,
        )

        team_name = get_team(self.submitted_for) or "*No team*"
        current_tile = None
        records = team_data_sheet.get_all_records()
        for record in records:
            if record.get("Team") == team_name:
                current_tile = int(record.get("Position", 0))
                break

        tile_boss_map = {
            1: ["Zulrah"],
            3: ["General Graardor", "K'ril Tsutsaroth", "Kree'arra", "Commander Zilyana"],
            4: ["Vet'ion", "Venenatis", "Callisto"],
            5: ["The Whisperer"],
            6: ["Tombs of Amascut"],
            8: ["Theatre of Blood"],
            9: ["Chambers of Xeric"],
            10: ["Gauntlet", "Nex"],
            11: ["Barrows"],
            13: ["Moons of Peril"],
            14: ["Nightmare"],
            15: ["The Leviathan"],
            16: ["Yama"],
            18: ["Scorpia", "Chaos Fanatic", "Crazy Archaeologist"],
            19: ["Cerberus"],
            21: ["Tombs of Amascut"],
            23: ["Theatre of Blood"],
            24: ["Chambers of Xeric"],
            25: ["Vardorvis"],
            26: ["Hueycoatl"],
            27: ["Colosseum"],
            29: ["Doom of Mokhaiotl"],
            31: ["Tombs of Amascut"],
            32: ["Theatre of Blood"],
            34: ["Chambers of Xeric"],
            35: ["Duke Sucellus"],
            37: ["Phantom Muspah"],
            39: ["Araxxor"]
        }

        bosses_for_tile = tile_boss_map.get(current_tile, [])
        if self.boss not in bosses_for_tile:
            await interaction.response.edit_message(
                content=f"❌ Invalid drop: **{self.boss}** is not valid for your team's current tile ({current_tile}).",
                embed=None,
                view=None
            )
            return

        sent_msg = await review_channel.send(embed=embed, view=view)
        view.message = sent_msg
        print(f"✅ Sent drop submission to review channel ({review_channel.name})")

        await interaction.response.edit_message(
            content=f"✅ Drop submission for **{self.boss} - {selected_drop}** sent for review.",
            embed=None,
            view=None,
        )

        log_command(
            self.submitting_user.name,
            "/submitdrop",
            {
                "boss": self.boss,
                "drop": selected_drop,
                "screenshot": self.screenshot_url,
                "submitted_for": str(self.submitted_for),
            },
        )


class DropSelectView(ui.View):
    def __init__(self, submitting_user: discord.Member, submitted_for: discord.Member, screenshot_url: str, boss: str):
        super().__init__(timeout=180)
        self.add_item(DropSelect(submitting_user, submitted_for, screenshot_url, boss))


@bot.tree.command(name="submitdrop", description="Submit a boss drop for review")
@discord.app_commands.describe(
    screenshot="Attach a screenshot of the drop",
    submitted_for="User you are submitting the drop for (optional)",
)
async def submitdrop(interaction: discord.Interaction, screenshot: discord.Attachment, submitted_for: Optional[discord.Member] = None):
    if interaction.channel_id != COMMAND_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ You can only use this command in the designated command channel.", ephemeral=True
        )
        return

    if submitted_for is None:
        submitted_for = interaction.user

    await interaction.response.send_message(
        content=f"Submitting drop for {submitted_for.display_name}. Select the boss you received the drop from:",
        view=BossSelectView(interaction.user, submitted_for, screenshot.url),
        ephemeral=True
    )

#======================================================================

def get_team(member: discord.Member) -> Optional[str]:
    for role in member.roles:
        if role.name in TEAM_ROLES:
            return role.name
    return None

async def team_receives_card(team_name: str, card_type: str, log_channel):
    print(f"[DEBUG] Assigning {card_type} card to {team_name}...")

    sheet_name = f"{card_type}Cards"
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        rows = sheet.get_all_records()
        print(f"[DEBUG] Loaded {len(rows)} rows from {sheet_name}")
    except Exception as e:
        print(f"[ERROR] Failed to load sheet {sheet_name}: {e}")
        return

    # Shuffle and pick a random card not yet held by this team
    random.shuffle(rows)
    for idx, row in enumerate(rows, start=2):
        held_by = row.get("Held By Team", "")
        if team_name in held_by:
            continue  # Skip if already held

        # Add team to the Held By Team column
        updated_teams = (held_by + f",{team_name}").strip(",") if held_by else team_name
        print(f"[DEBUG] Assigning card '{row.get('Name')}' at row {idx} to {team_name}")
        sheet.update_cell(idx, 3, updated_teams)  # Assuming Held By Team is col 3

        # Log to Discord
        card_name = row.get("Name")
        card_text = row.get("Card Text")

        embed = discord.Embed(
            title=f"{card_type} Card Drawn 🎴",
            description=f"**{team_name}** pulled **{card_name}**!\n> {card_text}",
            color=discord.Color.gold() if card_type == "Chest" else discord.Color.blue()
        )
        await log_channel.send(embed=embed)
        return

    print(f"[WARN] No available {card_type} cards to assign to {team_name}")


def get_held_cards(sheet, team_name: str):
    data = sheet.get_all_values()
    cards = []
    for idx, row in enumerate(data[1:], start=2):
        if len(row) < 4:
            continue
        held_raw = row[2].strip()
        held = [t.strip() for t in held_raw.split(",")] if held_raw else []
        if team_name in held:
            cards.append({
                "row": idx,
                "name": row[0],
                "text": row[1],
                "wildcard": row[3]
            })
    return cards

async def update_team_position(team_data_sheet, team_name: str, move_by: int, bot) -> int:
    records = team_data_sheet.get_all_records()
    for idx, record in enumerate(records, start=2):
        if record.get("Team") == team_name:
            current_pos = int(record.get("Position", 0))
            new_pos = max(0, current_pos + move_by)
            team_data_sheet.update_cell(idx, 2, new_pos)

            print(f"[DEBUG] Team {team_name} moved from {current_pos} to {new_pos}")

            # Ensure log channel is fetched
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel is None:
                log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)

            # Special tile logic
            if new_pos in CHEST_TILES:
                print(f"[DEBUG] {team_name} landed on Chest tile {new_pos}")
                await team_receives_card(team_name, "Chest", log_channel)
            elif new_pos in CHANCE_TILES:
                print(f"[DEBUG] {team_name} landed on Chance tile {new_pos}")
                await team_receives_card(team_name, "Chance", log_channel)
            else:
                print(f"[DEBUG] {team_name} landed on tile {new_pos}, no card drawn")

            return new_pos

    print(f"[DEBUG] Team {team_name} not found in team sheet.")
    return -1


async def send_team_cards_embed(team_name: str, channel: discord.TextChannel):
    chest_cards = get_held_cards(chest_sheet, team_name)
    chance_cards = get_held_cards(chance_sheet, team_name)

    embed = discord.Embed(title=f"{team_name} Held Cards", color=discord.Color.blue())

    idx = 0
    for card in chest_cards:
        wc = card["wildcard"]
        display_text = card["text"].replace("%d6", wc if wc.isdigit() else "?").replace("%", wc if wc.isdigit() else "?")
        embed.add_field(name=f"[{idx}] Chest: {card['name']}", value=display_text, inline=False)
        idx += 1

    for card in chance_cards:
        wc = card["wildcard"]
        display_text = card["text"].replace("%d6", wc if wc.isdigit() else "?").replace("%", wc if wc.isdigit() else "?")
        embed.add_field(name=f"[{idx}] Chance: {card['name']}", value=display_text, inline=False)
        idx += 1

    if idx == 0:
        await channel.send(f"{team_name} holds no cards currently.")
        return

    await channel.send(embed=embed)

@bot.tree.command(name="show_cards", description="Show all cards currently held by your team.")
async def show_cards(interaction: discord.Interaction):
    print("show_cards called")
    await interaction.response.defer(ephemeral=True)

    team_name = get_team(interaction.user)
    print(f"Team: {team_name}")
    if not team_name:
        await interaction.followup.send("❌ You don't have a team role assigned.", ephemeral=True)
        return

    try:
        global chest_sheet, chance_sheet
        chest_sheet = sheet.worksheet("ChestCards")
        chance_sheet = sheet.worksheet("ChanceCards")
    except Exception as e:
        print(f"Error accessing sheets: {e}")
        await interaction.followup.send("❌ Error accessing card sheets.", ephemeral=True)
        return

    await send_team_cards_embed(team_name, interaction.channel)

@bot.tree.command(name="use_card", description="Use a held Chest or Chance card by index")
async def use_card(interaction: discord.Interaction, card_type: str, index: int):
    card_type = card_type.capitalize()
    if card_type not in ("Chest", "Chance"):
        await interaction.response.send_message("❌ Invalid card type. Choose 'Chest' or 'Chance'.", ephemeral=True)
        return

    team_name = get_team(interaction.user)
    if not team_name:
        await interaction.response.send_message("❌ You are not assigned to a team.", ephemeral=True)
        return

    sheet = chest_sheet if card_type == "Chest" else chance_sheet
    held_cards = get_held_cards(sheet, team_name)

    if index < 0 or index >= len(held_cards):
        await interaction.response.send_message("❌ Invalid card index.", ephemeral=True)
        return

    card = held_cards[index]
    card_row = card["row"]
    card_name = card["name"]
    card_text = card["text"]
    wildcard = card["wildcard"]

    if not wildcard.isdigit():
        await interaction.response.send_message("❌ Wildcard roll missing or invalid for this card.", ephemeral=True)
        return
    roll = int(wildcard)

    move_by = 0
    lowered = card_text.lower()
    if "move forward" in lowered:
        move_by = roll
    elif "move back" in lowered or "move backward" in lowered:
        move_by = -roll

    new_pos = None
    if move_by != 0:
        new_pos = update_team_position(team_data_sheet, team_name, move_by)

    # Remove team from Held By Team cell
    held_val = sheet.cell(card_row, 3).value or ""
    held_teams = [t.strip() for t in held_val.split(",") if t.strip() and t.strip() != team_name]
    sheet.update_cell(card_row, 3, ", ".join(held_teams))

    # Clear wildcard column
    sheet.update_cell(card_row, 4, "")

    embed = discord.Embed(
        title=f"{team_name} used {card_type} card: {card_name}",
        description=card_text.replace("%d6", str(roll)).replace("%", str(roll)),
        color=discord.Color.green()
    )
    if new_pos is not None:
        embed.add_field(name="New Position", value=str(new_pos), inline=False)

    images = {
        "Chest": "https://i.postimg.cc/XZ0nmsRP/chest.png",
        "Chance": "https://i.postimg.cc/WFxVmSwS/chance.png"
    }
    embed.set_image(url=images[card_type])

    await interaction.response.send_message(embed=embed)
    await send_team_cards_embed(team_name, interaction.channel)

# Example test commands
@bot.command()
async def test_receive_chest(ctx):
    team_name = get_team(ctx.author)
    if not team_name:
        await ctx.send("You are not on a team.")
        return
    await team_receives_card(team_name, "chest", ctx.channel)

@bot.command()
async def test_receive_chance(ctx):
    team_name = get_team(ctx.author)
    if not team_name:
        await ctx.send("You are not on a team.")
        return
    await team_receives_card(team_name, "chance", ctx.channel)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


bot.run(os.getenv('bot_token'))


