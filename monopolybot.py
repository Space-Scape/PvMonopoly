import os
import discord
from discord.ext import commands
import gspread
from gspread.utils import rowcol_to_a1
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
import json
import asyncio
import math
import random
import traceback
from discord.ui import Modal, TextInput
from discord import app_commands, ui, Interaction, Member, TextStyle
from typing import List, Optional
from discord import ui, Interaction, Member
from typing import Optional
from discord import SelectOption, Attachment
from discord import ui, Interaction, SelectOption, TextStyle, Attachment, Member

# ========== CONFIG ==========
SPREADSHEET_ID = "1OVC8HImUpoh2keU-h2v_b2gFDa4zyfWsaJxBWRoSJ08"
SIGNUP_SPREADSHEET_ID = "1c7TzXlyn8KinCKNJadIBfY_6PcXF-9icbfC_E8NAGqI"
TEAM_ROLES = ["Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6", "Team 7"]

REVIEW_CHANNEL = "1558574050740281466"
LOG_CHANNEL = "1558574472787791972"
GAME_LOG_CHANNEL_ID = 1558574136127787049
GAME_LOG_TEAM_COLOR_MAP = {
    "Team 1": 0x00BCD4,
    "Team 2": 0x9B59B6,
    "Team 3": 0xE74C3C,
    "Team 4": 0x2ECC71,
    "Team 5": 0x00BCD4,
    "Team 6": 0xC4A484,
    "Team 7": 0x3498DB,
}


TEAM_CHANNELS_MAP = {
    "Team 1": 1558575253792366632,
    "Team 2": 1558575281076437102,
    "Team 3": 1558575310172061876
}
TEAM_CHANNEL_IDS_AS_STR = [str(cid) for cid in TEAM_CHANNELS_MAP.values()]

ACTIVE_TEAMS = ["Team 1", "Team 2", "Team 3"]
TEAM_LIST_CONFIG_FILE = "team_list_config.json"

SIGNUP_LIST_CONFIG_FILE = "signup_list_config.json"

EVENT_STAFF_ROLE_ID = 1558581672268537856
EVENT_CAPTAIN_ROLE_ID = 1558581790946500628
BINGO_PLAYER_ROLE_ID = 1558581910211526756

BOARD_SIZE = 40

# ========== CARD EMOJI MAPPING ==========
CARD_EMOJIS = {
    "Escape Crystal": "<:crystal:1558986564124545065>", 
    "Pickpocket": "<:pickpocket:1558986509242212412>",
    "Low Alchemy": "<:lowalch:1558986671725351063>",
    "High Alchemy": "<:MaxCash:1558959942394847372>",
    "Vengeance": "<:venge:1558986464409297077>",
    "Redemption": "<:redemption:1558985458195898389>",
    "Elder Maul": "<:eldermaul:1558986407735861359>",
    "Vile Vigour": "<:vilevigour:1558986367558492200>",
    "Varrock Tele": "<:varrocktele:1558986322532896788>",
    "POH Voucher": "<:pohvoucher:1558986290895003780>",
    "Home Tele": "<:housetp:1558986199685795901>",
    "Dragon Spear": "<:dragon_spear:1558986141846347776>",
    "Rogue's Gloves": "<:roguegloves:1558986623486660648>",
    "Lure": "<:lure:1558986093796392960>",
    "Backstab": "<:boner:1558986033440489563>",
    "Smite": "<:smite:1558986008404697199>",
    "Tele Other": "<:teleother:1558985957561213000>",
    "Tele Block": "<:teleblock:1558985901831364710>",
    "Chest": "<:chest:1558985858516787251>",
    "Chance": "<:chance:1558993615152353360>"
}

GO_TILE = 0
JAIL_TILE = 10
BANK_STANDING_TILE = 20

CHEST_TILES = {2, 17, 33}
CHANCE_TILES = {7, 22, 36}
GLIDER_TILES = {12, 28, 38}

ROLL_GRANTING_TILES = {GO_TILE, BANK_STANDING_TILE} | GLIDER_TILES | CHEST_TILES | CHANCE_TILES

# ---------------------------
# 🔹 Boss-Drop Mapping
# ---------------------------

SCAVENGER_BOSSES = [
    "Dagannoth Kings",
    "Sarachnis",
    "Royal Titans",
    "Vorkath"
]

boss_drops = {
    "Abyssal Sire": ["Abyssal dagger", "Abyssal head", "Abyssal orphan", "Abyssal whip", "Bludgeon claw", "Bludgeon spine", "Bludgeon axon", "Jar of miasma"],
    "Alchemical Hydra": ["Ikkle hydra", "Hydra's claw", "Hydra tail", "Hydra leather", "Hydra's fang", "Hydra's eye", "Hydra's heart", "Jar of chemicals", "Alchemical hydra heads", "Dragon knife", "Dragon thrownaxe"],
    "Araxxor": ["Noxious pommel", "Noxious point", "Noxious blade", "Araxyte fang", "Araxyte head", "Jar of venom", "Nid"],
    "Corp": ["Spectral sigil", "Arcane sigil", "Elysian sigil", "Holy elixir", "Jar of spirits", "Pet dark core", "Spirit shield"],
    "Callisto": ["Callisto cub", "Tyrannical ring", "Dragon pickaxe", "Dragon 2h sword", "Claws of callisto", "Voidwaker hilt"],
    "Cerberus": ["Hellpuppy", "Eternal crystal", "Pegasian crystal", "Primordial crystal", "Jar of souls", "Smouldering stone"],
    "Chambers of Xeric": ["Dexterous prayer scroll", "Arcane prayer scroll", "Twisted buckler", "Dragon hunter crossbow", "Dinh's bulwark", "Ancestral hat", "Ancestral robe top", "Ancestral robe bottom", "Dragon claws", "Elder maul", "Kodai insignia", "Twisted bow", "Olmlet", "Twisted ancestral colour kit", "Metamorphic dust"],
    "Colosseum": ["Sunfire fanatic cuirass", "Sunfire fanatic chausses", "Sunfire fanatic helm", "Echo crystal", "Tonalztics of ralos (uncharged)"],
    "Commander Zilyana": ["Pet zilyana", "Armadyl crossbow", "Saradomin hilt", "Saradomin sword", "Saradomin's light"],
    "Dagannoth Kings": ["Berserker ring", "Warrior ring", "Archers ring", "Seers ring", "Dragon axe", "Pet dagannoth supreme", "Pet dagannoth prime", "Pet dagannoth rex", "Seercull", "Mud Battlestaff", "Fremennik shield", "Fremennik helm", "Fremennik blade", "Rock-shell plate", "Rock-shell legs", "Farseer helm", "Skeletal top", "Skeletal bottoms", "Archer helm", "Spined body", "Spined chaps"],
    "Doom of Mokhaiotl": ["Dom", "Avernic treads", "Eye of ayak (uncharged)", "Mokhaiotl cloth"],
    "Duke Sucellus": ["Baron", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Magus vestige", "Eye of the duke", "Ice quartz"],
    "Gauntlet": ["Youngllef", "Crystal weapon seed", "Crystal armour seed", "Enhanced crystal weapon seed"],
    "General Graardor": ["Pet general graardor", "Bandos hilt", "Bandos chestplate", "Bandos tassets", "Bandos boots"],
    "Grotesque Guardians": ["Noon", "Black tourmaline core", "Granite gloves", "Granite ring", "Granite hammer", "Jar of stone"],
    "Hueycoatl": ["Huberte", "Dragon hunter wand", "Hueycoatl hide", "Tome of earth (empty)"],
    "Kalphite Queen": ["Kalphite princess", "Kq head", "Jar of sand", "Dragon 2h sword", "Dragon chainbody", "Dragon pickaxe"],
    "King Black Dragon": ["Prince black dragon", "Kbd heads", "Dragon pickaxe", "Draconic visage"],
    "Kraken": ["Pet kraken", "Kraken tentacle", "Trident of the seas (full)", "Jar of dirt"],
    "Kree'arra": ["Pet kree'arra", "Armadyl helmet", "Armadyl chestplate", "Armadyl chainskirt", "Armadyl hilt"],
    "K'ril Tsutsaroth": ["Pet K'ril Tsutsaroth", "Zamorakian spear", "Staff of the dead", "Zamorak hilt", "Steam battlestaff"],
    "Moons of Peril": ["Eclipse atlatl", "Eclipse moon helm", "Eclipse moon chestplate", "Eclipse moon tassets", "Dual macuahuitl", "Blood moon helm", "Blood moon chestplate", "Blood moon tassets", "Blue moon spear", "Blue moon helm", "Blue moon chestplate", "Blue moon tassets"],
    "Nightmare": ["Little nightmare", "Nightmare staff", "Inquisitor's great helm", "Inquisitor's hauberk", "Inquisitor's plateskirt", "Inquisitor's mace", "Eldritch orb", "Harmonised orb", "Volatile orb", "Parasitic egg", "Jar of dreams", "Slepey tablet"],
    "Nex": ["Nexling", "Ancient hilt", "Nihil horn", "Zaryte vambraces", "Torva full helm (damaged)", "Torva platebody (damaged)", "Torva platelegs (damaged)"],
    "Phantom Muspah": ["Muphin", "Venator shard", "Ancient icon"],
    "Royal Titans": ["Fire element staff crown", "Mystic vigour prayer scroll", "Bran", "Ice element staff crown", "Deadeye prayer scroll"],
    "Sarachnis": ["Sarachnis cudgel", "Sraracha", "Pristine spider silk"],
    "Scorpia": ["Scorpia's offspring", "Odium shard 3", "Malediction shard 3", "Dragon 2h sword"],
    "Tempoross": ["Tiny tempor", "Big harpoonfish", "Tome of water (empty)", "Tackle box", "Fish barrel", "Dragon harpoon"],
    "The Leviathan": ["Lil'viathan", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Venator vestige", "Leviathan's lure", "Smoke quartz"],
    "The Whisperer": ["Wisp", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Bellator vestige", "Siren's staff", "Shadow quartz"],
    "Theatre of Blood": ["Lil' zik", "Avernic defender hilt", "Ghrazi rapier", "Sanguinesti staff (uncharged)", "Justiciar faceguard", "Justiciar chestguard", "Justiciar legguards", "Scythe of vitur (uncharged)", "Holy ornament kit", "Sanguine ornament kit", "Sanguine dust"],
    "Thermonuclear smoke devil": ["Pet smoke devil", "Occult necklace", "Smoke battlestaff", "Dragon chainbody", "Jar of smoke"],
    "Tombs of Amascut": ["Tumeken's Guardian", "Masori mask", "Masori body", "Masori chaps", "Lightbearer", "Osmumten's fang", "Elidinis' ward", "Tumeken's shadow (uncharged)"],
    "Vardorvis": ["Butch", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Ultor vestige", "Executioner's axe head", "Blood quartz"],
    "Venenatis": ["Venenatis spiderling", "Fangs of venenatis", "Dragon 2h sword", "Dragon pickaxe", "Voidwaker gem", "Treasonous ring"],
    "Vet'ion": ["Vet'ion jr.", "Skull of vet'ion", "Dragon 2h sword", "Dragon pickaxe", "Voidwaker blade", "Ring of the gods", "Skeleton champion scroll"],
    "Vorkath": ["Vorki", "Vorkath's head", "Draconic visage", "Skeletal visage", "Dragonbone necklace", "Jar of decay"],
    "Wintertodt": ["Phoenix", "Tome of fire (empty)", "Pyromancer hood", "Pyromancer garb", "Pyromancer robe", "Pyromancer boots", "Warm gloves", "Bruma Torch"],
    "Yama": ["Soulflame horn", "Oathplate helm", "Oathplate chest", "Oathplate legs"],
    "Zalcano": ["Smolcano", "Crystal tool seed", "Zalcano shard", "Uncut onyx"],
    "Zulrah": ["Pet snakeling", "Tanzanite mutagen", "Magma mutagen", "Jar of swamp", "Tanzanite fang", "Magic fang", "Serpentine visage", "Uncut onyx"]
}

# ========== COG CLASS ==========
class MonopolyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.player_stances = {}
        self.team_scavenges_per_tile = {}
        self.signup_sheet = None
        self.signup_sheet_book = None
        
        required_env_vars = [
            'EVENT_TYPE', 'EVENT_PROJECT_ID', 'EVENT_PRIVATE_KEY_ID', 
            'EVENT_PRIVATE_KEY', 'EVENT_CLIENT_EMAIL', 'EVENT_CLIENT_ID', 
            'EVENT_AUTH_URI', 'EVENT_TOKEN_URI', 'EVENT_AUTH_PROVIDER_X509_CERT_URL', 
            'EVENT_CLIENT_X509_CERT_URL', 'EVENT_UNIVERSE_DOMAIN'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            print("❌ FATAL ERROR: The following required environment variables are missing:")
            for var in missing_vars:
                print(f"- {var}")
            print("Monopoly Cog will not load.")
            return

        print("✅ Monopoly Cog: All required environment variables are present.")

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        private_key_env = os.getenv('EVENT_PRIVATE_KEY')
        if not private_key_env:
            print("❌ FATAL ERROR: 'EVENT_PRIVATE_KEY' environment variable is not set.")
            private_key_formatted = None
        else:
            private_key_formatted = private_key_env.replace("\\n", "\n")

        credentials_dict = {
            "type": os.getenv('EVENT_TYPE'),
            "project_id": os.getenv('EVENT_PROJECT_ID'),
            "private_key_id": os.getenv('EVENT_PRIVATE_KEY_ID'),
            "private_key": private_key_formatted,
            "client_email": os.getenv('EVENT_CLIENT_EMAIL'),
            "client_id": os.getenv('EVENT_CLIENT_ID'),
            "auth_uri": os.getenv('EVENT_AUTH_URI'),
            "token_uri": os.getenv('EVENT_TOKEN_URI'),
            "auth_provider_x509_cert_url": os.getenv('EVENT_AUTH_PROVIDER_X509_CERT_URL'),
            "client_x509_cert_url": os.getenv('EVENT_CLIENT_X509_CERT_URL'),
            "universe_domain": os.getenv('EVENT_UNIVERSE_DOMAIN')
        }
        
        try:
            creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)
            sheet_client = gspread.authorize(creds)
            
            sheet = sheet_client.open_by_key(SPREADSHEET_ID)

            print("Attempting to load worksheets...")
            self.command_log = sheet.worksheet("Command Log")
            print("... loaded Command Log")
            self.team_data_sheet = sheet.worksheet("TeamData")
            print("... loaded TeamData")
            self.chest_sheet = sheet.worksheet("ChestCards")
            print("... loaded ChestCards")
            self.chance_sheet = sheet.worksheet("ChanceCards")
            print("... loaded ChanceCards")
            self.drop_log_sheet = sheet.worksheet("DropLog")
            print("... loaded DropLog")
            self.item_values_sheet = sheet.worksheet("ItemValues")
            print("... loaded ItemValues")
            self.house_data_sheet = sheet.worksheet("HouseData")
            print("... loaded HouseData")
            
            print("✅ Monopoly Cog: Google Sheets initialized.")

            # Signup spreadsheet is optional
            try:
                self.signup_sheet_book = sheet_client.open_by_key(SIGNUP_SPREADSHEET_ID)
                try:
                    self.signup_sheet = self.signup_sheet_book.worksheet("Signups")
                    print("... loaded Signups worksheet (signup sheet)")
                except gspread.exceptions.WorksheetNotFound:
                    self.signup_sheet = self.signup_sheet_book.sheet1
                    print(f"... loaded signup sheet first worksheet: {self.signup_sheet.title}")
                print("✅ Signup sheet initialized.")
            except Exception as signup_err:
                self.signup_sheet = None
                self.signup_sheet_book = None
                print(f"⚠️ Signup sheet not initialized yet: {signup_err}")

        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ FATAL ERROR: Spreadsheet with ID '{SPREADSHEET_ID}' not found.")
        except gspread.exceptions.WorksheetNotFound as e:
            print(f"❌ FATAL ERROR: Could not find a required worksheet in your Google Sheet.")
            print(f"Details: {e}")
        except gspread.exceptions.APIError as e:
            if "PERMISSION_DENIED" in str(e):
                print(f"❌ FATAL ERROR: Permission denied for Spreadsheet ID '{SPREADSHEET_ID}'.")
                print(f"Ensure the service account '{os.getenv('EVENT_CLIENT_EMAIL')}' has 'Editor' permissions on the Google Sheet.")
            else:
                print(f"❌ FATAL ERROR: An API error occurred: {e}")
        except Exception as e:
            print(f"❌ FATAL ERROR: An unexpected error occurred during GSheets initialization:")
            traceback.print_exc()
            print("This might be due to incorrect 'EVENT_' credentials in your .env file.")

    def log_command(self, player_name, command, args_dict):
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            args_json = json.dumps(args_dict)
            self.command_log.append_row([player_name, command, args_json, timestamp, "no"])
            print(f"✅ Logged {command} for {player_name}: {args_json}")
        except Exception as e:
            print(f"❌ Error logging command: {e}")

    def get_team_data(self, team_role_name: str) -> dict:
        """Fetches all data for a specific team."""
        try:
            team_row = self.team_data_sheet.find(team_role_name)
            data = self.team_data_sheet.row_values(team_row.row)
            headers = self.team_data_sheet.row_values(1)
            team_dict = dict(zip(headers, data))
            return team_dict
        except gspread.exceptions.CellNotFound:
            print(f"Error: Team '{team_role_name}' not found in TeamData.")
            return None
        except Exception as e:
            print(f"Error in get_team_data: {e}")
            return None
    
    def get_jail_status(self, team_name: str) -> str:
        """Checks if a team is actually in jail or just visiting."""
        try:
            records = self.team_data_sheet.get_all_records()
            team_info = next((r for r in records if r.get("Team") == team_name), None)
            return str(team_info.get("In Jail", "no")).strip().lower() if team_info else "no"
        except Exception as e:
            print(f"❌ Error getting jail status: {e}")
            return "no"

    def set_jail_status(self, team_name: str, status: str):
        """Updates the team's jail status ('yes' or 'no')."""
        try:
            records = self.team_data_sheet.get_all_records()
            headers = list(records[0].keys())
            
            if "In Jail" not in headers:
                print("❌ 'In Jail' column not found in TeamData sheet.")
                return
                
            col_index = headers.index("In Jail") + 1
            team_row = next((i for i, r in enumerate(records, start=2) if r.get("Team") == team_name), None)
            
            if team_row:
                self.team_data_sheet.update_cell(team_row, col_index, status)
        except Exception as e:
            print(f"❌ Error setting jail status: {e}")
    
    def get_team(self, member: discord.Member) -> Optional[str]:
        for role in member.roles:
            if role.name in TEAM_ROLES:
                return role.name
        return None

    def get_team_channel(self, team_name: str) -> Optional[discord.TextChannel]:
        """Fetches the discord.TextChannel object for a given team name."""
        channel_id = TEAM_CHANNELS_MAP.get(team_name)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                return channel
        print(f"❌ Could not find channel for team: {team_name}")
        return None

    def get_team_name_from_channel(self, channel: Optional[discord.abc.GuildChannel]) -> Optional[str]:
        """Best-effort reverse lookup from a team channel object to its team name."""
        try:
            if not channel:
                return None
            channel_id = getattr(channel, "id", None)
            if channel_id is None:
                return None
            for team_name, team_channel_id in TEAM_CHANNELS_MAP.items():
                if int(team_channel_id) == int(channel_id):
                    return team_name
        except Exception as e:
            print(f"❌ Error resolving team from channel: {e}")
        return None

    def _get_game_log_team_color(self, team_name: Optional[str]) -> discord.Color:
        try:
            return discord.Color(GAME_LOG_TEAM_COLOR_MAP.get(str(team_name), 0x5865F2))
        except Exception:
            return discord.Color.blurple()

    def _format_game_log_title(self, team_name: Optional[str]) -> str:
        return f"🕹️ Game Log • {team_name or 'Unknown Team'}"

    def _normalize_game_log_victim_description(self, description: Optional[str], team_name: Optional[str]) -> Optional[str]:
        """Convert victim-facing phrasing (you/your team) into neutral game-log phrasing."""
        try:
            if not description:
                return description
            team_name = team_name or "Unknown Team"
            desc = str(description).strip()
            first_line = desc.split('\n', 1)[0].strip()
            first_sentence = first_line.split('. ', 1)[0].strip()
            candidate = (first_sentence + ('.' if first_sentence and not first_sentence.endswith('.') else '')) if first_sentence else first_line

            replacements = [
                (" on your team", f" on {team_name}"),
                (" on you", f" on {team_name}"),
                (" your team", f" {team_name}"),
                ("Your team", f"{team_name}"),
                ("You are ", f"{team_name} is "),
                ("You've been ", f"{team_name} was "),
                ("You were ", f"{team_name} was "),
            ]
            for old, new in replacements:
                candidate = candidate.replace(old, new)

            candidate = candidate.replace('**', '')
            return candidate or desc
        except Exception as e:
            print(f"❌ Error normalizing game log victim description: {e}")
            return description

    def _is_secret_game_log_message(self, content: Optional[str] = None, embed: Optional[discord.Embed] = None) -> bool:
        """Messages that should stay private to team channels (activation/status/card-receive secrets)."""
        try:
            parts = []
            if content:
                parts.append(str(content))
            if embed:
                if embed.title:
                    parts.append(str(embed.title))
                if embed.description:
                    parts.append(str(embed.description))
                for field in getattr(embed, 'fields', []):
                    parts.append(str(getattr(field, 'name', '')))
                    parts.append(str(getattr(field, 'value', '')))
            text_blob = ' '.join(parts).lower()

            secret_card_phrases = [
                'drew a chance card', 'drew a chest card',
                'received a chance card', 'received a chest card',
                'tried to draw a chance card', 'tried to draw a chest card'
            ]
            if any(phrase in text_blob for phrase in secret_card_phrases):
                return True

            secret_activation_phrases = [
                'vengeance activated',
                'redemption activated',
                'elder maul activated'
            ]
            if any(phrase in text_blob for phrase in secret_activation_phrases):
                return True

            return False
        except Exception as e:
            print(f"❌ Error checking game log secrecy filter: {e}")
            return False

    async def mirror_to_game_log(
        self,
        channel: Optional[discord.TextChannel],
        *,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        team_name: Optional[str] = None
    ):
        """Mirror public game action messages to the shared game log channel as embeds."""
        try:
            if self._is_secret_game_log_message(content=content, embed=embed):
                return

            if channel is None:
                return

            game_log_channel = self.bot.get_channel(int(GAME_LOG_CHANNEL_ID))
            if not isinstance(game_log_channel, discord.TextChannel):
                print(f"❌ Game log channel {GAME_LOG_CHANNEL_ID} not found")
                return

            if getattr(channel, 'id', None) == getattr(game_log_channel, 'id', None):
                return

            team_name = team_name or self.get_team_name_from_channel(channel) or 'Unknown Team'

            team_color = self._get_game_log_team_color(team_name)
            log_title = self._format_game_log_title(team_name)

            if embed is not None:
                log_embed = embed.copy()
                original_title = str(log_embed.title).strip() if log_embed.title else ""
                original_description = str(log_embed.description).strip() if log_embed.description else ""

                log_embed.color = team_color
                log_embed.title = log_title

                lower_title = original_title.lower()
                lower_desc = original_description.lower()
                looks_victim_facing = (
                    lower_title.startswith('you ')
                    or "you were" in lower_title
                    or "you've" in lower_title
                    or " your team" in lower_desc
                    or " on your team" in lower_desc
                    or lower_desc.startswith('you ')
                )
                if looks_victim_facing and original_description:
                    log_embed.description = self._normalize_game_log_victim_description(original_description, team_name)

                if content:
                    extra = str(content).strip()
                    if extra:
                        if log_embed.description:
                            log_embed.description = f"{log_embed.description}\n{extra}"[:4096]
                        else:
                            log_embed.description = extra[:4096]
                await game_log_channel.send(embed=log_embed)
                return

            if content:
                log_embed = discord.Embed(
                    title=log_title,
                    description=str(content),
                    color=team_color
                )
                await game_log_channel.send(embed=log_embed)
        except Exception as e:
            print(f"❌ Error mirroring to game log: {e}")

    def has_event_captain_role(self, member: discord.Member) -> bool:
        return any(role.id == EVENT_CAPTAIN_ROLE_ID for role in member.roles)

    def has_event_staff_role(self, member: discord.Member) -> bool:
        return any(role.id == EVENT_STAFF_ROLE_ID for role in member.roles)
        
    def get_houses(self) -> list:
        """Retrieves all active houses. Optimized to use exactly 2 API calls total."""
        try:
            house_data = self.house_data_sheet.get_all_records()
            team_data = self.team_data_sheet.get_all_records()
            
            color_map = {}
            for r in team_data:
                color_hex = r.get("BG Color", "#FFFFFF")
                if not str(color_hex).startswith("#"): 
                    color_hex = f"#{color_hex}"
                color_map[r.get("Team")] = color_hex

            houses = []
            for record in house_data:
                tile = int(record.get("Tile", 0) or 0)
                owner = record.get("OwnerTeam", "")
                if tile > 0 and owner:
                    houses.append({"tile": tile, "color": color_map.get(owner, "#FFFFFF")})
            return houses
            
        except Exception as e:
            print(f"❌ Error fetching house data: {e}")
            return []


    def place_house(self, team_name: str, tile_number: int, is_free: bool) -> bool:
        """
        Places or buys a house.
        For POH Voucher (is_free=True), immediately updates the HouseData sheet.
        For normal houses, sends a /buy_house command to the game engine.
        
        :returns: True if successful.
        """
        try:
            if is_free:
                data = self.house_data_sheet.get_all_records()
                updated = False

                for idx, row in enumerate(data, start=2):
                    if int(row.get("Tile", 0)) == tile_number:
                        if row.get("OwnerTeam", "") == team_name:
                            count = int(row.get("HouseCount", 0)) + 1
                        else:
                            count = 1

                        self.house_data_sheet.update_acell(f"C{idx}", team_name)
                        self.house_data_sheet.update_acell(f"D{idx}", str(count))
                        updated = True
                        print(f"<:housetp:1558986199685795901> Updated existing house on tile {tile_number} for {team_name} (now {count} houses).")
                        break

                if not updated:
                    self.house_data_sheet.append_row([tile_number, "", team_name, 1])
                    print(f"<:housetp:1558986199685795901> Added new free house for {team_name} on tile {tile_number}.")

                self.sync_houses_owned(team_name)

                return True

            else:
                self.log_command(
                    team_name,
                    "/buy_house",
                    {"team": team_name, "tile": tile_number}
                )
                return True

        except Exception as e:
            print(f"❌ Error placing house for {team_name} on tile {tile_number}: {e}")
            return False

    def get_team_rolls(self, team_name: str) -> int:
        """
        Retrieves the current 'Rolls Available' count for a team.

        Uses a direct cell read (instead of get_all_records) to avoid stale reads
        immediately after a roll is spent, which can suppress the "Free Roll Granted"
        message on Chance/Chest/Glider/GO/Bank Standing landings.
        """
        try:
            headers = self.team_data_sheet.row_values(1)
            if "Rolls Available" not in headers:
                return 0
            rolls_col_index = headers.index("Rolls Available") + 1

            records = self.team_data_sheet.get_all_records()
            for idx, record in enumerate(records, start=2):
                if record.get("Team") == team_name:
                    raw_val = self.team_data_sheet.cell(idx, rolls_col_index).value
                    raw_str = str(raw_val).replace(',', '').strip() if raw_val is not None else "0"
                    return int(raw_str) if raw_str.lstrip('-').isdigit() else 0
            return 0
        except Exception as e:
            print(f"❌ Error getting team rolls for {team_name}: {e}")
            return 0

    def increment_rolls_available(self, team_name: str):
        try:
            records = self.team_data_sheet.get_all_records()
            for idx, record in enumerate(records, start=2):
                if record.get("Team") == team_name:
                    headers = self.team_data_sheet.row_values(1)
                    if "Rolls Available" not in headers:
                        print("❌ 'Rolls Available' column not found.")
                        return
                    col_index = headers.index("Rolls Available") + 1
                    current_rolls = self.team_data_sheet.cell(idx, col_index).value
                    current_rolls_int = int(current_rolls) if current_rolls and str(current_rolls).isdigit() else 0
                    self.team_data_sheet.update_cell(idx, col_index, current_rolls_int + 1)
                    print(f"✅ Incremented rolls for {team_name} to {current_rolls_int + 1}")
                    return
        except Exception as e:
            print(f"❌ Error incrementing rolls: {e}")

    def decrement_rolls_available(self, team_name: str):
        try:
            records = self.team_data_sheet.get_all_records()
            for idx, record in enumerate(records, start=2):
                if record.get("Team") == team_name:
                    headers = self.team_data_sheet.row_values(1)
                    if "Rolls Available" not in headers:
                        print("❌ 'Rolls Available' column not found.")
                        return
                    col_index = headers.index("Rolls Available") + 1
                    current_rolls = self.team_data_sheet.cell(idx, col_index).value
                    current_rolls_int = int(current_rolls) if current_rolls and str(current_rolls).isdigit() else 0
                    new_val = max(0, current_rolls_int - 1)
                    self.team_data_sheet.update_cell(idx, col_index, new_val)
                    print(f"✅ Decremented rolls for {team_name}: {current_rolls_int} → {new_val}")
                    return
        except Exception as e:
            print(f"❌ Error decrementing rolls: {e}")

    async def process_manual_pass_go(self, team_name: str, team_row_idx: int, team_record: dict) -> str:
        """Helper to process GP and Passes when a card effect forces a player over GO."""
        try:
            all_records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            headers = list(all_records[0].keys())
            
            pass_go_col = headers.index("Go Passes") + 1
            gp_col = headers.index("GP") + 1
            
            cur_passes = int(team_record.get("Go Passes", 0))
            cur_gp = int(str(team_record.get("GP", 0)).replace(',',''))
            
            is_gp_halved = str(team_record.get("GP Halved", "no")).strip().lower() == "yes"
            go_reward = 10_000_000 if is_gp_halved else 20_000_000

            await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, pass_go_col, cur_passes + 1)
            await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, cur_gp + go_reward)
            
            team_chan = self.get_team_channel(team_name)
            if team_chan:
                for _ in range(3):
                    card_type = random.choice(["Chest", "Chance"])
                    await self.team_receives_card(team_name, card_type, team_chan)
            
            if is_gp_halved:
                asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "GP Halved"))
                return f"\n\n<:go:1559018777343950848> **PASS GO!** You crossed GO and received **10,000,000 GP** (Halved by <:ent:1558999589317640262> **The Ents**!) and **3 Random Cards**!"
            
            return f"\n\n<:go:1559018777343950848> **PASS GO!** You crossed GO and received **20,000,000 GP** and **3 Random Cards**!"
            
        except Exception as e:
            print(f"❌ Error processing manual Pass Go: {e}")
            return ""
    
    def get_used_card_flag(self, team_name: str) -> str:
        """Checks the 'Used Card This Turn' flag for a team. Defaults to 'no'."""
        try:
            records = self.team_data_sheet.get_all_records()
            for record in records:
                if record.get("Team") == team_name:
                    return record.get("Used Card This Turn", "no")
        except Exception as e:
            print(f"❌ Error in get_used_card_flag: {e}")
        return "no"

    def set_used_card_flag(self, team_name: str, status: str):
        """Sets the 'Used Card This Turn' flag (Col I) for a team."""
        try:
            records = self.team_data_sheet.get_all_records()
            headers = self.team_data_sheet.row_values(1)
            
            col_name = "Used Card This Turn"
            if col_name not in headers:
                print(f"❌ '{col_name}' column not found in TeamData.")
                return
                
            col_index = headers.index(col_name) + 1

            for idx, record in enumerate(records, start=2):
                if record.get("Team") == team_name:
                    self.team_data_sheet.update_cell(idx, col_index, status)
                    print(f"✅ Set '{col_name}' for {team_name} to '{status}'")
                    return
        except Exception as e:
            print(f"❌ Error in set_used_card_flag: {e}")


    def get_bought_house_flag(self, team_name: str) -> str:
        """Checks the 'Bought House This Turn' flag for a team. Defaults to 'no'."""
        try:
            records = self.team_data_sheet.get_all_records()
            for record in records:
                if record.get("Team") == team_name:
                    return record.get("Bought House This Turn", "no")
        except Exception as e:
            print(f"❌ Error in get_bought_house_flag: {e}")
        return "no"

    def set_bought_house_flag(self, team_name: str, status: str):
        """Sets the 'Bought House This Turn' flag for a team."""
        try:
            records = self.team_data_sheet.get_all_records()
            headers = self.team_data_sheet.row_values(1)
            
            col_name = "Bought House This Turn"
            if col_name not in headers:
                print(f"❌ '{col_name}' column not found in TeamData.")
                return
                
            col_index = headers.index(col_name) + 1

            for idx, record in enumerate(records, start=2):
                if record.get("Team") == team_name:
                    self.team_data_sheet.update_cell(idx, col_index, status)
                    print(f"✅ Set '{col_name}' for {team_name} to '{status}'")
                    return
        except Exception as e:
            print(f"❌ Error in set_bought_house_flag: {e}")

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
                log_chan = interaction.client.get_channel(int(LOG_CHANNEL))
                if log_chan:
                    await log_chan.send(
                        f"❌ Drop submission rejected for {self.submitter.mention} by {interaction.user.mention}.\n"
                        f"**Reason:** {self.reason.value}"
                    )
                else:
                    print(f"❌ RejectModal: Log channel {LOG_CHANNEL} not found.")

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
    
    class CardTargetView(discord.ui.View):
        def __init__(self, cog, user_team: str, valid_targets: list, card_name: str, card_action: str, extra_data: dict = None):
            super().__init__(timeout=180)
            self.cog = cog
            self.user_team = user_team
            self.card_name = card_name
            self.card_action = card_action
            self.extra_data = extra_data or {} 
    
            options = []
            for target in valid_targets:
                desc = None
                if card_action in ["rogues_gloves", "smite"]:
                    try:
                        list_key = "stealable_cards" if card_action == "rogues_gloves" else "smitable_cards"
                        card_list = self.extra_data.get(list_key, [])
                        target_count = len([c for c in card_list if c["victim_team"] == target])
                        desc = f"Holding {target_count} eligible card(s)"
                    except:
                        pass
                elif card_action == "pickpocket":
                    try:
                        gp_amt = self.extra_data.get("target_gp_data", {}).get(target, 0)
                        desc = f"Holding {gp_amt:,} GP"
                    except:
                        pass
                        
                options.append(discord.SelectOption(label=target, description=desc, value=target))
    
            select = discord.ui.Select(placeholder=f"Select target for {card_name}...", options=options)
            select.callback = self.select_callback
            self.add_item(select)
    
        async def select_callback(self, interaction: discord.Interaction):
            if self.cog.get_team(interaction.user) != self.user_team:
                await interaction.response.send_message("❌ You cannot make selections for this team.", ephemeral=True)
                return
    
            target_team = self.children[0].values[0]
            self.children[0].disabled = True
            await interaction.response.edit_message(view=self)
            
            await self.cog.execute_targeted_card_effect(interaction, self.user_team, target_team, self.card_name, self.card_action, self.extra_data)
    
    def log_drop_to_sheet(self, submitted_for: str, team: str, boss: str, drop: str, verified_by: str, screenshot: str):
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            self.drop_log_sheet.append_row([
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


    class DropReviewButtons(ui.View):
        def __init__(self, cog: 'MonopolyCog', submitted_user, drop, image_url, submitting_user, team_mention, boss):
            super().__init__(timeout=None)
            self.cog = cog # Store cog instance
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
            if not self.cog.has_event_staff_role(interaction.user):
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
                await interaction.response.defer(ephemeral=True)

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

                log_chan = self.cog.bot.get_channel(int(LOG_CHANNEL))
                team_name = self.cog.get_team(self.submitted_user) or "*No team*"
                team_chan = self.cog.get_team_channel(team_name)

                if log_chan:
                    mention = self.team_mention or self.submitted_user.mention or self.submitting_user.mention
                    await log_chan.send(content=f"{mention} Drop submission approved by {interaction.user.mention}.", embed=embed)
                    print(f"✅ Sent approval to DropLog ({log_chan.name})")

                await asyncio.to_thread(
                    self.cog.log_drop_to_sheet,
                    submitted_for=str(self.submitted_user),
                    team=team_name,
                    boss=self.boss,
                    drop=self.drop,
                    verified_by=interaction.user.name,
                    screenshot=self.image_url
                )

                is_scavenger = self.boss in SCAVENGER_BOSSES
                scavenger_reward = None
                
                if is_scavenger:
                    scavenger_reward = random.choices(["GP", "Chest", "Chance"], weights=[90, 5, 5], k=1)[0]

                if not is_scavenger or scavenger_reward == "GP":
                    try:
                        gp_multiplier, consumed_card_name = await asyncio.to_thread(self.cog.check_and_consume_alchemy, team_name)

                        item_values_records = await asyncio.to_thread(self.cog.item_values_sheet.get_all_records)
                        gp_lookup = {item['Item']: int(str(item['GP']).replace(',', '')) for item in item_values_records}
                        
                        base_gp_value = gp_lookup.get(self.drop, 0)
                        final_gp_value = base_gp_value * gp_multiplier

                        if is_scavenger:
                            final_gp_value = final_gp_value // 2
                        
                        records = await asyncio.to_thread(self.cog.team_data_sheet.get_all_records)
                        team_record = next((r for r in records if r.get("Team") == team_name), None)
                        
                        is_gp_halved = False
                        is_gp_doubled = False
                        if team_record:
                            is_gp_halved = str(team_record.get("GP Halved", "no")).strip().lower() == "yes"
                            is_gp_doubled = str(team_record.get("GP Doubled", "no")).strip().lower() == "yes"
                            
                        if is_gp_doubled:
                            final_gp_value = final_gp_value * 2
                        if is_gp_halved:
                            final_gp_value = final_gp_value // 2
                            
                        original_gp_value_pre_tax = final_gp_value

                        bonus_parts = []
                        if gp_multiplier > 1 and consumed_card_name:
                            emoji = CARD_EMOJIS.get(consumed_card_name, "")
                            bonus_parts.append(f"x{gp_multiplier} from {emoji} **{consumed_card_name}**")
                        if is_gp_doubled:
                            bonus_parts.append("Doubled by 🎯 **Pinball Troll**")
                        if is_gp_halved:
                            bonus_parts.append("Halved by <:ent:1558999589317640262> **The Ents**")
                            
                        alchemy_bonus = f" ({', '.join(bonus_parts)}!)" if bonus_parts else ""

                        if final_gp_value > 0 and team_name != "*No team*":
                            house_records = await asyncio.to_thread(self.cog.house_data_sheet.get_all_records)
                            current_tile_for_tax = int(team_record.get("Position", 0) or 0) if team_record else None

                            tax_amount = 0
                            owner_team = None
                            house_count = 0

                            if current_tile_for_tax is not None:
                                for hrec in house_records:
                                    tile = int(hrec.get("Tile", 0) or 0)
                                    if tile == current_tile_for_tax:
                                        owner_team = hrec.get("OwnerTeam", "")
                                        house_count = int(hrec.get("HouseCount", 0) or 0)
                                        break

                                if owner_team and owner_team != team_name and house_count > 0:
                                    tax_map = {1: 0.20, 2: 0.40, 3: 0.60, 4: 0.80}
                                    tax_percent = tax_map.get(house_count, 0)
                                    tax_amount = int(final_gp_value * tax_percent)
                                    
                                    has_phoenix = str(team_record.get("Phoenix Necklace", "no")).strip().lower() == "yes"
                                    
                                    if has_phoenix and tax_amount > 0:
                                        await self.cog.consume_phoenix_necklace(team_name)
                                        blocked_tax = tax_amount
                                        tax_amount = 0
                                        
                                        phoenix_msg = (
                                            f"<:pneck:1558990483110367242> **Phoenix Necklace Shattered!** **{team_name}** was about to pay "
                                            f"**{blocked_tax:,} GP** in taxes to **{owner_team}**, but the necklace completely absorbed the blow!"
                                        )
                                        
                                        if team_chan:
                                            await team_chan.send(phoenix_msg)
                                            await self.cog.mirror_to_game_log(team_chan, content=phoenix_msg, team_name=team_name)
                                            
                                        owner_team_chan = self.cog.get_team_channel(owner_team)
                                        if owner_team_chan:
                                            await owner_team_chan.send(phoenix_msg)
                                            await self.cog.mirror_to_game_log(owner_team_chan, content=phoenix_msg, team_name=owner_team)
                                    else:
                                        final_gp_value -= tax_amount

                            headers = await asyncio.to_thread(self.cog.team_data_sheet.row_values, 1)
                            gp_col_index = headers.index("GP") + 1

                            for idx, record in enumerate(records, start=2):
                                if record.get("Team") == team_name:
                                    current_gp_raw = str(record.get("GP", 0)).replace(',', '')
                                    current_gp = int(current_gp_raw) if current_gp_raw.isdigit() else 0
                                    new_gp = max(0, current_gp + final_gp_value)
                                    
                                    await asyncio.to_thread(self.cog.team_data_sheet.update_cell, idx, gp_col_index, new_gp)
                                    
                                    if is_scavenger:
                                        gp_message = (
                                            f"<:MaxCash:1558959942394847372> **Scavenger Loot!** **{team_name}** rolled the GP prize and earned **{final_gp_value:,} GP** "
                                            f"from their off-board **{self.drop}** drop!{alchemy_bonus}"
                                        )
                                    else:
                                        gp_message = (
                                            f"<:MaxCash:1558959942394847372> **{team_name}** earned **{final_gp_value:,} GP** "
                                            f"from a **{self.drop}** drop!{alchemy_bonus}"
                                        )

                                    if team_chan:
                                        await team_chan.send(gp_message)
                                        await self.cog.mirror_to_game_log(team_chan, content=gp_message, team_name=team_name)
                                    break

                            if tax_amount > 0 and owner_team:
                                owner_team_chan = self.cog.get_team_channel(owner_team)
                                for o_idx, orec in enumerate(records, start=2):
                                    if orec.get("Team") == owner_team:
                                        owner_gp_raw = str(orec.get("GP", 0)).replace(',', '')
                                        owner_gp = int(owner_gp_raw) if owner_gp_raw.isdigit() else 0
                                        new_owner_gp = owner_gp + tax_amount
                                        await asyncio.to_thread(self.cog.team_data_sheet.update_cell, o_idx, gp_col_index, new_owner_gp)
                                        
                                        tax_message = (
                                            f"<:houseicon:1438085020156821555> **House Tax:** {team_name} paid **{tax_amount:,} GP** "
                                            f"to **{owner_team}** for a level {house_count} house on tile {current_tile_for_tax} "
                                            f"(Original Value: **{original_gp_value_pre_tax:,} GP** | Tax: **{int(tax_percent * 100)}%**)."
                                        )
                                        if team_chan:
                                            await team_chan.send(tax_message)
                                            await self.cog.mirror_to_game_log(team_chan, content=tax_message, team_name=team_name)
                                        if owner_team_chan:
                                            await owner_team_chan.send(tax_message)
                                            await self.cog.mirror_to_game_log(owner_team_chan, content=tax_message, team_name=owner_team)
                                        break

                        if is_gp_doubled:
                            asyncio.create_task(asyncio.to_thread(self.cog.clear_flag_column, team_name, "GP Doubled"))

                    except Exception as inner_e:
                        print(f"❌ Error in GP calculation: {inner_e}")
                        traceback.print_exc()

                # --- ROLL / CARD GRANTING LOGIC ---
                try:
                    records = await asyncio.to_thread(self.cog.team_data_sheet.get_all_records)
                    current_tile = None
                    is_in_jail = False
                    team_row_idx = None
                    target_record = None
                    
                    for idx, record in enumerate(records, start=2):
                        if record.get("Team") == team_name:
                            current_tile = int(record.get("Position", 0) or 0)
                            is_in_jail = str(record.get("In Jail", "no")).strip().lower() == "yes"
                            team_row_idx = idx
                            target_record = record
                            break
                    
                    if is_scavenger and current_tile is not None and target_record is not None:
                        headers = list(target_record.keys())
                        
                        boss_col_map = {
                            "Vorkath": "Scavenged Vorkath",
                            "Dagannoth Kings": "Scavenged DKS",
                            "Sarachnis": "Scavenged Sarachnis",
                            "Royal Titans": "Scavenged Titans"
                        }
                        
                        missing_cols = [col for col in boss_col_map.values() if col not in headers]
                        if missing_cols:
                            print(f"⚠️ Missing columns in Sheet: {missing_cols}")
                        else:
                            vork_idx = headers.index("Scavenged Vorkath") + 1
                            dks_idx = headers.index("Scavenged DKS") + 1
                            sara_idx = headers.index("Scavenged Sarachnis") + 1
                            titan_idx = headers.index("Scavenged Titans") + 1
                            
                            vork_done = str(target_record.get("Scavenged Vorkath", "")).strip().lower() in ["yes", "true", "1"]
                            dks_done = str(target_record.get("Scavenged DKS", "")).strip().lower() in ["yes", "true", "1"]
                            sara_done = str(target_record.get("Scavenged Sarachnis", "")).strip().lower() in ["yes", "true", "1"]
                            titan_done = str(target_record.get("Scavenged Titans", "")).strip().lower() in ["yes", "true", "1"]
                            
                            target_col_name = boss_col_map.get(self.boss)
                            target_col_idx = headers.index(target_col_name) + 1
                            
                            if self.boss == "Vorkath": vork_done = True
                            elif self.boss == "Dagannoth Kings": dks_done = True
                            elif self.boss == "Sarachnis": sara_done = True
                            elif self.boss == "Royal Titans": titan_done = True
                            
                            has_all_4 = vork_done and dks_done and sara_done and titan_done
                            
                            if has_all_4:
                                await asyncio.to_thread(self.cog.increment_rolls_available, team_name)
                                
                                await asyncio.to_thread(self.cog.team_data_sheet.update_cell, team_row_idx, target_col_idx, "Yes")

                                if "Scavenge Progress" in headers:
                                    prog_col_idx = headers.index("Scavenge Progress") + 1
                                    await asyncio.to_thread(self.cog.team_data_sheet.update_cell, team_row_idx, prog_col_idx, 4)
                                
                                tax_msg = ""
                                house_records = await asyncio.to_thread(self.cog.house_data_sheet.get_all_records)
                                
                                house_on_current = None
                                any_other_house = None
                                
                                for h_idx, h_rec in enumerate(house_records, start=2):
                                    if h_rec.get("OwnerTeam") == team_name and int(h_rec.get("HouseCount", 0) or 0) > 0:
                                        if int(h_rec.get("Tile", 0) or 0) == current_tile:
                                            house_on_current = (h_idx, int(h_rec.get("HouseCount", 0)))
                                            break
                                        elif any_other_house is None:
                                            any_other_house = (h_idx, int(h_rec.get("HouseCount", 0)))
                                            
                                house_count_col = list(house_records[0].keys()).index("HouseCount") + 1 if house_records else 0
                                
                                if house_on_current:
                                    await asyncio.to_thread(self.cog.house_data_sheet.update_cell, house_on_current[0], house_count_col, 0)
                                    tax_msg = f"🏠 **Skip Tax:** You forfeited your property rights here. The house you built on Tile {current_tile} was instantly **destroyed**!"
                                elif any_other_house:
                                    new_count = any_other_house[1] - 1
                                    await asyncio.to_thread(self.cog.house_data_sheet.update_cell, any_other_house[0], house_count_col, new_count)
                                    tax_msg = "🏠 **Skip Tax:** Since you didn't have a house on this tile, the Bank **repossessed 1 house** from another property you own!"
                                else:
                                    tax_msg = "🏠 **Skip Tax:** You own zero houses, so the Bank couldn't repossess anything! (However, you forfeit the right to build on this tile for your current turn)."

                                bingo_embed = discord.Embed(
                                    title="<:quest:1559017087723241593> SCAVENGING COMPLETED! <:quest:1559017087723241593>",
                                    description=(
                                        f"**{team_name}**'s scavengers have successfully hunted 1 drop from all 4 Scavenger Bosses on Tile {current_tile}!\n\n"
                                        f"{tax_msg}\n\n"
                                        f"🎲 **A FREE ROLL has been granted to the team!**"
                                    ),
                                    color=discord.Color.orange()
                                )
                                if team_chan:
                                    await team_chan.send(embed=bingo_embed)
                                    await self.cog.mirror_to_game_log(team_chan, embed=bingo_embed, team_name=team_name)
                            
                            else:
                                await asyncio.to_thread(self.cog.team_data_sheet.update_cell, team_row_idx, target_col_idx, "Yes")

                                boss_count = sum([vork_done, dks_done, sara_done, titan_done])
                                
                                if "Scavenge Progress" in headers:
                                    prog_col_idx = headers.index("Scavenge Progress") + 1
                                    await asyncio.to_thread(self.cog.team_data_sheet.update_cell, team_row_idx, prog_col_idx, boss_count)
                                
                                if team_chan:
                                    await team_chan.send(f"<:quest:1559017087723241593> **Scavenger Drop Approved!**\nYour team has completed **{boss_count}/4** Scavenger bosses for this tile. (**{self.boss}** marked as complete!)")

                    if not is_scavenger:
                        tile_boss_map = self.cog._get_tile_boss_map()
                        bosses_for_tile = tile_boss_map.get(current_tile, [])
                        
                        if self.boss in bosses_for_tile:
                            await asyncio.to_thread(self.cog.increment_rolls_available, team_name)
                            
                            extra_jail_text = ""
                            if current_tile == 10 and is_in_jail:
                                await asyncio.to_thread(self.cog.set_jail_status, team_name, "no")
                                extra_jail_text = "\n\n⛓️ **Jailbreak!** Your team has completed their sentence and is no longer In Jail!"

                            if team_chan:
                                roll_grant_embed = discord.Embed(
                                    title="🎲 Roll Granted!",
                                    description=f"Your team landed a drop at **{self.boss}**! A free roll has been granted!{extra_jail_text}",
                                    color=discord.Color.green()
                                )
                                await team_chan.send(embed=roll_grant_embed)
                                await self.cog.mirror_to_game_log(team_chan, embed=roll_grant_embed, team_name=team_name)
                    else:
                        if scavenger_reward in ["Chest", "Chance"]:
                            if team_chan:
                                scavenge_embed = discord.Embed(
                                    title="<:chest:1558985858516787251> Scavenger Loot!",
                                    description=f"Your off-board grinding at **{self.boss}** paid off! Instead of GP, you found a **{scavenger_reward}** card!",
                                    color=discord.Color.purple()
                                )
                                await team_chan.send(embed=scavenge_embed)
                                await self.cog.mirror_to_game_log(team_chan, embed=scavenge_embed, team_name=team_name)
                                
                            await self.cog.team_receives_card(team_name, scavenger_reward, team_chan)

                except Exception as roll_e:
                    print(f"❌ Error checking tile before granting roll/card: {roll_e}")
                    traceback.print_exc()

                await interaction.followup.send("✅ Drop approved and logged.", ephemeral=True)
                
                # --- RARE DROP TABLE ---
                try:
                    rdt_chance = random.randint(1, 100)
                    if rdt_chance <= 10 and team_name != "*No team*":
                        all_recs = await asyncio.to_thread(self.cog.team_data_sheet.get_all_records)
                        t_info = next((r for r in all_recs if r.get("Team") == team_name), {})
                        
                        hp = str(t_info.get("Protect Item", "no")).strip().lower() == "yes"
                        hr = str(t_info.get("Ring of Recoil", "no")).strip().lower() == "yes"
                        hpn = str(t_info.get("Phoenix Necklace", "no")).strip().lower() == "yes"
                        hc = str(t_info.get("Ring of Charos", "no")).strip().lower() == "yes"
                        hs = str(t_info.get("Ring of Stone", "no")).strip().lower() == "yes"

                        if not (hp or hr or hpn or hc or hs):
                            passive_choices = ["Protect Item", "Ring of Recoil", "Phoenix Necklace", "Ring of Charos", "Ring of Stone"]
                            chosen_passive = random.choice(passive_choices)
                            
                            headers = list(all_recs[0].keys())
                            if chosen_passive in headers:
                                t_idx = all_recs.index(t_info) + 2
                                c_idx = headers.index(chosen_passive) + 1
                                await asyncio.to_thread(self.cog.team_data_sheet.update_cell, t_idx, c_idx, "yes")
                                
                                emoji_map = {
                                    "Protect Item": "<:protect_item:1559003530050670632>", 
                                    "Ring of Recoil": "<:recoil:1558985588055609374>", 
                                    "Phoenix Necklace": "<:pneck:1558990483110367242>", 
                                    "Ring of Charos": "<:charos:1558985798483837049>",
                                    "Ring of Stone": "<:ring_of_stone:1558985677134241873>"
                                }
                                p_emoji = emoji_map.get(chosen_passive, "💎")
                                
                                passive_descriptions = {
                                    "Protect Item": "Passive - Saves a player from item losses until one occurs.",
                                    "Ring of Recoil": "Passive - Affects triggered on you are also triggered to the attacker.",
                                    "Phoenix Necklace": "Passive - Automatically shatters to absorb your next rent payment.",
                                    "Ring of Charos": "Passive - Automatically halves the cost of your next house purchase.",
                                    "Ring of Stone": "Passive - Automatically shatters to block forced movement or teleports."
                                }
                                card_text = passive_descriptions.get(chosen_passive, "")
                                display_name = "Protect Item Scroll" if chosen_passive == "Protect Item" else ("Ring of Charos (a)" if chosen_passive == "Ring of Charos" else chosen_passive)
                                
                                rdt_embed = discord.Embed(
                                    title="💎 Rare Drop Table Hit!",
                                    description=(
                                        f"**{team_name}** got lucky on the RDT!\n"
                                        f"Along with your boss drop, you found a **{display_name}**!\n\n"
                                        f"> {card_text}\n\n"
                                        f"{p_emoji} This item has been added to your inventory and is now **ACTIVE**."
                                    ),
                                    color=discord.Color.magenta()
                                )
                                if team_chan:
                                    await team_chan.send(embed=rdt_embed)
                except Exception as rdt_err:
                    print(f"❌ Error during RDT roll: {rdt_err}")

            except Exception as e:
                print(f"❌ Error in overall approve_button: {e}")
                traceback.print_exc()
                await interaction.followup.send(f"❌ Error approving drop: {e}", ephemeral=True)

        @ui.button(label="Reject Drop", style=discord.ButtonStyle.danger, custom_id="reject_drop")
        async def reject_button(self, interaction: discord.Interaction, button: ui.Button):
            if not self.current_reviewer:
                await interaction.response.send_message("You must start reviewing before rejecting.", ephemeral=True)
                return
            await interaction.response.send_modal(self.cog.RejectModal(self.message, self.submitted_user))

    class RestrictedBossSelectView(ui.View):
        def __init__(self, cog: 'MonopolyCog', submitting_user: discord.Member, submitted_for: discord.Member, screenshot_url: str, valid_bosses: list, current_tile: int):
            super().__init__(timeout=180)
            self.cog = cog
            self.submitting_user = submitting_user
            self.submitted_for = submitted_for
            self.screenshot_url = screenshot_url
            self.current_tile = current_tile

            options = [discord.SelectOption(label=boss) for boss in valid_bosses]
            self.boss_dropdown = ui.Select(
                placeholder="Select the boss",
                options=options,
                min_values=1,
                max_values=1,
            )
            self.boss_dropdown.callback = self.boss_selected
            self.add_item(self.boss_dropdown)

        async def boss_selected(self, interaction: discord.Interaction):
            selected_boss = self.boss_dropdown.values[0]
            await interaction.response.edit_message(
                content=f"Selected boss: **{selected_boss}**. Now select the drop:",
                view=self.cog.DropSelectView(
                    cog=self.cog,
                    submitting_user=self.submitting_user,
                    submitted_for=self.submitted_for,
                    screenshot_url=self.screenshot_url,
                    boss=selected_boss,
                    current_tile=self.current_tile
                ),
            )

    class DropSelectView(ui.View):
        def __init__(self, cog: 'MonopolyCog', submitting_user: discord.Member, submitted_for: discord.Member, screenshot_url: str, boss: str, current_tile: int):
            super().__init__(timeout=180)
            self.cog = cog
            self.add_item(self.cog.DropSelect(cog, submitting_user, submitted_for, screenshot_url, boss, current_tile))

    class DropSelect(ui.Select):
        def __init__(self, cog: 'MonopolyCog', submitting_user: discord.Member, submitted_for: discord.Member, screenshot_url: str, boss: str, current_tile: int):
            self.cog = cog
            self.submitting_user = submitting_user
            self.submitted_for = submitted_for
            self.screenshot_url = screenshot_url
            self.boss = boss
            self.current_tile = current_tile
            options = [discord.SelectOption(label=drop) for drop in sorted(boss_drops[boss])]
            super().__init__(placeholder=f"Select the drop from {boss}", options=options, min_values=1, max_values=1)

        async def callback(self, interaction: discord.Interaction):
            selected_drop = self.values[0]
            
            team_name = self.cog.get_team(self.submitted_for) or "*No team*"
            if team_name == "*No team*":
                await interaction.response.edit_message(content=f"❌ **{self.submitted_for.display_name}** is not on a team.", view=None, embed=None)
                return

            is_scavenger = self.boss in SCAVENGER_BOSSES
            requested_stance = "scavenge" if is_scavenger else "main"
            
            allowed, error_msg = self.cog.check_turn_stance(self.submitted_for.id, team_name, self.current_tile, requested_stance)
            if not allowed:
                await interaction.response.edit_message(content=error_msg, view=None, embed=None)
                return
                
            self.cog.lock_turn_stance(self.submitted_for.id, team_name, self.current_tile, requested_stance)

            embed = discord.Embed(title=f"Drop Submission: {self.boss}", colour=discord.Colour.blurple())
            embed.add_field(name="Review Status", value="Awaiting review...", inline=False)
            embed.add_field(name="Submitted For", value=f"{self.submitted_for.mention} `({self.submitted_for.id})`", inline=False)
            embed.add_field(name="Drop Received", value=selected_drop, inline=False)
            embed.add_field(name="Submitted By", value=f"{self.submitting_user.mention} `({self.submitting_user.id})`", inline=False)
            embed.set_image(url=self.screenshot_url)

            review_channel = self.cog.bot.get_channel(int(REVIEW_CHANNEL))
            if not review_channel:
                await interaction.response.edit_message(content="❌ Review channel not found.", view=None, embed=None)
                return

            team_role_obj = discord.utils.get(interaction.guild.roles, name=team_name)
            team_mention = team_role_obj.mention if team_role_obj else team_name

            view = self.cog.DropReviewButtons(
                cog=self.cog,
                submitted_user=self.submitted_for,
                drop=selected_drop,
                image_url=self.screenshot_url,
                submitting_user=self.submitting_user,
                team_mention=team_mention,
                boss=self.boss,
            )

            sent_msg = await review_channel.send(embed=embed, view=view)
            view.message = sent_msg

            await interaction.response.edit_message(
                content=f"✅ Drop submission for **{self.boss} - {selected_drop}** sent for review.",
                embed=None,
                view=None,
            )

    def get_teleblock_status(self, team_name):
        """Checks if a team is teleblocked. Returns 'yes' or 'no'."""
        try:
            team_data_headers = self.team_data_sheet.row_values(1)
            tb_col_index = team_data_headers.index("Teleblocked") + 1
            team_cell = self.team_data_sheet.find(team_name)
            if team_cell:
                return self.team_data_sheet.cell(team_cell.row, tb_col_index).value or "no"
            return "no"
        except Exception as e:
            print(f"Error getting teleblock status for {team_name}: {e}")
            return "no"

    def set_teleblock_status(self, team_name, status="yes"):
        """Sets a team's teleblock status. status should be 'yes' or 'no'."""
        try:
            team_data_headers = self.team_data_sheet.row_values(1)
            tb_col_index = team_data_headers.index("Teleblocked") + 1
            team_cell = self.team_data_sheet.find(team_name)
            if team_cell:
                self.team_data_sheet.update_cell(team_cell.row, tb_col_index, status)
                print(f"Set teleblock status for {team_name} to {status}")
        except Exception as e:
            print(f"Error setting teleblock status for {team_name}: {e}")

    @app_commands.command(name="start_game", description="[Staff] Start the game and deal 3 random cards to all active teams.")
    async def start_game(self, interaction: discord.Interaction):
        if not self.has_event_staff_role(interaction.user):
            await interaction.response.send_message("❌ Only Event Staff can use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)
        
        for team_name in ACTIVE_TEAMS:
            team_chan = self.get_team_channel(team_name)
            if team_chan:
                await team_chan.send(f"<a:fire:1559013496455168082> **The game has begun!** Here are your 3 starting cards. (Type /use_card followed by the [index number] to use cards):")
                for _ in range(3):
                    card_type = random.choice(["Chest", "Chance"])
                    await self.team_receives_card(team_name, card_type, team_chan)
    
    @app_commands.command(name="signup", description="Submit your signup with RSN and a screenshot")
    @app_commands.describe(rsn="Your RSN (RuneScape name)", screenshot="Upload a screenshot for your signup")
    async def signup(self, interaction: discord.Interaction, rsn: str, screenshot: discord.Attachment):
        rsn_clean = (rsn or "").strip()
        if not rsn_clean:
            await interaction.response.send_message("❌ You must provide an RSN.", ephemeral=True)
            return

        content_type = (getattr(screenshot, "content_type", None) or "").lower()
        filename = (getattr(screenshot, "filename", None) or "").lower()
        looks_like_image = content_type.startswith("image/") or filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
        if not looks_like_image:
            await interaction.response.send_message(
                "❌ The uploaded file must be an image screenshot (PNG/JPG/WEBP/GIF).",
                ephemeral=True
            )
            return

        if not self.signup_sheet:
            await interaction.response.send_message(
                "❌ Signup sheet is not configured yet. Make sure the bot service account has access to the signup spreadsheet.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            discord_username = getattr(interaction.user, "display_name", None) or getattr(interaction.user, "name", "Unknown")
            discord_id = str(interaction.user.id)
            screenshot_url = screenshot.url

            self.signup_sheet.append_row(
                [discord_username, discord_id, rsn_clean, screenshot_url],
                value_input_option="USER_ENTERED"
            )

            role_status_line = ""
            try:
                guild = interaction.guild
                if guild is None:
                    role_status_line = "\n**Role:** Not assigned (command was not used in a server)."
                else:
                    bingo_player_role = guild.get_role(BINGO_PLAYER_ROLE_ID)
                    if bingo_player_role is None:
                        bingo_player_role = discord.utils.get(guild.roles, name="Bingo Player")
                    if bingo_player_role is None:
                        role_status_line = f"\n**Role:** Not assigned (`Bingo Player` role not found by ID `{BINGO_PLAYER_ROLE_ID}`)."
                    elif bingo_player_role in getattr(interaction.user, "roles", []):
                        role_status_line = "\n**Role:** `Bingo Player` already assigned."
                    else:
                        await interaction.user.add_roles(bingo_player_role, reason="User completed /signup")
                        role_status_line = "\n**Role:** `Bingo Player` assigned."
            except discord.Forbidden:
                role_status_line = "\n**Role:** Could not assign `Bingo Player` (missing Manage Roles permission / role hierarchy issue)."
            except discord.HTTPException as role_err:
                role_status_line = f"\n**Role:** Could not assign `Bingo Player` ({role_err})."
            except Exception as role_err:
                print(f"❌ Error assigning Bingo Player role in /signup: {role_err}")
                traceback.print_exc()
                role_status_line = "\n**Role:** Signup saved, but role assignment failed."

            success_embed = discord.Embed(
                title="✅ Signup Submitted!",
                description=(
                    f"Your signup has been recorded.\n\n"
                    f"**RSN:** {rsn_clean}\n"
                    f"**Screenshot:** [Open Image]({screenshot_url})"
                    f"{role_status_line}"
                ),
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=success_embed, ephemeral=False)

            async def delayed_list_update():
                await asyncio.sleep(2.5)
                if interaction.guild:
                    try:
                        await self.update_live_team_list(interaction.guild)
                        print(f"✅ Live team list successfully updated for {rsn_clean}'s signup.")
                    except Exception as err:
                        print(f"❌ Error updating team list: {err}")
                        
                    try:
                        await self.update_live_signup_list(interaction.guild)
                        print(f"✅ Live signup list successfully updated for {rsn_clean}'s signup.")
                    except Exception as err:
                        print(f"❌ Error updating signup list: {err}")
            
            self.bot.loop.create_task(delayed_list_update())
            
        except Exception as e:
            print(f"❌ Error in /signup: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Failed to submit signup: {e}", ephemeral=True)

    @app_commands.command(name="roll", description="Roll a dice (1-6)")
    async def roll(self, interaction: discord.Interaction):
        if str(interaction.channel_id) not in TEAM_CHANNEL_IDS_AS_STR:
            await interaction.response.send_message("❌ You can only use this command in your team's channel.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)  
        team_name = self.get_team(interaction.user) or "*No team*"
        if team_name == "*No team*":
            await interaction.followup.send("❌ You are not on a team.", ephemeral=True)
            return
            
        await asyncio.to_thread(self.set_teleblock_status, team_name, "no")
        team_chan = self.get_team_channel(team_name)

        # 1. Turn Reset
        try:
            cleared_cards = await asyncio.to_thread(self.clear_all_active_statuses, team_name)
            if cleared_cards and team_chan:
                await team_chan.send(f"<:hourglass:1559014128046051339> **{team_name}**'s active status effect for: `({', '.join(cleared_cards)})` expired.")
            
            await asyncio.to_thread(self.set_used_card_flag, team_name, "no")
            await asyncio.to_thread(self.set_bought_house_flag, team_name, "no")

            # --- Clear Random Event ---
            asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "Silenced"))
            asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "Double Card"))

        except Exception as e:
            print(f"❌ Error during turn reset: {e}")

        # 2. Fetch Team Data
        all_records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
        headers = list(all_records[0].keys()) if all_records else []
        
        team_row_index = -1
        current_tile = 0
        rolls_available = 0

        for idx, record in enumerate(all_records, start=2):
            if record.get("Team") == team_name:
                rolls_available = int(record.get("Rolls Available", 0) or 0)
                current_tile = int(record.get("Position", 0) or 0)
                team_row_index = idx
                break
        
        if team_row_index == -1:
            await interaction.followup.send(f"❌ Could not find data for **{team_name}**.", ephemeral=True)
            return

        if rolls_available <= 0:
            await interaction.followup.send("❌ Your team has no rolls available.", ephemeral=True)
            return

        raw_result = random.randint(1, 6)
        
        # --- Apply Nerfs ---
        team_record = all_records[team_row_index-2]
        is_poisoned = str(team_record.get("Poisoned Roll", "no")).strip().lower() == "yes"
        is_halved = str(team_record.get("Roll Halved", "no")).strip().lower() == "yes"
        is_gp_halved = str(team_record.get("GP Halved", "no")).strip().lower() == "yes"

        try:
            rp_raw = str(team_record.get("Roll Penalty", "0")).strip().lower()
            roll_penalty = 3 if rp_raw == "yes" else (int(rp_raw) if rp_raw.isdigit() else 0)
        except Exception:
            roll_penalty = 0

        try:
            rb_raw = str(team_record.get("Roll Bonus", "0")).strip().lower()
            roll_bonus = 3 if rb_raw == "yes" else (int(rb_raw) if rb_raw.isdigit() else 0)
        except Exception:
            roll_bonus = 0

        result = raw_result
        if is_poisoned:
            result = min(result, 3)
            asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "Poisoned Roll"))
        if is_halved:
            result = max(1, result // 2)
            asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "Roll Halved"))
        if roll_penalty > 0:
            result = max(1, result - roll_penalty)
            asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "Roll Penalty"))
        if roll_bonus > 0:
            result += roll_bonus
            asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "Roll Bonus"))
        if is_gp_halved:
            asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "GP Halved"))

        await asyncio.to_thread(self.decrement_rolls_available, team_name)

        raw_pos = current_tile + result
        new_pos = raw_pos % 40 # BOARD_SIZE
        
        # --- RESET SCAVENGER SLOT ---
        self.team_scavenges_per_tile.pop(team_name, None)
        
        try:
            vork_idx = headers.index("Scavenged Vorkath") + 1
            dks_idx = headers.index("Scavenged DKS") + 1
            sara_idx = headers.index("Scavenged Sarachnis") + 1
            titan_idx = headers.index("Scavenged Titans") + 1
            
            await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, vork_idx, "")
            await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, dks_idx, "")
            await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, sara_idx, "")
            await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, titan_idx, "")
        except ValueError:
            print("⚠️ Could not clear Scavenge progress: Columns missing in Sheet.")
        except Exception as e:
            print(f"❌ Error clearing Scavenge progress on roll: {e}")

        go_message = ""
        
        # 4. Go logic
        if raw_pos >= 40 and new_pos != 30: 
            try:
                pass_go_col = headers.index("Go Passes") + 1
                gp_col = headers.index("GP") + 1
                
                cur_passes = int(all_records[team_row_index-2].get("Go Passes", 0))
                cur_gp = int(str(all_records[team_row_index-2].get("GP", 0)).replace(',',''))
                
                is_gp_halved = str(all_records[team_row_index-2].get("GP Halved", "no")).strip().lower() == "yes"
                go_reward = 10_000_000 if is_gp_halved else 20_000_000

                await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, pass_go_col, cur_passes + 1)
                await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, gp_col, cur_gp + go_reward)
            
                if is_gp_halved:
                    go_message = f"<:MaxCash:1558959942394847372> **PASS GO!** You passed **GO** and received **10,000,000 GP** (Halved by <:ent:1558999589317640262> **The Ents**!) and **3 Random Cards**!"
                else:
                    go_message = f"<:MaxCash:1558959942394847372> **CONGRATULATIONS!** You passed **GO** and received **20,000,000 GP** and **3 Random Cards**!"
                
                # ---> ADDED THIS LOOP <---
                for _ in range(3):
                    card_type = random.choice(["Chest", "Chance"])
                    await self.team_receives_card(team_name, card_type, team_chan)
            
            except Exception as e:
                print(f"❌ Error updating Pass Go: {e}")

        # 5. Special Tiles (Gliders / Jail)
        glider_message = ""
        
        if new_pos in (12, 28, 38):
            try:
                gp_col = headers.index("GP") + 1
                cur_gp = int(str(all_records[team_row_index-2].get("GP", 0)).replace(',',''))
                glider_fee = 8_000_000
                
                if cur_gp >= glider_fee:
                    cur_gp -= glider_fee
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, gp_col, cur_gp)
                    glider_message = f"<:gnome_glider:1559011826442838066> **Glider Flight:** The gnomes take an automatic payment of **8,000,000 GP** to use their glider!"
                    
                    if new_pos == 12: 
                        new_pos = 28 if current_tile != 38 else 12
                    elif new_pos == 28: 
                        new_pos = 38 if current_tile != 12 else 28
                    elif new_pos == 38: 
                        if current_tile != 12:
                            new_pos = 12
                            try:
                                pass_go_col = headers.index("Go Passes") + 1
                                cur_passes = int(all_records[team_row_index-2].get("Go Passes", 0))
                                is_gp_halved = str(all_records[team_row_index-2].get("GP Halved", "no")).strip().lower() == "yes"
                                glider_reward = 10_000_000 if is_gp_halved else 20_000_000
                                if is_gp_halved:
                                    asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "GP Halved"))
                                await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, pass_go_col, cur_passes + 1)
                                await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, gp_col, cur_gp + glider_reward)
                                
                                if is_gp_halved:
                                    go_message = f"<:ent:1558999589317640262> <:gnome_glider:1559011826442838066> **GLIDER BONUS REDUCED!** You flew over **GO**, but the Ents damaged your glider. You only received **10,000,000 GP** and **3 Random Cards**!"
                                else:
                                    go_message = "<:go:1559018777343950848> **GLIDER BONUS!** You flew over **GO** and received **20,000,000 GP** and **3 Random Cards**!"
                                
                                for _ in range(3):
                                    card_type = random.choice(["Chest", "Chance"])
                                    await self.team_receives_card(team_name, card_type, team_chan)
                                    
                            except Exception as e:
                                print(f"❌ Error updating Glider Go Bonus: {e}")
                        else:
                            new_pos = 38
                else:
                    glider_message = f"🚫 You cannot afford the gnome's **8,000,000 GP** glider fee! You stay on Tile {new_pos} and are granted a **Free Roll** instead!"
                    await asyncio.to_thread(self.increment_rolls_available, team_name)
                    
            except Exception as e:
                print(f"❌ Error processing glider fee: {e}")

        elif new_pos == 30:
            new_pos = 10 # JAIL_TILE
            go_message = "⛓️ **GO TO JAIL!** You are immediately sent to prison."
            await asyncio.to_thread(self.set_jail_status, team_name, "yes")

        # 6. Update Position & Results
        pos_idx = headers.index("Position") + 1
        await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_index, pos_idx, new_pos)
        
        tile_name = self.get_tile_name_for_display(new_pos)
        
        just_sent_to_jail = (new_pos == 10 and "GO TO JAIL" in go_message)
        
        if new_pos == 10 and not just_sent_to_jail:
            tile_name = "Jail (Just Visiting) - Nex, Gauntlet"
        elif new_pos == 10 and just_sent_to_jail:
            tile_name = "Jail"
            
        roll_status_details = []
        if is_poisoned:
            roll_status_details.append(f"<:strange_plant:1558995237098094602> *The Strange Plant's poison caps your roll at **3**!*")
            
        roll_status_details.append(f"**{interaction.user.display_name}** rolled a **{raw_result}**!")
        
        if is_halved:
            roll_status_details.append(f"<:sergeant_damien:1558999790556028998> *The Demon's exhaustion cut your roll to **{result}**!*")
        
        if roll_penalty > 0:
            roll_status_details.append(f"<:leo:1558999609601294346> *The Gravedigger's fatigue reduced your roll to **{result}**!*")
            
        if roll_bonus > 0:
            roll_status_details.append(f"<:sandwich_lady:1558999634096037898> *The Sandwich Lady's snack boosted your roll to **{result}**!*")
            
        roll_status_details.append(f"\nMoving to the **{tile_name}** tile.")

        if new_pos == 0:
            await asyncio.to_thread(self.increment_rolls_available, team_name)
            roll_status_details.append("\n🎯 **BULLSEYE!** You landed directly on **GO** and earned a **Free Roll**!")

        if glider_message:
            roll_status_details.append(f"\n{glider_message}")

        roll_desc = "\n".join(roll_status_details)
        
        roll_embed = discord.Embed(
            title=f"🎲 {team_name} Rolled!",
            description=roll_desc,
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=roll_embed)
        await self.mirror_to_game_log(interaction.channel, embed=roll_embed)

        if go_message:
            await interaction.channel.send(go_message)

        # --- RANDOM EVENTS ---
        try:
            team_mult = float(all_records[team_row_index-2].get("Multiplier", 1))
        except ValueError:
            team_mult = 1.0

        spawn_chance = int(team_mult * 10)
        final_pos = new_pos
        event_triggered = False
        triggered_event = None

        if new_pos not in (0, 2, 7, 17, 10, 30, 20, 12, 28, 38, 22, 33, 36) and random.randint(1, 100) <= spawn_chance:
            event_triggered = True
            
            event_result = await self.trigger_passive_random_event(interaction.channel, team_name, current_pos=new_pos)
            if event_result:
                triggered_event, event_final_pos = event_result
                if event_final_pos is not None:
                    final_pos = event_final_pos

        # 7. POST-MOVE
        tile_boss_map = self._get_tile_boss_map()
        
        pete_jailed = (event_triggered and final_pos == 10 and new_pos != 10)
        
        if final_pos in tile_boss_map:
            if not just_sent_to_jail and not pete_jailed:
                await self.auto_post_show_drops_if_boss_tile(team_name, final_pos)

        await self.check_and_award_card_on_land(team_name, final_pos, "rolling")

    def _get_tile_boss_map(self) -> dict[int, list[str]]:
        return {
            1: ["Zulrah"], 3: ["General Graardor"],
            4: ["Phantom Muspah"], 5: ["The Whisperer"], 6: ["Callisto"],
            8: ["Vet'ion"], 9: ["Venenatis"], 10: ["Gauntlet", "Nex"], 11: ["Corp"],
            13: ["Moons of Peril"], 14: ["Hueycoatl"], 15: ["Duke Sucellus"], 16: ["Wintertodt", "Zalcano", "Tempoross"],
            18: ["K'ril Tsutsaroth"], 19: ["Abyssal Sire", "Alchemical Hydra", "Araxxor", "Cerberus", "Grotesque Guardians", "Kraken", "Thermonuclear Smoke Devil"],
            21: ["Tombs of Amascut"], 23: ["Theatre of Blood"], 24: ["Chambers of Xeric"],
            25: ["Vardorvis"], 26: ["Yama"], 27: ["Colosseum"], 29: ["Doom of Mokhaiotl"],
            31: ["Kree'arra"], 32: ["Kalphite Queen"], 34: ["Nightmare"],
            35: ["The Leviathan"], 37: ["Zilyana"], 39: ["Scorpia, King Black Dragon"]
        }


    def get_tile_name_for_display(self, position: int) -> str:
        """Returns a human-readable tile name (boss/property/special) for a board tile."""
        try:
            tile_boss_map = self._get_tile_boss_map()
            if position in CHEST_TILES:
                return "Chest"
            if position in CHANCE_TILES:
                return "Chance"
            if position == GO_TILE:
                return "GO"
            if position == JAIL_TILE:
                return "Jail"
            if position == BANK_STANDING_TILE:
                return "Bank Standing"
            if position in GLIDER_TILES:
                return "Next Glider"
            if position in tile_boss_map:
                return ", ".join(tile_boss_map[position])

            for prop in self.house_data_sheet.get_all_records():
                try:
                    if int(prop.get("Tile", -1)) == position:
                        return prop.get("Name", f"Tile {position}")
                except Exception:
                    continue
        except Exception as e:
            print(f"❌ Error resolving tile name for {position}: {e}")
        return f"Tile {position}"

    def resolve_nonroll_landing_tile(self, intended_pos: int) -> int:
        """Resolve one-step board effects for card teleports/forced moves (gliders, go-to-jail)."""
        try:
            pos = int(intended_pos)
        except Exception:
            return intended_pos

        if pos == 12:
            return 28
        if pos == 28:
            return 38
        if pos == 38:
            return 12
        if pos == 30:
            return JAIL_TILE
        return pos

    def get_glider_redirect_note(self, intended_pos: int, final_pos: int, *, second_person: bool = False, quoted: bool = True) -> str:
        """Return feedback text when a non-roll move lands on a glider and is redirected."""
        try:
            intended = int(intended_pos)
            final = int(final_pos)
        except Exception:
            return ""

        if intended == final or intended not in GLIDER_TILES:
            return ""

        final_tile_name = self.get_tile_name_for_display(final)
        if second_person:
            msg = (
                f"You landed on a **Glider** tile and were launched to the **{final_tile_name}** tile "
                f"(Tile **{final}**)."
            )
        else:
            msg = (
                f"Landed on a **Glider** tile and was launched to the **{final_tile_name}** tile "
                f"(Tile **{final}**)."
            )

        return f"\n> {msg}" if quoted else f"\n{msg}"

    async def auto_post_show_drops_if_boss_tile(self, team_name: str, position: int):
        """Auto-post the /show_drops embed in a team's channel if the tile has boss drops."""
        try:
            if position == 10:
                is_in_jail = await asyncio.to_thread(self.get_jail_status, team_name)
                if is_in_jail != "yes":
                    return

            team_chan = self.get_team_channel(team_name)
            if not team_chan:
                return
            drops_embed = self.build_show_drops_embed_for_tile(position)
            if drops_embed is not None:
                await team_chan.send(embed=drops_embed)
        except Exception as e:
            print(f"❌ Error auto-posting /show_drops for {team_name} on tile {position}: {e}")


    def build_show_drops_embed_for_tile(self, position: int) -> discord.Embed | None:
        """Build the same embed used by /show_drops for a board tile. Returns None if tile has no boss drops."""
        tile_boss_map = self._get_tile_boss_map()
        boss_list = tile_boss_map.get(position)
        if not boss_list:
            return None

        boss_name_str = ", ".join(boss_list)
        embed = discord.Embed(
            title=f"Available Drops for {boss_name_str} (Tile {position})",
            description="This list shows potential drops and their GP values.",
            color=discord.Color.gold()
        )

        all_items = self.item_values_sheet.get_all_records()

        drop_list_text = ""
        found_any_drops = False

        for boss in boss_list:
            boss_drops_text = ""
            for item in all_items:
                item_boss = item.get("Boss Name")
                if item_boss == boss:
                    item_name = item.get("Item", "Unknown Item")
                    item_gp = item.get("GP", "0")
                    formatted_gp = self._format_gp(item_gp)
                    boss_drops_text += f"• **{item_name}**: {formatted_gp} GP\n"
                    found_any_drops = True

            drop_list_text += f"\n**--- {boss} ---**\n"
            if not boss_drops_text:
                drop_list_text += "No drops found for this boss.\n"
            else:
                drop_list_text += boss_drops_text

        if not found_any_drops:
            drop_list_text = "No drops found for this boss in the `ItemValues` sheet. (Sheet must have 'Boss Name', 'Item', and 'GP' columns)."

        if len(drop_list_text) > 4096:
            drop_list_text = drop_list_text[:4090] + "...\n(List too long to display)"

        embed.description = drop_list_text
        return embed

    def _format_gp(self, gp_value_str: str) -> str:
        """Formats a GP string into M (Million) or K (Thousand)."""
        try:
            gp = int(str(gp_value_str).replace(',', ''))
        except ValueError:
            return gp_value_str

        if gp >= 1_000_000:
            if (gp % 1_000_000) == 0:
                return f"{gp // 1_000_000}M"
            else:
                return f"{gp / 1_000_000:.1f}M"
        elif gp >= 1_000:
            if (gp % 1_000) == 0:
                return f"{gp // 1_000}K"
            else:
                return f"{gp / 1_000:.1f}K"
        else:
            return f"{gp:,}"

    def clear_flag_column(self, team_name: str, column_name: str):
        """Helper to quickly clear a status flag from the TeamData sheet."""
        try:
            records = self.team_data_sheet.get_all_records()
            headers = list(records[0].keys())
            if column_name not in headers:
                return
                
            col_idx = headers.index(column_name) + 1
            for idx, r in enumerate(records, start=2):
                if r.get("Team", "").strip() == team_name:
                    self.team_data_sheet.update_cell(idx, col_idx, "")
                    break
        except Exception as e:
            print(f"❌ Error clearing {column_name} flag for {team_name}: {e}")
    
    @app_commands.command(name="show_drops", description="Show available drops and prices for your current tile.")
    @app_commands.checks.has_any_role(*TEAM_ROLES)
    async def show_drops(self, interaction: Interaction):
        team_name = None
        for role in interaction.user.roles:
            if role.name in TEAM_ROLES:
                team_name = role.name
                break
        
        if not team_name:
            await interaction.response.send_message("You are not on a team.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)
        
        try:
            team_data = await asyncio.to_thread(self.get_team_data, team_name)
            if not team_data:
                await interaction.followup.send("Could not retrieve your team's data.", ephemeral=True)
                return

            position = int(team_data.get("Position", 0))

            try:
                embed = await asyncio.to_thread(self.build_show_drops_embed_for_tile, position)
            except Exception as e:
                print(f"Error fetching ItemValues: {e}")
                await interaction.followup.send("Error fetching item data from the sheet.", ephemeral=True)
                return
            if not embed:
                await interaction.followup.send("There are no special boss drops on this tile.", ephemeral=False)
                return

            await interaction.followup.send(embed=embed, ephemeral=False)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            traceback.print_exc()

    @app_commands.command(name="monopoly_help", description="Show the help and rules for the Monopoly event.")
    async def monopoly_help(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            embed1 = discord.Embed(
                title="How to Play (The Basics)",
                description=(
                    "The whole game runs on drop submissions:\n"
                    "1. **Submit a Drop:** A team member uses `/submitdrop` in their team channel. Screenshots must **strictly** be in the room where the drop was received.\n"
                    "2. **Get Approved:** Staff checks it out and approves it. All approvals have a chance for a rare passive drop!\n"
                    "3. **Get GP & a Roll:** Once it's approved, two things happen:\n"
                    "    - Your team gets GP for the drop.\n"
                    "    - Your team gets one roll.\n"
                    "4. **Use Your Roll:** Head to your team channel and use the `/roll` command.\n"
                    "5. **Move:** The bot rolls a 1-6, and your team moves on the board.\n"
                    "6. **Repeat:** Keep submitting drops to get more rolls!"
                ),
                color=discord.Color.green()
            )
            
            embed2 = discord.Embed(
                title="⚙️ Advanced Game Mechanics",
                color=discord.Color.orange()
            )
            embed2.add_field(
                name="🏠 Houses & Taxes",
                value="When you land on a boss tile, your Captain can buy a house (up to 4 per tile). If another team lands on your property and gets a drop, they pay you a massive percentage of their earnings as tax!",
                inline=False
            )
            embed2.add_field(
                name="🃏 Cards & PvP",
                value="Landing on Chest or Chance tiles grants your team a card. Captains can use these to teleport, boost GP, or ruthlessly attack and steal from other teams! Teams can only use one card per turn.",
                inline=False
            )
            embed2.add_field(
                name="💎 Rare Drop Table (Passives)",
                value="Every approved drop has a chance to roll on the Rare Drop Table. You can win powerful passive items (like a Ring of Recoil or Protect Item) that automatically defend your team from attacks or taxes. You can only hold **ONE** passive at a time!",
                inline=False
            )
            embed2.add_field(
                name="🎲 Random Events",
                value="Every time you roll the dice, there is a chance to trigger a Random Event. Some will bless your team, while others will sabotage you.",
                inline=False
            )
            
            embed3 = discord.Embed(
                title="⚙️ Game Commands",
                color=discord.Color.blue()
            )
            embed3.add_field(
                name="For Team Captains Only!",
                value=(
                    "**/use_card:** Lets you see and use the cards your team is holding.\n"
                    "**/buy_house:** Landed on a tile? Use this to buy a house for it (up to 4).\n"
                    "**/customize:** Change your character's icon and color!\n"
                    "**/player_request:** Draft a player to your team."
                ),
                inline=False
            )
            embed3.add_field(
                name="For Everyone on the Team!",
                value=(
                    "**/roll:** Uses one of your team's rolls to move.\n"
                    "**/stats:** View your team's passes, GP, houses, and leaderboard position.\n"
                    "**/gp:** Curious about your GP? Use this to check the team's total.\n"
                    "**/cards:** See all the cards your team is currently holding. *Visible only to you.*\n"
                    "**/show_drops:** Shows every drop available for the tile you're on.\n"
                    "**/submitdrop:** Use this to submit a boss drop for a roll."
                ),
                inline=False
            )
            
            await interaction.followup.send(embeds=[embed1, embed2, embed3], ephemeral=False)
        
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            traceback.print_exc()

    @app_commands.command(name="gp", description="Check your team's current GP balance.")
    async def gp(self, interaction: discord.Interaction):
        if str(interaction.channel_id) not in TEAM_CHANNEL_IDS_AS_STR:
            await interaction.response.send_message(
                "❌ You can only use this command in your team's channel.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)  
        team_name = self.get_team(interaction.user)
        if not team_name:
            await interaction.followup.send("❌ You must be on a team to check GP.", ephemeral=True)
            return
        try:
            records = self.team_data_sheet.get_all_records()
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
                title=f"<:MaxCash:1558959942394847372> {team_name} Team Status",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="GP Balance",
                value=f"**{team_gp:,} GP**",
                inline=False
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"❌ Error in /gp command: {e}")
            await interaction.followup.send("❌ An error occurred while fetching GP balance.", ephemeral=True)

    @app_commands.command(name="stats", description="Show GP, Go Passes, and Houses Owned for all teams.")
    async def stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            if not records:
                await interaction.followup.send("❌ Team data is unavailable.", ephemeral=True)
                return
            
            gp_list = []
            go_passes_list = []
            houses_list = []

            for record in records:
                team_name = record.get("Team", "")
                if not team_name: 
                    continue
                
                team_gp_str = str(record.get("GP", 0)).replace(',', '').strip()
                team_gp = int(team_gp_str) if team_gp_str and team_gp_str.lstrip('-').isdigit() else 0
                
                team_passes_str = str(record.get("Go Passes", 0)).replace(',', '').strip()
                team_passes = int(team_passes_str) if team_passes_str and team_passes_str.lstrip('-').isdigit() else 0
                
                team_houses_str = str(record.get("Houses Owned", 0)).replace(',', '').strip()
                team_houses = int(team_houses_str) if team_houses_str and team_houses_str.lstrip('-').isdigit() else 0
                
                gp_list.append({"team": team_name, "value": team_gp})
                go_passes_list.append({"team": team_name, "value": team_passes})
                houses_list.append({"team": team_name, "value": team_houses})
                
            gp_list.sort(key=lambda x: x["value"], reverse=True)
            go_passes_list.sort(key=lambda x: x["value"], reverse=True)
            houses_list.sort(key=lambda x: x["value"], reverse=True)

            gp_output = ""
            for i, entry in enumerate(gp_list, 1):
                gp_output += f"**{i}. {entry['team']}**: {entry['value']:,}\n"

            passes_output = ""
            for i, entry in enumerate(go_passes_list, 1):
                passes_output += f"**{i}. {entry['team']}**: {entry['value']}\n"

            houses_output = ""
            for i, entry in enumerate(houses_list, 1):
                houses_output += f"**{i}. {entry['team']}**: {entry['value']}\n"

            embed = discord.Embed(
                title="🌐 Monopoly Board Leaderboard",
                description="Current progress stats for all teams.",
                color=discord.Color.blue()
            )
            
            if gp_output:
                embed.add_field(name="<:MaxCash:1558959942394847372> GP Holdings", value=gp_output, inline=True)
                
            if passes_output:
                embed.add_field(name="🚶 Go Passes", value=passes_output, inline=True)

            if houses_output:
                embed.add_field(name="<:houseicon:1438085020156821555> Houses Owned", value=houses_output, inline=True)
                
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"❌ Error in /stats command: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ An error occurred while fetching leaderboard data.", ephemeral=True)

    @app_commands.command(name="buy_house", description="Attempt to buy a house on your current tile.")
    async def buy_house(self, interaction: discord.Interaction):
        if str(interaction.channel_id) not in TEAM_CHANNEL_IDS_AS_STR:
            await interaction.response.send_message("❌ You can only use this command in your team's channel.", ephemeral=True)
            return
        if not self.has_event_captain_role(interaction.user):
            await interaction.response.send_message("❌ Only the Event Captain can use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)
        team_name = self.get_team(interaction.user)
        if not team_name:
            await interaction.followup.send("❌ You must be on a team to buy a house.", ephemeral=True)
            return

        try:
            # 1. CHECK
            bought_flag = await asyncio.to_thread(self.get_bought_house_flag, team_name)
            if bought_flag.strip().lower() in ["yes", "true", "1"]:
                await interaction.followup.send("❌ You have already purchased a house this turn. Use `/roll` to move to a new tile before buying another.", ephemeral=True)
                return
            
            COST_MAP = {0: 25_000_000, 1: 50_000_000, 2: 100_000_000, 3: 200_000_000}
            
            # 2. DATA
            team_data = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            house_data = await asyncio.to_thread(self.house_data_sheet.get_all_records)
            
            team_info = next((r for r in team_data if str(r.get("Team", "")).strip() == team_name.strip()), None)
            
            if not team_info:
                await interaction.followup.send("❌ Could not find team data.", ephemeral=True)
                return

            current_pos = int(team_info.get("Position", -1))
            current_gp = int(str(team_info.get("GP", 0)).replace(",", ""))

            vork_done = str(team_info.get("Scavenged Vorkath", "")).strip().lower() in ["yes", "true", "1"]
            dks_done = str(team_info.get("Scavenged DKS", "")).strip().lower() in ["yes", "true", "1"]
            sara_done = str(team_info.get("Scavenged Sarachnis", "")).strip().lower() in ["yes", "true", "1"]
            titan_done = str(team_info.get("Scavenged Titans", "")).strip().lower() in ["yes", "true", "1"]
            
            if vork_done and dks_done and sara_done and titan_done:
                await interaction.followup.send("❌ **Action Denied:** You completed a Scavenger Bingo on this tile and triggered the Skip Tax. You forfeit the right to build here for the remainder of this turn!", ephemeral=True)
                return
            
            # 3. HOUSE
            prop_index = -1
            prop_data = None
            for idx, row in enumerate(house_data, start=2):
                if int(row.get("Tile", -1)) == current_pos:
                    prop_data = row
                    prop_index = idx
                    break

            if not prop_data:
                await interaction.followup.send("❌ This tile is not a buyable property.", ephemeral=True)
                return

            owner = prop_data.get("OwnerTeam", "").strip()
            if owner and owner != team_name:
                await interaction.followup.send(f"❌ This property is already owned by **{owner}**.", ephemeral=True)
                return

            house_count = int(prop_data.get("HouseCount", 0) or 0)
            if house_count >= 4:
                await interaction.followup.send("❌ Max houses (4) reached on this tile.", ephemeral=True)
                return

            cost = COST_MAP.get(house_count, 999_999_999)

            # --- <:charos:1558985798483837049> RING OF CHAROS CHECK ---
            has_charos = str(team_info.get("Ring of Charos", "no")).strip().lower() == "yes"
            if has_charos:
                cost = cost // 2

            if current_gp < cost:
                await interaction.followup.send(f"❌ Not enough GP. Need **{cost:,}**, but you have **{current_gp:,}**.", ephemeral=True)
                return

            # 4. EXECUTE
            headers = list(team_data[0].keys())
            gp_col = headers.index("GP") + 1
            team_row_in_sheet = team_data.index(team_info) + 2

            await asyncio.to_thread(self.house_data_sheet.update_cell, prop_index, 3, team_name) 
            await asyncio.to_thread(self.house_data_sheet.update_cell, prop_index, 4, house_count + 1) 
            await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_in_sheet, gp_col, current_gp - cost)

            await asyncio.to_thread(self.sync_houses_owned, team_name)
            
            await asyncio.to_thread(self.set_bought_house_flag, team_name, "yes")

            charos_msg = ""
            if has_charos:
                await asyncio.to_thread(self.consume_charos, team_name)
                charos_msg = f"\n\n<:charos:1558985798483837049> *Your **Ring of Charos** charmed the real estate agent, securing a 50% discount! The ring shatters!*"

            buy_msg = f"<:houseicon:1438085020156821555> **{team_name}** bought a house on tile **{current_pos}** for **{cost:,} GP**!{charos_msg}"
            await interaction.followup.send(buy_msg)
            await self.mirror_to_game_log(interaction.channel, content=buy_msg)

        except Exception as e:
            print(f"❌ Error in /buy_house: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)
   
    @app_commands.command(name="submitdrop", description="Submit a boss drop for review")
    @app_commands.describe(
        screenshot="Attach a screenshot of the drop. Must be in boss room!",
        submitted_for="User you are submitting the drop for (optional)",
    )
    async def submitdrop(self, interaction: discord.Interaction, screenshot: discord.Attachment, submitted_for: Optional[discord.Member] = None):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.NotFound:
            print("❌ Interaction not found. (Original timeout)")
            return
        except discord.errors.InteractionResponded:
            print("❌ Interaction already responded to. (Likely >3s lag before defer)")
            return
            
        if submitted_for is None:
            submitted_for = interaction.user

        team_name = self.get_team(submitted_for) or "*No team*"
        if team_name == "*No team*":
            await interaction.followup.send(content=f"❌ **{submitted_for.display_name}** is not on a team.", ephemeral=True)
            return

        # 1. Fetch current tile
        current_tile = None
        records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
        for record in records:
            if record.get("Team") == team_name:
                current_tile = int(record.get("Position", 0))
                break
        
        if current_tile is None:
            await interaction.followup.send(content=f"❌ Could not find data for **{team_name}**.", ephemeral=True)
            return

        allowed, error_msg = self.check_turn_stance(submitted_for.id, team_name, current_tile, "main")
        if not allowed:
            await interaction.followup.send(content=error_msg, ephemeral=True)
            return
        
        # 2. Boss Map
        tile_boss_map = {
            1: ["Zulrah"], 3: ["General Graardor"],
            4: ["Phantom Muspah"], 5: ["The Whisperer"], 6: ["Callisto"],
            8: ["Vet'ion"], 9: ["Venenatis"], 10: ["Gauntlet", "Nex"], 11: ["Corp"],
            13: ["Moons of Peril"], 14: ["Hueycoatl"], 15: ["Duke Sucellus"], 16: ["Wintertodt", "Zalcano", "Tempoross"],
            18: ["K'ril Tsutsaroth"], 19: ["Abyssal Sire", "Alchemical Hydra", "Araxxor", "Cerberus", "Grotesque Guardians", "Kraken", "Thermonuclear Smoke Devil"],
            21: ["Tombs of Amascut"], 23: ["Theatre of Blood"], 24: ["Chambers of Xeric"],
            25: ["Vardorvis"], 26: ["Yama"], 27: ["Colosseum"], 29: ["Doom of Mokhaiotl"],
            31: ["Kree'arra"], 32: ["Kalphite Queen"], 34: ["Nightmare"],
            35: ["The Leviathan"], 37: ["Zilyana"], 39: ["Scorpia, King Black Dragon"]
        }

        bosses_for_tile = tile_boss_map.get(current_tile, [])

        if not bosses_for_tile:
            await interaction.followup.send(content=f"❌ Your team is on Tile **{current_tile}**, which does not have any boss drops.", ephemeral=True)
            return

        # 3. Route UI
        warning_text = (
            "⚠️ **Notice:** Submitting a drop here locks you into the **Main Fighter** role for this tile.\n"
            "You will **NOT** be able to use `/scavenge` for off-board bosses until your team moves to a new tile.\n\n"
        )

        if len(bosses_for_tile) == 1:
            selected_boss = bosses_for_tile[0]
            await interaction.followup.send(
                content=warning_text + f"Detected **{selected_boss}** (Tile {current_tile}). Select the drop:",
                view=self.DropSelectView(
                    cog=self,
                    submitting_user=interaction.user,
                    submitted_for=submitted_for,
                    screenshot_url=screenshot.url,
                    boss=selected_boss,
                    current_tile=current_tile 
                ),
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                content=warning_text + f"Multiple bosses found on Tile {current_tile}. Select the boss:",
                view=self.RestrictedBossSelectView(
                    cog=self,
                    submitting_user=interaction.user,
                    submitted_for=submitted_for,
                    screenshot_url=screenshot.url,
                    valid_bosses=bosses_for_tile,
                    current_tile=current_tile 
                ),
                ephemeral=True
            )

    def check_turn_stance(self, user_id: int, team_name: str, current_tile: int, requested_stance: str) -> tuple[bool, str]:
        """Checks if a player is allowed to use the requested command type on the current tile."""
        data = self.player_stances.get(user_id)
        
        if data and data["team"] == team_name and data["tile"] == current_tile:
            if data["stance"] != requested_stance:
                other_cmd = "/scavenge" if requested_stance == "main" else "/submitdrop"
                stance_name = "Main Board" if data["stance"] == "main" else "Scavenger"
                return False, f"⏳ **Dual-Prevention:** That player has already submitted a drop as a **{stance_name}** for this tile (Tile {current_tile}). They can only use `{other_cmd}` until the team moves!"
        
        return True, ""

    def lock_turn_stance(self, user_id: int, team_name: str, current_tile: int, requested_stance: str):
        """Locks the player into their chosen stance for the current tile."""
        self.player_stances[user_id] = {
            "stance": requested_stance,
            "team": team_name,
            "tile": current_tile
        }
    
    @app_commands.command(name="scavenge", description="Locks you out of the current tile's submissions to scavenge elsewhere.")
    @app_commands.describe(
        screenshot="Attach a screenshot of the drop (Must be in boss room!)",
        submitted_for="User you are submitting the drop for (optional)",
    )
    async def scavenge(self, interaction: discord.Interaction, screenshot: discord.Attachment, submitted_for: Optional[discord.Member] = None):
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            return
            
        if submitted_for is None:
            submitted_for = interaction.user

        team_name = self.get_team(submitted_for) or "*No team*"
        if team_name == "*No team*":
            await interaction.followup.send(content=f"❌ **{submitted_for.display_name}** is not on a team.", ephemeral=True)
            return

        current_tile = None
        records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
        for record in records:
            if record.get("Team") == team_name:
                current_tile = int(record.get("Position", 0))
                break

        if current_tile is None:
            await interaction.followup.send(content=f"❌ Could not find data for **{team_name}**.", ephemeral=True)
            return

        team_record = next((r for r in records if r.get("Team") == team_name), None)
        completed_bosses = []
        
        if team_record:
            if str(team_record.get("Scavenged Vorkath", "")).strip().lower() in ["yes", "true", "1"]:
                completed_bosses.append("Vorkath")
            if str(team_record.get("Scavenged DKS", "")).strip().lower() in ["yes", "true", "1"]:
                completed_bosses.append("Dagannoth Kings")
            if str(team_record.get("Scavenged Sarachnis", "")).strip().lower() in ["yes", "true", "1"]:
                completed_bosses.append("Sarachnis")
            if str(team_record.get("Scavenged Titans", "")).strip().lower() in ["yes", "true", "1"]:
                completed_bosses.append("Royal Titans")
                
        available_bosses = [b for b in SCAVENGER_BOSSES if b not in completed_bosses]
        
        if not available_bosses:
            await interaction.followup.send(content=f"❌ **{team_name}** has already scavenged all 4 bosses for Tile {current_tile} and earned their Free Roll! You must wait until your team moves.", ephemeral=True)
            return
            
        allowed, error_msg = self.check_turn_stance(submitted_for.id, team_name, current_tile, "scavenge")
        if not allowed:
            await interaction.followup.send(content=error_msg, ephemeral=True)
            return

        current_scavenges = len(completed_bosses)
        
        if current_scavenges == 3:
            dynamic_warning = (
                "🚨 **WARNING: 3/4 Scavenges Complete!** 🚨\n"
                "*Submitting this 4th and final boss will instantly trigger Scavenger Bingo. "
                "You will earn a **Free Roll**, but the Bank will execute the **Skip Tax** (destroying or repossessing 1 house)!*"
            )
        else:
            dynamic_warning = (
                f"🎰 **SCAVENGER BONUS:** Your team has scavenged **{current_scavenges}/4** bosses on this tile.\n"
                "*(Note: The Free Roll and the House Repossession Penalty ONLY trigger when you complete your 4th unique boss!)*"
            )

        warning_text = (
            "⚠️ **Notice:** This forfeits all your drops for a **tile's boss**, but allows you to **Scavenge** for loot elsewhere.\n\n"
            f"{dynamic_warning}\n\n"
            "**Select the Scavenger Boss you defeated (already scavenged bosses are removed):**"
        )

        await interaction.followup.send(
            content=warning_text,
            view=self.RestrictedBossSelectView(
                cog=self,
                submitting_user=interaction.user,
                submitted_for=submitted_for,
                screenshot_url=screenshot.url,
                valid_bosses=available_bosses,
                current_tile=current_tile
            ),
            ephemeral=True
        )
    
    async def team_receives_card(self, team_name: str, card_type: str, team_channel: discord.TextChannel):
        card_sheet = self.chance_sheet if card_type == "Chance" else self.chest_sheet
        try:
            rows = await asyncio.to_thread(card_sheet.get_all_records)
            team_records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            
            team_info = next((r for r in team_records if r.get("Team") == team_name), {})
            has_protect_item = str(team_info.get("Protect Item", "no")).strip().lower() == "yes"
            has_recoil = str(team_info.get("Ring of Recoil", "no")).strip().lower() == "yes"
            has_phoenix = str(team_info.get("Phoenix Necklace", "no")).strip().lower() == "yes"
            has_charos = str(team_info.get("Ring of Charos", "no")).strip().lower() == "yes"
            has_stone = str(team_info.get("Ring of Stone", "no")).strip().lower() == "yes"
            
            has_any_passive = has_protect_item or has_recoil or has_phoenix or has_charos or has_stone

            eligible_cards = []
            if rows:
                for i, row in enumerate(rows, start=2):
                    card_name = str(row.get("Name", "")).strip()
                    held_by = str(row.get("Held By Team", ""))
                    teams_holding = [t.strip() for t in held_by.split(',') if t.strip()]
                    
                    if team_name not in teams_holding:
                        eligible_cards.append({
                            "type": "physical", 
                            "index": i, 
                            "data": row, 
                            "teams_holding": teams_holding
                        })

            if not has_any_passive:
                eligible_cards.append({"type": "virtual", "data": {"Name": "Protect Item", "Card Text": "Passive - Can't be used. Saves a player from item losses until one occurs."}})
                eligible_cards.append({"type": "virtual", "data": {"Name": "Ring of Recoil", "Card Text": "Passive - Dealing with you has a price. Attacking this team causes the effect to trigger on both teams."}})
                eligible_cards.append({"type": "virtual", "data": {"Name": "Phoenix Necklace", "Card Text": "Passive - Can't be used. Automatically shatters to absorb your next rent payment."}})
                eligible_cards.append({"type": "virtual", "data": {"Name": "Ring of Charos", "Card Text": "Passive - Can't be used. Automatically halves the cost of your next house purchase."}})
                eligible_cards.append({"type": "virtual", "data": {"Name": "Ring of Stone", "Card Text": "Passive - Can't be used. Automatically shatters to block forced movement or teleports."}})

            if not eligible_cards:
                await team_channel.send(f"❗ **{team_name}** tried to draw a {card_type} card, but they already hold every available card in the deck!")
                return

            chosen_card = random.choice(eligible_cards)
            card_data = chosen_card["data"]
            card_name = card_data.get("Name", "Unknown Card")
            card_text = card_data.get("Card Text", "")
            
            display_name = "Protect Item Scroll" if card_name == "Protect Item" else ("Ring of Charos (a)" if card_name == "Ring of Charos" else card_name)
            
            if card_name == "Ring of Recoil":
                card_emoji = "<:recoil:1558985588055609374>"
            elif card_name == "Protect Item":
                card_emoji = "<:protect_item:1559003530050670632>"
            elif card_name == "Phoenix Necklace":
                card_emoji = "<:pneck:1558990483110367242>"
            elif card_name == "Ring of Charos":
                card_emoji = "<:charos:1558985798483837049>"
            elif card_name == "Ring of Stone":
                card_emoji = "<:ring_of_stone:1558985677134241873>"
            else:
                card_emoji = CARD_EMOJIS.get(card_name, CARD_EMOJIS.get(card_type, "🃏"))
            
            if chosen_card["type"] == "virtual":
                team_row_idx = team_records.index(team_info) + 2
                headers = list(team_records[0].keys()) if team_records else []
                
                if card_name in headers:
                    passive_col = headers.index(card_name) + 1
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, passive_col, "yes")
                    
                embed = discord.Embed(
                    title=f"{card_emoji} {card_type} Card Drawn!",
                    description=f"**{team_name}** drew **{display_name}**!\n\n> {card_text}",
                    color=discord.Color.gold() if card_type == "Chest" else discord.Color.blue()
                )
                await team_channel.send(embed=embed)
                
                if card_name == "Protect Item":
                    await team_channel.send(f"<:protect_item:1559003530050670632> **{team_name}** drew a **Protect Item Scroll**!\nThe prayer is now **ACTIVE** in your inventory and will automatically block the next effect that steals your GP or cards!")
                elif card_name == "Ring of Recoil":
                    await team_channel.send(f"<:recoil:1558985588055609374> **{team_name}** drew a **Ring of Recoil**!\nThe ring is now **ACTIVE** in your inventory and will force the next team that attacks you to suffer the same fate!")
                elif card_name == "Phoenix Necklace":
                    await team_channel.send(f"<:pneck:1558990483110367242> **{team_name}** drew a **Phoenix Necklace**!\nThe necklace is now **ACTIVE** in your inventory and will absorb the next rent payment you owe!")
                elif card_name == "Ring of Charos":
                    await team_channel.send(f"<:charos:1558985798483837049> **{team_name}** drew a **Ring of Charos (a)**!\nThe ring is now **ACTIVE** in your inventory and will halve the cost of your next house purchase!")
                elif card_name == "Ring of Stone":
                    await team_channel.send(f"<:ring_of_stone:1558985677134241873> **{team_name}** drew a **Ring of Stone**!\nThe ring is now **ACTIVE** in your inventory and will prevent the next card effect that tries to move or teleport you!")

            else:
                card_row_index = chosen_card["index"]
                teams_holding = chosen_card["teams_holding"]
                new_roll = None

                if "%d6" in card_text or "%d3" in card_text:
                    if "%d6" in card_text:
                        new_roll = random.randint(1, 6)
                    elif "%d3" in card_text:
                        new_roll = random.randint(1, 3)

                    wildcard_str = str(card_data.get("Wildcard", "{}"))
                    if not wildcard_str.strip(): wildcard_str = "{}"
                    try: wildcard_data = json.loads(wildcard_str)
                    except Exception: wildcard_data = {}

                    wildcard_data[team_name] = new_roll
                    await asyncio.to_thread(card_sheet.update_cell, card_row_index, 4, json.dumps(wildcard_data))

                teams_holding.append(team_name)
                await asyncio.to_thread(card_sheet.update_cell, card_row_index, 3, ", ".join(teams_holding))

                card_text_display = card_text
                if new_roll is not None:
                    card_text_display = card_text_display.replace("%d6", str(new_roll)).replace("%d3", str(new_roll))

                embed = discord.Embed(
                    title=f"{card_emoji} {card_type} Card Drawn!",
                    description=f"**{team_name}** drew **{display_name}**!\n\n> {card_text_display}",
                    color=discord.Color.gold() if card_type == "Chest" else discord.Color.blue()
                )
                await team_channel.send(embed=embed) 

        except Exception as e:
            print(f"❌ Error in team_receives_card: {e}")
            traceback.print_exc()
            
    def get_held_cards(self, sheet_obj, team_name: str):
        cards = []
        try:
            data = sheet_obj.get_all_values() 
            if not data:
                return []
            headers = data[0]
            
            try:
                name_col = headers.index("Name")
                text_col = headers.index("Card Text")
                held_by_col = headers.index("Held By Team")
                wildcard_col = headers.index("Wildcard")
            except ValueError as e:
                print(f"❌ Missing column in {sheet_obj.title}: {e}")
                return []

            for idx, row in enumerate(data[1:], start=2):
                if len(row) <= max(name_col, text_col, held_by_col, wildcard_col):
                    continue
                    
                held_by = str(row[held_by_col] or "")
                
                if team_name in held_by:
                    card_text = str(row[text_col] or "")
                    card_name = str(row[name_col] or "")
                    
                    wildcard_data_str = str(row[wildcard_col] or "{}")
                    if wildcard_data_str != "{}" and wildcard_data_str:
                        try:
                            wildcard_data = json.loads(wildcard_data_str)
                            stored_val = wildcard_data.get(team_name)
                            
                            if stored_val:
                                if isinstance(stored_val, int):
                                    card_text = card_text.replace("%d6", str(stored_val))
                                    card_text = card_text.replace("%d3", str(stored_val))
                                elif isinstance(stored_val, str) and stored_val.strip() == "active": 
                                    card_text += " **(ACTIVE)**"
                                    
                        except Exception as e:
                            print(f"❌ Error parsing wildcard JSON for {team_name}: {wildcard_data_str} | {e}")
                            
                    cards.append({
                        "row_index": idx,
                        "name": card_name,
                        "text": card_text,
                    })
        except Exception as e:
            print(f"❌ Error in get_held_cards: {e}")
        return cards

    def check_and_consume_vengeance(self, target_team_name: str) -> bool:
        try:
            for sheet_obj in (self.chest_sheet, self.chance_sheet):
                data = sheet_obj.get_all_values()
                if not data:
                    continue

                headers = data[0]
                if "Name" not in headers or "Held By Team" not in headers or "Wildcard" not in headers:
                    continue

                name_col = headers.index("Name")
                held_by_col = headers.index("Held By Team")
                wildcard_col = headers.index("Wildcard")

                for i, row in enumerate(data[1:], start=2):
                    if len(row) <= max(name_col, held_by_col, wildcard_col):
                        continue
                    if str(row[name_col]).strip() != "Vengeance":
                        continue

                    try:
                        wildcard_data = json.loads(row[wildcard_col] or "{}")
                    except Exception:
                        wildcard_data = {}

                    if wildcard_data.get(target_team_name) == "active":
                        wildcard_data.pop(target_team_name, None)
                        sheet_obj.update_cell(i, wildcard_col + 1, json.dumps(wildcard_data))

                        held_by_str = str(sheet_obj.cell(i, held_by_col + 1).value or "")
                        teams = [t.strip() for t in held_by_str.split(",") if t.strip()]
                        if target_team_name in teams:
                            teams.remove(target_team_name)
                        sheet_obj.update_cell(i, held_by_col + 1, ", ".join(teams))

                        print(f"Consumed Vengeance for {target_team_name} from {sheet_obj.title}")
                        return True

            return False

        except Exception as e:
            print(f"Error in check_and_consume_vengeance: {e}")
            return False
        
    def check_and_consume_redemption(self, target_team_name: str) -> bool:
        """
        Checks if a target team has Redemption active across both card sheets.
        If yes, consumes it (clears wildcard AND held by) and returns True.
        If no, returns False.
        """
        try:
            for sheet_obj in (self.chest_sheet, self.chance_sheet):
                cards_data = sheet_obj.get_all_values()
                if not cards_data:
                    continue
                    
                headers = cards_data[0]
                if "Name" not in headers or "Held By Team" not in headers or "Wildcard" not in headers:
                    continue

                name_col = headers.index("Name")
                held_by_col = headers.index("Held By Team")
                wildcard_col = headers.index("Wildcard")
                
                for i, row in enumerate(cards_data[1:], start=2):
                    if len(row) <= max(name_col, held_by_col, wildcard_col):
                        continue
                    if str(row[name_col]).strip() != "Redemption":
                        continue
                        
                    try:
                        wildcard_data = json.loads(row[wildcard_col] or "{}")
                    except:
                        wildcard_data = {}
                        
                    team_status = wildcard_data.get(target_team_name)
                    if team_status and isinstance(team_status, str) and team_status.strip() == "active":
                        del wildcard_data[target_team_name]
                        sheet_obj.update_cell(i, wildcard_col + 1, json.dumps(wildcard_data))
                        
                        held_by_str = str(sheet_obj.cell(i, held_by_col + 1).value or "")
                        teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                        if target_team_name in teams:
                            teams.remove(target_team_name)
                        sheet_obj.update_cell(i, held_by_col + 1, ", ".join(teams))
                        
                        print(f"✅ Consumed Redemption for {target_team_name} from {sheet_obj.title}")
                        return True
                        
            return False
                
        except Exception as e:
            print(f"❌ Error in check_and_consume_redemption: {e}")
            return False

    def check_and_consume_elder_maul(self, target_team_name: str) -> bool:
        """
        Checks if a target team has Elder Maul active across both card sheets.
        Consolidates API calls and handles removal in a single threaded flow.
        """
        try:
            for sheet_obj in (self.chest_sheet, self.chance_sheet):
                cards_data = sheet_obj.get_all_values()
                if not cards_data:
                    continue
                    
                headers = cards_data[0]
                if "Name" not in headers or "Held By Team" not in headers or "Wildcard" not in headers:
                    continue

                name_col = headers.index("Name")
                held_by_col = headers.index("Held By Team")
                wildcard_col = headers.index("Wildcard")
                
                for i, row in enumerate(cards_data[1:], start=2):
                    if len(row) <= max(name_col, held_by_col, wildcard_col):
                        continue
                    if str(row[name_col]).strip() != "Elder Maul":
                        continue
                        
                    try:
                        wildcard_data = json.loads(row[wildcard_col] or "{}")
                    except:
                        wildcard_data = {}

                    team_status = wildcard_data.get(target_team_name)
                    
                    if team_status and isinstance(team_status, str) and team_status.strip() == "active":
                        del wildcard_data[target_team_name]
                        sheet_obj.update_cell(i, wildcard_col + 1, json.dumps(wildcard_data))
                        
                        held_by_str = str(sheet_obj.cell(i, held_by_col + 1).value or "")
                        teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                        if target_team_name in teams:
                            teams.remove(target_team_name)
                        sheet_obj.update_cell(i, held_by_col + 1, ", ".join(teams))
                        
                        print(f"✅ Consumed Elder Maul for {target_team_name} from {sheet_obj.title}")
                        return True
            
            return False
                
        except Exception as e:
            print(f"❌ Error in check_and_consume_elder_maul: {e}")
            return False

    async def consume_protect_item(self, team_name: str) -> bool:
        """
        Consumes the Protect Item shield for a team.
        Returns True if it successfully cleared the shield and removed the card.
        """
        try:
            # 1. Clear the Active Flag in the Team Data Sheet
            records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            headers = list(records[0].keys()) if records else []
            
            team_row_idx = -1
            for idx, r in enumerate(records, start=2):
                if str(r.get("Team", "")).strip().lower() == team_name.strip().lower():
                    team_row_idx = idx
                    break
                    
            if team_row_idx != -1 and "Protect Item" in headers:
                prot_col = headers.index("Protect Item") + 1
                await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, prot_col, "no")

            # 2. Find and Remove the physical card from their inventory
            for sheet in [self.chance_sheet, self.chest_sheet]:
                card_records = await asyncio.to_thread(sheet.get_all_records)
                
                for idx, r in enumerate(card_records, start=2):
                    if str(r.get("Name", "")).strip().lower() == "protect item":
                        held_by = [t.strip() for t in str(r.get("Held By Team", "")).split(",") if t.strip()]
                        
                        # If the team has the card, remove them from the list
                        target_team_lower = team_name.strip().lower()
                        if any(t.lower() == target_team_lower for t in held_by):
                            updated_holders = [t for t in held_by if t.lower() != target_team_lower]
                            
                            # Update Column 3 (Held By Team)
                            await asyncio.to_thread(sheet.update_cell, idx, 3, ", ".join(updated_holders))
                            return True
            return True

        except Exception as e:
            print(f"❌ Error consuming Protect Item for {team_name}: {e}")
            return False

    async def consume_recoil(self, team_name: str):
        """Shatters the Ring of Recoil after one use by setting the sheet flag back to 'no'."""
        try:
            # Fetch all records asynchronously
            records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            headers = list(records[0].keys()) if records else []
            
            if "Ring of Recoil" in headers:
                # Find the specific team's row
                team_info = next((r for r in records if str(r.get("Team", "")).strip().lower() == team_name.strip().lower()), None)
                
                if team_info:
                    team_row_idx = records.index(team_info) + 2
                    col_idx = headers.index("Ring of Recoil") + 1
                    
                    # Flip the flag back to "no"
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col_idx, "no")
                    
        except Exception as e:
            print(f"❌ Error consuming Ring of Recoil for {team_name}: {e}")
            traceback.print_exc()

    async def consume_phoenix_necklace(self, team_name: str):
        """Shatters the Phoenix Necklace after absorbing a rent payment."""
        try:
            records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            headers = list(records[0].keys()) if records else []
            if "Phoenix Necklace" in headers:
                team_info = next((r for r in records if str(r.get("Team", "")).strip().lower() == team_name.strip().lower()), None)
                if team_info:
                    team_row_idx = records.index(team_info) + 2
                    col_idx = headers.index("Phoenix Necklace") + 1
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col_idx, "no")
        except Exception as e:
            print(f"❌ Error consuming Phoenix Necklace for {team_name}: {e}")

    async def consume_charos(self, team_name: str):
        """Shatters the Ring of Charos (a) after halving a house purchase cost."""
        try:
            records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            headers = list(records[0].keys()) if records else []
            if "Ring of Charos" in headers:
                team_info = next((r for r in records if str(r.get("Team", "")).strip().lower() == team_name.strip().lower()), None)
                if team_info:
                    team_row_idx = records.index(team_info) + 2
                    col_idx = headers.index("Ring of Charos") + 1
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col_idx, "no")
        except Exception as e:
            print(f"❌ Error consuming Ring of Charos for {team_name}: {e}")

    async def consume_ring_of_stone(self, team_name: str):
        """Shatters the Ring of Stone after preventing forced movement."""
        try:
            records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            headers = list(records[0].keys()) if records else []
            if "Ring of Stone" in headers:
                team_info = next((r for r in records if str(r.get("Team", "")).strip().lower() == team_name.strip().lower()), None)
                if team_info:
                    team_row_idx = records.index(team_info) + 2
                    col_idx = headers.index("Ring of Stone") + 1
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col_idx, "no")
        except Exception as e:
            print(f"❌ Error consuming Ring of Stone for {team_name}: {e}")
    
    def check_and_consume_alchemy(self, team_name: str) -> tuple[int, str]:
        """
        Checks if a team has an active Alchemy card across both card sheets.
        If yes, consumes it and returns the multiplier (2 or 3) and card name.
        If no, returns 1 and None.
        """
        try:
            for sheet_obj in (self.chance_sheet, self.chest_sheet):
                cards_data = sheet_obj.get_all_values()
                if not cards_data:
                    continue
                    
                headers = cards_data[0]
                name_col = headers.index("Name")
                held_by_col = headers.index("Held By Team")
                wildcard_col = headers.index("Wildcard")
                
                for i, row in enumerate(cards_data[1:], start=2):
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

                    team_status = None
                    found_key = None
                    for key, value in wildcard_data.items():
                        if key.strip() == team_name:
                            team_status = value
                            found_key = key
                            break
                    
                    if team_status and isinstance(team_status, str) and team_status.strip() == "active":
                        multiplier = 3 if card_name == "High Alchemy" else 2
                        
                        del wildcard_data[found_key]
                        sheet_obj.update_cell(i, wildcard_col + 1, json.dumps(wildcard_data))
                        
                        held_by_str = str(sheet_obj.cell(i, held_by_col + 1).value or "")
                        teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                        if team_name in teams:
                            teams.remove(team_name)
                        sheet_obj.update_cell(i, held_by_col + 1, ", ".join(teams))
                        
                        print(f"✅ Consumed {card_name} for {team_name}, applying x{multiplier} GP multiplier.")
                        return multiplier, card_name
                        
            return 1, None
                
        except Exception as e:
            print(f"❌ Error in check_and_consume_alchemy: {e}")
            return 1, None

    def clear_all_active_statuses(self, team_name: str):
        """
        Finds and clears all "active" statuses for a given team
        from both card sheets. This is called at the start of a team's turn.
        """
        print(f"❗ Clearing all active statuses for {team_name}...")
        sheets_to_check = [self.chance_sheet, self.chest_sheet]
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

                for i, row in enumerate(data[1:], start=2):
                    if len(row) <= max(name_col, held_by_col, wildcard_col):
                        continue
                    
                    card_name = row[name_col]
                    wildcard_str = str(row[wildcard_col] or "{}")
                    if "active" not in wildcard_str:
                        continue

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
                    
                    if team_status and isinstance(team_status, str) and team_status.strip() == "active":
                        print(f"        > Found active card: {card_name}. Consuming...")
                        
                        del wildcard_data[found_key]
                        sheet_obj.update_cell(i, wildcard_col + 1, json.dumps(wildcard_data))
                        
                        held_by_str = str(row[held_by_col] or "")
                        teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                        if team_name in teams:
                            teams.remove(team_name)
                        sheet_obj.update_cell(i, held_by_col + 1, ", ".join(teams))
                        
                        cards_cleared.append(card_name)

            except Exception as e:
                print(f"❌ Error in clear_all_active_statuses for sheet {sheet_obj.title}: {e}")
                
        return cards_cleared

    def sync_houses_owned(self, team_name: str):
        """
        Calculates the total number of houses a team owns across all properties 
        in HouseData and updates the 'Houses Owned' column in TeamData.
        """
        try:
            # 1. Tally up houses from HouseData
            house_records = self.house_data_sheet.get_all_records()
            total_houses = 0
            
            for row in house_records:
                if str(row.get("OwnerTeam", "")).strip() == team_name:
                    count_str = str(row.get("HouseCount", "0")).strip()
                    if count_str.isdigit():
                        total_houses += int(count_str)
            
            # 2. Update the TeamData sheet
            team_records = self.team_data_sheet.get_all_records()
            headers = self.team_data_sheet.row_values(1)
            
            if "Houses Owned" not in headers:
                print("❌ 'Houses Owned' column not found in TeamData. Please check the header name.")
                return
                
            houses_col_idx = headers.index("Houses Owned") + 1
            
            for idx, record in enumerate(team_records, start=2):
                if record.get("Team") == team_name:
                    self.team_data_sheet.update_cell(idx, houses_col_idx, total_houses)
                    print(f"✅ Synced {total_houses} total houses for {team_name} in TeamData.")
                    return
                    
        except Exception as e:
            print(f"❌ Error syncing houses owned for {team_name}: {e}")

    async def check_and_award_card_on_land(self, team_name: str, new_pos: int, reason: str = "landing on"):
        """
        Handles post-move checks:
        1. Grants a free roll if landing on a special tile with 0 rolls left.
        2. Awards Chest/Chance cards with correct emojis.
        """
        team_channel = self.get_team_channel(team_name)
        if not team_channel:
            return

        is_in_jail = await asyncio.to_thread(self.get_jail_status, team_name)
        is_just_visiting = (new_pos == JAIL_TILE and is_in_jail == "no")

        if new_pos in ROLL_GRANTING_TILES or is_just_visiting:
            try:
                rolls_available = self.get_team_rolls(team_name)
                
                if rolls_available <= 0:
                    self.increment_rolls_available(team_name)
                    
                    try:
                        tile_name = self.get_tile_name_for_display(new_pos)
                        if is_just_visiting:
                            tile_name = "Jail (Just Visiting) - Nex, Gauntlet"
                            
                        roll_embed = discord.Embed(
                            title="🎲 Free Roll Granted!",
                            description=f"**{team_name}** reached **{tile_name}** with no rolls remaining. A free roll has been granted!",
                            color=discord.Color.yellow()
                        )
                        await team_channel.send(embed=roll_embed)
                        await self.mirror_to_game_log(team_channel, embed=roll_embed)
                        print(f"✅ Roll message sent for {team_name}")
                    except Exception as msg_err:
                        print(f"⚠️ Sheet updated, but Discord message failed: {msg_err}")

            except Exception as e:
                print(f"❌ Error during roll protection check: {e}")

        if new_pos in CHEST_TILES:
            print(f"<:chest:1558985858516787251> {team_name} triggered CHEST on tile {new_pos}")
            await self.team_receives_card(team_name, "Chest", team_channel)
            
        elif new_pos in CHANCE_TILES:
            print(f"<:chance:1558993615152353360> {team_name} triggered CHANCE on tile {new_pos}")
            await self.team_receives_card(team_name, "Chance", team_channel)

    @app_commands.command(name="cards", description="Show all cards currently held by your team.")
    async def cards(self, interaction: discord.Interaction):
        if str(interaction.channel_id) not in TEAM_CHANNEL_IDS_AS_STR:
            await interaction.response.send_message(
                "❌ You can only use this command in your team's channel.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        team_name = self.get_team(interaction.user)
        if not team_name:
            await interaction.followup.send("❌ You don't have a team role assigned.", ephemeral=True)
            return

        chest_cards = self.get_held_cards(self.chest_sheet, team_name)
        chance_cards = self.get_held_cards(self.chance_sheet, team_name)

        try:
            records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            team_record = next((r for r in records if str(r.get("Team", "")).strip().lower() == team_name.strip().lower()), {})
            is_protected = str(team_record.get("Protect Item", "no")).strip().lower() == "yes"
            has_recoil = str(team_record.get("Ring of Recoil", "no")).strip().lower() == "yes"
            has_phoenix = str(team_record.get("Phoenix Necklace", "no")).strip().lower() == "yes"
            has_charos = str(team_record.get("Ring of Charos", "no")).strip().lower() == "yes"
            has_stone = str(team_record.get("Ring of Stone", "no")).strip().lower() == "yes"
        except Exception as e:
            print(f"❌ Error fetching passives status: {e}")
            is_protected, has_recoil, has_phoenix, has_charos, has_stone = False, False, False, False, False

        if not chest_cards and not chance_cards and not is_protected and not has_recoil and not has_phoenix and not has_charos and not has_stone:
            await interaction.followup.send("❌ Your team holds no cards and has no active passives.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{team_name}'s Inventory",
            color=discord.Color.purple(),
            description="Active passives and held items:"
        )

        passives_text = ""
        if is_protected:
            passives_text += "<:protect_item:1559003530050670632> **Protect Item**\n*This prayer is active and will automatically block the next effect that steals your GP or cards.*\n\n"
        if has_recoil:
            passives_text += "<:recoil:1558985588055609374> **Ring of Recoil**\n*Speak of mutually assured destruction... Affects triggered on you are also triggered to the attacker.*\n\n"
        if has_phoenix:
            passives_text += "<:pneck:1558990483110367242> **Phoenix Necklace**\n*This necklace will completely absorb the next rent payment you owe to another team before shattering.*\n\n"
        if has_charos:
            passives_text += "<:charos:1558985798483837049> **Ring of Charos (a)**\n*This ring will automatically charm the real estate agent into giving you a 50% discount on your next house purchase.*\n\n"
        if has_stone:
            passives_text += "<:ring_of_stone:1558985677134241873> **Ring of Stone**\n*This ring turns you into a heavy rock, preventing the next card effect that attempts to forcefully move or teleport you.*\n\n"

        if passives_text:
            embed.add_field(
                name="<:passive:1558986754403336235> Passives <:passive:1558986754403336235>",
                value=passives_text.strip(),
                inline=False
            )

        # --- CHEST CARDS SECTION ---
        if chest_cards:
            for i, card in enumerate(chest_cards, start=1):
                emoji = CARD_EMOJIS.get(card['name'], "<:chest:1558985858516787251>")
                embed.add_field(
                    name=f"{emoji} [{i}] Chest Card — {card['name']}",
                    value=f"```{card['text']}```",
                    inline=False
                )

        # --- CHANCE CARDS SECTION ---
        offset = len(chest_cards)
        if chance_cards:
            for i, card in enumerate(chance_cards, start=1):
                emoji = CARD_EMOJIS.get(card['name'], "<:chance:1558993615152353360>")
                embed.add_field(
                    name=f"{emoji} [{i+offset}] Chance Card — {card['name']}",
                    value=f"```{card['text']}```",
                    inline=False
                )

        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="use_card", description="Use a held card by its index from /cards")
    @app_commands.describe(index="The index of the card you want to use (starts at 1)")
    async def use_card(self, interaction: discord.Interaction, index: int):
        if str(interaction.channel_id) not in TEAM_CHANNEL_IDS_AS_STR:
            await interaction.response.send_message(
                "❌ You can only use this command in your team's channel.", ephemeral=True
            )
            return
            
        if not self.has_event_captain_role(interaction.user):
            await interaction.response.send_message(
                "❌ Only the Event Captain can use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)  
        team_name = self.get_team(interaction.user)
        if not team_name:
            await interaction.followup.send("❌ You are not on a team.", ephemeral=True)
            return

        try:
            team_data_headers = self.team_data_sheet.row_values(1)
            gp_col_index = team_data_headers.index("GP") + 1
            teleblocked_col_index = team_data_headers.index("Teleblocked") + 1
        except ValueError as e:
            if 'GP' in str(e):
                await interaction.followup.send("❌ Data sheet error: Missing 'GP' column.", ephemeral=True)
            elif 'Teleblocked' in str(e):
                await interaction.followup.send("❌ Data sheet error: Missing 'Teleblocked' column. Please add it.", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Data sheet error: {e}", ephemeral=True)
            return

        try:
            all_records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            team_info = next((r for r in all_records if r.get("Team") == team_name), None)
            
            if not team_info:
                await interaction.followup.send(f"❌ Could not find data for **{team_name}**.", ephemeral=True)
                return

            is_silenced = str(team_info.get("Silenced", "no")).strip().lower()
            if is_silenced == "yes":
                await interaction.followup.send("❌ <:mime:1559001543557251212> **You are Silenced!** The Mime's aura prevents you from using any cards. You must roll the dice to break the silence.", ephemeral=True)
                return
            
            has_double_card = str(team_info.get("Double Card", "no")).strip().lower() == "yes"
            used_card_flag = str(team_info.get("Used Card This Turn", "no")).strip().lower()
            
            double_card_note = ""
            
            if used_card_flag == "yes":
                if has_double_card:
                    double_card_note = "\n\n<:count_check:1559005679656763452> **Count Check says:** You have no card uses remaining this turn (bleeeh bleeeh!)."
                    asyncio.create_task(asyncio.to_thread(self.clear_flag_column, team_name, "Double Card"))
                else:
                    await interaction.followup.send("❌ You can only use one card per turn. Roll again to use another card.", ephemeral=True)
                    return
            else:
                if has_double_card:
                    double_card_note = "\n\n🃏 **Double Cards Active!** You still have **1** more card use available this turn!"
                
        except Exception as e:
            print(f"❌ Error checking team status flags: {e}")
        
        chest_cards = self.get_held_cards(self.chest_sheet, team_name)
        chance_cards = self.get_held_cards(self.chance_sheet, team_name)
        all_cards = chest_cards + chance_cards

        if index < 1 or index > len(all_cards):
            await interaction.followup.send(f"❌ Invalid card index. Use `/cards` and pick a number between 1 and {len(all_cards)}.", ephemeral=True)
            return
        
        selected_card = all_cards[index - 1]
        card_type = "Chest" if (index - 1) < len(chest_cards) else "Chance"
        card_sheet = self.chest_sheet if card_type == "Chest" else self.chance_sheet
        card_row = selected_card['row_index']
        
        card_name = selected_card['name']
        card_emoji = CARD_EMOJIS.get(card_name, "✅")
        
        stored_roll = None
        final_card_text = selected_card['text']
        
        is_status_activation = False
        embed_description = ""
        
        loop = asyncio.get_event_loop()

        try:
            wildcard_data_str = card_sheet.cell(card_row, 4).value or "{}"
            wildcard_data = {}
            team_wildcard_value = None
            try:
                wildcard_data = json.loads(wildcard_data_str)
                val = wildcard_data.get(team_name)
                if val is not None and isinstance(val, str):
                    val_str = val.strip()
                    if val_str.lstrip('-').isdigit():
                        team_wildcard_value = int(val_str)
                    else:
                        team_wildcard_value = val_str
                else:
                    team_wildcard_value = val
            except Exception as e:
                print(f"❌ Error parsing wildcard for {team_name}: {e}")

            if card_name == "Vengeance":
                if team_wildcard_value == "active":
                    await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                    return
                
                wildcard_data[team_name] = "active"
                card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
                is_status_activation = True
                
                embed_description = "> The next card effect used on your team will be rebounded."

            elif card_name == "Redemption":
                if team_wildcard_value == "active":
                    await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                    return
                
                wildcard_data[team_name] = "active"
                card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
                is_status_activation = True
                
                embed_description = "> The next negative card effect used on your team will be fizzled."

            elif card_name == "Elder Maul":
                if team_wildcard_value == "active":
                    await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                    return
                
                wildcard_data[team_name] = "active"
                
                await asyncio.to_thread(
                    card_sheet.update_cell, 
                    card_row, 
                    4, 
                    json.dumps(wildcard_data)
                )
                
                is_status_activation = True
                embed_description = "> <:eldermaul:1558986407735861359> **Elder Maul Activated!** The next negative card effect used on your team will be reduced."

            elif card_name == "Low Alchemy":
                if team_wildcard_value == "active":
                    await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                    return

                wildcard_data[team_name] = "active"
                card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
                is_status_activation = True
                
                embed_description = "> Your next drop this turn will be worth **double GP**."
                
            elif card_name == "High Alchemy":
                if team_wildcard_value == "active":
                    await interaction.followup.send("❌ This card is already active!", ephemeral=True)
                    return
                    
                wildcard_data[team_name] = "active"
                card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data))
                is_status_activation = True
                
                embed_description = "> Your next drop this turn will be worth **triple GP**."
                
            elif card_name == "Vile Vigour" and isinstance(team_wildcard_value, int):
                stored_roll = team_wildcard_value
                
                all_teams_data = await asyncio.to_thread(self.team_data_sheet.get_all_records)
                caster_pos = -1
                team_row_idx = -1
                for idx, record in enumerate(all_teams_data, start=2):
                    if record.get("Team") == team_name:
                        caster_pos = int(record.get("Position", -1))
                        team_row_idx = idx
                        break
                
                if caster_pos == -1:
                    await interaction.followup.send("❌ Could not find your team's position.", ephemeral=True)
                    return

                raw_new_pos = caster_pos + stored_roll
                intended_pos = raw_new_pos % BOARD_SIZE
                new_pos = self.resolve_nonroll_landing_tile(intended_pos)

                # --- 💰 PASS GO CHECK ---
                go_msg = ""
                if raw_new_pos >= BOARD_SIZE and new_pos != 30:
                    go_msg = await self.process_manual_pass_go(team_name, team_row_idx, all_teams_data[team_row_idx-2])

                await asyncio.to_thread(self.log_command, team_name, "/card_effect_set_tile", {"team": team_name, "tile": new_pos})
                
                destination_tile_name = self.get_tile_name_for_display(new_pos)
                embed_description = f"> Moved **{stored_roll}** spaces forward to the **{destination_tile_name}** tile (Tile **{new_pos}**).{go_msg}"
                embed_description += self.get_glider_redirect_note(intended_pos, new_pos)

                await self.check_and_award_card_on_land(team_name, new_pos, "using Vile Vigour to")
                await self.auto_post_show_drops_if_boss_tile(team_name, new_pos)
                
            elif card_name == "Lure":
                all_teams_data = await asyncio.to_thread(self.team_data_sheet.get_all_records)
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
                    if opponent_team_name == team_name or not opponent_team_name:
                        continue
                    
                    opponent_pos = int(record.get("Position", -1))
                    
                    dist = (opponent_pos - caster_pos) % BOARD_SIZE
                    
                    if 1 <= dist <= 12:
                        opponents_ahead.append((opponent_team_name, opponent_pos, dist))
                
                if not opponents_ahead:
                    await interaction.followup.send("❌ Card effect failed: No opponents are within 12 tiles ahead of you.", ephemeral=True)
                    return 

                sorted_opponents = sorted(opponents_ahead, key=lambda x: x[2])
                closest_dist = sorted_opponents[0][2]
                
                closest_teams = [opp for opp in sorted_opponents if opp[2] == closest_dist]
                chosen_target = random.choice(closest_teams)
                
                target_team = chosen_target[0]
                target_pos = chosen_target[1]
                
                victim_channel = self.get_team_channel(target_team)

                # --- <:defence:1559009393884925952> PASSIVE CHECKS ---
                victim_info = next((r for r in all_teams_data if r.get("Team") == target_team), {})
                has_stone = str(victim_info.get("Ring of Stone", "no")).strip().lower() == "yes"

                if await asyncio.to_thread(self.check_and_consume_redemption, target_team):
                    embed_description = f"<:lure:1558986093796392960> **{team_name}** tried to use **Lure** on **{target_team}**...\n\n<:redemption:1558985458195898389> But **{target_team}**'s Redemption activated!"
                    if victim_channel:
                        fizzle_embed = discord.Embed(title="<:redemption:1558985458195898389> Redemption Activated!", description=f"**{team_name}** tried to use **Lure** on you, but your **Redemption** activated!", color=discord.Color.blue())
                        await victim_channel.send(embed=fizzle_embed)
                        await self.mirror_to_game_log(victim_channel, embed=fizzle_embed)
                
                elif has_stone:
                    await self.consume_ring_of_stone(target_team)
                    embed_description = f"<:lure:1558986093796392960> **{team_name}** tried to use **Lure** on **{target_team}**...\n\n<:ring_of_stone:1558985677134241873> But **{target_team}** was wearing a **Ring of Stone**! They turned into a heavy rock and could not be moved. The Lure failed!"
                    
                    stone_caster_embed = discord.Embed(
                        title="<:ring_of_stone:1558985677134241873> Attack Blocked!", 
                        description=f"You tried to Lure **{target_team}**, but they were wearing a **Ring of Stone** and couldn't be moved!\nYour attack failed and your card was wasted.", 
                        color=discord.Color.red()
                    )
                    await interaction.channel.send(embed=stone_caster_embed)
                    await self.mirror_to_game_log(interaction.channel, embed=stone_caster_embed)

                    if victim_channel:
                        stone_embed = discord.Embed(title="<:ring_of_stone:1558985677134241873> Ring of Stone Activated!", description=f"**{team_name}** tried to **Lure** you, but your **Ring of Stone** turned you into a rock and prevented you from being moved!", color=discord.Color.blue())
                        await victim_channel.send(embed=stone_embed)
                        await self.mirror_to_game_log(victim_channel, embed=stone_embed)
                
                else:
                    intended_lure_pos = caster_pos
                    final_lure_pos = self.resolve_nonroll_landing_tile(intended_lure_pos)
                    glider_note = self.get_glider_redirect_note(intended_lure_pos, final_lure_pos)
                    glider_note_victim = self.get_glider_redirect_note(intended_lure_pos, final_lure_pos, second_person=True, quoted=False)
                    self.log_command(
                        team_name,
                        "/card_effect_set_tile",
                        {"team": target_team, "tile": final_lure_pos}
                    )
                    source_tile_name = self.get_tile_name_for_display(target_pos)
                    destination_tile_name = self.get_tile_name_for_display(final_lure_pos)
                    embed_description = (
                        f"<:lure:1558986093796392960> **{target_team}** was lured from the "
                        f"**{source_tile_name}** tile (Tile **{target_pos}**) to your tile: the "
                        f"**{destination_tile_name}** tile (Tile **{final_lure_pos}**)!"
                    )
                    embed_description += glider_note
                    
                    if victim_channel:
                    
                        lure_embed = discord.Embed(
                    
                            title="<:lure:1558986093796392960> You Were Lured!",
                    
                            description=(f"**{team_name}** used **Lure** and pulled your team to the **{self.get_tile_name_for_display(final_lure_pos)}** tile (Tile **{final_lure_pos}**)." + glider_note_victim),
                    
                            color=discord.Color.orange()
                    
                        )
                    
                        await victim_channel.send(embed=lure_embed)

                    
                        await self.mirror_to_game_log(victim_channel, embed=lure_embed)

                    
                    await self.check_and_award_card_on_land(target_team, final_lure_pos, "being lured to")
                    await self.auto_post_show_drops_if_boss_tile(target_team, final_lure_pos)

            elif card_name == "Escape Crystal":
                # 1. Teleblock Check
                if self.get_teleblock_status(team_name) == "yes":
                    await interaction.followup.send("<:teleblock:1558985901831364710> You are Teleblocked! You cannot use this card, even in jail!", ephemeral=True)
                    return 

                # 2. Jail Status Check (The new guard clause)
                jail_status = await asyncio.to_thread(self.get_jail_status, team_name)
                if jail_status != "yes":
                    await interaction.followup.send(
                        "❌ **Action Denied:** You are currently 'Just Visiting' Tile 10. "
                        "The Escape Crystal can only be used if you were sent to Jail!",
                        ephemeral=True
                    )
                    return

                # 3. Execution
                await asyncio.to_thread(self.increment_rolls_available, team_name)
                # Clear
                await asyncio.to_thread(self.set_jail_status, team_name, "no")
                
                embed_description = "> 🎲 You have used your crystal to escape! You gained a free roll."

            elif card_name == "Tele Block":
                all_teams_data = self.team_data_sheet.get_all_records()
                valid_targets = []

                for record in all_teams_data:
                    current_team_name = record.get("Team")
                    if current_team_name and current_team_name != team_name:
                        valid_targets.append(current_team_name)

                if not valid_targets:
                    await interaction.followup.send("❌ Card effect failed: No opponents to Tele Block.", ephemeral=True)
                    return 
                
                embed = discord.Embed(title="🎯 Target Selection: Tele Block", description="Select a team to Teleblock!", color=discord.Color.dark_purple())
                extra_memory = {"card_sheet": card_sheet, "card_row": card_row, "wildcard_data": wildcard_data, "team_wildcard_value": team_wildcard_value, "double_card_note": double_card_note}
                view = self.CardTargetView(self, team_name, valid_targets, "Tele Block", "tele_block", extra_data=extra_memory)
                await interaction.followup.send(embed=embed, view=view, ephemeral=False)
                return

            elif card_name == "Rogue's Gloves":
                stealable_cards = []
                for sheet, sheet_name in [(self.chance_sheet, "Chance"), (self.chest_sheet, "Chest")]:
                    data = sheet.get_all_values()
                    if not data: continue
                    headers = data[0]
                    name_col, held_by_col, wildcard_col = headers.index("Name"), headers.index("Held By Team"), headers.index("Wildcard")
                    for i, row in enumerate(data[1:], start=2):
                        if len(row) <= max(name_col, held_by_col, wildcard_col): continue
                        held_by_str = str(row[held_by_col] or "")
                        if not held_by_str: continue
                        
                        all_holders = [t.strip() for t in held_by_str.split(',') if t.strip()]
                        wildcard_str = str(row[wildcard_col] or "{}")
                        wildcard_data_json = {}
                        if wildcard_str.strip():
                            try: wildcard_data_json = json.loads(wildcard_str)
                            except: pass
                            
                        valid_victims = [h for h in all_holders if h != team_name and wildcard_data_json.get(h) != "active"]
                        for v in valid_victims:
                            stealable_cards.append({"sheet": sheet, "row_index": i, "card_name": str(row[name_col]), "card_type": sheet_name, "victim_team": v})

                if not stealable_cards:
                    await interaction.followup.send("❌ Card effect failed: There are no eligible cards to steal.", ephemeral=True)
                    return 

                team_card_counts = {}
                for c in stealable_cards:
                    team_card_counts[c["victim_team"]] = team_card_counts.get(c["victim_team"], 0) + 1

                embed = discord.Embed(title="🎯 Target Selection: Rogue's Gloves", description="Select a team to steal from!", color=discord.Color.dark_gray())
                extra_memory = {"card_sheet": card_sheet, "card_row": card_row, "wildcard_data": wildcard_data, "team_wildcard_value": team_wildcard_value, "stealable_cards": stealable_cards, "double_card_note": double_card_note}
                view = self.CardTargetView(self, team_name, list(team_card_counts.keys()), "Rogue's Gloves", "rogues_gloves", extra_data=extra_memory)
                await interaction.followup.send(embed=embed, view=view, ephemeral=False)
                return

            elif card_name == "Smite":
                smitable_cards = []
                for sheet, sheet_name in [(self.chance_sheet, "Chance"), (self.chest_sheet, "Chest")]:
                    data = sheet.get_all_values()
                    if not data: continue
                    headers = data[0]
                    name_col, held_by_col, wildcard_col = headers.index("Name"), headers.index("Held By Team"), headers.index("Wildcard")
                    for i, row in enumerate(data[1:], start=2):
                        if len(row) <= max(name_col, held_by_col, wildcard_col): continue
                        held_by_str = str(row[held_by_col] or "")
                        if not held_by_str: continue
                        
                        all_holders = [t.strip() for t in held_by_str.split(',') if t.strip()]
                        wildcard_str = str(row[wildcard_col] or "{}")
                        wildcard_data_json = {}
                        if wildcard_str.strip():
                            try: wildcard_data_json = json.loads(wildcard_str)
                            except: pass
                            
                        valid_victims = [h for h in all_holders if h != team_name and wildcard_data_json.get(h) != "active"]
                        for v in valid_victims:
                            smitable_cards.append({"sheet": sheet, "row_index": i, "card_name": str(row[name_col]), "card_type": sheet_name, "victim_team": v})

                if not smitable_cards:
                    await interaction.followup.send("❌ Card effect failed: No opponents have removable cards to Smite.", ephemeral=True)
                    return 

                team_card_counts = {}
                for c in smitable_cards:
                    team_card_counts[c["victim_team"]] = team_card_counts.get(c["victim_team"], 0) + 1

                embed = discord.Embed(title="🎯 Target Selection: Smite", description="Select a team to Smite!", color=discord.Color.red())
                extra_memory = {"card_sheet": card_sheet, "card_row": card_row, "wildcard_data": wildcard_data, "team_wildcard_value": team_wildcard_value, "smitable_cards": smitable_cards, "double_card_note": double_card_note}
                view = self.CardTargetView(self, team_name, list(team_card_counts.keys()), "Smite", "smite", extra_data=extra_memory)
                await interaction.followup.send(embed=embed, view=view, ephemeral=False)
                return

                chest_data = self.chest_sheet.get_all_values()
                if chest_data:
                    headers = chest_data[0]
                    name_col, held_by_col, wildcard_col = headers.index("Name"), headers.index("Held By Team"), headers.index("Wildcard")
                    for i, row in enumerate(chest_data[1:], start=2):
                        if len(row) <= max(name_col, held_by_col, wildcard_col): continue
                        held_by_str = str(row[held_by_col] or "")
                        if held_by_str and team_name not in held_by_str:
                            all_holders = [t.strip() for t in held_by_str.split(',') if t.strip()]
                            wildcard_str = str(row[wildcard_col] or "{}")
                            wildcard_data_json = {}
                            try: wildcard_data_json = json.loads(wildcard_str)
                            except: pass
                            valid_victims = [h for h in all_holders if h != team_name and wildcard_data_json.get(h) != "active"]
                            if valid_victims:
                                for v in valid_victims:
                                    stealable_cards.append({"sheet": self.chest_sheet, "row_index": i, "card_name": str(row[name_col]), "card_type": "Chest", "victim_team": v})
                
                if not stealable_cards:
                    await interaction.followup.send("❌ Card effect failed: There are no eligible cards to steal.", ephemeral=True)
                    return 

                team_card_counts = {}
                for c in stealable_cards:
                    team_card_counts[c["victim_team"]] = team_card_counts.get(c["victim_team"], 0) + 1

                embed = discord.Embed(title="🎯 Target Selection: Rogue's Gloves", description="Select a team to steal from!", color=discord.Color.dark_gray())
                extra_memory = {"card_sheet": card_sheet, "card_row": card_row, "wildcard_data": wildcard_data, "team_wildcard_value": team_wildcard_value, "stealable_cards": stealable_cards, "double_card_note": double_card_note}
                view = self.CardTargetView(self, team_name, list(team_card_counts.keys()), "Rogue's Gloves", "rogues_gloves", extra_data=extra_memory)
                await interaction.followup.send(embed=embed, view=view, ephemeral=False)
                return

            elif card_name == "Pickpocket":
                all_teams_data = self.team_data_sheet.get_all_records()
                caster = team_name
                valid_targets = []
                target_gp_data = {}
                caster_record = None

                for record in all_teams_data:
                    current_team = record.get("Team")
                    if not current_team: continue
                    try:
                        current_gp = int(str(record.get("GP", 0)).replace(",", "") or 0)
                    except ValueError:
                        current_gp = 0

                    if current_team == caster:
                        caster_record = record
                        continue

                    if current_gp > 0:
                        valid_targets.append(current_team)
                        target_gp_data[current_team] = current_gp

                if not valid_targets or not caster_record:
                    await interaction.followup.send("❌ Card effect failed: No eligible team has GP to steal.", ephemeral=True)
                    return

                embed = discord.Embed(title="🎯 Target Selection: Pickpocket", description="Select a team to pickpocket! Here is the current GP of all eligible targets:\n", color=discord.Color.dark_gold())
                for t in valid_targets: embed.description += f"\n• **{t}**: {target_gp_data[t]:,} GP"

                extra_memory = {"card_sheet": card_sheet, "card_row": card_row, "wildcard_data": wildcard_data, "team_wildcard_value": team_wildcard_value, "all_teams_data": all_teams_data, "caster_record": caster_record, "target_gp_data": target_gp_data, "double_card_note": double_card_note}
                view = self.CardTargetView(self, team_name, valid_targets, "Pickpocket", "pickpocket", extra_data=extra_memory)
                await interaction.followup.send(embed=embed, view=view, ephemeral=False)
                return
            
            elif card_name == "Backstab" and isinstance(team_wildcard_value, int):
                stored_roll = team_wildcard_value
                
                all_teams_data = await asyncio.to_thread(self.team_data_sheet.get_all_records)
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
                    
                    # Calculate distance, wrapping around GO
                    dist = (opponent_pos - caster_pos) % BOARD_SIZE
                    
                    # Only target if they are 1 to 5 tiles ahead
                    if 1 <= dist <= 5:
                        opponents_ahead.append((opponent_team_name, opponent_pos, dist))
                
                if not opponents_ahead:
                    await interaction.followup.send("❌ Card effect failed: No opponents are within 5 tiles ahead of you.", ephemeral=True)
                    return 

                sorted_opponents = sorted(opponents_ahead, key=lambda x: x[2])
                closest_dist = sorted_opponents[0][2]
                
                closest_teams = [opp for opp in sorted_opponents if opp[2] == closest_dist]
                chosen_target = random.choice(closest_teams)
                
                target_team = chosen_target[0]
                target_pos = chosen_target[1] 
                
                embed_description = ""
                victim_channel = self.get_team_channel(target_team)

                # --- <:defence:1559009393884925952> PASSIVE CHECKS ---
                victim_info = next((r for r in all_teams_data if r.get("Team") == target_team), {})
                has_stone = str(victim_info.get("Ring of Stone", "no")).strip().lower() == "yes"

                # 1. Check Redemption (Total Immunity)
                if await asyncio.to_thread(self.check_and_consume_redemption, target_team):
                    embed_description += f"> <:redemption:1558985458195898389> **{target_team}**'s Redemption activated. **Backstab** fizzled.\n"
                    if victim_channel:
                        fizzle_embed = discord.Embed(
                            title="<:redemption:1558985458195898389> Redemption Activated!", 
                            description=f"**{team_name}** tried to use **Backstab** on you, but your **Redemption** activated!", 
                            color=discord.Color.blue()
                        )
                        await victim_channel.send(embed=fizzle_embed)
                        await self.mirror_to_game_log(victim_channel, embed=fizzle_embed)
                
                elif has_stone:
                    await self.consume_ring_of_stone(target_team)
                    embed_description += f"> <:ring_of_stone:1558985677134241873> **{target_team}** was wearing a **Ring of Stone**! They turned into a heavy rock and could not be moved. **Backstab** failed!\n"
                    
                    stone_caster_embed = discord.Embed(
                        title="<:ring_of_stone:1558985677134241873> Attack Blocked!", 
                        description=f"You tried to Backstab **{target_team}**, but they were wearing a **Ring of Stone** and couldn't be moved!\nYour attack failed and your card was wasted.", 
                        color=discord.Color.red()
                    )
                    await interaction.channel.send(embed=stone_caster_embed)
                    await self.mirror_to_game_log(interaction.channel, embed=stone_caster_embed)

                    if victim_channel:
                        stone_embed = discord.Embed(title="<:ring_of_stone:1558985677134241873> Ring of Stone Activated!", description=f"**{team_name}** tried to **Backstab** you, but your **Ring of Stone** turned you into a rock and prevented you from being moved!", color=discord.Color.blue())
                        await victim_channel.send(embed=stone_embed)
                        await self.mirror_to_game_log(victim_channel, embed=stone_embed)
                
                # 2. Check Vengeance (Rebound)
                elif await asyncio.to_thread(self.check_and_consume_vengeance, target_team):
                    elder_maul_active = await asyncio.to_thread(self.check_and_consume_elder_maul, team_name) 
                    
                    final_roll_val = (stored_roll // 2) if elder_maul_active else stored_roll
                    maul_suffix = " (Halved by <:eldermaul:1558986407735861359> **Elder Maul**!)" if elder_maul_active else ""
                    
                    intended_rebound_pos = max(0, target_pos - final_roll_val)
                    new_pos = self.resolve_nonroll_landing_tile(intended_rebound_pos)
                    destination_tile_name = self.get_tile_name_for_display(new_pos)
                    glider_note = self.get_glider_redirect_note(intended_rebound_pos, new_pos)
                    glider_note_victim = self.get_glider_redirect_note(intended_rebound_pos, new_pos, second_person=True, quoted=False)
                    
                    await asyncio.to_thread(self.log_command, team_name, "/card_effect_set_tile", {"team": team_name, "tile": new_pos})
                    
                    embed_description += (
                        f"> <:venge:1558986464409297077> **{target_team}** had Vengeance! Your team was rebounded and dragged "
                        f"**{final_roll_val}** tiles behind them to the **{destination_tile_name}** tile (Tile **{new_pos}**){maul_suffix}.\n"
                    )
                    embed_description += glider_note
                    
                    await self.check_and_award_card_on_land(team_name, new_pos, "being rebounded by Backstab to")
                    await self.auto_post_show_drops_if_boss_tile(team_name, new_pos)
                    
                    skull_embed = discord.Embed(
                        title="<:venge:1558986464409297077> Vengeance Activated!", 
                        description=(f"You activated **{target_team}**'s Vengeance!\nYour team was dragged **{final_roll_val}** tiles behind them to the **{destination_tile_name}** tile (Tile **{new_pos}**)!" + glider_note_victim), 
                        color=discord.Color.dark_red()
                    )
                    await interaction.channel.send(embed=skull_embed)
                    await self.mirror_to_game_log(interaction.channel, embed=skull_embed)
                    
                    if victim_channel:
                        victim_embed = discord.Embed(
                            title="<:venge:1558986464409297077> Vengeance Activated!",
                            description=(
                                f"**{team_name}** tried to use **Backstab** on your team, but your **Vengeance** rebounded the effect!\n"
                                f"They were dragged **{final_roll_val}** tiles behind your team to the **{destination_tile_name}** tile (Tile **{new_pos}**) (stops at Go)."
                                + glider_note_victim
                            ),
                            color=discord.Color.dark_red()
                        )
                        await victim_channel.send(embed=victim_embed)
                        await self.mirror_to_game_log(victim_channel, embed=victim_embed)
                
                # 3. Normal Hit
                else:
                    elder_maul_active = await asyncio.to_thread(self.check_and_consume_elder_maul, target_team)
                    
                    final_roll_val = (stored_roll // 2) if elder_maul_active else stored_roll 
                    maul_suffix = " (Halved by <:eldermaul:1558986407735861359> **Elder Maul**!)" if elder_maul_active else ""
                    
                    intended_backstab_pos = max(0, caster_pos - final_roll_val) 
                    new_pos = self.resolve_nonroll_landing_tile(intended_backstab_pos)
                    glider_note = self.get_glider_redirect_note(intended_backstab_pos, new_pos)
                    glider_note_victim = self.get_glider_redirect_note(intended_backstab_pos, new_pos, second_person=True, quoted=False)
                    source_tile_name = self.get_tile_name_for_display(target_pos)
                    destination_tile_name = self.get_tile_name_for_display(new_pos)
                    
                    await asyncio.to_thread(self.log_command, team_name, "/card_effect_set_tile", {"team": target_team, "tile": new_pos})
                    
                    embed_description += (
                        f"> **{target_team}** was pulled from the **{source_tile_name}** tile (Tile **{target_pos}**) "
                        f"and placed **{final_roll_val}** tiles behind your team on the **{destination_tile_name}** tile (Tile **{new_pos}**){maul_suffix}."
                    )
                    embed_description += glider_note

                    await self.check_and_award_card_on_land(target_team, new_pos, "being backstabbed to")
                    await self.auto_post_show_drops_if_boss_tile(target_team, new_pos)
                    
                    if victim_channel:
                        victim_embed = discord.Embed(
                            title="<:boner:1558986033440489563> You Were Backstabbed!",
                            description=(
                                f"**{team_name}** used **Backstab** on your team.\n"
                                f"You were dragged from Tile **{target_pos}** to **{final_roll_val}** tiles behind them, landing on the **{destination_tile_name}** tile (Tile **{new_pos}**) (stops at Go){maul_suffix}."
                                + glider_note_victim
                            ),
                            color=discord.Color.dark_red()
                        )
                        await victim_channel.send(embed=victim_embed)
                        await self.mirror_to_game_log(victim_channel, embed=victim_embed)

            elif card_name == "Dragon Spear" and isinstance(team_wildcard_value, int):
                stored_roll = team_wildcard_value
                move_amount = -stored_roll
                
                all_teams_data = await asyncio.to_thread(self.team_data_sheet.get_all_records)
                caster_pos = -1
                targets = []
                
                for record in all_teams_data:
                    if record.get("Team") == team_name:
                        caster_pos = int(record.get("Position", -1))
                        break
                
                if caster_pos != -1:
                    target_tiles = [caster_pos - 1, caster_pos, caster_pos + 1]
                    if caster_pos == 0: 
                        target_tiles = [0, 1, BOARD_SIZE - 1] 
                    elif caster_pos == BOARD_SIZE - 1: 
                        target_tiles = [BOARD_SIZE - 1, BOARD_SIZE - 2, 0] 

                    for record in all_teams_data:
                        opponent_team_name = record.get("Team")
                        if opponent_team_name == team_name:
                            continue
                        
                        opp_pos = int(record.get("Position", -1))
                        if opp_pos in target_tiles:
                            targets.append((opponent_team_name, opp_pos))
                
                if not targets:
                    await interaction.followup.send("❌ Card effect failed: No opponents are within 1 tile of you.", ephemeral=True)
                    return 

                embed_description = ""
                for target_team, target_pos in targets:
                    victim_channel = self.get_team_channel(target_team)
                    
                    # --- <:defence:1559009393884925952> PASSIVE CHECKS ---
                    victim_info = next((r for r in all_teams_data if r.get("Team") == target_team), {})
                    has_stone = str(victim_info.get("Ring of Stone", "no")).strip().lower() == "yes"

                    # 1. Check Redemption (Total Immunity)
                    if await asyncio.to_thread(self.check_and_consume_redemption, target_team):
                        embed_description += f"> <:redemption:1558985458195898389> **{target_team}**'s Redemption activated. **Dragon Spear** fizzled.\n"
                        if victim_channel:
                            fizzle_embed = discord.Embed(
                                title="<:redemption:1558985458195898389> Redemption Activated!", 
                                description=f"**{team_name}** tried to use **Dragon Spear** on you, but your **Redemption** activated!", 
                                color=discord.Color.blue()
                            )
                            await victim_channel.send(embed=fizzle_embed)
                            await self.mirror_to_game_log(victim_channel, embed=fizzle_embed)
                        continue  
                    
                    elif has_stone:
                        await self.consume_ring_of_stone(target_team)
                        embed_description += f"> <:ring_of_stone:1558985677134241873> **{target_team}** was wearing a **Ring of Stone**! They turned into a heavy rock and could not be speared.\n"
                        
                        stone_caster_embed = discord.Embed(
                            title="<:ring_of_stone:1558985677134241873> Attack Blocked!", 
                            description=f"You tried to Dragon Spear **{target_team}**, but they were wearing a **Ring of Stone** and couldn't be moved!", 
                            color=discord.Color.red()
                        )
                        await interaction.channel.send(embed=stone_caster_embed)
                        await self.mirror_to_game_log(interaction.channel, embed=stone_caster_embed)

                        if victim_channel:
                            stone_embed = discord.Embed(title="<:ring_of_stone:1558985677134241873> Ring of Stone Activated!", description=f"**{team_name}** tried to use a **Dragon Spear** on you, but your **Ring of Stone** turned you into a rock and prevented you from being moved!", color=discord.Color.blue())
                            await victim_channel.send(embed=stone_embed)
                            await self.mirror_to_game_log(victim_channel, embed=stone_embed)
                        continue 

                    # 2. Check Vengeance (Rebound)
                    elif await asyncio.to_thread(self.check_and_consume_vengeance, target_team):
                        elder_maul_active = await asyncio.to_thread(self.check_and_consume_elder_maul, team_name) 
                        
                        final_move_amount = -(stored_roll // 2) if elder_maul_active else move_amount
                        maul_suffix = " (Halved by <:eldermaul:1558986407735861359> **Elder Maul**!)" if elder_maul_active else ""
                        
                        intended_pos_after_rebound = max(0, caster_pos + final_move_amount)
                        new_pos = self.resolve_nonroll_landing_tile(intended_pos_after_rebound)
                        destination_tile_name = self.get_tile_name_for_display(new_pos)
                        glider_note = self.get_glider_redirect_note(intended_pos_after_rebound, new_pos)
                        glider_note_victim = self.get_glider_redirect_note(intended_pos_after_rebound, new_pos, second_person=True, quoted=False)
                        
                        await asyncio.to_thread(self.log_command, team_name, "/card_effect_set_tile", {"team": team_name, "tile": new_pos})
                        
                        embed_description += (
                            f"> <:venge:1558986464409297077> **{target_team}** had Vengeance! Your team was moved back "
                            f"**{abs(final_move_amount)}** tiles to the **{destination_tile_name}** tile (Tile **{new_pos}**) "
                            f"(stops at Go){maul_suffix}.\n"
                        )
                        embed_description += glider_note
                        
                        await self.check_and_award_card_on_land(team_name, new_pos, "being rebounded by Dragon Spear to")
                        await self.auto_post_show_drops_if_boss_tile(team_name, new_pos)
                        
                        skull_embed = discord.Embed(
                            title="<:venge:1558986464409297077> Vengeance Activated!", 
                            description=(f"You activated **{target_team}**'s Vengeance!\nYour team moved back **{abs(final_move_amount)}** spaces to the **{destination_tile_name}** tile (Tile **{new_pos}**)!" + glider_note_victim), 
                            color=discord.Color.dark_red()
                        )
                        await interaction.channel.send(embed=skull_embed)
                        await self.mirror_to_game_log(interaction.channel, embed=skull_embed)
                        
                        if victim_channel:
                            victim_embed = discord.Embed(
                                title="<:venge:1558986464409297077> Vengeance Activated!",
                                description=(
                                    f"**{team_name}** tried to use **Dragon Spear** on your team, but your **Vengeance** rebounded the effect!\n"
                                    f"They were moved back **{abs(final_move_amount)}** tiles to the **{destination_tile_name}** tile (Tile **{new_pos}**) (stops at Go)."
                                    + glider_note_victim
                                ),
                                color=discord.Color.dark_red()
                            )
                            await victim_channel.send(embed=victim_embed)
                            await self.mirror_to_game_log(victim_channel, embed=victim_embed)
                        continue  
                    
                    # 3. Normal Hit
                    else:
                        elder_maul_active = await asyncio.to_thread(self.check_and_consume_elder_maul, target_team)
                        
                        final_move_amount = -(stored_roll // 2) if elder_maul_active else move_amount
                        maul_suffix = " (Halved by <:eldermaul:1558986407735861359> **Elder Maul**!)" if elder_maul_active else ""
                        
                        intended_target_pos = max(0, target_pos + final_move_amount)
                        new_pos = self.resolve_nonroll_landing_tile(intended_target_pos)
                        glider_note = self.get_glider_redirect_note(intended_target_pos, new_pos)
                        glider_note_victim = self.get_glider_redirect_note(intended_target_pos, new_pos, second_person=True, quoted=False)
                        
                        await asyncio.to_thread(self.log_command, team_name, "/card_effect_set_tile", {"team": target_team, "tile": new_pos})
                        
                        destination_tile_name = self.get_tile_name_for_display(new_pos)
                        embed_description += f"> **{target_team}** was moved back **{abs(final_move_amount)}** tiles to the **{destination_tile_name}** tile (Tile **{new_pos}**) (stops at Go){maul_suffix}.\n"
                        embed_description += glider_note
                        
                        await self.check_and_award_card_on_land(target_team, new_pos, "being hit by Dragon Spear to")
                        await self.auto_post_show_drops_if_boss_tile(target_team, new_pos)
                        
                        if victim_channel:
                            victim_embed = discord.Embed(
                                title="<:dragon_spear:1558986141846347776> You Were Hit by Dragon Spear!",
                                description=(
                                    f"**{team_name}** used **Dragon Spear** on your team.\n"
                                    f"You were moved back **{abs(final_move_amount)}** tiles to the **{self.get_tile_name_for_display(new_pos)}** tile (Tile **{new_pos}**) (stops at Go){maul_suffix}."
                                    + glider_note_victim
                                ),
                                color=discord.Color.dark_red()
                            )
                            await victim_channel.send(embed=victim_embed)
                            await self.mirror_to_game_log(victim_channel, embed=victim_embed)
            
            elif card_name == "Varrock Tele":
                # Check Teleblock
                if await asyncio.to_thread(self.get_teleblock_status, team_name) == "yes":
                    await interaction.followup.send("<:teleblock:1558985901831364710> You are Teleblocked! You cannot use this card.", ephemeral=True)
                    return 

                all_teams_data = await asyncio.to_thread(self.team_data_sheet.get_all_records)
                caster_pos = -1
                for record in all_teams_data:
                    if record.get("Team") == team_name:
                        caster_pos = int(record.get("Position", -1))
                        break
                
                if caster_pos == 10:
                    await interaction.followup.send("❌ You cannot use **Varrock Tele** while on tile 10 (Nex/Gauntlet).", ephemeral=True)
                    return 

                new_pos = self.resolve_nonroll_landing_tile(BANK_STANDING_TILE)
                await asyncio.to_thread(self.log_command, team_name, "/card_effect_set_tile", {"team": team_name, "tile": new_pos})
                
                embed_description = "> Teleported to **Bank Standing** (Tile 20)."

                await self.check_and_award_card_on_land(team_name, new_pos, "teleporting to via Varrock Tele")
                await self.auto_post_show_drops_if_boss_tile(team_name, new_pos)

            elif card_name == "POH Voucher":
                all_teams_data = await asyncio.to_thread(self.team_data_sheet.get_all_records)
                house_data = await asyncio.to_thread(self.house_data_sheet.get_all_records)
                
                team_info = next((r for r in all_teams_data if r.get("Team") == team_name), None)
                if not team_info:
                    await interaction.followup.send("❌ Could not find your team's position.", ephemeral=True)
                    return 

                caster_pos = int(team_info.get("Position", -1))

                target_tile_data = next((h for h in house_data if int(h.get("Tile", -1)) == caster_pos), None)

                if not target_tile_data:
                    await interaction.followup.send("❌ This tile is not a valid tile for housing.", ephemeral=True)
                    return

                current_owner = str(target_tile_data.get("OwnerTeam", "")).strip()
                try:
                    current_house_count = int(target_tile_data.get("HouseCount", 0) or 0)
                except ValueError:
                    current_house_count = 0

                if current_owner and current_owner != team_name:
                    await interaction.followup.send(
                        f"❌ **Action Denied:** Tile {caster_pos} is already owned by **{current_owner}**. "
                        "You cannot use a POH Voucher on another team's property!",
                        ephemeral=True
                    )
                    return

                if current_owner == team_name and current_house_count >= 4:
                    await interaction.followup.send(
                        f"❌ **Action Denied:** Tile {caster_pos} already has the maximum of 4 houses! "
                        "Save your POH Voucher for another property.",
                        ephemeral=True
                    )
                    return

                house_placed_successfully = await asyncio.to_thread(self.place_house, team_name, caster_pos, True)
                
                if house_placed_successfully:
                    await asyncio.to_thread(self.log_command, team_name, "/card_effect_place_house_free", {"team": team_name, "tile": caster_pos})
                    embed_description = f"> <:houseicon:1438085020156821555> Placed a **free house** on tile **{caster_pos}**!"
                else:
                    await interaction.followup.send("❌ A database error occurred while trying to place the house. Your card was not consumed.", ephemeral=True)
                    return

            elif card_name == "Home Tele":
                if self.get_teleblock_status(team_name) == "yes":
                    await interaction.followup.send("<:teleblock:1558985901831364710> You are Teleblocked! You cannot use this card.", ephemeral=True)
                    return 

                all_teams_data = await asyncio.to_thread(self.team_data_sheet.get_all_records)
                caster_pos = -1
                team_row_idx = -1
                for idx, record in enumerate(all_teams_data, start=2):
                    if record.get("Team") == team_name:
                        caster_pos = int(record.get("Position", -1))
                        team_row_idx = idx
                        break

                if caster_pos == 10:
                    await interaction.followup.send("❌ You cannot use **Home Tele** while on tile 10 (Nex/Gauntlet).", ephemeral=True)
                    return  

                houses = self.get_houses()
                closest_house_pos = -1
                min_distance = float('inf')
                passed_go_on_tele = False

                for house in houses:
                    house_tile = int(house.get("tile", 0))
                    
                    distance = (house_tile - caster_pos) % BOARD_SIZE
                    
                    if 0 < distance < min_distance:
                        min_distance = distance
                        closest_house_pos = house_tile

                if closest_house_pos != -1 and closest_house_pos < caster_pos:
                    passed_go_on_tele = True

                if closest_house_pos == -1:
                    await interaction.followup.send("❌ Card effect failed: No other house tiles exist on the board.", ephemeral=True)
                    return

                intended_pos = closest_house_pos
                new_pos = self.resolve_nonroll_landing_tile(intended_pos)

                # --- 💰 PASS GO CHECK ---
                go_msg = ""
                if passed_go_on_tele and new_pos != 30:
                    go_msg = await self.process_manual_pass_go(team_name, team_row_idx, all_teams_data[team_row_idx-2])

                destination_tile_name = self.get_tile_name_for_display(new_pos)
                embed_description = f"> Teleported to the **{destination_tile_name}** tile (Tile **{new_pos}**).{go_msg}"
                await loop.run_in_executor(None, self.log_command, team_name, "/card_effect_set_tile", {"team": team_name, "tile": new_pos})
                await self.check_and_award_card_on_land(team_name, new_pos, "teleporting to")
                await self.auto_post_show_drops_if_boss_tile(team_name, new_pos)
                
            elif card_name == "Tele Other":
                all_teams_data = self.team_data_sheet.get_all_records()
                caster_pos = -1
                caster_row = -1
                valid_opponents = []

                headers = list(all_teams_data[0].keys())
                pos_col = headers.index("Position") + 1

                for idx, record in enumerate(all_teams_data, start=2):
                    current_team_name = record.get("Team")
                    if current_team_name == team_name:
                        caster_pos = int(record.get("Position", -1))
                        caster_row = idx
                        break
                
                if caster_pos == 10:
                    await interaction.followup.send("❌ You cannot use **Tele Other** while on tile 10 (Nex/Gauntlet).", ephemeral=True)
                    return 

                if caster_pos == -1:
                    await interaction.followup.send("❌ Could not find your team's position.", ephemeral=True)
                    return

                for idx, record in enumerate(all_teams_data, start=2):
                    opponent_team_name = record.get("Team")
                    if opponent_team_name == team_name or not opponent_team_name:
                        continue
                    
                    opponent_pos = int(record.get("Position", -1))
                    
                    dist = abs(opponent_pos - caster_pos)
                    shortest_dist = min(dist, BOARD_SIZE - dist)
                    
                    if 1 <= shortest_dist <= 10:
                        valid_opponents.append({
                            "team": opponent_team_name, 
                            "pos": opponent_pos, 
                            "row": idx
                        })
                
                if not valid_opponents:
                    await interaction.followup.send("❌ Card effect failed: No opponents are within 10 tiles of you.", ephemeral=True)
                    return 

                chosen_target = random.choice(valid_opponents)
                target_team = chosen_target["team"]
                target_pos = chosen_target["pos"]
                target_row = chosen_target["row"]
                
                victim_channel = self.get_team_channel(target_team)
                embed_description = ""

                # --- <:defence:1559009393884925952> PASSIVE CHECKS ---
                victim_info = next((r for r in all_teams_data if r.get("Team") == target_team), {})
                has_stone = str(victim_info.get("Ring of Stone", "no")).strip().lower() == "yes"

                if self.check_and_consume_vengeance(target_team):
                    embed_description += f"> <:venge:1558986464409297077> **{target_team}** had Vengeance active! The teleport fizzled, and both cards were consumed."
                    if victim_channel:
                        victim_embed = discord.Embed(title="<:venge:1558986464409297077> Vengeance Activated!", description=f"**{team_name}** tried to use **Tele Other** on your team, but your **Vengeance** caused the teleport to fizzle.", color=discord.Color.dark_red())
                        await victim_channel.send(embed=victim_embed)
                        await self.mirror_to_game_log(victim_channel, embed=victim_embed)
                
                elif self.check_and_consume_redemption(target_team):
                    embed_description += f"> <:redemption:1558985458195898389> **{target_team}**'s Redemption activated! The teleport was cancelled."
                    if victim_channel:
                        fizzle_embed = discord.Embed(title="<:redemption:1558985458195898389> Redemption Activated!", description=f"**{team_name}** tried to use **Tele Other** on you, but your **Redemption** activated!", color=discord.Color.blue())
                        await victim_channel.send(embed=fizzle_embed)
                        await self.mirror_to_game_log(victim_channel, embed=fizzle_embed)
                
                elif has_stone:
                    await self.consume_ring_of_stone(target_team)
                    embed_description += f"> <:ring_of_stone:1558985677134241873> **{target_team}** was wearing a **Ring of Stone**! They turned into a heavy rock and could not be teleported. The spell failed!"
                    
                    stone_caster_embed = discord.Embed(
                        title="<:ring_of_stone:1558985677134241873> Attack Blocked!", 
                        description=f"You tried to Tele Other **{target_team}**, but they were wearing a **Ring of Stone** and couldn't be teleported!\nYour attack failed and your card was wasted.", 
                        color=discord.Color.red()
                    )
                    await interaction.channel.send(embed=stone_caster_embed)
                    await self.mirror_to_game_log(interaction.channel, embed=stone_caster_embed)

                    if victim_channel:
                        stone_embed = discord.Embed(title="<:ring_of_stone:1558985677134241873> Ring of Stone Activated!", description=f"**{team_name}** tried to use **Tele Other** on you, but your **Ring of Stone** turned you into a rock and prevented you from being moved!", color=discord.Color.blue())
                        await victim_channel.send(embed=stone_embed)
                        await self.mirror_to_game_log(victim_channel, embed=stone_embed)
                
                else:
                    caster_intended_pos = target_pos
                    target_intended_pos = caster_pos
                    caster_final_pos = self.resolve_nonroll_landing_tile(caster_intended_pos)
                    target_final_pos = self.resolve_nonroll_landing_tile(target_intended_pos)
                    caster_glider_note = self.get_glider_redirect_note(caster_intended_pos, caster_final_pos)
                    target_glider_note = self.get_glider_redirect_note(target_intended_pos, target_final_pos)
                    target_glider_note_victim = self.get_glider_redirect_note(target_intended_pos, target_final_pos, second_person=True, quoted=False)
                    caster_dest_name = self.get_tile_name_for_display(caster_final_pos)
                    target_dest_name = self.get_tile_name_for_display(target_final_pos)
                    embed_description += (
                        f"> Swapped places with **{target_team}**. "
                        f"You moved to the **{caster_dest_name}** tile (Tile **{caster_final_pos}**), "
                        f"and they moved to the **{target_dest_name}** tile (Tile **{target_final_pos}**)."
                    )
                    embed_description += caster_glider_note
                    if target_glider_note:
                        embed_description += target_glider_note.replace(" was launched", f" {target_team} was launched")
                    
                    await loop.run_in_executor(None, self.log_command, team_name, "/card_effect_set_tile", {"team": team_name, "tile": caster_final_pos})
                    await loop.run_in_executor(None, self.log_command, team_name, "/card_effect_set_tile", {"team": target_team, "tile": target_final_pos})

                    if victim_channel:
                        swap_embed = discord.Embed(title="<:teleother:1558985957561213000> You've Been Swapped!", description=(f"**{team_name}** used **Tele Other** and swapped places with your team!\nYour team is now on the **{target_dest_name}** tile (Tile **{target_final_pos}**)." + target_glider_note_victim), color=discord.Color.orange())
                        await victim_channel.send(embed=swap_embed)
                        await self.mirror_to_game_log(victim_channel, embed=swap_embed)

                    await self.check_and_award_card_on_land(team_name, caster_final_pos, "being teleported to")
                    await self.check_and_award_card_on_land(target_team, target_final_pos, "being teleported to")
                    await self.auto_post_show_drops_if_boss_tile(team_name, caster_final_pos)
                    await self.auto_post_show_drops_if_boss_tile(target_team, target_final_pos)

            else:
                embed_description = f"> {final_card_text}"
            
            if not is_status_activation:
                if team_wildcard_value is not None:
                    wildcard_data.pop(team_name, None) 
                    await asyncio.to_thread(card_sheet.update_cell, card_row, 4, json.dumps(wildcard_data))
                    print(f"✅ Cleared wildcard for {team_name} from card {selected_card['name']}")
                
                cell_obj = await asyncio.to_thread(card_sheet.cell, card_row, 3)
                cell_val = str(cell_obj.value or "")
                
                teams = [t.strip() for t in cell_val.split(',') if t.strip()]
                if team_name in teams:
                    teams.remove(team_name)
                
                await asyncio.to_thread(card_sheet.update_cell, card_row, 3, ", ".join(teams))
                
                embed = discord.Embed(
                    title=f"{card_emoji} {team_name} used {card_name}!",
                    description=embed_description,
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=False)
                await self.mirror_to_game_log(interaction.channel, embed=embed)

            if is_status_activation:
                embed = discord.Embed(
                    title=f"{card_emoji} {team_name} activated {card_name}!",
                    description=f"{embed_description}{double_card_note}",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=False)

            await asyncio.to_thread(self.set_used_card_flag, team_name, "yes")
        
        except Exception as e:
            print(f"❌ Error in /use_card: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ An error occurred while using the card: {e}", ephemeral=True)
    
    async def execute_targeted_card_effect(self, interaction: discord.Interaction, team_name: str, target_team: str, card_name: str, action: str, extra_data: dict):        
        embed_description = ""
        victim_channel = self.get_team_channel(target_team)
        card_emoji = CARD_EMOJIS.get(card_name, "🃏")
        embed_color = discord.Color.blue()
        double_card_note = extra_data.get("double_card_note", "")
        
        loop = asyncio.get_event_loop()

        if action == "tele_block":
            embed_color = discord.Color.dark_purple()
            if await asyncio.to_thread(self.check_and_consume_redemption, target_team):
                embed_description += f"> <:redemption:1558985458195898389> **{target_team}**'s Redemption activated! The effect fizzled."
                if victim_channel:
                    fizzle_embed = discord.Embed(title="<:redemption:1558985458195898389> Redemption Activated!", description=f"**{team_name}** tried to use **Tele Block** on you, but your **Redemption** activated!", color=discord.Color.blue())
                    await victim_channel.send(embed=fizzle_embed)
                    await self.mirror_to_game_log(victim_channel, embed=fizzle_embed)

            elif await asyncio.to_thread(self.check_and_consume_vengeance, target_team):
                embed_description += f"> <:venge:1558986464409297077> **{target_team}** had Vengeance! The effect rebounded, and your team is now **Teleblocked**."
                await asyncio.to_thread(self.set_teleblock_status, team_name, "yes") 
                skull_embed = discord.Embed(title="<:venge:1558986464409297077> Vengeance Activated!", description=f"You activated **{target_team}**'s Vengeance!\nYour team is now **Teleblocked**!", color=discord.Color.dark_red())
                await interaction.channel.send(embed=skull_embed)
                await self.mirror_to_game_log(interaction.channel, embed=skull_embed) 
                if victim_channel:
                    victim_embed = discord.Embed(title="<:venge:1558986464409297077> Vengeance Activated!", description=f"**{team_name}** tried to use **Tele Block** on your team, but your **Vengeance** rebounded the effect and **Teleblocked** them instead!", color=discord.Color.dark_red())
                    await victim_channel.send(embed=victim_embed)
                    await self.mirror_to_game_log(victim_channel, embed=victim_embed)

            else:
                embed_description += f"> <:teleblock:1558985901831364710> **{target_team}** is now **Teleblocked** until after their next roll."
                await asyncio.to_thread(self.set_teleblock_status, target_team, "yes") 
                if victim_channel:
                    tb_embed = discord.Embed(title="<:teleblock:1558985901831364710> You are Teleblocked!", description=f"**{team_name}** used **Tele Block** on your team! You cannot use teleport cards until after your next roll.", color=discord.Color.dark_purple())
                    await victim_channel.send(embed=tb_embed)
                    await self.mirror_to_game_log(victim_channel, embed=tb_embed)

        elif action == "rogues_gloves":
            embed_color = discord.Color.dark_gray()
            victim_team = target_team
            stealable_cards = extra_data.get("stealable_cards", [])
            target_cards = [c for c in stealable_cards if c["victim_team"] == victim_team]
            
            if not target_cards:
                embed_description = f"<:roguegloves:1558986623486660648> **{team_name}** tried to pick **{victim_team}**'s pocket, but they have no removable items left!"
                if victim_channel:
                    fail_embed = discord.Embed(
                        title="<:roguegloves:1558986623486660648> Rogue's Gloves Failed",
                        description=f"**{team_name}** tried to steal from you, but you have no cards left to take!",
                        color=discord.Color.blue()
                    )
                    await victim_channel.send(embed=fail_embed)
                    await self.mirror_to_game_log(victim_channel, embed=fail_embed)
                return

            # --- <:defence:1559009393884925952> PASSIVE CHECKS ---
            team_records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            victim_info = next((r for r in team_records if r.get("Team") == victim_team), {})
            has_protect = str(victim_info.get("Protect Item", "no")).strip().lower() == "yes"
            has_recoil = str(victim_info.get("Ring of Recoil", "no")).strip().lower() == "yes"

            if has_protect:
                await self.consume_protect_item(victim_team)
                embed_description = f"<:roguegloves:1558986623486660648> **{team_name}** tried to use **Rogue's Gloves** on **{victim_team}**...\n\n<:protect_item:1559003530050670632> But **{victim_team}**'s Protect Item prayer activated! The steal was blocked."
                
                protect_caster_embed = discord.Embed(
                    title="<:protect_item:1559003530050670632> Attack Blocked!", 
                    description=f"You tried to use Rogue's Gloves on **{victim_team}**, but their **Protect Item** prayer was active!\nYour attack failed and your card was wasted.", 
                    color=discord.Color.red()
                )
                await interaction.channel.send(embed=protect_caster_embed)
                await self.mirror_to_game_log(interaction.channel, embed=protect_caster_embed)

                if victim_channel:
                    protect_embed = discord.Embed(
                        title="<:protect_item:1559003530050670632> Protect Item Activated!",
                        description=f"**{team_name}** tried to use **Rogue's Gloves** on you, but your **Protect Item** prayer saved your card!",
                        color=discord.Color.blue()
                    )
                    await victim_channel.send(embed=protect_embed)
                    await self.mirror_to_game_log(victim_channel, embed=protect_embed)

            elif await asyncio.to_thread(self.check_and_consume_redemption, victim_team):
                embed_description = f"<:roguegloves:1558986623486660648> **{team_name}** tried to use **Rogue's Gloves** on **{victim_team}**...\n\n<:redemption:1558985458195898389> But **{victim_team}**'s Redemption activated!"
                if victim_channel:
                    fizzle_embed = discord.Embed(
                        title="<:redemption:1558985458195898389> Redemption Activated!",
                        description=f"**{team_name}** tried to use **Rogue's Gloves** on you, but your **Redemption** activated!",
                        color=discord.Color.blue()
                    )
                    await victim_channel.send(embed=fizzle_embed)
                    await self.mirror_to_game_log(victim_channel, embed=fizzle_embed)

            elif await asyncio.to_thread(self.check_and_consume_vengeance, victim_team):
                embed_description = f"<:roguegloves:1558986623486660648> **{team_name}** tried to use **Rogue's Gloves** on **{victim_team}**...\n\n<:venge:1558986464409297077> **{victim_team}** had Vengeance! The effect was rebounded!\n"

                caster_chest_cards = self.get_held_cards(self.chest_sheet, team_name)
                caster_chance_cards = self.get_held_cards(self.chance_sheet, team_name)

                caster_cards_with_sheet = []
                for c in caster_chest_cards:
                    caster_cards_with_sheet.append({"sheet": self.chest_sheet, "row_index": c["row_index"], "card_name": c["name"], "card_type": "Chest"})
                for c in caster_chance_cards:
                    caster_cards_with_sheet.append({"sheet": self.chance_sheet, "row_index": c["row_index"], "card_name": c["name"], "card_type": "Chance"})

                card_sheet = extra_data.get("card_sheet")
                card_row = extra_data.get("card_row")

                other_caster_cards = [
                    c for c in caster_cards_with_sheet
                    if not (c["sheet"] == card_sheet and c["row_index"] == card_row)
                ]

                stolen_from_caster_name = None

                if other_caster_cards:
                    rebounded_card = random.choice(other_caster_cards)
                    rebound_sheet = rebounded_card["sheet"]
                    rebound_row = rebounded_card["row_index"]
                    stolen_from_caster_name = rebounded_card["card_name"]

                    held_by_str_rebound = str(rebound_sheet.cell(rebound_row, 3).value or "")
                    teams_rebound = [t.strip() for t in held_by_str_rebound.split(',') if t.strip()]
                    if team_name in teams_rebound: teams_rebound.remove(team_name)
                    if victim_team not in teams_rebound: teams_rebound.append(victim_team)
                    rebound_sheet.update_cell(rebound_row, 3, ", ".join(teams_rebound))

                    wildcard_str_rebound = str(rebound_sheet.cell(rebound_row, 4).value or "{}")
                    try:
                        wildcard_data_json_rebound = json.loads(wildcard_str_rebound)
                        caster_wildcard = wildcard_data_json_rebound.pop(team_name, None)
                        if caster_wildcard is not None: wildcard_data_json_rebound[victim_team] = caster_wildcard
                        rebound_sheet.update_cell(rebound_row, 4, json.dumps(wildcard_data_json_rebound))
                    except: pass

                    embed_description += f"<:roguegloves:1558986623486660648> The steal rebounded! **{victim_team}** stole **{stolen_from_caster_name}** from **{team_name}** instead."

                else:
                    stolen_from_caster_name = "Rogue's Gloves"

                    held_by_str_rg = str(card_sheet.cell(card_row, 3).value or "")
                    teams_rg = [t.strip() for t in held_by_str_rg.split(',') if t.strip()]
                    if team_name in teams_rg: teams_rg.remove(team_name)
                    if victim_team not in teams_rg: teams_rg.append(victim_team)
                    card_sheet.update_cell(card_row, 3, ", ".join(teams_rg))

                    wildcard_str_rg = str(card_sheet.cell(card_row, 4).value or "{}")
                    try:
                        wildcard_data_json_rg = json.loads(wildcard_str_rg)
                        caster_wildcard = wildcard_data_json_rg.pop(team_name, None)
                        if caster_wildcard is not None: wildcard_data_json_rg[victim_team] = caster_wildcard
                        card_sheet.update_cell(card_row, 4, json.dumps(wildcard_data_json_rg))
                    except: pass

                    embed_description += f"<:roguegloves:1558986623486660648> The steal rebounded! **{victim_team}** stole the **Rogue's Gloves** card from **{team_name}**!"

                skull_embed = discord.Embed(title="<:venge:1558986464409297077> Vengeance Activated!", description=f"You activated **{victim_team}**'s Vengeance!\nThey stole your **{stolen_from_caster_name}** card!", color=discord.Color.dark_red())
                await interaction.channel.send(embed=skull_embed)
                await self.mirror_to_game_log(interaction.channel, embed=skull_embed)

                if victim_channel:
                    victim_embed = discord.Embed(title="<:venge:1558986464409297077> Vengeance Activated!", description=f"**{team_name}** tried to use **Rogue's Gloves** on you, but your **Vengeance** rebounded the effect!\nYou stole **{stolen_from_caster_name}** from their team.", color=discord.Color.dark_red())
                    await victim_channel.send(embed=victim_embed)
                    await self.mirror_to_game_log(victim_channel, embed=victim_embed)
                
            elif has_recoil:
                caster_chest = self.get_held_cards(self.chest_sheet, team_name)
                caster_chance = self.get_held_cards(self.chance_sheet, team_name)
                all_caster = [c for c in (caster_chest + caster_chance) if "(ACTIVE)" not in c['text']]
                
                card_sheet = extra_data.get("card_sheet")
                card_row = extra_data.get("card_row")
                
                other_caster_cards = [
                    c for c in all_caster
                    if not ( (c in caster_chest and card_sheet == self.chest_sheet and c["row_index"] == card_row) or 
                             (c in caster_chance and card_sheet == self.chance_sheet and c["row_index"] == card_row) )
                ]
                
                if not other_caster_cards:
                    embed_description += f"> <:recoil:1558985588055609374> **{victim_team}** has a **Ring of Recoil**! The Steal failed because **{team_name}** has no other cards to lose to the recoil."
                    if victim_channel:
                        fail_embed = discord.Embed(title="<:defence:1559009393884925952> Attack Failed!", description=f"**{team_name}** tried to steal from you, but the attack failed due to a lack of cards for the **Ring of Recoil** penalty.", color=discord.Color.blue())
                        await victim_channel.send(embed=fail_embed)
                        await self.mirror_to_game_log(victim_channel, embed=fail_embed)
                else:
                    await self.consume_recoil(victim_team)
                    
                    stolen_from_caster = random.choice(other_caster_cards)
                    c_sheet = self.chest_sheet if stolen_from_caster in caster_chest else self.chance_sheet
                    c_row = stolen_from_caster["row_index"]
                    
                    c_holders = str(c_sheet.cell(c_row, 3).value or "").split(",")
                    c_holders = [h.strip() for h in c_holders if h.strip() and h.strip() != team_name]
                    c_holders.append(victim_team)
                    c_sheet.update_cell(c_row, 3, ", ".join(c_holders))

                    try:
                        c_wild_str = str(c_sheet.cell(c_row, 4).value or "{}")
                        c_wild_data = json.loads(c_wild_str)
                        cw = c_wild_data.pop(team_name, None)
                        if cw is not None: c_wild_data[victim_team] = cw
                        c_sheet.update_cell(c_row, 4, json.dumps(c_wild_data))
                    except: pass

                    embed_description += f"> <:recoil:1558985588055609374> **Recoil Triggered!** **{team_name}** tried to steal, but the ring blocked it and forced them to give up a card! **{victim_team}** got **{stolen_from_caster['name']}**!"
                    
                    recoil_caster_embed = discord.Embed(
                        title="<:recoil:1558985588055609374> Recoil Activated!", 
                        description=f"You attacked a team wearing a **Ring of Recoil**!\nYour steal was blocked, and the recoil forced you to give them a card!\n\n🔴 You lost **{stolen_from_caster['name']}**.", 
                        color=discord.Color.dark_red()
                    )
                    await interaction.channel.send(embed=recoil_caster_embed)
                    await self.mirror_to_game_log(interaction.channel, embed=recoil_caster_embed)

                    if victim_channel:
                        victim_embed = discord.Embed(
                            title="<:recoil:1558985588055609374> Recoil Shattered!", 
                            description=f"**{team_name}** tried to use **Rogue's Gloves** on you, but your **Ring of Recoil** triggered! It blocked the steal and forced them to surrender a card!\n\n🟢 You received **{stolen_from_caster['name']}**.", 
                            color=discord.Color.green()
                        )
                        await victim_channel.send(embed=victim_embed)
                        await self.mirror_to_game_log(victim_channel, embed=victim_embed)

            else:
                stolen_card = random.choice(target_cards)
                target_sheet = stolen_card["sheet"]
                target_row = stolen_card["row_index"]

                held_by_str = str(target_sheet.cell(target_row, 3).value or "")
                teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                if victim_team in teams: teams.remove(victim_team)
                if team_name not in teams: teams.append(team_name)
                target_sheet.update_cell(target_row, 3, ", ".join(teams))

                wildcard_str = str(target_sheet.cell(target_row, 4).value or "{}")
                try:
                    wildcard_data_json = json.loads(wildcard_str)
                    victim_wildcard = wildcard_data_json.pop(victim_team, None)
                    if victim_wildcard is not None: wildcard_data_json[team_name] = victim_wildcard
                    target_sheet.update_cell(target_row, 4, json.dumps(wildcard_data_json))
                except: pass

                embed_description = f"<:roguegloves:1558986623486660648> **{team_name}** used **Rogue's Gloves** and stole **{stolen_card['card_name']}** from **{victim_team}**!"
                
                if victim_channel:
                    victim_embed = discord.Embed(
                        title="‼️ Card Stolen!",
                        description=f"**{team_name}** used **Rogue's Gloves** and stole your **{stolen_card['card_name']}** card!",
                        color=discord.Color.dark_red()
                    )
                    await victim_channel.send(embed=victim_embed)
                    await self.mirror_to_game_log(victim_channel, embed=victim_embed)

        elif action == "pickpocket":
            embed_color = discord.Color.dark_gold()
            all_teams_data = extra_data.get("all_teams_data")
            caster_record = extra_data.get("caster_record")
            target_record = next((r for r in all_teams_data if r.get("Team") == target_team), None)
            
            highest_gp = int(str(target_record.get("GP", 0)).replace(",", "") or 0)
            caster_gp = int(str(caster_record.get("GP", 0)).replace(",", ""))
            
            embed_description = f"**{team_name}** targeted **{target_team}** with **Pickpocket**!\n"
            headers = list(all_teams_data[0].keys())
            gp_col_idx = headers.index("GP") + 1
            target_row_idx = all_teams_data.index(target_record) + 2
            caster_row_idx = all_teams_data.index(caster_record) + 2

            # --- <:defence:1559009393884925952> PASSIVE CHECKS ---
            has_protect = str(target_record.get("Protect Item", "no")).strip().lower() == "yes"
            has_recoil = str(target_record.get("Ring of Recoil", "no")).strip().lower() == "yes"

            if has_protect:
                await self.consume_protect_item(target_team)
                embed_description += f"> <:protect_item:1559003530050670632> **{target_team}**'s Protect Item prayer activated! The Pickpocket was blocked."
                
                protect_caster_embed = discord.Embed(
                    title="<:protect_item:1559003530050670632> Attack Blocked!", 
                    description=f"You tried to Pickpocket **{target_team}**, but their **Protect Item** prayer was active!\nYour attack failed and your card was wasted.", 
                    color=discord.Color.red()
                )
                await interaction.channel.send(embed=protect_caster_embed)
                await self.mirror_to_game_log(interaction.channel, embed=protect_caster_embed)

                if victim_channel:
                    protect_embed = discord.Embed(
                        title="<:protect_item:1559003530050670632> Protect Item Activated!", 
                        description=f"**{team_name}** tried to use **Pickpocket** on you, but your **Protect Item** prayer saved your GP!", 
                        color=discord.Color.blue()
                    )
                    await victim_channel.send(embed=protect_embed)
                    await self.mirror_to_game_log(victim_channel, embed=protect_embed)

            elif await asyncio.to_thread(self.check_and_consume_redemption, target_team):
                embed_description += f"> <:redemption:1558985458195898389> **{target_team}**'s Redemption activated! The Pickpocket fizzled."
                if victim_channel:
                    fizzle_embed = discord.Embed(title="<:redemption:1558985458195898389> Redemption Activated!", description=f"**{team_name}** tried to use **Pickpocket** on you, but your **Redemption** activated!", color=discord.Color.blue())
                    await victim_channel.send(embed=fizzle_embed)
                    await self.mirror_to_game_log(victim_channel, embed=fizzle_embed)

            elif await asyncio.to_thread(self.check_and_consume_vengeance, target_team):
                base_percent = 0.20
                maul_active = await asyncio.to_thread(self.check_and_consume_elder_maul, team_name)
                maul_note = " (Halved by <:eldermaul:1558986407735861359> **Elder Maul**!)" if maul_active else ""
                
                steal_amount = max(1, int(caster_gp * (0.10 if maul_active else base_percent)))
                new_caster_gp = max(0, caster_gp - steal_amount)
                new_target_gp = highest_gp + steal_amount

                self.team_data_sheet.update_cell(caster_row_idx, gp_col_idx, new_caster_gp)
                self.team_data_sheet.update_cell(target_row_idx, gp_col_idx, new_target_gp)

                embed_description += f"> <:venge:1558986464409297077> **{target_team}** had Vengeance! They stole **{steal_amount:,} GP** from **{team_name}** instead!{maul_note}"

                if victim_channel:
                    victim_embed = discord.Embed(title="<:venge:1558986464409297077> Vengeance Activated!", description=f"**{team_name}** tried to use **Pickpocket** on you, but your **Vengeance** rebounded it! You stole **{steal_amount:,} GP** from them!{maul_note}", color=discord.Color.green())
                    await victim_channel.send(embed=victim_embed)
                    await self.mirror_to_game_log(victim_channel, embed=victim_embed)

            elif has_recoil:
                base_percent = 0.20
                maul_active = await asyncio.to_thread(self.check_and_consume_elder_maul, target_team)
                maul_note = " (Halved by <:eldermaul:1558986407735861359> **Elder Maul**!)" if maul_active else ""
                
                steal_amount = max(1, int(highest_gp * (0.10 if maul_active else base_percent)))
                
                if caster_gp < steal_amount:
                    embed_description += f"> <:recoil:1558985588055609374> **{target_team}** has a **Ring of Recoil**! The Pickpocket failed because **{team_name}** did not have enough GP to afford the recoil damage."
                    if victim_channel:
                        fail_embed = discord.Embed(title="<:defence:1559009393884925952> Attack Failed!", description=f"**{team_name}** tried to Pickpocket you, but couldn't survive your **Ring of Recoil**!", color=discord.Color.blue())
                        await victim_channel.send(embed=fail_embed)
                        await self.mirror_to_game_log(victim_channel, embed=fail_embed)
                else:
                    await self.consume_recoil(target_team)
                    new_target_gp = max(0, highest_gp - steal_amount)
                    new_caster_gp = max(0, caster_gp - steal_amount)

                    self.team_data_sheet.update_cell(target_row_idx, gp_col_idx, new_target_gp)
                    self.team_data_sheet.update_cell(caster_row_idx, gp_col_idx, new_caster_gp)

                    embed_description += f"> <:recoil:1558985588055609374> **Recoil Triggered!** Both **{team_name}** and **{target_team}** lost **{steal_amount:,} GP**!{maul_note}"

                    recoil_caster_embed = discord.Embed(
                        title="<:recoil:1558985588055609374> Recoil Activated!", 
                        description=f"You attacked a team wearing a **Ring of Recoil**!\nBoth your team and **{target_team}** lost **{steal_amount:,} GP**!{maul_note}", 
                        color=discord.Color.dark_red()
                    )
                    await interaction.channel.send(embed=recoil_caster_embed)
                    await self.mirror_to_game_log(interaction.channel, embed=recoil_caster_embed)

                    if victim_channel:
                        victim_embed = discord.Embed(title="<:recoil:1558985588055609374> Recoil Activated!", description=f"**{team_name}** tried to use **Pickpocket** on you, but your **Ring of Recoil** triggered! Both teams lost **{steal_amount:,} GP**!{maul_note}", color=discord.Color.green())
                        await victim_channel.send(embed=victim_embed)
                        await self.mirror_to_game_log(victim_channel, embed=victim_embed)

            else:
                base_percent = 0.20
                maul_active = await asyncio.to_thread(self.check_and_consume_elder_maul, target_team)
                maul_note = " (Halved by <:eldermaul:1558986407735861359> **Elder Maul**!)" if maul_active else ""
                
                steal_amount = max(1, int(highest_gp * (0.10 if maul_active else base_percent)))
                new_target_gp = max(0, highest_gp - steal_amount)
                new_caster_gp = caster_gp + steal_amount

                self.team_data_sheet.update_cell(target_row_idx, gp_col_idx, new_target_gp)
                self.team_data_sheet.update_cell(caster_row_idx, gp_col_idx, new_caster_gp)

                embed_description += f"> Stole **{steal_amount:,} GP** from **{target_team}**!{maul_note}"

                if victim_channel:
                    maul_msg = "\n\n<:defence:1559009393884925952> Your **Elder Maul** activated and halved the losses!" if maul_active else ""
                    victim_embed = discord.Embed(
                        title="<:pickpocket:1558986509242212412> Pickpocketed!",
                        description=f"**{team_name}** used **Pickpocket** and stole **{steal_amount:,} GP** from your team.{maul_msg}",
                        color=discord.Color.dark_red() if not maul_active else discord.Color.blue()
                    )
                    await victim_channel.send(embed=victim_embed)
                    await self.mirror_to_game_log(victim_channel, embed=victim_embed)

        elif action == "smite":
            embed_color = discord.Color.red()
            victim_team = target_team
            victim_chest_cards = self.get_held_cards(self.chest_sheet, victim_team)
            victim_chance_cards = self.get_held_cards(self.chance_sheet, victim_team)
            all_victim_cards = victim_chest_cards + victim_chance_cards
            
            non_active_cards = [card for card in all_victim_cards if "(ACTIVE)" not in card['text']]

            if not non_active_cards:
                embed_description = f"<:smite:1558986008404697199> **{team_name}** tried to Smite **{victim_team}**, but they have no removable cards left!"
                if victim_channel:
                    fail_embed = discord.Embed(
                        title="<:defence:1559009393884925952> Smite Failed!",
                        description=f"**{team_name}** tried to Smite you, but you have no cards to lose!",
                        color=discord.Color.blue()
                    )
                    await victim_channel.send(embed=fail_embed)
                    await self.mirror_to_game_log(victim_channel, embed=fail_embed)
                return  

            # --- <:defence:1559009393884925952> PASSIVE CHECKS ---
            team_records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            victim_info = next((r for r in team_records if r.get("Team") == victim_team), {})
            has_protect = str(victim_info.get("Protect Item", "no")).strip().lower() == "yes"
            has_recoil = str(victim_info.get("Ring of Recoil", "no")).strip().lower() == "yes"

            if has_protect:
                await self.consume_protect_item(victim_team)
                embed_description += f"> <:protect_item:1559003530050670632> **{victim_team}**'s Protect Item prayer activated! The Smite was blocked."
                
                protect_caster_embed = discord.Embed(
                    title="<:protect_item:1559003530050670632> Attack Blocked!", 
                    description=f"You tried to Smite **{victim_team}**, but their **Protect Item** prayer was active!\nYour attack failed and your card was wasted.", 
                    color=discord.Color.red()
                )
                await interaction.channel.send(embed=protect_caster_embed)
                await self.mirror_to_game_log(interaction.channel, embed=protect_caster_embed)

                if victim_channel:
                    protect_embed = discord.Embed(
                        title="<:protect_item:1559003530050670632> Protect Item Activated!", 
                        description=f"**{team_name}** tried to use **Smite** on you, but your **Protect Item** prayer saved your inventory!", 
                        color=discord.Color.blue()
                    )
                    await victim_channel.send(embed=protect_embed)
                    await self.mirror_to_game_log(victim_channel, embed=protect_embed)

            elif await asyncio.to_thread(self.check_and_consume_redemption, victim_team):
                embed_description += f"> <:redemption:1558985458195898389> **{victim_team}**'s Redemption activated!"
                if victim_channel:
                    fizzle_embed = discord.Embed(title="<:redemption:1558985458195898389> Redemption Activated!", description=f"**{team_name}** tried to use **Smite** on you, but your **Redemption** activated!", color=discord.Color.blue())
                    await victim_channel.send(embed=fizzle_embed)
                    await self.mirror_to_game_log(victim_channel, embed=fizzle_embed)
            
            elif await asyncio.to_thread(self.check_and_consume_vengeance, victim_team):
                embed_description += f"> <:venge:1558986464409297077> **{victim_team}** had Vengeance! The effect rebounded.\n> "
                
                caster_chest_cards = self.get_held_cards(self.chest_sheet, team_name)
                caster_chance_cards = self.get_held_cards(self.chance_sheet, team_name)
                all_caster_cards = caster_chest_cards + caster_chance_cards
                non_active_caster_cards = [card for card in all_caster_cards if "(ACTIVE)" not in card['text']]
                
                if not non_active_caster_cards:
                    embed_description += f"**{team_name}** had no cards to lose."
                    if victim_channel:
                        victim_embed = discord.Embed(
                            title="<:venge:1558986464409297077> Vengeance Activated!",
                            description=f"**{team_name}** tried to use **Smite** on your team, but your **Vengeance** rebounded the effect!\nThey had no removable cards to lose.",
                            color=discord.Color.dark_red()
                        )
                        await victim_channel.send(embed=victim_embed)
                        await self.mirror_to_game_log(victim_channel, embed=victim_embed)
                else:
                    card_to_remove = random.choice(non_active_caster_cards)
                    remove_sheet = self.chest_sheet if card_to_remove in caster_chest_cards else self.chance_sheet
                    remove_row = card_to_remove['row_index']
                    
                    wildcard_str = str(remove_sheet.cell(remove_row, 4).value or "{}")
                    try:
                        wildcard_data = json.loads(wildcard_str)
                        wildcard_data.pop(team_name, None)
                        remove_sheet.update_cell(remove_row, 4, json.dumps(wildcard_data))
                    except: pass
                        
                    held_by_str = str(remove_sheet.cell(remove_row, 3).value or "")
                    teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                    if team_name in teams: teams.remove(team_name)
                    remove_sheet.update_cell(remove_row, 3, ", ".join(teams))
                    
                    embed_description += f"**{team_name}** lost their **{card_to_remove['name']}** card."
                    
                    skull_embed = discord.Embed(title="<:venge:1558986464409297077> Vengeance Activated!", description=f"You activated **{victim_team}**'s Vengeance!\nYou lost your **{card_to_remove['name']}** card!", color=discord.Color.dark_red())
                    await interaction.channel.send(embed=skull_embed)
                    await self.mirror_to_game_log(interaction.channel, embed=skull_embed)
                    
                    if victim_channel:
                        victim_embed = discord.Embed(
                            title="<:venge:1558986464409297077> Vengeance Activated!",
                            description=f"**{team_name}** tried to use **Smite** on your team, but your **Vengeance** rebounded the effect!\nThey lost their **{card_to_remove['name']}** card.",
                            color=discord.Color.dark_red()
                        )
                        await victim_channel.send(embed=victim_embed)
                        await self.mirror_to_game_log(victim_channel, embed=victim_embed)

            elif has_recoil:
                caster_chest = self.get_held_cards(self.chest_sheet, team_name)
                caster_chance = self.get_held_cards(self.chance_sheet, team_name)
                all_caster = [c for c in (caster_chest + caster_chance) if "(ACTIVE)" not in c['text']]
                
                card_sheet = extra_data.get("card_sheet")
                card_row = extra_data.get("card_row")

                other_caster_cards = [
                    c for c in all_caster
                    if not ( (c in caster_chest and card_sheet == self.chest_sheet and c["row_index"] == card_row) or 
                             (c in caster_chance and card_sheet == self.chance_sheet and c["row_index"] == card_row) )
                ]
                
                if not other_caster_cards or not non_active_cards:
                    embed_description += f"> <:recoil:1558985588055609374> **{victim_team}** has a **Ring of Recoil**! The Smite failed because one team has no removable cards for the recoil destruction."
                    if victim_channel:
                        fail_embed = discord.Embed(title="<:defence:1559009393884925952> Attack Failed!", description=f"**{team_name}** tried to Smite you, but the attack failed due to a lack of cards for the **Ring of Recoil** swap.", color=discord.Color.blue())
                        await victim_channel.send(embed=fail_embed)
                        await self.mirror_to_game_log(victim_channel, embed=fail_embed)
                else:
                    await self.consume_recoil(victim_team)
                    
                    target_card = random.choice(non_active_cards)
                    t_sheet = self.chest_sheet if target_card in victim_chest_cards else self.chance_sheet
                    t_row = target_card['row_index']
                    
                    w_str = str(t_sheet.cell(t_row, 4).value or "{}")
                    try:
                        w_data = json.loads(w_str)
                        w_data.pop(victim_team, None)
                        t_sheet.update_cell(t_row, 4, json.dumps(w_data))
                    except: pass
                    
                    h_str = str(t_sheet.cell(t_row, 3).value or "")
                    t_teams = [t.strip() for t in h_str.split(',') if t.strip()]
                    if victim_team in t_teams: t_teams.remove(victim_team)
                    t_sheet.update_cell(t_row, 3, ", ".join(t_teams))
                    
                    caster_card = random.choice(other_caster_cards)
                    c_sheet = self.chest_sheet if caster_card in caster_chest else self.chance_sheet
                    c_row = caster_card['row_index']
                    
                    cw_str = str(c_sheet.cell(c_row, 4).value or "{}")
                    try:
                        cw_data = json.loads(cw_str)
                        cw_data.pop(team_name, None)
                        c_sheet.update_cell(c_row, 4, json.dumps(cw_data))
                    except: pass
                    
                    ch_str = str(c_sheet.cell(c_row, 3).value or "")
                    c_teams = [t.strip() for t in ch_str.split(',') if t.strip()]
                    if team_name in c_teams: c_teams.remove(team_name)
                    c_sheet.update_cell(c_row, 3, ", ".join(c_teams))

                    embed_description += f"> <:recoil:1558985588055609374> **Recoil Triggered!** Both **{team_name}** and **{victim_team}** lost a card! (**{caster_card['name']}** and **{target_card['name']}**)"
                    
                    recoil_caster_embed = discord.Embed(
                        title="<:recoil:1558985588055609374> Recoil Activated!", 
                        description=f"You attacked a team wearing a **Ring of Recoil**!\nBoth your team and **{victim_team}** lost a card!\n\n🔴 You lost **{caster_card['name']}**.\n🟢 They lost **{target_card['name']}**.", 
                        color=discord.Color.dark_red()
                    )
                    await interaction.channel.send(embed=recoil_caster_embed)
                    await self.mirror_to_game_log(interaction.channel, embed=recoil_caster_embed)

                    if victim_channel:
                        victim_embed = discord.Embed(
                            title="<:recoil:1558985588055609374> Recoil Shattered!", 
                            description=f"**{team_name}** tried to use **Smite** on you, but your **Ring of Recoil** triggered! Both teams lost a card!\n\n🔴 You lost **{target_card['name']}**.\n🟢 They lost **{caster_card['name']}**.", 
                            color=discord.Color.green()
                        )
                        await victim_channel.send(embed=victim_embed)
                        await self.mirror_to_game_log(victim_channel, embed=victim_embed)

            else:
                card_to_remove = random.choice(non_active_cards)
                remove_sheet = self.chest_sheet if card_to_remove in victim_chest_cards else self.chance_sheet
                remove_row = card_to_remove['row_index']

                wildcard_str = str(remove_sheet.cell(remove_row, 4).value or "{}")
                try:
                    wildcard_data = json.loads(wildcard_str)
                    wildcard_data.pop(victim_team, None)
                    remove_sheet.update_cell(remove_row, 4, json.dumps(wildcard_data))
                except: pass
                    
                held_by_str = str(remove_sheet.cell(remove_row, 3).value or "")
                teams = [t.strip() for t in held_by_str.split(',') if t.strip()]
                if victim_team in teams: teams.remove(victim_team)
                remove_sheet.update_cell(remove_row, 3, ", ".join(teams))

                embed_description += f"> **{victim_team}** lost their **{card_to_remove['name']}** card."
                
                if victim_channel:
                    victim_embed = discord.Embed(title="‼️ Card Lost!", description=f"**{team_name}** used **Smite**! Your team lost your **{card_to_remove['name']}** card!", color=discord.Color.dark_red())
                    await victim_channel.send(embed=victim_embed)
                    await self.mirror_to_game_log(victim_channel, embed=victim_embed)
                        
        card_sheet = extra_data.get("card_sheet")
        card_row = extra_data.get("card_row")
        wildcard_data = extra_data.get("wildcard_data", {})
        team_wildcard_value = extra_data.get("team_wildcard_value")

        try:
            if team_wildcard_value is not None:
                wildcard_data.pop(team_name, None) 
                await asyncio.to_thread(card_sheet.update_cell, card_row, 4, json.dumps(wildcard_data))
                print(f"✅ Cleared wildcard for {team_name} from card {card_name}")
            
            cell_obj = await asyncio.to_thread(card_sheet.cell, card_row, 3)
            cell_val = str(cell_obj.value or "")
            
            teams = [t.strip() for t in cell_val.split(',') if t.strip()]
            if team_name in teams:
                teams.remove(team_name)
            
            await asyncio.to_thread(card_sheet.update_cell, card_row, 3, ", ".join(teams))
        except Exception as e:
            print(f"❌ Error updating inventory for targeted card: {e}")

        await asyncio.to_thread(self.set_used_card_flag, team_name, "yes")

        final_embed = discord.Embed(
            title=f"{card_emoji} {team_name} used {card_name}!",
            description=f"{embed_description}{double_card_note}",
            color=embed_color
        )
        await interaction.channel.send(embed=final_embed)
        await self.mirror_to_game_log(interaction.channel, embed=final_embed)

    async def trigger_passive_random_event(self, channel: discord.TextChannel, team_name: str, forced_event: str = None, current_pos: int = None):
        """Silently handles a random event if the 5% spawn chance is met, or forces one if requested."""
        try:
            records = await asyncio.to_thread(self.team_data_sheet.get_all_records)
            
            team_info = next((r for r in records if str(r.get("Team", "")).strip().lower() == team_name.strip().lower()), None)
            if not team_info: return None, None

            chosen_team = str(team_info.get("Team")).strip()
            team_row_idx = records.index(team_info) + 2
            
            headers = list(records[0].keys())
            gp_col = headers.index("GP") + 1 if "GP" in headers else -1
            pos_col = headers.index("Position") + 1 if "Position" in headers else -1
            current_gp = int(str(team_info.get("GP", 0)).replace(',', ''))
            
            if current_pos is None:
                current_pos = int(team_info.get("Position", 0))

            event_final_pos = current_pos

            embed_desc = ""
            event_title = ""
            
            nerf_pool = ["dwarf", "whirlpool", "ents", "gravedigger", "sandwich", "jekyll", "demon", "plant", "beekeeper", "mime", "maze", "pete", "bob", "twin"]
            buff_pool = ["certers", "arnav", "oldman", "frog", "countcheck", "exam", "genie", "postie", "pinball", "sandwich_good", "turpentine", "quiz"]

            if forced_event:
                if forced_event in nerf_pool:
                    event_type = "nerf"
                    chosen_nerf = forced_event
                elif forced_event in buff_pool:
                    event_type = "buff"
                    chosen_buff = forced_event
                else:
                    print(f"❌ Invalid forced event: {forced_event}")
                    return None, None
            else:
                try:
                    victim_mult = float(team_info.get("Multiplier", 1))
                except ValueError:
                    victim_mult = 1.0

                nerf_chance = max(5.0, min(95.0, 50.0 + ((victim_mult - 3.0) * 5.0)))
                buff_chance = 100.0 - nerf_chance
                
                event_type = random.choices(["nerf", "buff"], weights=[nerf_chance, buff_chance], k=1)[0]
                
                if event_type == "nerf":
                    chosen_nerf = random.choice(nerf_pool)
                else:
                    chosen_buff = random.choice(buff_pool)

            embed_color = discord.Color.red() if event_type == "nerf" else discord.Color.green()

            # ==========================================
            # 🔴 NERF MECHANICS
            # ==========================================
            if event_type == "nerf":
                event_title = "😈 A Disastrous Random Event Appears!"
                if chosen_nerf == "dwarf":
                    has_protect = str(team_info.get("Protect Item", "no")).strip().lower() == "yes"
                    if has_protect:
                        await self.consume_protect_item(chosen_team)
                        embed_desc = f"<:drunken_dwarf:1558999600323629116> **The Drunken Dwarf!**\n*\"Have a kebab, mate!\"* The dwarf tries to force **{chosen_team}** to pay his massive bar tab, but their <:protect_item:1559003530050670632> **Protect Item** prayer activates! The prayer is drained, but their GP is perfectly safe!"
                    else:
                        fine = int(current_gp * 0.20)
                        await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, current_gp - fine)
                        embed_desc = f"<:drunken_dwarf:1558999600323629116> **The Drunken Dwarf!**\n*\"Have a kebab, mate!\"* The dwarf corners **{chosen_team}** and forces them to pay his massive bar tab! They lose **20%** of their total wealth (**{fine:,} GP**)!"
                
                elif chosen_nerf == "ents":
                    col = headers.index("GP Halved") + 1 if "GP Halved" in headers else -1
                    if col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                    embed_desc = f"<:ent:1558999589317640262> **The Ents!**\nAn ent grows and shakes **{chosen_team}** upside down! **All GP earned is cut in half** until their next roll!"

                elif chosen_nerf == "gravedigger":
                    col = headers.index("Roll Penalty") + 1
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                    embed_desc = f"<:leo:1558999609601294346> **Leo the Gravedigger!**\n*\"Give me a hand with these coffins!\"* **{chosen_team}** is exhausted from digging graves! Their next dice roll is reduced by **3**!"
                
                elif chosen_nerf == "plant":
                    col = headers.index("Poisoned Roll") + 1
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                    embed_desc = f"<:strange_plant:1558995237098094602> **The Strange Plant!**\n*It lashes out with poisonous vines!* **{chosen_team}** has been poisoned! Their next dice roll cannot exceed **3**!"
                
                elif chosen_nerf == "twin":
                    has_protect = str(team_info.get("Protect Item", "no")).strip().lower() == "yes"
                    if has_protect:
                        await self.consume_protect_item(chosen_team)
                        embed_desc = f"<:molly:1558999622100320347> **The Evil Twin!**\nMolly's evil twin attempts to confiscate a card from **{chosen_team}**, but their <:protect_item:1559003530050670632> **Protect Item** prayer activates! The prayer is drained, keeping their inventory safe!"
                    else:
                        all_chance = await asyncio.to_thread(self.chance_sheet.get_all_records)
                        all_chest = await asyncio.to_thread(self.chest_sheet.get_all_records)
                        held_cards = []
                        for sheet, records in [(self.chance_sheet, all_chance), (self.chest_sheet, all_chest)]:
                            for r in records:
                                if chosen_team in [t.strip() for t in str(r.get("Held By Team", "")).split(",")]:
                                    held_cards.append({"sheet": sheet, "row": records.index(r) + 2, "data": r})
                        
                        if held_cards:
                            stolen_card = random.choice(held_cards)
                            current_holders = [t.strip() for t in str(stolen_card["data"].get("Held By Team", "")).split(",") if t.strip()]
                            current_holders.remove(chosen_team)
                            await asyncio.to_thread(stolen_card["sheet"].update_cell, stolen_card["row"], 3, ", ".join(current_holders))
                            embed_desc = f"<:molly:1558999622100320347> **The Evil Twin!**\n*\"Gotcha!\"* Molly's evil twin corners **{chosen_team}** and confiscates their **{stolen_card['data'].get('Name')}** card!"
                        else:
                            embed_desc = f"<:molly:1558999622100320347> **The Evil Twin!**\nMolly's evil twin tries to steal from **{chosen_team}**, but she was caught!"
                
                elif chosen_nerf == "whirlpool":
                    spaces_back = random.randint(2, 4)
                    new_pos = max(0, current_pos - spaces_back)
                    if hasattr(self, "resolve_nonroll_landing_tile"): new_pos = self.resolve_nonroll_landing_tile(new_pos)
                    event_final_pos = new_pos
                    if pos_col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, pos_col, new_pos)
                    if new_pos == 0: await asyncio.to_thread(self.increment_rolls_available, chosen_team)
                    await asyncio.to_thread(self.log_command, chosen_team, "/card_effect_set_tile", {"team": chosen_team, "tile": new_pos})
                    embed_desc = f"<:whirlpool:1558998111253299323> **The Whirlpool!**\nA sudden whirlpool sucks **{chosen_team}** under! They wash up **{spaces_back}** spaces backwards on Tile **{new_pos}**!"
                    if new_pos == 0: embed_desc += "\n\n🎯 **BULLSEYE!** Washing up perfectly on GO grants a **Free Roll**!"

                elif chosen_nerf == "sandwich":
                    spaces_back = random.randint(1, 6)
                    new_pos = max(0, current_pos - spaces_back)
                    event_final_pos = new_pos
                    if pos_col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, pos_col, new_pos)
                    if new_pos == 0: await asyncio.to_thread(self.increment_rolls_available, chosen_team)
                    await asyncio.to_thread(self.log_command, chosen_team, "/card_effect_set_tile", {"team": chosen_team, "tile": new_pos})
                    embed_desc = f"<:sandwich_lady:1558999634096037898> **The Sandwich Lady!**\n*\"You picked the wrong sandwich!\"* She whacks **{chosen_team}** with a stale baguette! They are knocked **{spaces_back}** tiles backwards to Tile **{new_pos}**!"
                    if new_pos == 0: embed_desc += "\n\n🎯 **BULLSEYE!** Landing perfectly on GO via baguette whack grants a **Free Roll**!"

                elif chosen_nerf == "demon":
                    col = headers.index("Roll Halved") + 1 if "Roll Halved" in headers else -1
                    if col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                    embed_desc = f"<:sergeant_damien:1558999790556028998> **The Demon Drill Sergeant!**\n*\"Drop and give me 50!\"* The Demon exhausts **{chosen_team}**. Their next dice roll is strictly **cut in half**!"

                elif chosen_nerf == "beekeeper":
                    new_pos = max(0, current_pos - 2)
                    if hasattr(self, "resolve_nonroll_landing_tile"): new_pos = self.resolve_nonroll_landing_tile(new_pos)
                    event_final_pos = new_pos
                    if pos_col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, pos_col, new_pos)
                    if new_pos == 0: await asyncio.to_thread(self.increment_rolls_available, chosen_team)
                    await asyncio.to_thread(self.log_command, chosen_team, "/card_effect_set_tile", {"team": chosen_team, "tile": new_pos})
                    embed_desc = f"<:bee_keeper:1559000442241814578> **The Beekeeper!**\n**{chosen_team}** failed to build the hive and got swarmed! They panic and flee backwards **2 tiles** to Tile **{new_pos}**!"
                    if new_pos == 0: embed_desc += "\n\n🎯 **BULLSEYE!** Fleeing perfectly onto GO grants a **Free Roll**!"

                elif chosen_nerf == "maze":
                    spaces_back = random.randint(1, 3)
                    new_pos = max(0, current_pos - spaces_back)
                    if hasattr(self, "resolve_nonroll_landing_tile"): new_pos = self.resolve_nonroll_landing_tile(new_pos)
                    event_final_pos = new_pos
                    if pos_col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, pos_col, new_pos)
                    if new_pos == 0: await asyncio.to_thread(self.increment_rolls_available, chosen_team)
                    await asyncio.to_thread(self.log_command, chosen_team, "/card_effect_set_tile", {"team": chosen_team, "tile": new_pos})
                    embed_desc = f"<:mysterious_old_man:1559000625746944080> **The Mysterious Old Man's Maze!**\n**{chosen_team}** is dragged into the maze and completely loses their sense of direction! They eventually stumble out **{spaces_back}** spaces backwards, ending up on Tile **{new_pos}**!"
                    if new_pos == 0: embed_desc += "\n\n🎯 **BULLSEYE!** Stumbling perfectly onto GO grants a **Free Roll**!"

                elif chosen_nerf == "pete":
                    new_pos = 10
                    event_final_pos = new_pos
                    if pos_col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, pos_col, new_pos)
                    if new_pos == 0: await asyncio.to_thread(self.increment_rolls_available, chosen_team)
                    await asyncio.to_thread(self.log_command, chosen_team, "/card_effect_set_tile", {"team": chosen_team, "tile": new_pos})
                    if hasattr(self, "set_jail_status"): await asyncio.to_thread(self.set_jail_status, chosen_team, "yes")
                    embed_desc = f"<:prison_pete:1559000820144541746> **Prison Pete!**\n**{chosen_team}** traps the player in a cage! They are instantly dragged to **Tile 10 (Jail)**!"
                
                elif chosen_nerf == "bob":
                    if hasattr(self, "set_teleblock_status"): await asyncio.to_thread(self.set_teleblock_status, chosen_team, "yes")
                    embed_desc = f"<:evil_bob:1559001028098138112> **Evil Bob!**\n**{chosen_team}** is kidnapped to ScapeRune to catch fish! They are **Teleblocked** until their next roll!"

                elif chosen_nerf == "jekyll":
                    try:
                        all_props = await asyncio.to_thread(self.house_data_sheet.get_all_records)
                        team_houses = [p for p in all_props if str(p.get("OwnerTeam", "")).strip().lower() == chosen_team.lower() and int(p.get("HouseCount", 0) or 0) > 0]
                        if team_houses:
                            target_prop = random.choice(team_houses)
                            prop_idx = all_props.index(target_prop) + 2
                            houses_col = list(all_props[0].keys()).index("HouseCount") + 1
                            current_houses = int(target_prop.get("HouseCount", 0))
                            tile_id = target_prop.get("Tile", "one of your properties")
                            
                            await asyncio.to_thread(self.house_data_sheet.update_cell, prop_idx, houses_col, current_houses - 1)
                            await asyncio.to_thread(self.sync_houses_owned, chosen_team)
                            embed_desc = f"<:dr_jekyll:1559001246222786560> **Dr. Jekyll & Mr. Hyde!**\n*\"You won't spare a single Guam leaf?!\"* **{chosen_team}** refuses to help Dr. Jekyll. Enraged, he drinks a strange potion and violently transforms into Mr. Hyde! He goes on a rampage and completely destroys a house on Tile **{tile_id}**!"
                        else:
                            embed_desc = f"<:dr_jekyll:1559001246222786560> **Dr. Jekyll & Mr. Hyde!**\n*\"You won't spare a single Guam leaf?!\"* **{chosen_team}** refuses to help Dr. Jekyll. He transforms into Mr. Hyde and goes on a rampage! Fortunately, **{chosen_team}** doesn't own any houses for him to destroy, so he just yells at a cloud and leaves!"
                    except Exception as e:
                        print(f"❌ Error during Jekyll house destruction: {e}")
                        embed_desc = f"<:dr_jekyll:1559001246222786560> **Dr. Jekyll & Mr. Hyde!**\nDr. Jekyll transformed, but got confused and wandered off..."
                
                elif chosen_nerf == "mime":
                    col = headers.index("Silenced") + 1 if "Silenced" in headers else -1
                    if col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                    embed_desc = f"<:mime:1559001543557251212> **The Mime!**\n**{chosen_team}** failed to copy the Mime's emotes! A silencing aura is cast over them. They are **unable to use ANY cards** until they roll the dice again!"

            # ==========================================
            # 🟢 BUFF MECHANICS
            # ==========================================
            else:
                event_title = "😇 A Blessing Appears!"
                chosen_buff = random.choice(buff_pool)
                
                has_protect = str(team_info.get("Protect Item", "no")).strip().lower() == "yes"
                has_recoil = str(team_info.get("Ring of Recoil", "no")).strip().lower() == "yes"
                has_phoenix = str(team_info.get("Phoenix Necklace", "no")).strip().lower() == "yes"
                has_charos = str(team_info.get("Ring of Charos", "no")).strip().lower() == "yes"
                has_stone = str(team_info.get("Ring of Stone", "no")).strip().lower() == "yes"
            
                has_any_passive = has_protect or has_recoil or has_phoenix or has_charos or has_stone

                if chosen_buff == "certers":
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, current_gp + 20_000_000)
                    embed_desc = f"<:miles:1559002337811365889> **The Certers!**\nNiles, Miles, and Giles unnote some rare items for **{chosen_team}**! They have been granted a massive injection of **20,000,000 GP**!"

                elif chosen_buff == "postie":
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, current_gp + 10_000_000)
                    embed_desc = f"<:postie_pete:1559001685475725392> **Postie Pete!**\n*\"Special delivery!\"* Pete hands **{chosen_team}** a parcel filled with inheritance! They receive **10,000,000 GP**!"

                elif chosen_buff == "pinball":
                    col = headers.index("GP Doubled") + 1 if "GP Doubled" in headers else -1
                    if col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                    embed_desc = f"<:flippa:1559002523422163024> **The Pinball Troll!**\n**{chosen_team}** successfully tags the pillars! The troll rewards them with a multiplier. Their next approved drop will be worth **DOUBLE GP**!"

                elif chosen_buff == "sandwich_good":
                    col = headers.index("Roll Bonus") + 1 if "Roll Bonus" in headers else -1
                    if col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                    embed_desc = f"<:sandwich_lady:1558999634096037898> **The Sandwich Lady!**\n*\"Have a snack, dear!\"* **{chosen_team}** picks the correct sandwich and feels energized! They are granted a **+3 Bonus** to their next dice roll!"

                elif chosen_buff == "turpentine":
                    all_chance = await asyncio.to_thread(self.chance_sheet.get_all_records)
                    all_chest = await asyncio.to_thread(self.chest_sheet.get_all_records)
                    stealable = []
                    for sheet, records in [(self.chance_sheet, all_chance), (self.chest_sheet, all_chest)]:
                        for r in records:
                            holders = [t.strip() for t in str(r.get("Held By Team", "")).split(",") if t.strip()]
                            valid_victims = [h for h in holders if h.lower() != chosen_team.lower()]
                            if valid_victims:
                                for v in valid_victims:
                                    stealable.append({"sheet": sheet, "row": records.index(r) + 2, "victim": v, "card_name": str(r.get("Name", "")), "holders": holders})
                                    
                    if stealable:
                        stolen = random.choice(stealable)
                        holders = stolen["holders"]
                        holders.remove(stolen["victim"])
                        holders.append(chosen_team)
                        await asyncio.to_thread(stolen["sheet"].update_cell, stolen["row"], 3, ", ".join(holders))
                        embed_desc = f"<:rick_turpentine:1559002837818806413> **Rick Turpentine!**\n*\"Stand and deliver!\"* Rick ambushes another team and hands the loot to you! **{chosen_team}** has stolen the **{stolen['card_name']}** card from **{stolen['victim']}**!"
                    else:
                        await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, current_gp + 10_000_000)
                        embed_desc = f"<:rick_turpentine:1559002837818806413> **Rick Turpentine!**\n*\"Stand and deliver!\"* Rick tried to steal from the other teams, but they were completely broke! He feels bad and gives **{chosen_team}** **10,000,000 GP** out of his own pocket!"

                elif chosen_buff == "quiz":
                    reward = random.choice(["roll", "gp", "card"])
                    if reward == "roll":
                        await asyncio.to_thread(self.increment_rolls_available, chosen_team)
                        embed_desc = f"<:quiz_master:1559002953724076052> **The Quiz Master!**\n**{chosen_team}** answered the odd-one-out correctly! The Quiz Master awards them a **Free Dice Roll**!"
                    
                    elif reward == "gp":
                        await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, current_gp + 15_000_000)
                        embed_desc = f"<:quiz_master:1559002953724076052> **The Quiz Master!**\n**{chosen_team}** answered the odd-one-out correctly! The Quiz Master awards them **15,000,000 GP**!"
                    
                    else:  
                        all_chance = await asyncio.to_thread(self.chance_sheet.get_all_records)
                        available_cards = [
                            {"type": "physical", "data": r, "index": all_chance.index(r) + 2} 
                            for r in all_chance if chosen_team not in [t.strip() for t in str(r.get("Held By Team", "")).split(",")]
                        ]
                        
                        if not has_any_passive:
                            available_cards.append({"type": "virtual", "data": {"Name": "Protect Item"}})
                            available_cards.append({"type": "virtual", "data": {"Name": "Ring of Recoil"}})
                            available_cards.append({"type": "virtual", "data": {"Name": "Phoenix Necklace"}})
                            available_cards.append({"type": "virtual", "data": {"Name": "Ring of Charos"}})
                            available_cards.append({"type": "virtual", "data": {"Name": "Ring of Stone"}})
                            
                        if available_cards:
                            drawn_card = random.choice(available_cards)
                            drawn_card_name = str(drawn_card["data"].get('Name', '')).strip()
                            display_name = "Protect Item Scroll" if drawn_card_name == "Protect Item" else ("Ring of Charos (a)" if drawn_card_name == "Ring of Charos" else drawn_card_name)
                            
                            embed_desc = f"<:quiz_master:1559002953724076052> **The Quiz Master!**\n**{chosen_team}** answered the odd-one-out correctly! The Quiz Master awards them a free **{display_name}**!"
                            
                            if drawn_card["type"] == "virtual":
                                col = headers.index(drawn_card_name) + 1 if drawn_card_name in headers else -1
                                if col != -1:
                                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                                    if drawn_card_name == "Protect Item":
                                        embed_desc += f"\n\n<:protect_item:1559003530050670632> The **Protect Item Scroll** is now **ACTIVE** in your inventory!"
                                    elif drawn_card_name == "Ring of Recoil":
                                        embed_desc += f"\n\n<:recoil:1558985588055609374> The **Ring of Recoil** is now **ACTIVE** in your inventory!"
                                    elif drawn_card_name == "Phoenix Necklace":
                                        embed_desc += f"\n\n<:pneck:1558990483110367242> The **Phoenix Necklace** is now **ACTIVE** in your inventory!"
                                    elif drawn_card_name == "Ring of Charos":
                                        embed_desc += f"\n\n<:charos:1558985798483837049> The **Ring of Charos (a)** is now **ACTIVE** in your inventory!"
                                    elif drawn_card_name == "Ring of Stone":
                                        embed_desc += f"\n\n<:ring_of_stone:1558985677134241873> The **Ring of Stone** is now **ACTIVE** in your inventory!"
                            else:
                                card_idx = drawn_card["index"]
                                current_holders = [t.strip() for t in str(drawn_card["data"].get("Held By Team", "")).split(",") if t.strip()]
                                current_holders.append(chosen_team)
                                await asyncio.to_thread(self.chance_sheet.update_cell, card_idx, 3, ", ".join(current_holders))
                        else:
                            await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, current_gp + 15_000_000)
                            embed_desc = f"<:quiz_master:1559002953724076052> **The Quiz Master!**\n**{chosen_team}** answered correctly, but already holds every Chance card! He awards **15,000,000 GP** instead!"

                elif chosen_buff == "arnav":
                    all_chest = await asyncio.to_thread(self.chest_sheet.get_all_records)
                    available_cards = [
                        {"type": "physical", "data": r, "index": all_chest.index(r) + 2} 
                        for r in all_chest if chosen_team not in [t.strip() for t in str(r.get("Held By Team", "")).split(",")]
                    ]
                    
                    if not has_any_passive:
                        available_cards.append({"type": "virtual", "data": {"Name": "Protect Item"}})
                        available_cards.append({"type": "virtual", "data": {"Name": "Ring of Recoil"}})
                        available_cards.append({"type": "virtual", "data": {"Name": "Phoenix Necklace"}})
                        available_cards.append({"type": "virtual", "data": {"Name": "Ring of Charos"}})
                        available_cards.append({"type": "virtual", "data": {"Name": "Ring of Stone"}})
                        
                    if available_cards:
                        drawn_card = random.choice(available_cards)
                        drawn_card_name = str(drawn_card["data"].get('Name', '')).strip()
                        display_name = "Protect Item Scroll" if drawn_card_name == "Protect Item" else ("Ring of Charos (a)" if drawn_card_name == "Ring of Charos" else drawn_card_name)

                        embed_desc = f"🏴‍☠️ **Capt' Arnav's Chest!**\n**{chosen_team}** successfully cracked the combination! They have been granted a free **{display_name}**!"
                        
                        if drawn_card["type"] == "virtual":
                            col = headers.index(drawn_card_name) + 1 if drawn_card_name in headers else -1
                            if col != -1:
                                await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                                if drawn_card_name == "Protect Item":
                                    embed_desc += f"\n\n<:protect_item:1559003530050670632> The **Protect Item Scroll** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Ring of Recoil":
                                    embed_desc += f"\n\n<:recoil:1558985588055609374> The **Ring of Recoil** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Phoenix Necklace":
                                    embed_desc += f"\n\n<:pneck:1558990483110367242> The **Phoenix Necklace** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Ring of Charos":
                                    embed_desc += f"\n\n<:charos:1558985798483837049> The **Ring of Charos (a)** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Ring of Stone":
                                    embed_desc += f"\n\n<:ring_of_stone:1558985677134241873> The **Ring of Stone** is now **ACTIVE** in your inventory!"
                        else:
                            card_idx = drawn_card["index"]
                            current_holders = [t.strip() for t in str(drawn_card["data"].get("Held By Team", "")).split(",") if t.strip()]
                            current_holders.append(chosen_team)
                            await asyncio.to_thread(self.chest_sheet.update_cell, card_idx, 3, ", ".join(current_holders))
                    else:
                        await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, current_gp + 10_000_000)
                        embed_desc = f"🏴‍☠️ **Capt' Arnav's Chest!**\n**{chosen_team}** opened the chest but already has all the cards! They found **10,000,000 GP** instead!"
                
                elif chosen_buff == "oldman":
                    all_chance = await asyncio.to_thread(self.chance_sheet.get_all_records)
                    available_cards = [
                        {"type": "physical", "data": r, "index": all_chance.index(r) + 2} 
                        for r in all_chance if chosen_team not in [t.strip() for t in str(r.get("Held By Team", "")).split(",")]
                    ]
                    
                    if not has_any_passive:
                        available_cards.append({"type": "virtual", "data": {"Name": "Protect Item"}})
                        available_cards.append({"type": "virtual", "data": {"Name": "Ring of Recoil"}})
                        available_cards.append({"type": "virtual", "data": {"Name": "Phoenix Necklace"}})
                        available_cards.append({"type": "virtual", "data": {"Name": "Ring of Charos"}})
                        available_cards.append({"type": "virtual", "data": {"Name": "Ring of Stone"}})
                        
                    if available_cards:
                        drawn_card = random.choice(available_cards)
                        drawn_card_name = str(drawn_card["data"].get('Name', '')).strip()
                        display_name = "Protect Item Scroll" if drawn_card_name == "Protect Item" else ("Ring of Charos (a)" if drawn_card_name == "Ring of Charos" else drawn_card_name)

                        embed_desc = f"<:mystery_box:1559004276175536128> **The Mysterious Old Man!**\n**{chosen_team}** was given a Strange Box! They have been granted a free **{display_name}**!"
                        
                        if drawn_card["type"] == "virtual":
                            col = headers.index(drawn_card_name) + 1 if drawn_card_name in headers else -1
                            if col != -1:
                                await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                                if drawn_card_name == "Protect Item":
                                    embed_desc += f"\n\n<:protect_item:1559003530050670632> The **Protect Item Scroll** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Ring of Recoil":
                                    embed_desc += f"\n\n<:recoil:1558985588055609374> The **Ring of Recoil** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Phoenix Necklace":
                                    embed_desc += f"\n\n<:pneck:1558990483110367242> The **Phoenix Necklace** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Ring of Charos":
                                    embed_desc += f"\n\n<:charos:1558985798483837049> The **Ring of Charos (a)** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Ring of Stone":
                                    embed_desc += f"\n\n<:ring_of_stone:1558985677134241873> The **Ring of Stone** is now **ACTIVE** in your inventory!"
                        else:
                            card_idx = drawn_card["index"]
                            current_holders = [t.strip() for t in str(drawn_card["data"].get("Held By Team", "")).split(",") if t.strip()]
                            current_holders.append(chosen_team)
                            await asyncio.to_thread(self.chance_sheet.update_cell, card_idx, 3, ", ".join(current_holders))
                    else:
                        await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, current_gp + 10_000_000)
                        embed_desc = f"<:mystery_box:1559004276175536128> **The Mysterious Old Man!**\n**{chosen_team}** solved the box but already has all the cards! They found **10,000,000 GP** inside instead!"

                elif chosen_buff == "frog":
                    await asyncio.to_thread(self.increment_rolls_available, chosen_team)
                    embed_desc = f"<:frog:1559005336214573087> **Kiss the Frog!**\n**{chosen_team}** kisses the Royal Frog! The Royal Frog has rewarded them with an immediate **Free Dice Roll**!"

                elif chosen_buff == "countcheck":
                    col = headers.index("Double Card") + 1 if "Double Card" in headers else -1
                    if col != -1: await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                    embed_desc = f"<:count_check:1559005679656763452> **Count Check!**\n**{chosen_team}** sets up their Authenticator and Bank PIN! Their account security grants them the ability to use **TWO cards** on their current tile instead of just one!"

                elif chosen_buff == "exam":
                    all_chance = await asyncio.to_thread(self.chance_sheet.get_all_records)
                    all_chest = await asyncio.to_thread(self.chest_sheet.get_all_records)
                    
                    unowned_cards = [
                        {"type": "physical", "sheet": self.chance_sheet, "row": all_chance.index(r) + 2, "data": r} 
                        for r in all_chance if chosen_team not in [t.strip() for t in str(r.get("Held By Team", "")).split(",")]
                    ] + [
                        {"type": "physical", "sheet": self.chest_sheet, "row": all_chest.index(r) + 2, "data": r} 
                        for r in all_chest if chosen_team not in [t.strip() for t in str(r.get("Held By Team", "")).split(",")]
                    ]
                    
                    if not has_any_passive:
                        unowned_cards.append({"type": "virtual", "data": {"Name": "Protect Item"}})
                        unowned_cards.append({"type": "virtual", "data": {"Name": "Ring of Recoil"}})
                        unowned_cards.append({"type": "virtual", "data": {"Name": "Phoenix Necklace"}})
                        unowned_cards.append({"type": "virtual", "data": {"Name": "Ring of Charos"}})
                        unowned_cards.append({"type": "virtual", "data": {"Name": "Ring of Stone"}})
                    
                    if not unowned_cards:
                        await asyncio.to_thread(self.increment_rolls_available, chosen_team)
                        embed_desc = f"<:dunce:1559005843683278848> **Surprise Exam!**\nMr. Mordaut is stunned—**{chosen_team}** already knows everything! He awards them a **Free Dice Roll** for their perfect score!"
                    else:
                        drawn_card = random.choice(unowned_cards)
                        drawn_card_name = str(drawn_card["data"].get('Name', '')).strip()
                        display_name = "Protect Item Scroll" if drawn_card_name == "Protect Item" else ("Ring of Charos (a)" if drawn_card_name == "Ring of Charos" else drawn_card_name)
                        
                        embed_desc = f"<:dunce:1559005843683278848> **Surprise Exam!**\nMr. Mordaut tests **{chosen_team}**, and they score an A+! They are awarded a free **{display_name}**!"
                        
                        if drawn_card["type"] == "virtual":
                            col = headers.index(drawn_card_name) + 1 if drawn_card_name in headers else -1
                            if col != -1:
                                await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, col, "yes")
                                if drawn_card_name == "Protect Item":
                                    embed_desc += f"\n\n<:protect_item:1559003530050670632> The **Protect Item Scroll** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Ring of Recoil":
                                    embed_desc += f"\n\n<:recoil:1558985588055609374> The **Ring of Recoil** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Phoenix Necklace":
                                    embed_desc += f"\n\n<:pneck:1558990483110367242> The **Phoenix Necklace** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Ring of Charos":
                                    embed_desc += f"\n\n<:charos:1558985798483837049> The **Ring of Charos (a)** is now **ACTIVE** in your inventory!"
                                elif drawn_card_name == "Ring of Stone":
                                    embed_desc += f"\n\n<:ring_of_stone:1558985677134241873> The **Ring of Stone** is now **ACTIVE** in your inventory!"
                        else:
                            current_holders = [t.strip() for t in str(drawn_card["data"].get("Held By Team", "")).split(",") if t.strip()]
                            current_holders.append(chosen_team)
                            await asyncio.to_thread(drawn_card["sheet"].update_cell, drawn_card["row"], 3, ", ".join(current_holders))

                elif chosen_buff == "genie":
                    boost = int(current_gp * 0.15)
                    await asyncio.to_thread(self.team_data_sheet.update_cell, team_row_idx, gp_col, current_gp + boost)
                    embed_desc = f"<:genie:1559006178535546980> **The Genie!**\n*\"A wish granted!\"* The Genie magically multiplies **{chosen_team}**'s wealth, granting them a permanent **15% boost** to their current GP stack (**+{boost:,} GP**)!"
            
            embed = discord.Embed(title=event_title, description=embed_desc, color=embed_color)
            await channel.send(embed=embed)
            await self.mirror_to_game_log(channel, embed=embed)

            event_name = chosen_nerf if event_type == "nerf" else chosen_buff
            return event_name, event_final_pos

        except Exception as e:
            print(f"❌ Error in trigger_passive_random_event: {e}")
            return None, None

    @app_commands.command(name="force_event", description="[Staff] Force a specific random event for testing.")
    @app_commands.describe(team_role="The team to trigger the event for", event_id="The event to test (Start typing to see list)")
    async def force_event(self, interaction: discord.Interaction, team_role: discord.Role, event_id: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only Administrators can use this command.", ephemeral=True)
            return

        team_name = team_role.name
        if team_name not in ACTIVE_TEAMS:
            await interaction.response.send_message(f"❌ Please select a valid Team role. ({team_name} is not active).", ephemeral=True)
            return

        team_chan = self.get_team_channel(team_name)
        if not team_chan:
            await interaction.response.send_message(f"❌ Could not find the text channel for {team_name}.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        try:
            await self.trigger_passive_random_event(team_chan, team_name, forced_event=event_id)
            await interaction.followup.send(f"✅ Successfully forced the `{event_id}` event for **{team_name}** in their channel.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error forcing event: {e}")

    @force_event.autocomplete('event_id')
    async def force_event_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        events = [
            "dwarf", "whirlpool", "ents", "gravedigger", "sandwich", "jekyll", "demon", "plant", 
            "beekeeper", "mime", "maze", "pete", "bob", "twin",
            "certers", "arnav", "oldman", "frog", "countcheck", "exam", "genie", "postie", 
            "pinball", "sandwich_good", "turpentine", "quiz"
        ]
        return [
            app_commands.Choice(name=event, value=event)
            for event in events if current.lower() in event.lower()
        ][:25]

async def setup(bot: commands.Bot):
    await bot.add_cog(MonopolyCog(bot))
