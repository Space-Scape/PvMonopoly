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
COMMAND_CHANNEL_ID = 1273094409432469605
REVIEW_CHANNEL_ID = 1273094409432469605
LOG_CHANNEL_ID = 1273094409432469605
REQUIRED_ROLE_NAME = "Event Staff"
EVENT_CAPTAIN_ROLE_NAME = "Event Captain"
BOARD_SIZE = 40 # Assuming a 40-tile board

# ========== DISCORD SETUP ==========
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ========== GOOGLE SHEETS SETUP ==========
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
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
drop_log_sheet = sheet.worksheet("DropLog")
item_values_sheet = sheet.worksheet("ItemValues")
# ✅ NEW: Add HouseData
house_data_sheet = sheet.worksheet("HouseData")

# For card logic
CHEST_TILES = [2, 17, 33]
CHANCE_TILES = [7, 22, 36]

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
    "Yama": ["Soulflame horn", "Oathplate helm", "Oathplate chest", "Oathplate legs"],
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

# ✅ NEW: Helper functions for "Used Card This Turn" flag (Column I)
def get_used_card_flag(team_name: str) -> str:
    """Checks the 'Used Card This Turn' flag for a team. Defaults to 'no'."""
    try:
        records = team_data_sheet.get_all_records()
        for record in records:
            if record.get("Team") == team_name:
                # Use .get() for safety, default to "no"
                return record.get("Used Card This Turn", "no")
    except Exception as e:
        print(f"❌ Error in get_used_card_flag: {e}")
    return "no" # Default to "no" on error or if not found

def set_used_card_flag(team_name: str, status: str):
    """Sets the 'Used Card This Turn' flag (Col I) for a team."""
    try:
        records = team_data_sheet.get_all_records()
        headers = team_data_sheet.row_values(1)
        
        col_name = "Used Card This Turn"
        if col_name not in headers:
            print(f"❌ '{col_name}' column not found in TeamData.")
            return
            
        col_index = headers.index(col_name) + 1 # 1-based index

        for idx, record in enumerate(records, start=2):
            if record.get("Team") == team_name:
                team_data_sheet.update_cell(idx, col_index, status)
                print(f"✅ Set '{col_name}' for {team_name} to '{status}'")
                return
    except Exception as e:
        print(f"❌ Error in set_used_card_flag: {e}")


# ✅ NEW: Helper functions for "Bought House This Turn" flag
def get_bought_house_flag(team_name: str) -> str:
    """Checks the 'Bought House This Turn' flag for a team. Defaults to 'no'."""
    try:
        records = team_data_sheet.get_all_records()
        for record in records:
            if record.get("Team") == team_name:
                # Use .get() for safety, default to "no"
                return record.get("Bought House This Turn", "no")
    except Exception as e:
        print(f"❌ Error in get_bought_house_flag: {e}")
    return "no" # Default to "no" on error or if not found

def set_bought_house_flag(team_name: str, status: str):
    """Sets the 'Bought House This Turn' flag for a team."""
    try:
        records = team_data_sheet.get_all_records()
        headers = team_data_sheet.row_values(1)
        
        col_name = "Bought House This Turn"
        if col_name not in headers:
            print(f"❌ '{col_name}' column not found in TeamData.")
            return
            
        col_index = headers.index(col_name) + 1 # 1-based index

        for idx, record in enumerate(records, start=2):
            if record.get("Team") == team_name:
                team_data_sheet.update_cell(idx, col_index, status)
                print(f"✅ Set '{col_name}' for {team_name} to '{status}'")
                return
    except Exception as e:
        print(f"❌ Error in set_bought_house_flag: {e}")
# ====================================


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
            if "[Rejected]" not in embed.title:
                embed.title += " [Rejected]"
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
            submitted_for,
            team,
            boss,
            drop,
            verified_by,
            screenshot,
            timestamp
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
            self.current_reviewer = None
            button.label = "Review"
            self.approve_button.disabled = True
            self.reject_button.disabled = True
            content = "Stopped reviewing."
        else:
            self.current_reviewer = interaction.user
            button.label = f"Reviewing: {interaction.user.display_name}"
            self.approve_button.disabled = False
            self.reject_button.disabled = False
            content = "You are now reviewing this submission."

        embed = self.message.embeds[0]
        status_field_index = -1
        for i, field in enumerate(embed.fields):
            if field.name == "Review Status":
                status_field_index = i
                break
        
        status_value = (f"Currently being reviewed by {self.current_reviewer.mention}" if self.current_reviewer else "Not currently being reviewed")
        
        if status_field_index != -1:
            embed.set_field_at(status_field_index, name="Review Status", value=status_value, inline=False)
        else:
            embed.insert_field_at(0, name="Review Status", value=status_value, inline=False)

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
            
            status_field_index = -1
            for i, field in enumerate(embed.fields):
                if field.name in ("Review Status", "Reviewed By"):
                    status_field_index = i
                    break
            
            if status_field_index != -1:
                embed.set_field_at(status_field_index, name="Reviewed By", value=interaction.user.mention, inline=False)
            else:
                embed.insert_field_at(0, name="Reviewed By", value=interaction.user.mention, inline=False)
            
            await self.message.delete()

            log_chan = bot.get_channel(LOG_CHANNEL_ID)
            if log_chan:
                mention = self.team_mention or self.submitted_user.mention or self.submitting_user.mention
                await log_chan.send(content=f"{mention} Drop submission approved by {interaction.user.mention}.", embed=embed)
                print(f"✅ Sent approval to DropLog ({log_chan.name})")
            else:
                print(f"❌ DropLog channel {LOG_CHANNEL_ID} not found")

            team_name = get_team(self.submitted_user) or "*No team*"
            log_drop_to_sheet(
                submitted_for=str(self.submitted_user),
                team=team_name,
                boss=self.boss,
                drop=self.drop,
                verified_by=interaction.user.name,
                screenshot=self.image_url
            )

            # ==========================================================
            # 🔹 START: GP CALCULATION LOGIC
            # ==========================================================
            try:
                # ✅ NEW: Check for alchemy multiplier
                gp_multiplier, consumed_card_name = check_and_consume_alchemy(team_name)
                alchemy_bonus = ""

                item_values_records = item_values_sheet.get_all_records()
                gp_lookup = {item['Item']: int(str(item['GP']).replace(',', '')) for item in item_values_records}
                
                base_gp_value = gp_lookup.get(self.drop, 0)
                final_gp_value = base_gp_value * gp_multiplier # Apply multiplier
                
                if gp_multiplier > 1 and consumed_card_name:
                    alchemy_bonus = f" (x{gp_multiplier} from {consumed_card_name}!)"

                if final_gp_value > 0 and team_name != "*No team*":
                    team_data_records = team_data_sheet.get_all_records()
                    for idx, record in enumerate(team_data_records, start=2):
                        if record.get("Team") == team_name:
                            current_gp = int(record.get("GP", 0) or 0)
                            new_gp = current_gp + final_gp_value # Add final value
                            team_data_sheet.update_cell(idx, 8, new_gp) # GP is in Column H (8)
                            print(f"✅ Awarded {final_gp_value} GP to {team_name}. New total: {new_gp}")
                            if log_chan:
                                # ✅ UPDATED Log Message
                                await log_chan.send(f"<:MaxCash:1347684049040183427> **{team_name}** earned **{final_gp_value:,} GP** from a **{self.drop}** drop!{alchemy_bonus}")
                            break
            except Exception as e:
                print(f"❌ Error during GP calculation: {e}")
            # ==========================================================
            # 🔹 END: GP CALCULATION LOGIC
            # ==========================================================

            if team_name and team_name != "*No team*":
                try:
                    records = team_data_sheet.get_all_records()
                    current_tile = None
                    for record in records:
                        if record.get("Team") == team_name:
                            current_tile = int(record.get("Position", 0))
                            break
                    
                    tile_boss_map = {
                        1: ["Zulrah"], 3: ["General Graardor", "K'ril Tsutsaroth", "Kree'arra", "Commander Zilyana"],
                        4: ["Vet'ion", "Venenatis", "Callisto"], 5: ["The Whisperer"], 6: ["Tombs of Amascut"],
                        8: ["Theatre of Blood"], 9: ["Chambers of Xeric"], 10: ["Gauntlet", "Nex"], 11: ["Barrows"],
                        13: ["Moons of Peril"], 14: ["Nightmare"], 15: ["The Leviathan"], 16: ["Yama"],
                        18: ["Scorpia", "Chaos Fanatic", "Crazy Archaeologist"], 19: ["Cerberus"],
                        21: ["Tombs of Amascut"], 23: ["Theatre of Blood"], 24: ["Chambers of Xeric"],
                        25: ["Vardorvis"], 26: ["Hueycoatl"], 27: ["Colosseum"], 29: ["Doom of Mokhaiotl"],
                        31: ["Tombs of Amascut"], 32: ["Theatre of Blood"], 34: ["Chambers of Xeric"],
                        35: ["Duke Sucellus"], 37: ["Phantom Muspah"], 39: ["Araxxor"]
                    }

                    bosses_for_tile = tile_boss_map.get(current_tile, [])
                    if self.boss in bosses_for_tile:
                        increment_rolls_available(team_name)
                        print(f"✅ Roll granted: Team {team_name} on tile {current_tile} ({self.boss})")
                    else:
                        print(f"❗ No roll granted: Team {team_name} on tile {current_tile}, drop boss {self.boss} not valid here.")
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

# ======= BossSelect Modal + View =======
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
        return [discord.SelectOption(label=boss) for boss in sorted(self.bosses)[start:end]]

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


class DropSelect(ui.Select):
    def __init__(self, submitting_user: discord.Member, submitted_for: discord.Member, screenshot_url: str, boss: str):
        self.submitting_user = submitting_user
        self.submitted_for = submitted_for
        self.screenshot_url = screenshot_url
        self.boss = boss
        options = [discord.SelectOption(label=drop) for drop in sorted(boss_drops[boss])]
        super().__init__(placeholder=f"Select the drop from {boss}", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected_drop = self.values[0]
        
        team_name = get_team(self.submitted_for) or "*No team*"
        if team_name == "*No team*":
            await interaction.response.edit_message(content=f"❌ **{self.submitted_for.display_name}** is not on a team.", view=None, embed=None)
            return

        current_tile = None
        records = team_data_sheet.get_all_records()
        for record in records:
            if record.get("Team") == team_name:
                current_tile = int(record.get("Position", 0))
                break

        if current_tile is None:
            await interaction.response.edit_message(content=f"❌ Could not find data for **{team_name}**.", view=None, embed=None)
            return
            
        tile_boss_map = {
            1: ["Zulrah"], 3: ["General Graardor", "K'ril Tsutsaroth", "Kree'arra", "Commander Zilyana"],
            4: ["Vet'ion", "Venenatis", "Callisto"], 5: ["The Whisperer"], 6: ["Tombs of Amascut"],
            8: ["Theatre of Blood"], 9: ["Chambers of Xeric"], 10: ["Gauntlet", "Nex"], 11: ["Barrows"],
            13: ["Moons of Peril"], 14: ["Nightmare"], 15: ["The Leviathan"], 16: ["Yama"],
            18: ["Scorpia", "Chaos Fanatic", "Crazy Archaeologist"], 19: ["Cerberus"],
            21: ["Tombs of Amascut"], 23: ["Theatre of Blood"], 24: ["Chambers of Xeric"],
            25: ["Vardorvis"], 26: ["Hueycoatl"], 27: ["Colosseum"], 29: ["Doom of Mokhaiotl"],
            31: ["Tombs of Amascut"], 32: ["Theatre of Blood"], 34: ["Chambers of Xeric"],
            35: ["Duke Sucellus"], 37: ["Phantom Muspah"], 39: ["Araxxor"]
        }

        bosses_for_tile = tile_boss_map.get(current_tile, [])
        if self.boss not in bosses_for_tile:
            await interaction.response.edit_message(
                content=f"❌ Invalid drop: Your team is on tile **{current_tile}**, which does not include **{self.boss}**.",
                embed=None,
                view=None
            )
            return

        embed = discord.Embed(title=f"Drop Submission: {self.boss}", colour=discord.Colour.blurple())
        embed.add_field(name="Review Status", value="Awaiting review...", inline=False)
        embed.add_field(name="Submitted For", value=f"{self.submitted_for.mention} `({self.submitted_for.id})`", inline=False)
        embed.add_field(name="Drop Received", value=selected_drop, inline=False)
        embed.add_field(name="Submitted By", value=f"{self.submitting_user.mention} `({self.submitting_user.id})`", inline=False)
        embed.set_image(url=self.screenshot_url)

        review_channel = bot.get_channel(REVIEW_CHANNEL_ID)
        if not review_channel:
            print(f"❌ Review channel {REVIEW_CHANNEL_ID} not found")
            await interaction.response.edit_message(content="❌ Review channel not found.", view=None, embed=None)
            return

        team_role_obj = discord.utils.get(interaction.guild.roles, name=team_name)
        team_mention = team_role_obj.mention if team_role_obj else team_name

        view = DropReviewButtons(
            submitted_user=self.submitted_for,
            drop=selected_drop,
            image_url=self.screenshot_url,
            submitting_user=self.submitting_user,
            team_mention=team_mention,
            boss=self.boss,
        )

        sent_msg = await review_channel.send(embed=embed, view=view)
        view.message = sent_msg
        print(f"✅ Sent drop submission to review channel ({review_channel.name})")

        await interaction.response.edit_message(
            content=f"✅ Drop submission for **{self.boss} - {selected_drop}** sent for review.",
            embed=None,
            view=None,
        )

class DropSelectView(ui.View):
    def __init__(self, submitting_user: discord.Member, submitted_for: discord.Member, screenshot_url: str, boss: str):
        super().__init__(timeout=180)
        self.add_item(DropSelect(submitting_user, submitted_for, screenshot_url, boss))


@bot.tree.command(name="roll", description="Roll a dice (1-6)")
async def roll(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False) 
    team_name = get_team(interaction.user) or "*No team*"
    if team_name == "*No team*":
        await interaction.followup.send("❌ You are not on a team.", ephemeral=True)
        return

    # ✅ NEW: Clear all active statuses at the start of the turn
    try:
        cleared_cards = clear_all_active_statuses(team_name)
        if cleared_cards and interaction.channel_id != LOG_CHANNEL_ID:
            log_chan = bot.get_channel(LOG_CHANNEL_ID)
            if log_chan:
                await log_chan.send(f"⌛️ **{team_name}**'s active status effects for: `({', '.join(cleared_cards)})` have expired at the start of their turn.")
    except Exception as e:
        print(f"❌ Error clearing active statuses: {e}")
    # ✅ END: Clear statuses

    records = team_data_sheet.get_all_records()
    rolls_available = 0
    current_tile = 0
    team_row_index = -1

    for idx, record in enumerate(records, start=2):
        if record.get("Team") == team_name:
            rolls_available = int(record.get("Rolls Available", 0) or 0)
            current_tile = int(record.get("Position", 0) or 0)
            team_row_index = idx
            break
    
    if team_row_index == -1:
        await interaction.followup.send(f"❌ Could not find data for **{team_name}**.", ephemeral=True)
        return

    if rolls_available <= 0:
        await interaction.followup.send(
            "❌ Your team has no rolls available right now.",
            ephemeral=True
        )
        return
        
    # ✅ NEW: Reset "Used Card This Turn" flag
    try:
        set_used_card_flag(team_name, "no")
    except Exception as e:
        print(f"❌ Error resetting 'Used Card This Turn' flag for {team_name}: {e}")

    # ✅ NEW: Reset "Bought House This Turn" flag
    try:
        set_bought_house_flag(team_name, "no")
    except Exception as e:
        print(f"❌ Error resetting 'Bought House This Turn' flag for {team_name}: {e}")

    result = random.randint(1, 6)
    
    # Log the command for Godot to process the move
    log_command(
        interaction.user.name,
        "/roll",
        {
            "team": team_name,
            "roll": result
        }
    )
    
    # Manually decrement rolls in the sheet
    try:
        decrement_rolls_available(team_name)
    except Exception as e:
        print(f"❌ Error decrementing rolls from /roll command: {e}")

    # Calculate new position to check for card tiles
    new_pos = (current_tile + result) % BOARD_SIZE

    # Handle special movement tiles (must match Apps Script)
    if new_pos == 12:
        new_pos = 28 if current_tile != 38 else 12
    elif new_pos == 28:
        new_pos = 38 if current_tile != 12 else 28
    elif new_pos == 38:
        new_pos = 12 if current_tile != 28 else 38
    elif new_pos == 30:
        new_pos = 10
    
    # Send roll result
    roll_embed = discord.Embed(
        title=f"🎲 {team_name} Rolled!",
        description=f"**{interaction.user.display_name}** rolled a **{result}**!",
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=roll_embed)

    # Check for card tiles AFTER moving
    log_chan = bot.get_channel(LOG_CHANNEL_ID)
    if not log_chan:
        print(f"❌ Log channel {LOG_CHANNEL_ID} not found, can't send card embeds.")
        return

    if new_pos in CHEST_TILES:
        print(f"❗ {team_name} landed on CHEST tile {new_pos}")
        await team_receives_card(team_name, "Chest", log_chan)
    elif new_pos in CHANCE_TILES:
        print(f"❗ {team_name} landed on CHANCE tile {new_pos}")
        await team_receives_card(team_name, "Chance", log_chan)


@bot.tree.command(name="customize", description="Open the customization panel for your team")
async def customize(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True) # Defer the response
    if interaction.channel_id != COMMAND_CHANNEL_ID:
        await interaction.followup.send(
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
    await interaction.followup.send(
        "✅ Your customization request has been sent. The game board will update shortly.", ephemeral=True
    )

@bot.tree.command(name="gp", description="Check your team's current GP balance.")
async def gp(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False) 

    team_name = get_team(interaction.user)
    if not team_name:
        await interaction.followup.send("❌ You must be on a team to check GP.", ephemeral=True)
        return

    try:
        records = team_data_sheet.get_all_records()
        team_gp = 0
        found_team = False
        for record in records:
            if record.get("Team") == team_name:
                team_gp = int(record.get("GP", 0) or 0)
                found_team = True
                break
        
        if not found_team:
            await interaction.followup.send(f"❌ Could not find data for **{team_name}**.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"<:MaxCash:1347684049040183427> {team_name} GP Balance <:MaxCash:1347684049040183427>",
            description=f"Your team currently has **{team_gp:,} GP**.",
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"❌ Error in /gp command: {e}")
        await interaction.followup.send("❌ An error occurred while fetching GP balance.", ephemeral=True)

# =============================================================================
# 🏠 NEW /buy_house COMMAND (WITH RULE CHECKS)
# =============================================================================
@bot.tree.command(name="buy_house", description="Attempt to buy a house on your current tile.")
async def buy_house(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if interaction.channel_id != COMMAND_CHANNEL_ID:
        await interaction.followup.send(
            "❌ You can only use this command in the designated command channel.", ephemeral=True
        )
        return

    team_name = get_team(interaction.user)
    if not team_name:
        await interaction.followup.send("❌ You must be on a team to buy a house.", ephemeral=True)
        return
    
    try:
        # === RULE 1: CHECK "Bought House This Turn" FLAG ===
        bought_flag = get_bought_house_flag(team_name)
        if bought_flag.lower() == "yes":
            await interaction.followup.send(
                "❌ You have already purchased a house this turn. You must roll again to buy another.", 
                ephemeral=True
            )
            return

        # === RULE 2: GET TEAM'S CURRENT TILE ===
        team_data_records = team_data_sheet.get_all_records()
        current_pos = -1
        for record in team_data_records:
            if record.get("Team") == team_name:
                current_pos = int(record.get("Position", -1))
                break
        
        if current_pos == -1:
            await interaction.followup.send("❌ Could not find your team's position.", ephemeral=True)
            return

        # === RULE 3: CHECK HOUSEDATA FOR THE TILE ===
        # Assuming HouseData schema: 'Tile' (A), 'Property Name' (B), 'OwnerTeam' (C), 'HouseCount' (D)
        # ✅ UPDATED: Use get_all_values() for real-time data
        house_data_values = house_data_sheet.get_all_values()
        property_row_data = None

        if not house_data_values or len(house_data_values) < 2:
            print("❌ HouseData sheet is empty or has no headers.")
            await interaction.followup.send("❌ HouseData sheet is empty.", ephemeral=True)
            return
            
        headers = house_data_values[0]
        try:
            tile_col = headers.index("Tile")
            owner_col = headers.index("OwnerTeam")
            count_col = headers.index("HouseCount")
        except ValueError as e:
            print(f"❌ Missing column in HouseData: {e}")
            await interaction.followup.send("❌ HouseData sheet is misconfigured.", ephemeral=True)
            return

        for row in house_data_values[1:]: # Skip headers
            try:
                # Ensure row has enough columns
                if len(row) > tile_col and int(row[tile_col]) == current_pos:
                    property_row_data = row
                    break
            except (ValueError, IndexError):
                continue # Skip empty or malformed rows
        
        if not property_row_data:
            await interaction.followup.send(
                "❌ You cannot buy a house on this tile. (It may not be a buyable property)", 
                ephemeral=True
            )
            return
        
        # === RULE 4: CHECK OWNERSHIP ===
        try:
            owner_team = property_row_data[owner_col]
            if owner_team != team_name:
                if not owner_team: # Handle blank owner
                    owner_team = "Unowned"
                await interaction.followup.send(
                    f"❌ You do not own this property. It is owned by **{owner_team}**.", 
                    ephemeral=True
                )
                return
        except IndexError:
            await interaction.followup.send("❌ This property does not have an owner.", ephemeral=True)
            return

        # === RULE 5: CHECK 4-HOUSE LIMIT ===
        try:
            house_count = int(property_row_data[count_col] or 0) # HouseCount
            if house_count >= 4:
                await interaction.followup.send(
                    "❌ This property already has the maximum of 4 houses.", 
                    ephemeral=True
                )
                return
        except IndexError:
            house_count = 0 # Assume 0 if column is missing
        except ValueError:
            house_count = 0 # Assume 0 if value is not a number

        # === ALL CHECKS PASSED ===
        
        # 1. Log the command for Godot/Apps Script to process
        log_command(
            interaction.user.name,
            "/buy_house",
            {"team": team_name}
        )
        
        # 2. Set the flag so they can't buy another
        set_bought_house_flag(team_name, "yes")
        
        # 3. Confirm to user
        await interaction.followup.send(
            f"✅ Your request to buy a house (currently {house_count}) has been sent. The game board will update shortly.", 
            ephemeral=True
        )

    except gspread.exceptions.APIError as e:
        print(f"❌ Google Sheets API error in /buy_house: {e}")
        await interaction.followup.send("❌ A database error occurred. Please try again.", ephemeral=True)
    except Exception as e:
        print(f"❌ General error in /buy_house: {e}")
        await interaction.followup.send("❌ An unexpected error occurred.", ephemeral=True)

# =============================================================================

@bot.tree.command(name="submitdrop", description="Submit a boss drop for review")
@app_commands.describe(
    screenshot="Attach a screenshot of the drop",
    submitted_for="User you are submitting the drop for (optional)",
)
async def submitdrop(interaction: discord.Interaction, screenshot: discord.Attachment, submitted_for: Optional[discord.Member] = None):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        print("❌ Interaction not found or timed out before defer.")
        return

    if interaction.channel_id != COMMAND_CHANNEL_ID:
        await interaction.followup.send(
            "❌ You can only use this command in the designated command channel.", ephemeral=True
        )
        return

    if submitted_for is None:
        submitted_for = interaction.user

    await interaction.followup.send(
        content=f"Submitting drop for {submitted_for.display_name}. Select the boss you received the drop from:",
        view=BossSelectView(interaction.user, submitted_for, screenshot.url),
        ephemeral=True
    )

#======================================================================
# CARD LOGIC
#======================================================================
async def team_receives_card(team_name: str, card_type: str, log_channel):
    card_sheet = chance_sheet if card_type == "Chance" else chest_sheet
    try:
        rows = card_sheet.get_all_records()
        if not rows:
            print(f"⚠️ No cards found in {card_type} sheet.")
            return

        # ✅ START: Logic for Chance Card (one per team)
        if card_type == "Chance":
            # ❌ REMOVED the 'already_holds_card' check that was blocking teams.
            
            eligible_cards = []
            for i, row in enumerate(rows, start=2):
                held_by = str(row.get("Held By Team", ""))
                if held_by == "": # Find a card no one holds
                    eligible_cards.append({"index": i, "data": row})
            
            if not eligible_cards:
                await log_channel.send(f"❗ **{team_name}** tried to draw a Chance card, but none were available!")
                return
                
            chosen_card = random.choice(eligible_cards)
            card_row_index = chosen_card["index"]
            card_data = chosen_card["data"]
            card_text = card_data.get("Card Text", "")
            
            # ✅ Handle Wildcard Roll
            if "%d6" in card_text:
                d6_roll = random.randint(1, 6)
                wildcard_data = {team_name: d6_roll}
                card_sheet.update_cell(card_row_index, 4, json.dumps(wildcard_data)) # Update Col D
                print(f"✅ Stored wildcard {wildcard_data} for {team_name} in {card_type} sheet")
            elif "%d3" in card_text: # 🔹 NEW
                d3_roll = random.randint(1, 3) # 🔹 NEW
                wildcard_data = {team_name: d3_roll} # 🔹 NEW
                card_sheet.update_cell(card_row_index, 4, json.dumps(wildcard_data)) # Update Col D # 🔹 NEW
                print(f"✅ Stored wildcard {wildcard_data} for {team_name} in {card_type} sheet") # 🔹 NEW

            # Assign card
            card_sheet.update_cell(card_row_index, 3, team_name) # Update Col C
        
        # ✅ START: Logic for Chest Card (multi-hold)
        else:
            eligible_cards = []
            for i, row in enumerate(rows, start=2):
                held_by = str(row.get("Held By Team", ""))
                if team_name not in held_by:
                    eligible_cards.append({"index": i, "data": row})
            
            if not eligible_cards:
                await log_channel.send(f"❗ **{team_name}** tried to draw a {card_type} card, but none were available!")
                return

            chosen_card = random.choice(eligible_cards)
            card_row_index = chosen_card["index"]
            card_data = chosen_card["data"]
            card_text = card_data.get("Card Text", "")
            
            # ✅ Handle Wildcard Roll
            if "%d6" in card_text:
                d6_roll = random.randint(1, 6)
                
                # Get existing wildcard data and add to it
                try:
                    wildcard_data_str = card_sheet.cell(card_row_index, 4).value or "{}"
                    wildcard_data = json.loads(wildcard_data_str)
                except:
                    wildcard_data = {}
                    
                wildcard_data[team_name] = d6_roll
                card_sheet.update_cell(card_row_index, 4, json.dumps(wildcard_data)) # Update Col D
                print(f"✅ Stored wildcard {wildcard_data} for {team_name} in {card_type} sheet")

            elif "%d3" in card_text: # 🔹 NEW
                d3_roll = random.randint(1, 3) # 🔹 NEW
                
                # Get existing wildcard data and add to it
                try: # 🔹 NEW
                    wildcard_data_str = card_sheet.cell(card_row_index, 4).value or "{}" # 🔹 NEW
                    wildcard_data = json.loads(wildcard_data_str) # 🔹 NEW
                except: # 🔹 NEW
                    wildcard_data = {} # 🔹 NEW
                    
                wildcard_data[team_name] = d3_roll # 🔹 NEW
                card_sheet.update_cell(card_row_index, 4, json.dumps(wildcard_data)) # Update Col D # 🔹 NEW
                print(f"✅ Stored wildcard {wildcard_data} for {team_name} in {card_type} sheet") # 🔹 NEW

            # Add team to "Held By"
            held_by_str = str(card_sheet.cell(card_row_index, 3).value or "")
            new_held_by = f"{held_by_str}, {team_name}".strip(", ")
            card_sheet.update_cell(card_row_index, 3, new_held_by)
        # ✅ END: Logic for Chest Card

        card_name = card_data.get("Name")
        card_text_display = card_data.get("Card Text")
        
        embed = discord.Embed(
            title=f"🎴 {card_type} Card Drawn!",
            description=f"**{team_name}** drew **{card_name}**!\n\n> {card_text_display}",
            color=discord.Color.gold() if card_type == "Chest" else discord.Color.blue()
        )
        await log_channel.send(embed=embed) 

    except Exception as e:
        print(f"❌ Error in team_receives_card: {e}")

# ✅ START: Updated 'get_held_cards' function
def get_held_cards(sheet_obj, team_name: str):
    cards = []
    try:
        # Get all values (including wildcard column)
        data = sheet_obj.get_all_values() 
        if not data: # Handle empty sheet
            return []
        headers = data[0]
        
        # Find column indexes
        try:
            name_col = headers.index("Name")
            text_col = headers.index("Card Text")
            held_by_col = headers.index("Held By Team")
            wildcard_col = headers.index("Wildcard")
        except ValueError as e:
            print(f"❌ Missing column in {sheet_obj.title}: {e}")
            return []

        for idx, row in enumerate(data[1:], start=2): # Start from row 2
            # Ensure row has enough columns
            if len(row) <= max(name_col, text_col, held_by_col, wildcard_col):
                continue # Skip malformed row
                
            held_by = str(row[held_by_col] or "")
            
            if team_name in held_by:
                card_text = str(row[text_col] or "")
                
                # ✅ Check for wildcard
                wildcard_data_str = str(row[wildcard_col] or "{}")
                if wildcard_data_str != "{}" and wildcard_data_str: # Check if there is any data
                    try:
                        wildcard_data = json.loads(wildcard_data_str)
                        stored_val = wildcard_data.get(team_name)
                        
                        if stored_val:
                            if isinstance(stored_val, int): # It's a number
                                card_text = card_text.replace("%d6", str(stored_val))
                                card_text = card_text.replace("%d3", str(stored_val)) # 🔹 NEW
                            # ✅ FIXED: ONLY look for "active"
                            elif isinstance(stored_val, str) and stored_val.strip() == "active": 
                                card_text += " **(ACTIVE)**"
                                
                    except Exception as e:
                        print(f"❌ Error parsing wildcard JSON for {team_name}: {wildcard_data_str} | {e}")
                        
                cards.append({
                    "row_index": idx,
                    "name": str(row[name_col] or ""),
                    "text": card_text,
                })
    except Exception as e:
        print(f"❌ Error in get_held_cards: {e}")
    return cards
# ✅ END: Updated 'get_held_cards' function

# ✅ START: Vengeance Helper Function
def check_and_consume_vengeance(target_team_name: str) -> bool:
    """
    Checks if a target team has Vengeance active.
    If yes, consumes it (clears wildcard AND held by) and returns True.
    If no, returns False.
    """
    try:
        # 1. Find the Vengeance card in the Chance sheet
        # ✅ FIXED: Use get_all_values() to avoid caching
        chance_cards_data = chance_sheet.get_all_values()
        if not chance_cards_data:
            return False
            
        headers = chance_cards_data[0]
        name_col = headers.index("Name")
        held_by_col = headers.index("Held By Team")
        wildcard_col = headers.index("Wildcard")
        
        vengeance_row_index = -1
        vengeance_wildcard_data = {}
        
        for i, row in enumerate(chance_cards_data[1:], start=2): # Start from row 2
            if len(row) > name_col and row[name_col] == "Vengeance":
                vengeance_row_index = i
                try:
                    # ✅ FIXED: Check for empty string
                    wildcard_str = row[wildcard_col] or "{}"
                    vengeance_wildcard_data = json.loads(wildcard_str)
                except:
                    vengeance_wildcard_data = {}
                break
        
        if vengeance_row_index == -1:
            print("❗ Vengeance card not found on sheet.")
            return False # Vengeance card not found

        # 2. Check if the target team has it "active"
        # ✅ FIXED: check for str(val).strip()
        team_status = vengeance_wildcard_data.get(target_team_name)
        if team_status and isinstance(team_status, str) and team_status.strip() == "active":
            # 3. Consume it
            # Remove from wildcard dict
            del vengeance_wildcard_data[target_team_name]
            chance_sheet.update_cell(vengeance_row_index, wildcard_col + 1, json.dumps(vengeance_wildcard_data)) # +1 for 1-based index
            
            # Remove from "Held By"
            held_by_str = str(chance_sheet.cell(vengeance_row_index, held_by_col + 1).value or "")
            teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
            if target_team_name in teams:
                teams.remove(target_team_name)
            chance_sheet.update_cell(vengeance_row_index, held_by_col + 1, ", ".join(teams))
            
            print(f"✅ Consumed Vengeance for {target_team_name}")
            return True
            
    except Exception as e:
        print(f"❌ Error in check_and_consume_vengeance: {e}")
        
    return False
# ✅ END: Vengeance Helper Function

# ✅ START: Redemption Helper Function
def check_and_consume_redemption(target_team_name: str) -> bool:
    """
    Checks if a target team has Redemption active.
    This is a CHANCE card.
    If yes, consumes it (clears wildcard AND held by) and returns True.
    If no, returns False.
    """
    try:
        # 1. Find the Redemption card in the Chance sheet
        chance_cards_data = chance_sheet.get_all_values()
        if not chance_cards_data:
            return False
            
        headers = chance_cards_data[0]
        name_col = headers.index("Name")
        held_by_col = headers.index("Held By Team")
        wildcard_col = headers.index("Wildcard")
        
        redemption_row_index = -1
        redemption_wildcard_data = {}
        
        for i, row in enumerate(chance_cards_data[1:], start=2): # Start from row 2
            if len(row) > name_col and row[name_col] == "Redemption":
                redemption_row_index = i
                try:
                    wildcard_str = row[wildcard_col] or "{}"
                    redemption_wildcard_data = json.loads(wildcard_str)
                except:
                    redemption_wildcard_data = {}
                break
        
        if redemption_row_index == -1:
            print("❗ Redemption card not found on chance sheet.")
            return False # Redemption card not found

        # 2. Check if the target team has it "active"
        team_status = redemption_wildcard_data.get(target_team_name)
        if team_status and isinstance(team_status, str) and team_status.strip() == "active":
            # 3. Consume it
            # Remove from wildcard dict
            del redemption_wildcard_data[target_team_name]
            chance_sheet.update_cell(redemption_row_index, wildcard_col + 1, json.dumps(redemption_wildcard_data)) # +1 for 1-based index
            
            # Remove from "Held By"
            held_by_str = str(chance_sheet.cell(redemption_row_index, held_by_col + 1).value or "")
            teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
            if target_team_name in teams:
                teams.remove(target_team_name)
            chance_sheet.update_cell(redemption_row_index, held_by_col + 1, ", ".join(teams))
            
            print(f"✅ Consumed Redemption for {target_team_name}")
            return True
            
    except Exception as e:
        print(f"❌ Error in check_and_consume_redemption: {e}")
        
    return False
# ✅ END: Redemption Helper Function


# ✅ START: Elder Maul Helper Function
def check_and_consume_elder_maul(target_team_name: str) -> bool:
    """
    Checks if a target team has Elder Maul active.
    This is a CHANCE card.
    If yes, consumes it (clears wildcard AND held by) and returns True.
    If no, returns False.
    """
    try:
        # 1. Find the Elder Maul card in the Chance sheet
        chance_cards_data = chance_sheet.get_all_values()
        if not chance_cards_data:
            return False
            
        headers = chance_cards_data[0]
        name_col = headers.index("Name")
        held_by_col = headers.index("Held By Team")
        wildcard_col = headers.index("Wildcard")
        
        card_row_index = -1
        card_wildcard_data = {}
        
        for i, row in enumerate(chance_cards_data[1:], start=2): # Start from row 2
            if len(row) > name_col and row[name_col] == "Elder Maul":
                card_row_index = i
                try:
                    wildcard_str = row[wildcard_col] or "{}"
                    card_wildcard_data = json.loads(wildcard_str)
                except:
                    card_wildcard_data = {}
                break
        
        if card_row_index == -1:
            print("❗ Elder Maul card not found on chance sheet.")
            return False # Card not found

        # 2. Check if the target team has it "active"
        team_status = card_wildcard_data.get(target_team_name)
        if team_status and isinstance(team_status, str) and team_status.strip() == "active":
            # 3. Consume it
            # Remove from wildcard dict
            del card_wildcard_data[target_team_name]
            chance_sheet.update_cell(card_row_index, wildcard_col + 1, json.dumps(card_wildcard_data)) # +1 for 1-based index
            
            # Remove from "Held By"
            held_by_str = str(chance_sheet.cell(card_row_index, held_by_col + 1).value or "")
            teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
            if target_team_name in teams:
                teams.remove(target_team_name)
            chance_sheet.update_cell(card_row_index, held_by_col + 1, ", ".join(teams))
            
            print(f"✅ Consumed Elder Maul for {target_team_name}")
            return True
            
    except Exception as e:
        print(f"❌ Error in check_and_consume_elder_maul: {e}")
        
    return False
# ✅ END: Elder Maul Helper Function


# ✅ START: Alchemy Helper Function
def check_and_consume_alchemy(team_name: str) -> (int, str):
    """
    Checks if a team has an active Alchemy card.
    If yes, consumes it and returns the multiplier (2 or 3) and card name.
    If no, returns 1 and None.
    """
    try:
        chance_cards_data = chance_sheet.get_all_values()
        if not chance_cards_data:
            return 1, None
            
        headers = chance_cards_data[0]
        name_col = headers.index("Name")
        held_by_col = headers.index("Held By Team")
        wildcard_col = headers.index("Wildcard")
        
        for i, row in enumerate(chance_cards_data[1:], start=2): # Start from row 2
            if len(row) <= max(name_col, held_by_col, wildcard_col):
                continue
                
            card_name = row[name_col]
            if card_name not in ("Low Alchemy", "High Alchemy"):
                continue

            try:
                wildcard_str = row[wildcard_col] or "{}"
                wildcard_data = json.loads(wildcard_str)
            except:
                wildcard_data = {}

            # ✅ FIXED: Iterate through keys and strip whitespace to prevent mismatch
            team_status = None
            found_key = None
            for key, value in wildcard_data.items():
                if key.strip() == team_name:
                    team_status = value
                    found_key = key
                    break
            
            # ✅ FIXED: Check for "active" status, then check card name
            if team_status and isinstance(team_status, str) and team_status.strip() == "active":
                multiplier = 3 if card_name == "High Alchemy" else 2
                
                # Consume the card
                # Remove from wildcard dict
                del wildcard_data[found_key] # Use the actual key we found
                chance_sheet.update_cell(i, wildcard_col + 1, json.dumps(wildcard_data)) # +1 for 1-based index
                
                # Remove from "Held By"
                held_by_str = str(chance_sheet.cell(i, held_by_col + 1).value or "")
                teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                if team_name in teams:
                    teams.remove(team_name)
                chance_sheet.update_cell(i, held_by_col + 1, ", ".join(teams))
                
                print(f"✅ Consumed {card_name} for {team_name}, applying x{multiplier} GP multiplier.")
                return multiplier, card_name
            
    except Exception as e:
        print(f"❌ Error in check_and_consume_alchemy: {e}")
        
    return 1, None # Default multiplier
# ✅ END: Alchemy Helper Function

# ✅ START: New Clear Statuses Helper Function
def clear_all_active_statuses(team_name: str):
    """
    Finds and clears all "active" statuses for a given team
    from both card sheets. This is called at the start of a team's turn.
    """
    print(f"❗ Clearing all active statuses for {team_name}...")
    sheets_to_check = [chance_sheet, chest_sheet]
    cards_cleared = []

    for sheet_obj in sheets_to_check:
        try:
            data = sheet_obj.get_all_values()
            if not data:
                continue
                
            headers = data[0]
            name_col = headers.index("Name")
            held_by_col = headers.index("Held By Team")
            wildcard_col = headers.index("Wildcard")

            for i, row in enumerate(data[1:], start=2): # Start from row 2
                if len(row) <= max(name_col, held_by_col, wildcard_col):
                    continue
                
                wildcard_str = str(row[wildcard_col] or "{}")
                if "active" not in wildcard_str: # ✅ FIXED: Only look for "active"
                    continue # Skip if the wildcard cell doesn't have a status

                try:
                    wildcard_data = json.loads(wildcard_str)
                except:
                    wildcard_data = {}

                team_status = None
                found_key = None
                for key, value in wildcard_data.items():
                    if key.strip() == team_name:
                        team_status = value
                        found_key = key
                        break
                
                # If an active status is found for this team
                # ✅ FIXED: Only look for "active"
                if team_status and isinstance(team_status, str) and team_status.strip() == "active":
                    card_name = row[name_col]
                    print(f"      > Found active card: {card_name}. Consuming...")
                    
                    # 1. Consume from Wildcard
                    del wildcard_data[found_key]
                    sheet_obj.update_cell(i, wildcard_col + 1, json.dumps(wildcard_data))
                    
                    # 2. Consume from "Held By"
                    held_by_str = str(row[held_by_col] or "")
                    teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                    if team_name in teams:
                        teams.remove(team_name)
                    sheet_obj.update_cell(i, held_by_col + 1, ", ".join(teams))
                    
                    cards_cleared.append(card_name)

        except Exception as e:
            print(f"❌ Error in clear_all_active_statuses for sheet {sheet_obj.title}: {e}")
            
    return cards_cleared
# ✅ END: New Clear Statuses Helper Function

# ✅ START: New Helper to award cards on landing
async def check_and_award_card_on_land(team_name: str, new_pos: int, log_channel, reason: str = "landing on"):
    """
    Checks if a new position is a card tile and awards a card if it is.
    """
    if new_pos in CHEST_TILES:
        print(f"❗ {team_name} is {reason} CHEST tile {new_pos}")
        await team_receives_card(team_name, "Chest", log_channel)
    elif new_pos in CHANCE_TILES:
        print(f"❗ {team_name} is {reason} CHANCE tile {new_pos}")
        await team_receives_card(team_name, "Chance", log_channel)
# ✅ END: New Helper


@bot.tree.command(name="show_cards", description="Show all cards currently held by your team.")
async def show_cards(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    team_name = get_team(interaction.user)
    if not team_name:
        await interaction.followup.send("❌ You don't have a team role assigned.", ephemeral=False)
        return

    # ✅ get_held_cards now correctly parses wildcards and 'active' status
    chest_cards = get_held_cards(chest_sheet, team_name)
    chance_cards = get_held_cards(chance_sheet, team_name)

    if not chest_cards and not chance_cards:
        await interaction.followup.send("❌ Your team holds no cards.", ephemeral=False)
        return

    embed = discord.Embed(
        title=f"{team_name}'s Cards",
        color=discord.Color.purple(),
        description="Cards currently held by your team:\n"
    )

    # 🟣 Add Chest Cards
    if chest_cards:
        for i, card in enumerate(chest_cards, start=1):
            embed.add_field(
                name=f"<:purp:1406234308749824051> [{i}] Chest Card — {card['name']}",
                value=f"```{card['text']}```",
                inline=False
            )

    # 🔵 Add Chance Cards
    offset = len(chest_cards)
    if chance_cards:
        for i, card in enumerate(chance_cards, start=1):
            embed.add_field(
                name=f"<:questioning:1287623035381350441> [{i+offset}] Chance Card — {card['name']}",
                value=f"```{card['text']}```",
                inline=False
            )

    await interaction.followup.send(embed=embed, ephemeral=True)


# ✅ START: Updated 'use_card' command
@bot.tree.command(name="use_card", description="Use a held card by its index from /show_cards")
@app_commands.describe(index="The index of the card you want to use (starts at 1)")
async def use_card(interaction: discord.Interaction, index: int):
    await interaction.response.defer(ephemeral=False) 
    team_name = get_team(interaction.user)
    if not team_name:
        await interaction.followup.send("❌ You are not on a team.", ephemeral=True)
        return

    # ✅ NEW: Check "Used Card This Turn" flag
    try:
        used_card_flag = get_used_card_flag(team_name)
        if used_card_flag == "yes":
            await interaction.followup.send("❌ You can only use one card per turn. Roll again to use another card.", ephemeral=True)
            return
    except Exception as e:
        print(f"❌ Error checking used_card_flag: {e}")

    # Get cards *with* parsed wildcard text
    chest_cards = get_held_cards(chest_sheet, team_name)
    chance_cards = get_held_cards(chance_sheet, team_name)
    all_cards = chest_cards + chance_cards

    if index < 1 or index > len(all_cards):
        await interaction.followup.send(f"❌ Invalid card index. Use `/show_cards` and pick a number between 1 and {len(all_cards)}.", ephemeral=True)
        return
    
    selected_card = all_cards[index - 1] # Convert 1-based index to 0-based
    card_type = "Chest" if (index - 1) < len(chest_cards) else "Chance"
    card_sheet = chest_sheet if card_type == "Chest" else chance_sheet
    card_row = selected_card['row_index']
    
    stored_roll = None
    final_card_text = selected_card['text']
    log_chan = bot.get_channel(LOG_CHANNEL_ID)
    
    # This boolean will be set to True if the card is a status effect and is NOT consumed
    is_status_activation = False
    embed_description = "" # Initialize embed description

    try:
        # --- 1. Get Wildcard Data ---
        wildcard_data_str = card_sheet.cell(card_row, 4).value or "{}"
        wildcard_data = {}
        team_wildcard_value = None
        try:
            wildcard_data = json.loads(wildcard_data_str)
            # ✅ FIXED: check for str(val).strip()
            val = wildcard_data.get(team_name)
            if val and isinstance(val, str):
                team_wildcard_value = val.strip()
            else:
                team_wildcard_value = val
        except Exception as e:
            print(f"❌ Error parsing wildcard for {team_name}: {e}")

        # --- 2. Handle Card Effect ---
        
        # --- Vengeance ---
        if selected_card['name'] == "Vengeance":
            # ✅ FIXED: Check if already active
            if team_wildcard_value == "active":
                await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                return
            
            wildcard_data[team_name] = "active"
            card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
            is_status_activation = True # Mark as activation
            
            embed_description = f"**{team_name}** used **Vengeance**!\n\n> The next card effect used on them will be rebounded."
            if log_chan:
                embed = discord.Embed(
                    title="💀 Card Activated: Vengeance",
                    description=embed_description,
                    color=discord.Color.from_rgb(172, 172, 172) # Silver
                )
                await log_chan.send(embed=embed)
            await interaction.followup.send(f"✅ **{interaction.user.display_name}** activated: **Vengeance**!", ephemeral=False)

        # ✅ NEW: Redemption
        elif selected_card['name'] == "Redemption":
            if team_wildcard_value == "active":
                await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                return
            
            wildcard_data[team_name] = "active"
            card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
            is_status_activation = True # Mark as activation
            
            embed_description = f"**{team_name}** used **Redemption**!\n\n> The next negative card effect used on your team will be fizzled."
            if log_chan:
                embed = discord.Embed(
                    title="🩵 Card Activated: Redemption",
                    description=embed_description,
                    color=discord.Color.from_rgb(255, 255, 204) # Light yellow
                )
                await log_chan.send(embed=embed)
            await interaction.followup.send(f"✅ **{interaction.user.display_name}** activated: **Redemption**!", ephemeral=False)

        # ✅ NEW: Elder Maul
        elif selected_card['name'] == "Elder Maul":
            if team_wildcard_value == "active":
                await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                return
            
            wildcard_data[team_name] = "active"
            card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
            is_status_activation = True # Mark as activation
            
            embed_description = f"**{team_name}** used **Elder Maul**!\n\n> The next negative card effect used on your team will be reduced."
            if log_chan:
                embed = discord.Embed(
                    title="🛡️ Card Activated: Elder Maul",
                    description=embed_description,
                    color=discord.Color.light_grey()
                )
                await log_chan.send(embed=embed)
            await interaction.followup.send(f"✅ **{interaction.user.display_name}** activated: **Elder Maul**!", ephemeral=False)

        # --- Low Alchemy ---
        elif selected_card['name'] == "Low Alchemy":
            # ✅ FIXED: Check if already active
            if team_wildcard_value == "active":
                await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                return

            wildcard_data[team_name] = "active" # ✅ FIXED: Store "active"
            card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
            is_status_activation = True # Mark as activation
            
            embed_description = f"**{team_name}** used **Low Alchemy**!\n\n> Your next drop this turn will be worth **double GP**."
            if log_chan:
                embed = discord.Embed(
                    title="<:coin:1406230459301630043> Card Activated: Low Alchemy",
                    description=embed_description,
                    color=discord.Color.from_rgb(204, 153, 0) # Gold
                )
                await log_chan.send(embed=embed)
            await interaction.followup.send(f"✅ **{interaction.user.display_name}** activated: **Low Alchemy**!", ephemeral=False)

        # --- High Alchemy ---
        elif selected_card['name'] == "High Alchemy":
            # ✅ FIXED: Check if already active
            if team_wildcard_value == "active":
                await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                return
                
            wildcard_data[team_name] = "active" # ✅ FIXED: Store "active"
            card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
            is_status_activation = True # Mark as activation
            
            embed_description = f"**{team_name}** used **High Alchemy**!\n\n> Your next drop this turn will be worth **triple GP**."
            if log_chan:
                embed = discord.Embed(
                    title="<:MaxCash:1347684049040183427> Card Activated: High Alchemy",
                    description=embed_description,
                    color=discord.Color.from_rgb(0, 204, 0) # Green
                )
                await log_chan.send(embed=embed)
            await interaction.followup.send(f"✅ **{interaction.user.display_name}** activated: **High Alchemy**!", ephemeral=False)

        # --- Vile Vigour ---
        elif selected_card['name'] == "Vile Vigour" and isinstance(team_wildcard_value, int):
            stored_roll = team_wildcard_value
            
            # 🔹 ADDED: Get caster pos 🔹
            all_teams_data = team_data_sheet.get_all_records()
            caster_pos = -1
            for record in all_teams_data:
                if record.get("Team") == team_name:
                    caster_pos = int(record.get("Position", -1))
                    break
            
            if caster_pos == -1:
                await interaction.followup.send("❌ Could not find your team's position.", ephemeral=True)
                return # Stop, card is not consumed

            # 🔹 ADDED: Calculate new_pos 🔹
            new_pos = (caster_pos + stored_roll) % BOARD_SIZE
            if new_pos == 12: new_pos = 28 if caster_pos != 38 else 12
            elif new_pos == 28: new_pos = 38 if caster_pos != 12 else 28
            elif new_pos == 38: new_pos = 12 if caster_pos != 28 else 38
            elif new_pos == 30: new_pos = 10
            
            log_command(
                team_name, 
                "/card_effect_move", 
                {"team": team_name, "move": stored_roll}
            )
            embed_description = f"**{team_name}** used **Vile Vigour** and moved **{stored_roll}** spaces forward!"

            # 🔹 ADDED: Check for card 🔹
            await check_and_award_card_on_land(team_name, new_pos, log_chan, "using Vile Vigour to")

        # --- Dragon Spear ---
        elif selected_card['name'] == "Dragon Spear" and isinstance(team_wildcard_value, int):
            stored_roll = team_wildcard_value
            move_amount = -stored_roll # Move back
            
            # --- PRE-CHECK ---
            all_teams_data = team_data_sheet.get_all_records()
            caster_pos = -1
            targets = []
            
            for record in all_teams_data:
                if record.get("Team") == team_name:
                    caster_pos = int(record.get("Position", -1))
                    break
            
            if caster_pos != -1:
                for record in all_teams_data:
                    opponent_team_name = record.get("Team")
                    if opponent_team_name == team_name:
                        continue
                    if int(record.get("Position", -1)) == caster_pos:
                        targets.append(opponent_team_name)
            
            if not targets:
                await interaction.followup.send("❌ Card effect failed: No other teams are on your tile.", ephemeral=True)
                return # Stop, card is not consumed
            # --- END PRE-CHECK ---

            # Log effects and build embed
            embed_description = f"**{team_name}** used **Dragon Spear**!\n\n"
            for target_team in targets:
                # ✅ NEW REDEMPTION CHECK
                if check_and_consume_redemption(target_team):
                    embed_description += f"🩵 **{target_team}**'s Redemption activated!\n"
                    if log_chan:
                        fizzle_embed = discord.Embed(
                            title="🩵 Redemption Activated!",
                            description=f"**{team_name}** tried to use **Dragon Spear** on you, but your **Redemption** activated!",
                            color=discord.Color.blue()
                        )
                        await log_chan.send(content=f"To {target_team}:", embed=fizzle_embed)
                    continue # Skip to the next target
                    
                # ✅ CHECK FOR VENGEANCE
                if check_and_consume_vengeance(target_team):
                    # Rebound
                    
                    # ✅ NEW ELDER MAUL CHECK (on caster)
                    elder_maul_active = check_and_consume_elder_maul(team_name) # Check caster
                    final_move_amount = move_amount # This is -stored_roll
                    if elder_maul_active:
                        final_move_amount = -(max(0, stored_roll - 1))
                        embed_description += f"🛡️ **{team_name}**'s Elder Maul activated! Rebounded effect reduced.\n"
                        if log_chan:
                            maul_embed = discord.Embed(
                                title="🛡️ Elder Maul Activated!",
                                description=f"Your **Elder Maul** activated and reduced the Vengeance effect!",
                                color=discord.Color.light_grey()
                            )
                            await log_chan.send(content=f"To {team_name}:", embed=maul_embed) # Send to caster
                    
                    new_pos = max(0, caster_pos + final_move_amount) # Calculate new_pos for caster
                    log_command(
                        team_name, # Logged by the caster
                        "/card_effect_move",
                        {"team": team_name, "move": final_move_amount} # Move the caster
                    )
                    embed_description += f"💀 **{target_team}** had Vengeance! The effect was rebounded!\n"
                    
                    # 🔹 ADDED: Check for card 🔹
                    await check_and_award_card_on_land(team_name, new_pos, log_chan, "being rebounded by Dragon Spear to")

                    if log_chan:
                        skull_embed = discord.Embed(
                            title="💀 Vengeance Activated!",
                            description=f"You activated **{target_team}**'s Vengeance!\nYour team moved back **{abs(final_move_amount)}** spaces!",
                            color=discord.Color.dark_red()
                        )
                        await log_chan.send(content=f"To {team_name}:", embed=skull_embed)
                    continue # Skip to next target
                
                else:
                    # Normal effect
                    
                    # ✅ NEW ELDER MAUL CHECK
                    elder_maul_active = check_and_consume_elder_maul(target_team)
                    final_move_amount = move_amount # This is -stored_roll
                    if elder_maul_active:
                        final_move_amount = -(max(0, stored_roll - 1)) # e.g., -3 (roll=3) becomes -2. -1 (roll=1) becomes 0.
                        embed_description += f"🛡️ **{target_team}**'s Elder Maul activated! Effect reduced.\n"
                        if log_chan:
                            maul_embed = discord.Embed(
                                title="🛡️ Elder Maul Activated!",
                                description=f"**{team_name}** tried to use **Dragon Spear** on you, but your **Elder Maul** reduced the effect!",
                                color=discord.Color.light_grey()
                            )
                            await log_chan.send(content=f"To {target_team}:", embed=maul_embed)

                    # Get target's current pos (which is same as caster_pos)
                    target_pos = caster_pos 
                    new_pos = max(0, target_pos + final_move_amount) # Calculate new_pos
                    log_command(
                        team_name, # Logged by the caster
                        "/card_effect_move",
                        {"team": target_team, "move": final_move_amount} # Move the target
                    )
                    embed_description += f"**{target_team}** was moved back **{abs(final_move_amount)}** tiles (stops at Go)!\n"
                    
                    # 🔹 ADDED: Check for card 🔹
                    await check_and_award_card_on_land(target_team, new_pos, log_chan, "being hit by Dragon Spear to")


        # --- Rogue's Gloves ---
        elif selected_card['name'] == "Rogue's Gloves":
            
            # --- PRE-CHECK ---
            stealable_cards = []
            
            # Check Chance cards
            chance_data = chance_sheet.get_all_values()
            if chance_data:
                headers = chance_data[0]
                name_col = headers.index("Name")
                held_by_col = headers.index("Held By Team")
                wildcard_col = headers.index("Wildcard")
                
                for i, row in enumerate(chance_data[1:], start=2):
                    if len(row) <= max(name_col, held_by_col, wildcard_col): continue
                    held_by_str = str(row[held_by_col] or "")
                    
                    if held_by_str and team_name not in held_by_str:
                        is_active = False
                        wildcard_str = str(row[wildcard_col] or "{}")
                        if wildcard_str != "{}" and wildcard_str:
                            try:
                                wildcard_data_json = json.loads(wildcard_str)
                                victim_team = held_by_str.strip() 
                                victim_status = wildcard_data_json.get(victim_team)
                                if victim_status and isinstance(victim_status, str) and victim_status.strip() == "active":
                                    is_active = True
                            except:
                                pass 
                        
                        if not is_active:
                            stealable_cards.append({
                                "sheet": chance_sheet,
                                "row_index": i,
                                "card_name": str(row[name_col]),
                                "card_type": "Chance",
                                "victim_team": held_by_str.strip() 
                            })

            # Check Chest cards
            chest_data = chest_sheet.get_all_values()
            if chest_data:
                headers = chest_data[0]
                name_col = headers.index("Name")
                held_by_col = headers.index("Held By Team")
                wildcard_col = headers.index("Wildcard")

                for i, row in enumerate(chest_data[1:], start=2):
                    if len(row) <= max(name_col, held_by_col, wildcard_col): continue
                    held_by_str = str(row[held_by_col] or "")
                    
                    if held_by_str and team_name not in held_by_str:
                        all_holders = [t.strip() for t in held_by_str.split(',') if t.strip()]
                        
                        wildcard_str = str(row[wildcard_col] or "{}")
                        wildcard_data_json = {}
                        try:
                            wildcard_data_json = json.loads(wildcard_str)
                        except:
                            pass

                        valid_victims = []
                        for holder in all_holders:
                            if holder == team_name: continue
                            holder_status = wildcard_data_json.get(holder)
                            if not (holder_status and isinstance(holder_status, str) and holder_status.strip() == "active"):
                                valid_victims.append(holder)

                        if valid_victims:
                            victim_team = random.choice(valid_victims) 
                            stealable_cards.append({
                                "sheet": chest_sheet,
                                "row_index": i,
                                "card_name": str(row[name_col]),
                                "card_type": "Chest",
                                "victim_team": victim_team
                            })
            
            if not stealable_cards:
                await interaction.followup.send("❌ Card effect failed: There are no eligible cards to steal.", ephemeral=True)
                return # Stop, card is not consumed
            # --- END PRE-CHECK ---

            # --- A card was found, let's steal it ---
            stolen_card = random.choice(stealable_cards)
            victim_team = stolen_card["victim_team"]
            target_sheet = stolen_card["sheet"]
            target_row = stolen_card["row_index"]
            
            # ✅ NEW REDEMPTION CHECK (on the victim)
            if check_and_consume_redemption(victim_team):
                embed_description = f"**{team_name}** tried to use **Rogue's Gloves** on **{victim_team}**...\n\n🩵 But **{victim_team}**'s Redemption activated!"
                if log_chan:
                    fizzle_embed = discord.Embed(
                        title="🩵 Redemption Activated!",
                        description=f"**{team_name}** tried to use **Rogue's Gloves** on you, but your **Redemption** activated!",
                        color=discord.Color.blue()
                    )
                    await log_chan.send(content=f"To {victim_team}:", embed=fizzle_embed)
                # Card is still consumed, but the effect stops here
            
            else:
                # --- NO REDEMPTION, PROCEED WITH STEAL ---
                # 1. Update "Held By Team"
                held_by_str = str(target_sheet.cell(target_row, 3).value or "")
                teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                if victim_team in teams:
                    teams.remove(victim_team)
                if team_name not in teams:
                    teams.append(team_name)
                target_sheet.update_cell(target_row, 3, ", ".join(teams))

                # 2. Transfer Wildcard Data
                wildcard_str = str(target_sheet.cell(target_row, 4).value or "{}")
                try:
                    wildcard_data_json = json.loads(wildcard_str)
                    victim_wildcard = wildcard_data_json.pop(victim_team, None)
                    if victim_wildcard:
                        wildcard_data_json[team_name] = victim_wildcard
                        target_sheet.update_cell(target_row, 4, json.dumps(wildcard_data_json))
                except Exception as e:
                    print(f"❌ Error transferring wildcard data: {e}")

                embed_description = f"**{team_name}** used **Rogue's Gloves** and stole **{stolen_card['card_name']}** from **{victim_team}**!"
                
                # Send a message to the victim
                if log_chan:
                    victim_embed = discord.Embed(
                        title="‼️ Card Stolen!",
                        description=f"**{team_name}** used **Rogue's Gloves** and stole your **{stolen_card['card_name']}** card!",
                        color=discord.Color.dark_red()
                    )
                    await log_chan.send(content=f"To {victim_team}:", embed=victim_embed)

        # ✅ START: Pickpocket
        elif selected_card['name'] == "Pickpocket":
            all_teams_data = team_data_sheet.get_all_records()
            opponents_gp = []

            caster_row = -1
            caster_gp = 0

            # Get all team GP
            for idx, record in enumerate(all_teams_data, start=2):
                gp = int(record.get("GP", 0) or 0)
                team = record.get("Team")
                if team == team_name:
                    caster_row = idx
                    caster_gp = gp
                    continue
                if team:
                    opponents_gp.append({"team": team, "gp": gp, "row": idx})
            
            if not opponents_gp:
                await interaction.followup.send("❌ Card effect failed: No other teams found.", ephemeral=True)
                return # Stop, card is not consumed
            
            # Find target with most GP
            target = max(opponents_gp, key=lambda x: x["gp"])
            target_team = target["team"]
            target_gp = target["gp"]
            target_row = target["row"]
            
            steal_amount = 0
            if target_gp >= 30_000_000:
                steal_amount = 30_000_000
            elif target_gp >= 15_000_000:
                steal_amount = 15_000_000
            elif target_gp >= 5_000_000:
                steal_amount = 5_000_000
            
            if steal_amount == 0:
                await interaction.followup.send("❌ Card effect failed: No teams have enough wealth to steal from (min 5M GP).", ephemeral=True)
                return # Stop, card is not consumed

            embed_description = f"**{team_name}** used **Pickpocket** on **{target_team}**!\n\n"

            # ✅ NEW REDEMPTION CHECK
            if check_and_consume_redemption(target_team):
                embed_description += f"🩵 **{target_team}**'s Redemption activated!"
                if log_chan:
                    fizzle_embed = discord.Embed(
                        title="🩵 Redemption Activated!",
                        description=f"**{team_name}** tried to use **Pickpocket** on you, but your **Redemption** activated!",
                        color=discord.Color.blue()
                    )
                    await log_chan.send(content=f"To {target_team}:", embed=fizzle_embed)
            
            # ✅ CHECK FOR VENGEANCE
            elif check_and_consume_vengeance(target_team):
                # Rebound
                
                # ✅ NEW ELDER MAUL CHECK (on the *caster* this time)
                elder_maul_active = check_and_consume_elder_maul(team_name) # Check caster
                final_steal_amount = steal_amount
                if elder_maul_active:
                    final_steal_amount = steal_amount // 2 # Halved
                    embed_description += f"🛡️ **{team_name}**'s Elder Maul activated! Rebounded loss halved.\n"
                    if log_chan:
                        maul_embed = discord.Embed(
                            title="🛡️ Elder Maul Activated!",
                            description=f"Your **Elder Maul** activated and halved the GP you lost from Vengeance!",
                            color=discord.Color.light_grey()
                        )
                        await log_chan.send(content=f"To {team_name}:", embed=maul_embed) # Send to caster
                
                new_caster_gp = max(0, caster_gp - final_steal_amount)
                new_target_gp = target_gp + final_steal_amount # Target GAINS the money
                
                team_data_sheet.update_cell(caster_row, 8, new_caster_gp) # GP is Col H (8)
                team_data_sheet.update_cell(target_row, 8, new_target_gp) # GP is Col H (8)

                embed_description += f"💀 **{target_team}** had Vengeance! The effect was rebounded!\n**{team_name}** loses **{final_steal_amount:,} GP**!"
                if log_chan:
                    skull_embed = discord.Embed(
                        title="💀 Vengeance Activated!",
                        description=f"You activated **{target_team}**'s Vengeance!\nYou lose **{final_steal_amount:,} GP**!",
                        color=discord.Color.dark_red()
                    )
                    await log_chan.send(content=f"To {team_name}:", embed=skull_embed)

            else:
                # --- NO REDEMPTION/VENGEANCE, PROCEED ---
                
                # ✅ NEW ELDER MAUL CHECK
                elder_maul_active = check_and_consume_elder_maul(target_team)
                final_steal_amount = steal_amount
                if elder_maul_active:
                    final_steal_amount = steal_amount // 2 # Halved
                    embed_description += f"🛡️ **{target_team}**'s Elder Maul activated! Steal amount halved.\n"
                    if log_chan:
                        maul_embed = discord.Embed(
                            title="🛡️ Elder Maul Activated!",
                            description=f"**{team_name}** tried to use **Pickpocket** on you, but your **Elder Maul** reduced the amount stolen!",
                            color=discord.Color.light_grey()
                        )
                        await log_chan.send(content=f"To {target_team}:", embed=maul_embed)
                
                new_caster_gp = caster_gp + final_steal_amount
                new_target_gp = target_gp - final_steal_amount
                
                team_data_sheet.update_cell(caster_row, 8, new_caster_gp) # GP is Col H (8)
                team_data_sheet.update_cell(target_row, 8, new_target_gp) # GP is Col H (8)

                embed_description += f"💰 Stole **{final_steal_amount:,} GP** from **{target_team}**!"
                
                # Send message to victim
                if log_chan:
                    victim_embed = discord.Embed(
                        title="‼️ GP Stolen!",
                        description=f"**{team_name}** used **Pickpocket** and stole **{final_steal_amount:,} GP** from your team!",
                        color=discord.Color.dark_red()
                    )
                    await log_chan.send(content=f"To {target_team}:", embed=victim_embed)
        # ✅ END: Pickpocket

        # ✅ START: Lure
        elif selected_card['name'] == "Lure":
            # --- PRE-CHECK ---
            all_teams_data = team_data_sheet.get_all_records()
            caster_pos = -1
            opponents_ahead = []

            for record in all_teams_data:
                if record.get("Team") == team_name:
                    caster_pos = int(record.get("Position", -1))
                    break
            
            if caster_pos == -1:
                await interaction.followup.send("❌ Could not find your team's position.", ephemeral=True)
                return

            for record in all_teams_data:
                opponent_team_name = record.get("Team")
                if opponent_team_name == team_name:
                    continue
                
                opponent_pos = int(record.get("Position", -1))
                if opponent_pos > caster_pos:
                    opponents_ahead.append((opponent_team_name, opponent_pos))
            
            if not opponents_ahead:
                await interaction.followup.send("❌ Card effect failed: No opponents are ahead of you.", ephemeral=True)
                return # Stop, card is not consumed
            # --- END PRE-CHECK ---

            # Find the closest target
            sorted_opponents = sorted(opponents_ahead, key=lambda x: x[1])
            target_team = sorted_opponents[0][0]
            target_pos = sorted_opponents[0][1]

            # ✅ NEW REDEMPTION CHECK
            if check_and_consume_redemption(target_team):
                embed_description = f"**{team_name}** tried to use **Lure** on **{target_team}**...\n\n🩵 But **{target_team}**'s Redemption activated!"
                if log_chan:
                    fizzle_embed = discord.Embed(
                        title="🩵 Redemption Activated!",
                        description=f"**{team_name}** tried to use **Lure** on you, but your **Redemption** activated!",
                        color=discord.Color.blue()
                    )
                    await log_chan.send(content=f"To {target_team}:", embed=fizzle_embed)
            
            else:
                # --- NO REDEMPTION, PROCEED WITH LURE ---
                log_command(
                    team_name,
                    "/card_effect_set_tile",
                    {"team": target_team, "tile": caster_pos}
                )
                embed_description = f"**{team_name}** used **Lure**!\n\n🎣 **{target_team}** (on tile {target_pos}) was lured to your tile (tile {caster_pos})!"
                
                # 🔹 ADDED: Check for card 🔹
                await check_and_award_card_on_land(target_team, caster_pos, log_chan, "being lured to")
        # ✅ END: Lure

        # 🔹 START: Escape Crystal
        elif selected_card['name'] == "Escape Crystal":
            # --- PRE-CHECK: Get caster position ---
            all_teams_data = team_data_sheet.get_all_records()
            caster_pos = -1
            for record in all_teams_data:
                if record.get("Team") == team_name:
                    caster_pos = int(record.get("Position", -1))
                    break
            
            if caster_pos != 10:
                await interaction.followup.send("❌ You can only use the **Escape Crystal** on tile 10 (Nex/Gauntlet).", ephemeral=True)
                return # Stop, card is not consumed
            # --- END PRE-CHECK ---

            # Card effect is valid
            increment_rolls_available(team_name)
            embed_description = f"**{team_name}** used the **Escape Crystal** on tile 10!\n\n> 🎲 You have gained a free roll!"
        # 🔹 END: Escape Crystal

        # ✅ START: Backstab
        elif selected_card['name'] == "Backstab" and isinstance(team_wildcard_value, int):
            stored_roll = team_wildcard_value
            
            # --- PRE-CHECK ---
            all_teams_data = team_data_sheet.get_all_records()
            caster_pos = -1
            opponents_ahead = []

            for record in all_teams_data:
                if record.get("Team") == team_name:
                    caster_pos = int(record.get("Position", -1))
                    break
            
            if caster_pos == -1:
                await interaction.followup.send("❌ Could not find your team's position.", ephemeral=True)
                return # Stop, card is not consumed

            for record in all_teams_data:
                opponent_team_name = record.get("Team")
                if opponent_team_name == team_name:
                    continue
                
                opponent_pos = int(record.get("Position", -1))
                if opponent_pos > caster_pos:
                    opponents_ahead.append((opponent_team_name, opponent_pos))
            
            if not opponents_ahead:
                await interaction.followup.send("❌ Card effect failed: No opponents are ahead of you.", ephemeral=True)
                return # Stop, card is not consumed
            # --- END PRE-CHECK ---

            # Find the closest target
            sorted_opponents = sorted(opponents_ahead, key=lambda x: x[1])
            target_team = sorted_opponents[0][0]
            target_pos = sorted_opponents[0][1] # Target's current position
            
            embed_description = f"**{team_name}** used **Backstab**!\n\n"

            # ✅ NEW REDEMPTION CHECK
            if check_and_consume_redemption(target_team):
                embed_description += f"🩵 **{target_team}**'s Redemption activated!"
                if log_chan:
                    fizzle_embed = discord.Embed(
                        title="🩵 Redemption Activated!",
                        description=f"**{team_name}** tried to use **Backstab** on you, but your **Redemption** activated!",
                        color=discord.Color.blue()
                    )
                    await log_chan.send(content=f"To {target_team}:", embed=fizzle_embed)
            
            # ✅ CHECK FOR VENGEANCE
            elif check_and_consume_vengeance(target_team):
                # Rebound
                
                # ✅ NEW ELDER MAUL CHECK (on caster)
                elder_maul_active = check_and_consume_elder_maul(team_name) # Check caster
                final_roll_val = stored_roll
                if elder_maul_active:
                    final_roll_val = max(0, stored_roll - 1)
                    embed_description += f"🛡️ **{team_name}**'s Elder Maul activated! Rebounded effect reduced.\n"
                    if log_chan:
                        maul_embed = discord.Embed(
                            title="🛡️ Elder Maul Activated!",
                            description=f"Your **Elder Maul** activated and reduced the Vengeance effect!",
                            color=discord.Color.light_grey()
                        )
                        await log_chan.send(content=f"To {team_name}:", embed=maul_embed) # Send to caster
                
                # Calculate new position (behind caster)
                new_pos = max(0, caster_pos - final_roll_val)
                
                log_command(
                    team_name, # Logged by the caster
                    "/card_effect_set_tile",
                    {"team": team_name, "tile": new_pos} # Move the caster
                )
                embed_description += f"💀 **{target_team}** had Vengeance! The effect was rebounded!\n"
                
                # 🔹 ADDED: Check for card 🔹
                await check_and_award_card_on_land(team_name, new_pos, log_chan, "being rebounded by Backstab to")

                if log_chan:
                    skull_embed = discord.Embed(
                        title="💀 Vengeance Activated!",
                        description=f"You activated **{target_team}**'s Vengeance!\nYour team was moved to tile **{new_pos}**!",
                        color=discord.Color.dark_red()
                    )
                    await log_chan.send(content=f"To {team_name}:", embed=skull_embed)
            
            else:
                # --- NO REDEMPTION/VENGEANCE, PROCEED ---
                
                # ✅ NEW ELDER MAUL CHECK
                elder_maul_active = check_and_consume_elder_maul(target_team)
                final_roll_val = stored_roll # This is the positive roll value
                if elder_maul_active:
                    final_roll_val = max(0, stored_roll - 1)
                    embed_description += f"🛡️ **{target_team}**'s Elder Maul activated! Effect reduced.\n"
                    if log_chan:
                        maul_embed = discord.Embed(
                            title="🛡️ Elder Maul Activated!",
                            description=f"**{team_name}** tried to use **Backstab** on you, but your **Elder Maul** reduced the effect!",
                            color=discord.Color.light_grey()
                        )
                        await log_chan.send(content=f"To {target_team}:", embed=maul_embed)

                # Calculate new position (behind caster)
                new_pos = max(0, caster_pos - final_roll_val)
                
                log_command(
                    team_name,
                    "/card_effect_set_tile",
                    {"team": target_team, "tile": new_pos}
                )
                embed_description += f"🔪 **{target_team}** (on tile {target_pos}) was backstabbed to tile {new_pos}!"
                
                # 🔹 ADDED: Check for card 🔹
                await check_and_award_card_on_land(target_team, new_pos, log_chan, "being backstabbed to")
        # ✅ END: Backstab

        # ✅ START: Smite
        elif selected_card['name'] == "Smite":
            # --- PRE-CHECK: Find valid targets ---
            all_teams_data = team_data_sheet.get_all_records()
            caster_pos = -1
            
            for record in all_teams_data:
                if record.get("Team") == team_name:
                    caster_pos = int(record.get("Position", -1))
                    break
            
            if caster_pos == -1:
                await interaction.followup.send("❌ Could not find your team's position.", ephemeral=True)
                return # Stop, card is not consumed

            target_tiles = [caster_pos - 1, caster_pos, caster_pos + 1]
            if caster_pos == 0:
                target_tiles = [0, 1] # Handle edge case at GO

            valid_targets = []
            for record in all_teams_data:
                opponent_team_name = record.get("Team")
                if opponent_team_name == team_name:
                    continue
                
                opponent_pos = int(record.get("Position", -1))
                if opponent_pos in target_tiles:
                    valid_targets.append(opponent_team_name)
            
            if not valid_targets:
                await interaction.followup.send("❌ Card effect failed: No opponents are within 1 tile of you.", ephemeral=True)
                return # Stop, card is not consumed
            # --- END PRE-CHECK ---

            victim_team = random.choice(valid_targets)
            embed_description = f"**{team_name}** used **Smite** on **{victim_team}**!\n\n"

            # --- PRE-CHECK 2: Find victim's cards ---
            victim_chest_cards = get_held_cards(chest_sheet, victim_team)
            victim_chance_cards = get_held_cards(chance_sheet, victim_team)
            all_victim_cards = victim_chest_cards + victim_chance_cards
            
            non_active_cards = [card for card in all_victim_cards if "(ACTIVE)" not in card['text']]
            
            if not non_active_cards:
                await interaction.followup.send(f"❌ Card effect failed: **{victim_team}** has no cards that can be removed.", ephemeral=True)
                return # Stop, card is not consumed
            # --- END PRE-CHECK 2 ---

            # ✅ NEW REDEMPTION CHECK
            if check_and_consume_redemption(victim_team):
                embed_description += f"🩵 **{victim_team}**'s Redemption activated!"
                if log_chan:
                    fizzle_embed = discord.Embed(
                        title="🩵 Redemption Activated!",
                        description=f"**{team_name}** tried to use **Smite** on you, but your **Redemption** activated!",
                        color=discord.Color.blue()
                    )
                    await log_chan.send(content=f"To {victim_team}:", embed=fizzle_embed)
            
            # ✅ CHECK FOR VENGEANCE
            elif check_and_consume_vengeance(victim_team):
                embed_description += f"💀 **{victim_team}** had Vengeance! The effect was rebounded!\n"
                
                # Find a card from the caster to remove
                caster_chest_cards = get_held_cards(chest_sheet, team_name)
                caster_chance_cards = get_held_cards(chance_sheet, team_name)
                all_caster_cards = caster_chest_cards + caster_chance_cards
                non_active_caster_cards = [card for card in all_caster_cards if "(ACTIVE)" not in card['text']]
                
                if not non_active_caster_cards:
                    embed_description += f"But **{team_name}** had no cards to lose!"
                else:
                    card_to_remove = random.choice(non_active_caster_cards)
                    remove_sheet = chest_sheet if card_to_remove in caster_chest_cards else chance_sheet
                    remove_row = card_to_remove['row_index']
                    
                    # Remove card from caster
                    # 1. Clear Wildcard
                    wildcard_str = str(remove_sheet.cell(remove_row, 4).value or "{}")
                    try:
                        wildcard_data = json.loads(wildcard_str)
                        wildcard_data.pop(team_name, None)
                        remove_sheet.update_cell(remove_row, 4, json.dumps(wildcard_data))
                    except Exception as e:
                        print(f"❌ Error clearing wildcard on Vengeance Smite: {e}")
                        
                    # 2. Clear "Held By"
                    held_by_str = str(remove_sheet.cell(remove_row, 3).value or "")
                    teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                    if team_name in teams:
                        teams.remove(team_name)
                    remove_sheet.update_cell(remove_row, 3, ", ".join(teams))
                    
                    embed_description += f"**{team_name}** lost their **{card_to_remove['name']}** card!"
                    
                    if log_chan:
                        skull_embed = discord.Embed(
                            title="💀 Vengeance Activated!",
                            description=f"You activated **{victim_team}**'s Vengeance!\nYou lost your **{card_to_remove['name']}** card!",
                            color=discord.Color.dark_red()
                        )
                        await log_chan.send(content=f"To {team_name}:", embed=skull_embed)

            else:
                # --- NO REDEMPTION/VENGEANCE, PROCEED ---
                
                # NOTE: Elder Maul does not block Smite, as Smite is not a "reduced" effect.
                
                card_to_remove = random.choice(non_active_cards)
                remove_sheet = chest_sheet if card_to_remove in victim_chest_cards else chance_sheet
                remove_row = card_to_remove['row_index']

                # Remove card from victim
                # 1. Clear Wildcard
                wildcard_str = str(remove_sheet.cell(remove_row, 4).value or "{}")
                try:
                    wildcard_data = json.loads(wildcard_str)
                    wildcard_data.pop(victim_team, None)
                    remove_sheet.update_cell(remove_row, 4, json.dumps(wildcard_data))
                except Exception as e:
                    print(f"❌ Error clearing wildcard on Smite: {e}")
                    
                # 2. Clear "Held By"
                held_by_str = str(remove_sheet.cell(remove_row, 3).value or "")
                teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                if victim_team in teams:
                    teams.remove(victim_team)
                remove_sheet.update_cell(remove_row, 3, ", ".join(teams))

                embed_description += f"🌩️ **{victim_team}** was smote and lost their **{card_to_remove['name']}** card!"
                
                # Send message to victim
                if log_chan:
                    victim_embed = discord.Embed(
                        title="‼️ Card Lost!",
                        description=f"**{team_name}** used **Smite**! Your team lost your **{card_to_remove['name']}** card!",
                        color=discord.Color.dark_red()
                    )
                    await log_chan.send(content=f"To {victim_team}:", embed=victim_embed)
        # ✅ END: Smite

        # ======================================================================
        # 🔹 START: NEW CARD - VARROCK TELE
        # ======================================================================
        elif selected_card['name'] == "Varrock Tele":
            # --- PRE-CHECK: Get caster position and rolls ---
            all_teams_data = team_data_sheet.get_all_records()
            caster_pos = -1
            rolls_available = 0
            for record in all_teams_data:
                if record.get("Team") == team_name:
                    caster_pos = int(record.get("Position", -1))
                    rolls_available = int(record.get("Rolls Available", 0) or 0)
                    break
            
            if caster_pos == 10:
                await interaction.followup.send("❌ You cannot use **Varrock Tele** while on tile 10 (Nex/Gauntlet).", ephemeral=True)
                return # Stop, card is not consumed
            # --- END PRE-CHECK ---

            # --- EFFECT ---
            new_pos = 20 # Bank Standing tile
            log_command(
                team_name,
                "/card_effect_set_tile",
                {"team": team_name, "tile": new_pos}
            )
            embed_description = f"**{team_name}** used **Varrock Tele** and teleported to **Bank Standing** (Tile 20)!"

            if rolls_available == 0:
                increment_rolls_available(team_name)
                embed_description += "\n\n> 🎲 You had no rolls, so you gained one!"

            # Check if they landed on a card tile (though tile 20 is not one)
            await check_and_award_card_on_land(team_name, new_pos, log_chan, "teleporting to")
        # ======================================================================
        # 🔹 END: NEW CARD - VARROCK TELE
        # ======================================================================
        
        # ======================================================================
        # 🔹 START: NEW CARD - TELE OTHER
        # ======================================================================
        elif selected_card['name'] == "Tele Other":
            # --- PRE-CHECK ---
            all_teams_data = team_data_sheet.get_all_records()
            caster_pos = -1
            opponents = []

            for record in all_teams_data:
                current_team_name = record.get("Team")
                if current_team_name == team_name:
                    caster_pos = int(record.get("Position", -1))
                elif current_team_name:
                    opponents.append({
                        "team": current_team_name,
                        "pos": int(record.get("Position", -1))
                    })
            
            if not opponents:
                await interaction.followup.send("❌ Card effect failed: There are no other teams to swap with.", ephemeral=True)
                return # Stop, card is not consumed
            # --- END PRE-CHECK ---

            # --- TARGET SELECTION & EFFECT ---
            target = random.choice(opponents)
            target_team = target["team"]
            target_pos = target["pos"]

            embed_description = f"**{team_name}** used **Tele Other** on **{target_team}**!\n\n"

            # Vengeance Check (Highest Priority)
            if check_and_consume_vengeance(target_team):
                embed_description += f"💀 But **{target_team}** had Vengeance active! The teleport fizzled, and both cards were consumed!"
                # No swap occurs, but both cards are used.
            
            # Redemption Check (Second Priority)
            elif check_and_consume_redemption(target_team):
                embed_description += f"🩵 But **{target_team}**'s Redemption activated! The teleport was cancelled!"
                if log_chan:
                    fizzle_embed = discord.Embed(
                        title="🩵 Redemption Activated!",
                        description=f"**{team_name}** tried to use **Tele Other** on you, but your **Redemption** activated!",
                        color=discord.Color.blue()
                    )
                    await log_chan.send(content=f"To {target_team}:", embed=fizzle_embed)

            # Normal Effect
            else:
                embed_description += f"🔄 **{team_name}** (from tile {caster_pos}) has swapped places with **{target_team}** (from tile {target_pos})!"
                
                # Log commands for Godot to process the swap
                log_command(team_name, "/card_effect_set_tile", {"team": team_name, "tile": target_pos})
                log_command(team_name, "/card_effect_set_tile", {"team": target_team, "tile": caster_pos})

                # Check if either team landed on a special tile
                await check_and_award_card_on_land(team_name, target_pos, log_chan, "being teleported to")
                await check_and_award_card_on_land(target_team, caster_pos, log_chan, "being teleported to")

        # ======================================================================
        # 🔹 END: NEW CARD - TELE OTHER
        # ======================================================================

        # --- Other Cards (default use) ---
        else:
            embed_description = f"**{team_name}** used the {card_type} card:\n\n> {final_card_text}"
        
        
        # --- 3. Clear Data IF NOT a status activation ---
        if not is_status_activation:
            # Clear Wildcard Data (if any)
            if team_wildcard_value is not None:
                wildcard_data.pop(team_name, None) # Remove team's roll/status
                card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
                print(f"✅ Cleared wildcard for {team_name} from card {selected_card['name']}")
            
            # Remove Team from "Held By"
            cell_val = str(card_sheet.cell(card_row, 3).value or "")
            teams = [t.strip() for t in cell_val.split(',') if t.strip()]
            if team_name in teams:
                teams.remove(team_name)
            card_sheet.update_cell(card_row, 3, ", ".join(teams))
            
            # --- 4. Send Confirmation Embed ---
            if log_chan:
                embed = discord.Embed(
                    title=f"🃏 Card Played: {selected_card['name']}",
                    description=embed_description,
                    color=discord.Color.green()
                )
                await log_chan.send(embed=embed)
            
            await interaction.followup.send(f"✅ **{interaction.user.display_name}** used the card: **{selected_card['name']}**!", ephemeral=False)
        
        # ✅ NEW: Set "Used Card This Turn" flag
        # This runs on ANY successful use (activation or consumption)
        set_used_card_flag(team_name, "yes")
            
    except Exception as e:
        print(f"❌ Error in /use_card: {e}")
        await interaction.followup.send(f"❌ An error occurred while using the card: {e}", ephemeral=True)
# ✅ END: Updated 'use_card' command


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# ✅ THIS IS THE MISSING PIECE
bot.run(os.getenv('bot_token'))
