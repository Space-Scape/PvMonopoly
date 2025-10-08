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
drop_log_sheet = sheet.worksheet("DropLog")
item_values_sheet = sheet.worksheet("ItemValues")

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
                item_values_records = item_values_sheet.get_all_records()
                gp_lookup = {item['Item']: int(str(item['GP']).replace(',', '')) for item in item_values_records}
                drop_gp_value = gp_lookup.get(self.drop, 0)

                if drop_gp_value > 0 and team_name != "*No team*":
                    team_data_records = team_data_sheet.get_all_records()
                    for idx, record in enumerate(team_data_records, start=2):
                        if record.get("Team") == team_name:
                            current_gp = int(record.get("GP", 0) or 0)
                            new_gp = current_gp + drop_gp_value
                            team_data_sheet.update_cell(idx, 8, new_gp) # GP is in Column H (8)
                            print(f"✅ Awarded {drop_gp_value} GP to {team_name}. New total: {new_gp}")
                            if log_chan:
                                await log_chan.send(f"<:MaxCash:1347684049040183427> **{team_name}** earned **{drop_gp_value:,} GP** from a **{self.drop}** drop!")
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

    records = team_data_sheet.get_all_records()
    rolls_available = 0
    for record in records:
        if record.get("Team") == team_name:
            rolls_available = int(record.get("Rolls Available", 0) or 0)
            break

    if rolls_available <= 0:
        await interaction.followup.send(
            "❌ Your team has no rolls available right now.",
            ephemeral=True
        )
        return

    result = random.randint(1, 6)
    await interaction.followup.send(f"🎲 **{interaction.user.display_name}** from **{team_name}** rolled a **{result}**!")
    log_command(
        interaction.user.name,
        "/roll",
        {
            "team": team_name,
            "roll": result
        }
    )

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

        eligible_cards = []
        for i, row in enumerate(rows, start=2):
            held_by = str(row.get("Held By Team", "")) # Force to string
            if team_name not in held_by:
                eligible_cards.append({"index": i, "data": row})
        
        if not eligible_cards:
            await log_channel.send(f"ℹ️ **{team_name}** tried to draw a {card_type} card, but none were available!")
            return

        chosen_card = random.choice(eligible_cards)
        card_row_index = chosen_card["index"]
        card_data = chosen_card["data"]
        
        held_by_str = str(card_sheet.cell(card_row_index, 3).value or "") # Force to string
        new_held_by = f"{held_by_str}, {team_name}".strip(", ")
        card_sheet.update_cell(card_row_index, 3, new_held_by)

        card_name = card_data.get("Name")
        card_text = card_data.get("Card Text")
        
        embed = discord.Embed(
            title=f"🎴 {card_type} Card Drawn!",
            description=f"**{team_name}** drew **{card_name}**!\n\n> {card_text}",
            color=discord.Color.gold() if card_type == "Chest" else discord.Color.blue()
        )
        await log_channel.send(embed=embed) 

    except Exception as e:
        print(f"❌ Error in team_receives_card: {e}")

def get_held_cards(sheet_obj, team_name: str):
    cards = []
    try:
        data = sheet_obj.get_all_records()
        for idx, row in enumerate(data, start=2):
            held_by = str(row.get("Held By Team", "")) # Force to string
            if held_by and team_name in held_by:
                cards.append({
                    "row_index": idx,
                    "name": row.get("Name"),
                    "text": row.get("Card Text"),
                })
    except Exception as e:
        print(f"❌ Error in get_held_cards: {e}")
    return cards

@bot.tree.command(name="show_cards", description="Show all cards currently held by your team.")
async def show_cards(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    team_name = get_team(interaction.user)
    if not team_name:
        await interaction.followup.send("❌ You don't have a team role assigned.", ephemeral=True)
        return

    chest_cards = get_held_cards(chest_sheet, team_name)
    chance_cards = get_held_cards(chance_sheet, team_name)

    if not chest_cards and not chance_cards:
        await interaction.followup.send("Your team holds no cards.", ephemeral=True)
        return

    embed = discord.Embed(title=f"{team_name}'s Hand", color=discord.Color.purple())
    
    card_list = ""
    for i, card in enumerate(chest_cards):
        card_list += f"**{i}:** `[Chest]` {card['name']}\n"
    
    offset = len(chest_cards)
    for i, card in enumerate(chance_cards):
        card_list += f"**{i+offset}:** `[Chance]` {card['name']}\n"
        
    embed.description = card_list
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="use_card", description="Use a held card by its index from /show_cards")
@app_commands.describe(index="The index of the card you want to use")
async def use_card(interaction: discord.Interaction, index: int):
    await interaction.response.defer(ephemeral=False) 
    team_name = get_team(interaction.user)
    if not team_name:
        await interaction.followup.send("❌ You are not on a team.", ephemeral=True)
        return

    chest_cards = get_held_cards(chest_sheet, team_name)
    chance_cards = get_held_cards(chance_sheet, team_name)
    all_cards = chest_cards + chance_cards

    if index < 0 or index >= len(all_cards):
        await interaction.followup.send("❌ Invalid card index.", ephemeral=True)
        return
    
    selected_card = all_cards[index]
    card_type = "Chest" if index < len(chest_cards) else "Chance"
    card_sheet = chest_sheet if card_type == "Chest" else chance_sheet
    
    log_command(
        interaction.user.name,
        "/use_card",
        {
            "team": team_name,
            "card_name": selected_card['name'],
            "card_text": selected_card['text'],
            "card_type": card_type
        }
    )
    
    try:
        cell_val = str(card_sheet.cell(selected_card['row_index'], 3).value or "")
        teams = [t.strip() for t in cell_val.split(',') if t.strip()]
        if team_name in teams:
            teams.remove(team_name)
        card_sheet.update_cell(selected_card['row_index'], 3, ", ".join(teams))
    except Exception as e:
        print(f"❌ Error updating card ownership: {e}")

    log_chan = bot.get_channel(LOG_CHANNEL_ID)
    if log_chan:
        embed = discord.Embed(
            title=f"🃏 Card Played: {selected_card['name']}",
            description=f"**{team_name}** used the {card_type} card:\n\n> {selected_card['text']}",
            color=discord.Color.green()
        )
        await log_chan.send(embed=embed)
    
    await interaction.followup.send(f"✅ **{interaction.user.display_name}** used the card: **{selected_card['name']}**!", ephemeral=False)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

bot.run(os.getenv('bot_token'))



