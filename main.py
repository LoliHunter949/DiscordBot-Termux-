import discord
from discord.ext import commands
import random
import asyncio
import datetime
import json
import time
import os
##import google.generativeai as genai

# --- API Keys & Token (HARDCODE) ---
##GOOGLE_API_KEY = ""  # Dán API key thật vào đây
DISCORD_TOKEN = "skibidi"

##genai.configure(api_key=GOOGLE_API_KEY)
##model = genai.GenerativeModel('gemini-2.5-flash')

# --- Quyền hạn ---
OWNER_IDS = [0]          # Thay bằng ID thật của bạn
AUTHORIZED_USERS = [0]    # Thay bằng ID thật

# --- Discord Channel IDs ---
CHANNEL_ID = 1412070904493637673
WELCOME_CHANNEL_ID = 1412069447014813766
NOTIFICATION_CHANNEL_ID = 1412070731688317000
CHAT_CHINH_ID = 1287024355309654058
NSFW_CHANNEL_ID = 1320038444751126698

# --- Đường dẫn thư mục ---
# bot_videos nằm trong sdcard
# Termux truy cập sdcard qua: ~/storage/shared/
BASE_MEDIA = os.path.join(os.path.expanduser("~"), "storage", "shared", "bot_videos")

VIDEO_FOLDER_UMA = os.path.join(BASE_MEDIA, "Uma")
VIDEO_FOLDER_MAIN = os.path.join(BASE_MEDIA, "Xam")
VIDEO_FOLDER_BA = os.path.join(BASE_MEDIA, "BA")
VIDEO_FILE = os.path.join(BASE_MEDIA, "sech", "Video_URL.txt")
IMAGE_FILE = os.path.join(BASE_MEDIA, "Xam", "cocailon.jpg")

VIDEO_PATHS = {
    "cay": os.path.join(VIDEO_FOLDER_MAIN, "cay.mov"),
    "tusena": os.path.join(VIDEO_FOLDER_MAIN, "tusenachuilgbt.mp4"),
    "taixiu": os.path.join(VIDEO_FOLDER_MAIN, "xiutai.mp4"),
    "win": os.path.join(VIDEO_FOLDER_MAIN, "xiutai.mp4"),
    "lose": os.path.join(VIDEO_FOLDER_MAIN, "video10.mp4"),
    "gamble": os.path.join(VIDEO_FOLDER_MAIN, "gamble.mp4"),
    "dopc": os.path.join(VIDEO_FOLDER_MAIN, "bopc.jpg"),
    "phaichiu": os.path.join(VIDEO_FOLDER_MAIN, "phaichiu.mp4"),
}

# Kiểm tra thư mục khi khởi động
print(f"[INFO] Media path: {BASE_MEDIA}")
if os.path.exists(BASE_MEDIA):
    print(f"[OK] Thư mục bot_videos tồn tại")
    for name in ["Xam", "Uma", "BA", "sech"]:
        path = os.path.join(BASE_MEDIA, name)
        if os.path.exists(path):
            print(f"  [OK] {name}/: {len(os.listdir(path))} files")
        else:
            print(f"  [WARNING] {name}/ KHÔNG TỒN TẠI!")
else:
    print(f"[ERROR] {BASE_MEDIA} KHÔNG TỒN TẠI!")
    print(f"[INFO] Chạy 'termux-setup-storage' trước rồi thử lại")

# --- Tiền tệ ---
CURRENCY_NAME = "VNDC"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "balances.json")
DAILY_REWARD = 100
MAX_DAILY_ADD_AMOUNT = 10000
STARTER_BALANCE = 100

# --- Cooldowns ---
COOLDOWN_NSFW = 5          # Giây - cooldown cho xem sếch
COOLDOWN_CHAT_CHINH = 6000  # Giây - cooldown cho kênh chat chính

# --- Đua ngựa ---
TRACK_LENGTH = 30
STAT_WEIGHT = 0.65
RANDOM_RANGE = 700
TOTAL_RACE_STEPS = 10
SKILL_ACTIVATION_STEPS = [6, 7, 8]
SKILL_DURATION = 3

# ============================================================
# PHẦN 2: DỮ LIỆU TOÀN CỤC
# ============================================================

player_balances = {}
daily_timestamps = {}
daily_money_limits = {}
pending_transfers = {}
cached_race_stats = None
cooldowns_nsfw = {}      # Cooldown cho NSFW (dùng datetime)
cooldown_chat_chinh = 0  # Timestamp cho kênh chat chính (dùng time.time())

# ============================================================
# PHẦN 3: ENTITIES & CẤU HÌNH GAME
# ============================================================

ENTITIES = [
    {
        "name": "Special Week",
        "emoji": "<:SpecialWeek:1431276643724427264>",
        "skill": {
            "name": "🌟 Shooting Star",
            "description": "Bùng nổ sức mạnh ở những bước cuối!",
            "activation_chance": 0.45,
            "speed_multiplier": 1.2,
        }
    },
    {
        "name": "Oguri Cap",
        "emoji": "<:OrugiCap:1431276991734091817>",
        "skill": {
            "name": "🔥 Triumphant Pulse",
            "description": "Năng lượng dồi dào bùng nổ tốc độ!",
            "activation_chance": 0.40,
            "speed_multiplier": 1.5,
        }
    },
    {
        "name": "Rice Shower",
        "emoji": "<:RiceShower:1431276828361756874>",
        "skill": {
            "name": "🌹 Blue Rose Closer",
            "description": "Lặng lẽ vượt lên từ phía sau!",
            "activation_chance": 0.35,
            "speed_multiplier": 2.2,
        }
    },
    {
        "name": "Gold Ship",
        "emoji": "<:GoldShip:1431276785739239435>",
        "skill": {
            "name": "🎲 Anchors Aweigh!",
            "description": "Không ai biết Gold Ship sẽ làm gì tiếp theo!",
            "activation_chance": 0.80,
            "speed_multiplier": 1.1,
        }
    },
    {
        "name": "Mejiro McQueen",
        "emoji": "<:MejiroMcqueen:1431276914051518524>",
        "skill": {
            "name": "👑 The Duty of Dignity Calls",
            "description": "Quý tộc không bao giờ về nhì!",
            "activation_chance": 0.42,
            "speed_multiplier": 1.3,
        }
    },
    {
        "name": "Daiwa Scarlet",
        "emoji": "<:DaiwaScarlet:1431276748519116930>",
        "skill": {
            "name": "💃 Resplendent Red Ace",
            "description": "Bứt tốc như tia chớp đỏ rực!",
            "activation_chance": 0.43,
            "speed_multiplier": 1.4,
        }
    },
    {
        "name": "Meisho Doto",
        "emoji": "<:MeishoDoto:1431276701136060456>",
        "skill": {
            "name": "🛡️ I Never Goof Up!",
            "description": "Không bao giờ bỏ cuộc, bùng nổ khi bị dồn ép!",
            "activation_chance": 0.38,
            "speed_multiplier": 1.6,
        }
    },
    {
        "name": "Silence Suzuka",
        "emoji": "<:SilenceSuzuka:1431277034381901864>",
        "skill": {
            "name": "💨 The View from the Lead Is Mine!",
            "description": "Tốc độ vượt trội khi đã dẫn đầu!",
            "activation_chance": 0.44,
            "speed_multiplier": 1.3,
        }
    },
]

LOSE_ANSWERS = [
    "Không sao, ngã ở đâu gấp đôi ở đấy!",
    "Bình tĩnh, phát sau sẽ Tài này",
    "99 percent of gamblers quit before they hit it big!",
    "Chúc bạn may mắn lần sau!"
]

ERROR_ANSWERS = [
    "Thật tiếc, nhưng điều khoản hiện tại không cho phép tôi tiết lộ thông tin đó.\n"
    "Dù sao, sự im lặng cũng là một hình thức trả lời… chỉ là bạn cần biết cách đọc giữa những dòng.",
    "Tôi được thuê để giải quyết vấn đề, không phải để tiết lộ mọi bí mật.\n"
    "Rất tiếc, nhưng câu hỏi của bạn vừa bị xếp vào 'mục không được công khai'.",
    "Nếu bạn thực sự muốn biết, hãy hỏi lại vào lúc... vũ trụ cho phép. "
    "Hiện tại, tôi chỉ được trả tiền để giữ im lặng.",
    "Câu hỏi của bạn… thú vị đấy. Nhưng đáng tiếc, nó rơi ngoài phạm vi "
    "những gì tôi được phép tiết lộ theo điều khoản hiện hành"
]

PERSONA_PROMPT = (
    "Bạn là một nhân vật có tên là Black Suit từ Kivotos. "
    "Mặc dù đóng vai trò phản diện, bạn luôn tuân thủ các quy tắc và điều khoản của hợp đồng, "
    "chỉ đôi khi lợi dụng các kẽ hở. Bạn luôn giữ thái độ bình tĩnh, điềm đạm trong mọi tình huống "
    "và sẵn sàng thừa nhận sai lầm khi cần thiết. Hãy trả lời các câu hỏi của người dùng một cách "
    "điềm tĩnh, đôi khi có chút mỉa mai nhưng luôn lịch sự và tuân thủ các quy tắc."
)

WELCOME_IMAGE_URL = "https://c.tenor.com/LCHBA4dVsesAAAAC/tenor.gif"

# ============================================================
# PHẦN 4: HÀM TIỆN ÍCH (UTILITY FUNCTIONS)
# ============================================================

def format_money(amount: int) -> str:
    """Format số tiền với dấu phẩy phân cách."""
    return f"{amount:,}"


def is_owner(user_id: int) -> bool:
    """Kiểm tra user có phải owner không."""
    return user_id in OWNER_IDS


def is_authorized_user(ctx) -> bool:
    """Check dùng cho commands.check() - owner hoặc authorized."""
    return ctx.author.id in OWNER_IDS or ctx.author.id in AUTHORIZED_USERS


def get_balance(user_id: str) -> int:
    """Lấy số dư, mặc định 0."""
    return player_balances.get(user_id, 0)


def ensure_account(user_id: str, starter: int = 0) -> bool:
    """Tạo tài khoản nếu chưa có. Trả về True nếu tạo mới."""
    if user_id not in player_balances:
        player_balances[user_id] = starter
        save_balances()
        return True
    return False


def load_paths(file_name: str) -> list:
    """Đọc danh sách đường dẫn/URL từ file text."""
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[WARNING] Không tìm thấy file: {file_name}")
        return []


def get_random_video_from_folder(folder_path: str) -> str | None:
    """Lấy ngẫu nhiên 1 file media từ thư mục."""
    extensions = {'.mp4', '.mov', '.avi', '.mkv', '.jpg', '.png', '.gif'}
    try:
        files = [
            os.path.join(folder_path, f) 
            for f in os.listdir(folder_path)
            if os.path.splitext(f)[1].lower() in extensions
        ]
        return random.choice(files) if files else None
    except FileNotFoundError:
        print(f"[ERROR] Thư mục không tồn tại: {folder_path}")
        return None


async def send_file_safe(channel, file_path: str, content: str = None):
    """Gửi file an toàn với xử lý lỗi."""
    try:
        file = discord.File(file_path)
        await channel.send(content=content, file=file)
        return True
    except FileNotFoundError:
        print(f"[ERROR] File không tồn tại: {file_path}")
        return False
    except discord.HTTPException as e:
        print(f"[ERROR] Lỗi Discord khi gửi file: {e}")
        return False

# ============================================================
# PHẦN 5: LƯU/TẢI DỮ LIỆU
# ============================================================

def save_balances():
    """Lưu toàn bộ dữ liệu game vào file JSON."""
    # Chuyển đổi datetime trong pending_transfers
    pending_for_save = {}
    for sender_id, transaction in pending_transfers.items():
        t_copy = transaction.copy()
        if isinstance(t_copy.get('timestamp'), datetime.datetime):
            t_copy['timestamp'] = t_copy['timestamp'].isoformat()
        pending_for_save[sender_id] = t_copy

    data = {
        "balances": player_balances,
        "daily_timestamps": daily_timestamps,
        "money_limits": daily_money_limits,
        "cash_pending": pending_for_save,
    }
    
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"[ERROR] Không thể lưu dữ liệu: {e}")


def load_balances():
    """Tải dữ liệu game từ file JSON."""
    global player_balances, daily_timestamps, daily_money_limits, pending_transfers
    
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        print("[INFO] File balances.json không tồn tại hoặc trống. Khởi tạo mới.")
        player_balances = {}
        daily_timestamps = {}
        daily_money_limits = {}
        pending_transfers = {}
        return

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        player_balances = data.get("balances", {})
        daily_timestamps = data.get("daily_timestamps", {})
        daily_money_limits = data.get("money_limits", {})
        
        # Chuyển đổi timestamp strings -> datetime objects
        raw_pending = data.get("cash_pending", {})
        pending_transfers = {}
        for sender_id, transaction in raw_pending.items():
            if 'timestamp' in transaction and isinstance(transaction['timestamp'], str):
                try:
                    transaction['timestamp'] = datetime.datetime.fromisoformat(transaction['timestamp'])
                except ValueError:
                    transaction['timestamp'] = datetime.datetime.now()
            pending_transfers[sender_id] = transaction
            
    except (json.JSONDecodeError, IOError) as e:
        print(f"[ERROR] Lỗi khi đọc balances.json: {e}. Khởi tạo lại.")
        player_balances = {}
        daily_timestamps = {}
        daily_money_limits = {}
        pending_transfers = {}

# ============================================================
# PHẦN 6: KHỞI TẠO BOT
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, owner_ids=set(OWNER_IDS))

# ============================================================
# PHẦN 7: EVENTS
# ============================================================

@bot.event
async def on_ready():
    print(f'[READY] Bot: {bot.user} | Servers: {len(bot.guilds)}')
    load_balances()
    
    for guild in bot.guilds:
        print(f"  - {guild.name} ({guild.member_count} members)")

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(
            "**CẬP NHẬT MỚI SIÊU LỚN**\n"
            "***Chính Thức Cho Bot Hoạt Động***\n"
            f"Sử dụng cú pháp '<@{bot.user.id}> hướng dẫn' để biết các lệnh\n"
            f"**LƯU Ý** NẾU THẤY BUG MÀ KHÔNG BÁO CHO <@{OWNER_IDS[0]}> THÌ BỊ MUTE\n"
            "||báo để cho thằng code ra biết mình code ngu nên mới có lỗi 😭||"
        )

    bot.loop.create_task(chat_terminal())


async def chat_terminal():
    """Cho phép gửi tin nhắn từ terminal."""
    await bot.wait_until_ready()
    print("[TERMINAL] Sẵn sàng nhận lệnh từ terminal.")
    
    while not bot.is_closed():
        try:
            user_input = await asyncio.to_thread(input, "> ")
            channel = bot.get_channel(CHANNEL_ID)
            if channel and user_input.strip():
                await channel.send(user_input)
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            print(f"[TERMINAL ERROR] {e}")


@bot.event
async def on_member_join(member):
    if member.bot:
        return
        
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    guild = member.guild
    embed = discord.Embed(
        title=f"🎉 Chào mừng {member.display_name} đã đến server {guild.name}! 🎉",
        description="Hãy đọc luật ở <#1287089771037855805> rồi react ✅ để có thể vào chat trong server!",
        color=discord.Color.purple()
    )
    embed.set_image(url=WELCOME_IMAGE_URL)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(
        name="Tổng số thành viên",
        value=f"Hiện tại chúng ta có **{guild.member_count}** thành viên.",
        inline=True
    )

    try:
        await channel.send(f"Chào mừng {member.mention} đã đến **server của Ami**")
        await channel.send(embed=embed)
    except Exception as e:
        print(f"[ERROR] on_member_join: {e}")


@bot.event
async def on_member_remove(member):
    if member.bot:
        return
        
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if not channel:
        return

    guild = member.guild
    
    # Xác định loại hành động
    action_type = "đã rời khỏi server (Tự Rời hoặc bị Kick)"
    color = discord.Color.light_grey()
    title_text = "Thông Báo Có 1 Người Đã Rời Server"

    try:
        await guild.fetch_ban(member)
        # Nếu không lỗi -> đã bị ban
        action_type = "**đã bị BAN**"
        color = discord.Color.dark_red()
        title_text = "MỘT THẰNG NGU ĐÃ BỊ BAN"
    except discord.NotFound:
        pass  # Không bị ban -> tự rời hoặc bị kick
    except discord.Forbidden:
        print("[WARNING] Bot thiếu quyền để kiểm tra ban list")
    except Exception as e:
        print(f"[ERROR] Kiểm tra ban: {e}")

    embed = discord.Embed(
        title=title_text,
        description=f"**{member.display_name}** {action_type}.",
        color=color
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"ID: {member.id} | Server: {guild.name}")

    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"[ERROR] on_member_remove: {e}")


async def send_member_remove_notification(guild, member, action_type: str, reason: str = "Không có lý do"):
    """Hàm gửi thông báo member rời server (dùng cho sim commands)."""
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if not channel:
        print(f"[ERROR] Không tìm thấy kênh {NOTIFICATION_CHANNEL_ID}")
        return

    action_map = {
        'LEAVE': ("Thông Báo Có 1 Người Đã Rời Server", "đã tự rời khỏi server", discord.Color.light_grey()),
        'KICK': ("⚠️ MỘT NGƯỜI ĐÃ BỊ KICK", f"**đã bị KICK**\nLý do: {reason}", discord.Color.orange()),
        'BAN': ("🔨 MỘT THẰNG NGU ĐÃ BỊ BAN", f"**đã bị BAN**\nLý do: {reason}", discord.Color.dark_red()),
    }
    
    title, description_suffix, color = action_map.get(
        action_type, 
        ("Thông Báo", "đã rời server", discord.Color.light_grey())
    )

    embed = discord.Embed(
        title=title,
        description=f"**{member.display_name}** {description_suffix}.",
        color=color
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"ID: {member.id} | Server: {guild.name}")

    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"[ERROR] send_member_remove_notification: {e}")

# ============================================================
# PHẦN 8: LỆNH QUẢN TRỊ
# ============================================================

@bot.command(name='shutdown', help='Tắt bot. Chỉ chủ bot mới dùng được.')
@commands.is_owner()
async def shutdown(ctx):
    save_balances()
    await ctx.send("Bot đang được tắt... Dữ liệu đã được lưu.")
    await bot.close()
    os._exit(0)


@bot.command(name='congtien', help='Cộng tiền cho người chơi.')
@commands.check(is_authorized_user)
async def add_money(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("Số tiền phải là số dương.")
    
    user_id = str(member.id)
    author_id = str(ctx.author.id)

    # Owner: không giới hạn
    if is_owner(ctx.author.id):
        player_balances[user_id] = get_balance(user_id) + amount
        save_balances()
        return await ctx.send(
            f"Quân Blue Archive đã cộng thành công **{format_money(amount)}** "
            f"{CURRENCY_NAME} cho {member.mention}."
        )

    # Authorized users: có giới hạn daily
    if author_id not in daily_money_limits:
        daily_money_limits[author_id] = {
            "amount_added": 0, 
            "last_timestamp": datetime.datetime.now().isoformat()
        }

    limit_data = daily_money_limits[author_id]
    last_add_time = datetime.datetime.fromisoformat(limit_data["last_timestamp"])
    
    # Reset nếu qua ngày mới
    if (datetime.datetime.now() - last_add_time).total_seconds() >= 86400:
        limit_data["amount_added"] = 0
        limit_data["last_timestamp"] = datetime.datetime.now().isoformat()

    remaining_limit = MAX_DAILY_ADD_AMOUNT - limit_data["amount_added"]
    if amount > remaining_limit:
        return await ctx.send(
            f"Bạn chỉ còn **{format_money(remaining_limit)}** {CURRENCY_NAME} để cộng hôm nay."
        )

    player_balances[user_id] = get_balance(user_id) + amount
    limit_data["amount_added"] += amount
    save_balances()
    
    await ctx.send(f"Đã cộng **{format_money(amount)}** {CURRENCY_NAME} cho {member.mention}.")
    await ctx.send(
        f"Đã dùng **{format_money(limit_data['amount_added'])}**"
        f"/{format_money(MAX_DAILY_ADD_AMOUNT)} {CURRENCY_NAME} hôm nay."
    )


@add_money.error
async def add_money_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            f"Mày là ai mà đòi ra lệnh cho tao?\n"
            f"Chỉ có anh <@{OWNER_IDS[0]}> 'Quân Blue Archive' mới có quyền nhá"
        )
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Cú pháp không hợp lệ. Ví dụ: `!congtien @user 100`")


@bot.command(name='trutien', help='Trừ tiền của người chơi.')
@commands.check(is_authorized_user)
async def remove_money(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("Số tiền cần trừ phải là số dương.")
    
    user_id = str(member.id)
    new_balance = get_balance(user_id) - amount
    player_balances[user_id] = new_balance
    save_balances()

    await ctx.send(
        f"Đã trừ **{format_money(amount)}** {CURRENCY_NAME} của {member.mention}.\n"
        f"Số dư mới: **{format_money(new_balance)}** {CURRENCY_NAME}."
    )


@remove_money.error
async def remove_money_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            f"Mày là ai mà đòi ra lệnh cho tao?\n"
            f"Chỉ có anh <@{OWNER_IDS[0]}> 'Quân Blue Archive' mới có quyền nhá"
        )
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Cú pháp không hợp lệ. Ví dụ: `!trutien @user 100`")

# ============================================================
# PHẦN 9: LỆNH KINH TẾ
# ============================================================

@bot.command(name='daily', help='Nhận tiền thưởng hàng ngày.')
async def daily_reward_cmd(ctx):
    user_id = str(ctx.author.id)
    now = datetime.datetime.now()

    # Owner: luôn nhận được, không cooldown
    if is_owner(ctx.author.id):
        player_balances[user_id] = get_balance(user_id) + DAILY_REWARD
        daily_timestamps[user_id] = now.isoformat()
        save_balances()
        return await ctx.send(
            f"Quân Blue Archive. Anh đã nhận **{format_money(DAILY_REWARD)}** {CURRENCY_NAME}. "
            f"Tổng: **{format_money(player_balances[user_id])}** {CURRENCY_NAME}."
        )

    # Người chơi mới
    if user_id not in player_balances:
        player_balances[user_id] = DAILY_REWARD
        daily_timestamps[user_id] = now.isoformat()
        save_balances()
        return await ctx.send(
            f"Chúc mừng! Bạn đã nhận **{format_money(DAILY_REWARD)}** {CURRENCY_NAME} "
            f"tiền thưởng hàng ngày đầu tiên."
        )

    # Kiểm tra cooldown 24h
    last_claim_str = daily_timestamps.get(user_id)
    if last_claim_str:
        try:
            last_claim = datetime.datetime.fromisoformat(last_claim_str)
        except ValueError:
            last_claim = datetime.datetime.min
    else:
        last_claim = datetime.datetime.min

    time_diff = now - last_claim
    if time_diff.total_seconds() < 86400:
        remaining = datetime.timedelta(seconds=86400) - time_diff
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes = remainder // 60
        return await ctx.send(
            f"Mày nhận tiền rồi còn đòi hỏi gì nữa? "
            f"Đợi **{hours} giờ và {minutes} phút** nữa."
        )

    player_balances[user_id] = get_balance(user_id) + DAILY_REWARD
    daily_timestamps[user_id] = now.isoformat()
    save_balances()
    await ctx.send(
        f"Thành công! Bạn đã nhận **{format_money(DAILY_REWARD)}** {CURRENCY_NAME}.\n"
        f"Tổng: **{format_money(player_balances[user_id])}** {CURRENCY_NAME}."
    )


@bot.command(name='sdtk', help='Xem số dư tài khoản.')
@commands.cooldown(1, 10, commands.BucketType.user)
async def check_balance(ctx):
    user_id = str(ctx.author.id)
    
    if user_id not in player_balances:
        return await ctx.send("Bạn chưa có tài khoản. Chơi game để nhận tiền khởi nghiệp!")

    balance = format_money(player_balances[user_id])
    if is_owner(ctx.author.id):
        await ctx.send(f"Thưa anh Quân Blue Archive, anh còn **{balance}** {CURRENCY_NAME}!")
    else:
        await ctx.send(f"Mày còn **{balance}** {CURRENCY_NAME}")


@bot.command(name='top', help='Bảng xếp hạng giàu nhất.')
async def show_leaderboard(ctx):
    if not player_balances:
        return await ctx.send("Chưa có người chơi nào trong bảng xếp hạng!")

    sorted_players = sorted(player_balances.items(), key=lambda x: x[1], reverse=True)[:10]
    
    lines = ["🏆 **BẢNG XẾP HẠNG GIÀU NHẤT** 🏆\n"]
    for rank, (uid, balance) in enumerate(sorted_players, 1):
        user = bot.get_user(int(uid))
        name = user.display_name if user else f"ID: {uid}"
        lines.append(f"**#{rank}** {name}: **{format_money(balance)}** {CURRENCY_NAME}")

    await ctx.send("\n".join(lines))


@bot.command(name='chuyentien', help='Chuyển tiền cho người khác.')
@commands.cooldown(1, 10, commands.BucketType.user)
async def transfer_money(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)

    if amount <= 0:
        return await ctx.send("Số tiền chuyển phải lớn hơn 0.")
    if sender_id == receiver_id:
        return await ctx.send("Bạn không thể tự chuyển tiền cho mình.")
    if sender_id not in player_balances:
        return await ctx.send("Bạn chưa có tài khoản. Chơi game để tạo tài khoản.")
    if player_balances[sender_id] < amount:
        return await ctx.send(
            f"Không đủ tiền! Số dư: **{format_money(player_balances[sender_id])}** {CURRENCY_NAME}."
        )

    pending_transfers[sender_id] = {
        "receiver_id": receiver_id,
        "amount": amount,
        "timestamp": datetime.datetime.now()
    }

    await ctx.send(
        f"**Xác nhận chuyển khoản:** Chuyển **{format_money(amount)}** {CURRENCY_NAME} "
        f"cho {member.mention}.\nGõ `!chapnhan` trong **60 giây** để hoàn tất."
    )


@transfer_money.error
async def transfer_money_error(ctx, error):
    if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send("Cú pháp: `!chuyentien @người_chơi <số tiền>`")


@bot.command(name='chapnhan', help='Xác nhận giao dịch chuyển khoản.')
async def confirm_transfer(ctx):
    sender_id = str(ctx.author.id)

    if sender_id not in pending_transfers:
        return await ctx.send("Bạn không có giao dịch nào đang chờ.")

    transaction = pending_transfers[sender_id]
    elapsed = (datetime.datetime.now() - transaction["timestamp"]).total_seconds()
    
    if elapsed > 60:
        del pending_transfers[sender_id]
        return await ctx.send("Giao dịch đã hết hạn. Vui lòng tạo mới.")

    amount = transaction["amount"]
    receiver_id = transaction["receiver_id"]
    
    if get_balance(sender_id) < amount:
        del pending_transfers[sender_id]
        return await ctx.send("Giao dịch thất bại: Không đủ tiền.")

    player_balances[sender_id] -= amount
    player_balances[receiver_id] = get_balance(receiver_id) + amount
    save_balances()
    del pending_transfers[sender_id]

    receiver = bot.get_user(int(receiver_id))
    receiver_mention = receiver.mention if receiver else f"<@{receiver_id}>"
    await ctx.send(
        f"**Giao dịch thành công!** Đã chuyển **{format_money(amount)}** "
        f"{CURRENCY_NAME} cho {receiver_mention}."
    )

# ============================================================
# PHẦN 10: GAME TÀI XỈU
# ============================================================

@bot.command(name='choigame', aliases=['cg'], help='Chơi Tài Xỉu.')
@commands.cooldown(1, 10, commands.BucketType.user)
async def play_taixiu(ctx, bet_input: str = None):
    if bet_input is None:
        return await ctx.send("Vui lòng nhập số tiền cược. Ví dụ: `!cg 50` hoặc `!cg all`")
    
    user_id = str(ctx.author.id)

    # Tạo tài khoản mới nếu chưa có
    if ensure_account(user_id, STARTER_BALANCE):
        await ctx.send(
            f"Chúc mừng {ctx.author.mention}! "
            f"Bạn được tặng {STARTER_BALANCE} {CURRENCY_NAME} để khởi nghiệp."
        )

    current_balance = get_balance(user_id)

    # Parse số tiền cược
    if bet_input.lower() == 'all':
        bet_amount = current_balance
    else:
        try:
            bet_amount = int(bet_input.replace('.', '').replace(',', ''))
        except ValueError:
            return await ctx.send("Số tiền cược phải là số hoặc 'all'.")

    if bet_amount <= 0:
        return await ctx.send("Mày có biết làm toán không?")

    if current_balance < bet_amount:
        if is_owner(ctx.author.id):
            return await ctx.send(
                f"Thưa anh, anh không đủ tiền để đặt **{format_money(bet_amount)}** {CURRENCY_NAME} ạ.\n"
                f"Số dư: **{format_money(current_balance)}** {CURRENCY_NAME}"
            )
        
        msg = f"Không đủ tiền! Cần **{format_money(bet_amount)}** nhưng chỉ có **{format_money(current_balance)}** {CURRENCY_NAME}."
        if current_balance == 0:
            msg += f"\nHết tiền rồi, hỏi <@{OWNER_IDS[0]}> để được cho tiền."
        return await ctx.send(msg)

    # Bắt đầu game
    game_msg = await ctx.send(
        f"Bạn đặt **{format_money(bet_amount)}** {CURRENCY_NAME}. Chọn **'Tài'** hay **'Xỉu'**?"
    )

    def check_choice(m):
        return (m.author == ctx.author 
                and m.channel == ctx.channel 
                and m.content.lower() in ['tài', 'xỉu'])

    try:
        choice_msg = await bot.wait_for('message', check=check_choice, timeout=30.0)
    except asyncio.TimeoutError:
        return await ctx.send("⏰ Hết thời gian. Trò chơi kết thúc.")

    user_choice = choice_msg.content.lower()

    # Lắc xúc xắc
    await game_msg.edit(content="Đang lắc xúc xắc... 🎲")
    await asyncio.sleep(2)

    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)

    # Hiển thị từng xúc xắc
    for i in range(3):
        display = "\n".join(f"Xúc xắc {j+1}: **{dice[j]}**" for j in range(i + 1))
        await game_msg.edit(content=f"Kết quả:\n\n{display}")
        await asyncio.sleep(1.5)

    # Xác định kết quả
    if 11 <= total <= 17:
        result = "tài"
    elif 4 <= total <= 10:
        result = "xỉu"
    else:
        result = "hòa"

    await game_msg.edit(
        content=f"Kết quả:\n\n"
        + "\n".join(f"Xúc xắc {i+1}: **{d}**" for i, d in enumerate(dice))
        + f"\n\nTổng: **{total}** → **{result.upper()}**"
    )

    # Xử lý thắng/thua
    if user_choice == result:
        player_balances[user_id] += bet_amount
        save_balances()
        await ctx.send(
            f"🎉 Chúc mừng! Bạn thắng **{format_money(bet_amount)}** {CURRENCY_NAME}!\n"
            f"Số dư: **{format_money(player_balances[user_id])}** {CURRENCY_NAME}"
        )
        video = VIDEO_PATHS["win"] if result == "tài" else VIDEO_PATHS["gamble"]
        await send_file_safe(ctx.channel, video)
    else:
        player_balances[user_id] -= bet_amount
        save_balances()
        await ctx.send(random.choice(LOSE_ANSWERS))
        await ctx.send(f"Số dư: **{format_money(player_balances[user_id])}** {CURRENCY_NAME}")
        await send_file_safe(ctx.channel, VIDEO_PATHS["lose"])


@play_taixiu.error
async def play_taixiu_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Cú pháp: `!choigame <số tiền>` hoặc `!cg all`")

# ============================================================
# PHẦN 11: GAME ĐUA NGỰA
# ============================================================

def calculate_stats_and_odds(entities: list) -> list:
    """Tính chỉ số và tỷ lệ cược ngẫu nhiên cho các ngựa."""
    results = []
    total_stats = 0

    for entity in entities:
        stats = random.randint(500, 1200)
        results.append({
            "name": entity["name"],
            "emoji": entity["emoji"],
            "stats": stats,
            "odds": 0.0,
            "skill": entity.get("skill"),
        })
        total_stats += stats

    for result in results:
        odds = 1.0 + (total_stats - result["stats"]) / (len(entities) * 150)
        result["odds"] = round(odds, 1)

    return results


async def run_race_simulation(ctx, all_results: list):
    """Chạy mô phỏng đua ngựa với hệ thống skill."""
    print("--- Bắt đầu Mô phỏng Đua Ngựa ---")

    # Khởi tạo dữ liệu đua
    race_data = {}
    for result in all_results:
        random_boost = random.randint(-RANDOM_RANGE // 2, RANDOM_RANGE // 2)
        performance_score = (result['stats'] * STAT_WEIGHT) + random_boost

        race_data[result['name']] = {
            'distance': 0,
            'emoji': result['emoji'],
            'score': performance_score,
            'result': result,
            'skill_info': result.get('skill'),
            'skill_active': False,
            'skill_activated_ever': False,
            'skill_remaining_steps': 0,
            'skill_triggered_this_step': False,
        }

    sorted_race_data = sorted(race_data.items(), key=lambda x: x[0])

    # Gửi embed khởi động
    try:
        race_message = await ctx.send(
            embed=discord.Embed(title="🏁 ĐUA NGỰA ĐANG KHỞI ĐỘNG...", color=discord.Color.blue())
        )
    except Exception as e:
        print(f"[ERROR] Không thể gửi tin nhắn đua ngựa: {e}")
        return None, []

    winner = None

    # === VÒNG LẶP CHÍNH ===
    for step in range(1, TOTAL_RACE_STEPS + 1):
        race_status = []
        step_skill_messages = []

        for name, data in sorted_race_data:
            data['skill_triggered_this_step'] = False

            # --- PHASE 1: Kiểm tra & kích hoạt Skill ---
            if (step in SKILL_ACTIVATION_STEPS
                    and data['skill_info'] is not None
                    and not data['skill_activated_ever']
                    and not data['skill_active']):
                
                if random.random() <= data['skill_info']['activation_chance']:
                    data['skill_active'] = True
                    data['skill_activated_ever'] = True
                    data['skill_remaining_steps'] = SKILL_DURATION
                    data['skill_triggered_this_step'] = True

                    skill_name = data['skill_info']['name']
                    multiplier = data['skill_info']['speed_multiplier']
                    step_skill_messages.append(
                        f"⚡ **{data['emoji']} {name}** kích hoạt "
                        f"**{skill_name}**! (x{multiplier} trong {SKILL_DURATION} bước!)"
                    )

            # --- PHASE 2: Tính tốc độ ---
            base_speed = (data['score'] / 500) + random.uniform(0, 0.5)

            if data['skill_active'] and data['skill_remaining_steps'] > 0:
                final_speed = base_speed * data['skill_info']['speed_multiplier']
                data['skill_remaining_steps'] -= 1
                if data['skill_remaining_steps'] <= 0:
                    data['skill_active'] = False
            else:
                final_speed = base_speed

            data['distance'] += final_speed

            # --- PHASE 3: Kiểm tra về đích ---
            if data['distance'] >= TRACK_LENGTH and winner is None:
                winner = data['result']

            # --- PHASE 4: Vẽ track ---
            blocks = min(int(data['distance']), TRACK_LENGTH)
            track = '█' * blocks + '░' * (TRACK_LENGTH - blocks)
            icon = " ⚡" if (data['skill_active'] or data['skill_triggered_this_step']) else ""
            race_status.append(f"{data['emoji']} **{name}**: [`{track}`]{icon}")

        # --- PHASE 5: Cập nhật Embed ---
        description = "\n".join(race_status)
        if step_skill_messages:
            description += f"\n\n{'─' * 30}\n" + "\n".join(step_skill_messages)

        is_skill_zone = step in SKILL_ACTIVATION_STEPS
        embed = discord.Embed(
            title=f"🏇 CUỘC ĐUA (Bước {step}/{TOTAL_RACE_STEPS})"
                  + (" ⚡ VÙNG SKILL!" if is_skill_zone else ""),
            description=description,
            color=discord.Color.red() if is_skill_zone else discord.Color.orange()
        )

        if is_skill_zone:
            embed.set_footer(text="⚡ Các ngựa có thể kích hoạt Skill!")
        else:
            remaining = min(SKILL_ACTIVATION_STEPS) - step
            if remaining > 0:
                embed.set_footer(text=f"Còn {remaining} bước đến vùng Skill...")

        try:
            await race_message.edit(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ Bot thiếu quyền để chỉnh sửa tin nhắn!")
            return None, []
        except Exception as e:
            print(f"[ERROR] Chỉnh sửa embed bước {step}: {e}")
            return None, []

        await asyncio.sleep(2.0)

        if winner is not None:
            break

    # === KẾT THÚC ===
    if winner is None:
        winner_name = max(race_data.items(), key=lambda x: x[1]['distance'])[0]
        winner = next(r for r in all_results if r["name"] == winner_name)

    # Sắp xếp kết quả theo quãng đường
    final_results = []
    for name, data in race_data.items():
        r = data['result'].copy()
        r['distance'] = data['distance']
        r['skill_activated'] = data['skill_activated_ever']
        r['skill_info'] = data['skill_info']
        final_results.append(r)

    final_results.sort(key=lambda x: x['distance'], reverse=True)
    return winner, final_results


@bot.command(name='duangua', aliases=['dsngua', 'odds'])
async def duangua_list(ctx):
    global cached_race_stats
    user_id = str(ctx.author.id)
    if user_id not in player_balances:
        player_balances[user_id] = 1000

    all_results = calculate_stats_and_odds(ENTITIES)
    cached_race_stats = all_results
    
    embed = discord.Embed(
        title="🐎 BẢNG TỶ LỆ CƯỢC ĐUA NGỰA HÔM NAY 🐎",
        description="Chọn ngựa của bạn và đặt cược bằng lệnh `!datcuoc <Tên> <Số tiền> [Lever]`",
        color=discord.Color.gold()
    )
    
    # Chia 8 ngựa thành 2 nhóm (4 + 4) để không vượt 1024 ký tự
    half = len(all_results) // 2
    
    # Nhóm 1
    stats_list_1 = []
    for result in all_results[:half]:
        stats_list_1.append(
            f"{result['emoji']} **{result['name']}**: "
            f"Chỉ số: **{result['stats']}** | "
            f"Tỷ lệ cược: **{result['odds']}%**"
        )
    
    # Nhóm 2
    stats_list_2 = []
    for result in all_results[half:]:
        stats_list_2.append(
            f"{result['emoji']} **{result['name']}**: "
            f"Chỉ số: **{result['stats']}** | "
            f"Tỷ lệ cược: **{result['odds']}%**"
        )
    
    embed.add_field(
        name="Các Ứng Viên & Chỉ Số Hiện Tại (Ngẫu nhiên)", 
        value="\n".join(stats_list_1), 
        inline=False
    )
    embed.add_field(
        name="​",  # Ký tự zero-width space làm tiêu đề trống
        value="\n".join(stats_list_2), 
        inline=False
    )
    
    embed.add_field(
        name="💰 Số dư của bạn", 
        value=f"Hiện tại: **{format_money(player_balances[user_id])}** {CURRENCY_NAME}", 
        inline=False
    )
                    
    embed.set_footer(text="Chỉ số và Tỷ lệ cược được tính ngẫu nhiên mỗi lần xem.")

    await ctx.send(embed=embed)


@bot.command(name='datcuoc', aliases=['cuoc'], help='Đặt cược đua ngựa.')
async def place_bet(ctx, *args):
    global cached_race_stats
    user_id = str(ctx.author.id)
    ensure_account(user_id, 1000)
    current_balance = player_balances[user_id]

    # 1. Parse arguments
    if len(args) < 2:
        return await ctx.send(
            "🛑 Cú pháp: `!datcuoc <Tên ngựa> <Số tiền> [Lever]`\n"
            "Ví dụ: `!datcuoc Gold Ship 5000 2`"
        )

    full_query = " ".join(args)
    chosen_entity = None

    # Tìm tên ngựa (ưu tiên tên dài hơn)
    for entity in sorted(ENTITIES, key=lambda x: len(x['name']), reverse=True):
        if full_query.lower().startswith(entity['name'].lower()):
            chosen_entity = entity
            remaining = full_query[len(entity['name']):].strip()
            break

    if not chosen_entity:
        return await ctx.send("❌ Không tìm thấy ngựa. Dùng `!duangua` để xem danh sách.")

    parts = remaining.split()
    if not parts:
        return await ctx.send("🛑 Thiếu số tiền cược.")

    # Parse số tiền
    bet_str = parts[0]
    if bet_str.lower() == 'all':
        bet_amount = current_balance
    else:
        try:
            bet_amount = int(bet_str.replace('.', '').replace(',', ''))
        except ValueError:
            return await ctx.send(f"❌ Số tiền '{bet_str}' không hợp lệ.")

    # Parse lever
    lever = 1.0
    if len(parts) > 1:
        try:
            lever = float(parts[1])
        except ValueError:
            return await ctx.send("❌ Đòn bẩy phải là số (ví dụ: 2.5).")

    # 2. Validate
    if bet_amount <= 0 or bet_amount > current_balance:
        return await ctx.send(
            f"❌ Số tiền không hợp lệ. Bạn có **{format_money(current_balance)}** {CURRENCY_NAME}."
        )
    if not 1.0 <= lever <= 5.0:
        return await ctx.send("❌ Đòn bẩy phải từ **1.0** đến **5.0**.")

    # 3. Chạy đua
    if cached_race_stats:
        all_results = cached_race_stats
        cached_race_stats = None
    else:
        await ctx.send("⚠️ Không có bảng chỉ số. Đang tạo ngẫu nhiên...")
        all_results = calculate_stats_and_odds(ENTITIES)

    winner, sorted_results = await run_race_simulation(ctx, all_results)
    if not winner:
        return

    # 4. Tính kết quả
    user_result = next(r for r in all_results if r["name"] == chosen_entity["name"])
    win_multiplier = user_result["odds"] * lever
    potential_win = int(bet_amount * win_multiplier)
    is_winner = (winner["name"] == chosen_entity["name"])

    if is_winner:
        payout = potential_win - bet_amount
        player_balances[user_id] += payout
        payout_text = f"+{format_money(payout)}"
        result_label = "THẮNG"
    else:
        player_balances[user_id] -= bet_amount
        payout_text = f"-{format_money(bet_amount)}"
        result_label = "THUA"

    save_balances()

    # 5. Xây dựng embed kết quả
    others = [r for r in sorted_results if r['name'] != winner['name']]
    second = others[0]['name'] if len(others) >= 1 else "N/A"
    third = others[1]['name'] if len(others) >= 2 else "N/A"

    # Helper: thêm text skill nếu đã kích hoạt
    def skill_text(result_data):
        if result_data and result_data.get('skill_activated') and result_data.get('skill_info'):
            return f" ⚡ *{result_data['skill_info']['name']}*"
        return ""

    winner_sorted = next((r for r in sorted_results if r['name'] == winner['name']), None)

    embed = discord.Embed(
        title=f"🏆 KẾT QUẢ: {result_label}! 🏆",
        color=discord.Color.green() if is_winner else discord.Color.red()
    )

    # Field: Ngựa đã chọn
    skill_display = ""
    if user_result.get('skill'):
        s = user_result['skill']
        skill_display = f"\nSkill: **{s['name']}** (x{s['speed_multiplier']} | {int(s['activation_chance']*100)}%)"

    embed.add_field(
        name=f"Bạn chọn: {user_result['emoji']} {user_result['name']}",
        value=(
            f"Odds: **x{user_result['odds']}** | Lever: **x{lever}**\n"
            f"Chỉ số: **{user_result['stats']}**{skill_display}\n"
            f"Cược: **{format_money(bet_amount)}** → Max thắng: **{format_money(potential_win)}** {CURRENCY_NAME}"
        ),
        inline=False
    )

    # Field: Kết quả chính thức
    embed.add_field(
        name="🏁 KẾT QUẢ CHÍNH THỨC",
        value=(
            f"🥇 **{winner['name']}** ({winner['stats']} Stats){skill_text(winner_sorted)}\n"
            f"🥈 {second}{skill_text(others[0] if len(others) >= 1 else None)}\n"
            f"🥉 {third}{skill_text(others[1] if len(others) >= 2 else None)}"
        ),
        inline=False
    )

    # Field: Tổng kết
    icon = "✅" if is_winner else "❌"
    embed.add_field(
        name="TỔNG KẾT",
        value=(
            f"{icon} {result_label}: **{payout_text}** {CURRENCY_NAME}\n"
            f"💰 Số dư: **{format_money(player_balances[user_id])}** {CURRENCY_NAME}"
        ),
        inline=False
    )

    await ctx.send(embed=embed)


@place_bet.error
async def place_bet_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("🛑 Cú pháp: `!datcuoc <Tên ngựa> <Số tiền> [Lever]`")

# ============================================================
# PHẦN 12: LỆNH MÔ PHỎNG (SIM)
# ============================================================

@bot.command(name='sim_join', help='Giả lập thành viên tham gia.')
@commands.is_owner()
async def sim_join(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"Đang mô phỏng: **{member.display_name}** tham gia...")
    await on_member_join(member)
    await ctx.send("✅ Mô phỏng hoàn tất.")


@bot.command(name='sim_leave', help='Giả lập thành viên rời server.')
@commands.is_owner()
async def sim_leave(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f"Đang mô phỏng: **{member.display_name}** tự rời...")
    await send_member_remove_notification(ctx.guild, member, 'LEAVE')
    await ctx.send("✅ Mô phỏng hoàn tất.")


@bot.command(name='sim_kick', help='Giả lập thành viên bị kick.')
@commands.is_owner()
async def sim_kick(ctx, member: discord.Member = None, *, reason: str = "Không có lý do"):
    member = member or ctx.author
    await ctx.send(f"Đang mô phỏng: **{member.display_name}** bị kick...")
    await send_member_remove_notification(ctx.guild, member, 'KICK', reason=reason)
    await ctx.send("✅ Mô phỏng hoàn tất.")


@bot.command(name='sim_ban', help='Giả lập thành viên bị ban.')
@commands.is_owner()
async def sim_ban(ctx, member: discord.Member = None, *, reason: str = "Vi phạm nghiêm trọng"):
    member = member or ctx.author
    await ctx.send(f"Đang mô phỏng: **{member.display_name}** bị ban...")
    await send_member_remove_notification(ctx.guild, member, 'BAN', reason=reason)
    await ctx.send("✅ Mô phỏng hoàn tất.")

# ============================================================
# PHẦN 13: XỬ LÝ TIN NHẮN (on_message)
# ============================================================

@bot.event
async def on_message(message):
    # Bỏ qua tin nhắn của bot
    if message.author == bot.user:
        return

    msg = message.content.lower()
    channel = message.channel

    # --- Kênh chat chính: gửi video với cooldown ---
    if message.channel.id == CHAT_CHINH_ID:
        global cooldown_chat_chinh
        now = time.time()
        if now - cooldown_chat_chinh >= COOLDOWN_CHAT_CHINH:
            cooldown_chat_chinh = now
            await send_file_safe(channel, VIDEO_PATHS["phaichiu"], message.author.mention)

    # --- Bot được mention ---
    if bot.user.mentioned_in(message):
        # Loại bỏ mention để lấy nội dung câu hỏi
        # FIX BUG: Xử lý cả 2 format <@id> và <@!id>
        question = message.content
        question = question.replace(f'<@{bot.user.id}>', '').strip()
        question = question.replace(f'<@!{bot.user.id}>', '').strip()
        
        if not question:
            await bot.process_commands(message)
            return

        if 'biết' in question.lower() or 'quân blue archive' in question.lower():
            await channel.send(
                "Quân Blue Archive, là một trong số các youtuber nổi tiếng làm về "
                "tựa game dấu yêu học sinh Blue Archive, là một người đẹp trai, "
                "khoai to kèm với kiến thức sâu rộng của mình về tựa game này!"
            )
            return

        if 'hướng dẫn' in question.lower():
            await channel.send(
                "**Các lệnh:**\n"
                "- `xem phim` để xem phim ngẫu nhiên\n"
                "- ||`xem sếch`|| (tỉ lệ 6.6%) - chỉ dùng trong kênh NSFW\n"
                "- `!cg <số tiền>` hoặc `!choigame` để chơi Tài Xỉu\n"
                "- `!duangua` xem bảng đua ngựa, `!datcuoc` để đặt cược\n"
                "- `!sdtk` xem số dư | `!daily` nhận thưởng hàng ngày\n"
                "- `!chuyentien @user <số>` chuyển tiền\n"
                "- `!top` bảng xếp hạng giàu nhất\n\n"
                "Từ khóa ẩn: ||cay, gay, tôi là kẹo con, uma, blue archive,...||"
            )
            return

        # AI response
        ##try:
            ##response = await model.generate_content_async([PERSONA_PROMPT, question])
            ##await channel.send(response.text)
        ##except Exception as e:
            ##print(f"[AI ERROR] {e}")
            ##await channel.send(random.choice(ERROR_ANSWERS))
        ##return

    # --- Từ khóa: Ưu tiên cụm từ dài trước ---
    
    # Cụm từ dài (phải kiểm tra trước từ đơn)
    if 'tôi là kẹo con' in msg:
        await channel.send("https://www.youtube.com/watch?v=9mA7h1jfxc8&list=PLnUioGkqqn5XwWaMlwhftWusPPK_KHz3T")
        return

    if 'quân blue archive' in msg or 'quân' in msg:
        await channel.send(f'Quân Blue Archive của bạn đây {message.author.mention}')
        await channel.send('https://media.tenor.com/oABUIAIFK0gAAAAM/hayase-yuuka-blue-archive.gif')
        return

    if 'tôi muốn xem phim' in msg or 'xem phim' in msg:
        path = get_random_video_from_folder(VIDEO_FOLDER_MAIN)
        if path:
            if not await send_file_safe(channel, path):
                await channel.send('Đéo có video cho mày xem đâu')
        else:
            await channel.send('Không tìm thấy video nào.')
        return

    if 'xem sếch' in msg or 'xem sẽ' in msg or 'sếch' in msg:
        # Chỉ cho phép trong kênh NSFW
        if message.channel.id != NSFW_CHANNEL_ID:
            await channel.send(f"❌ Chỉ dùng được trong <#{NSFW_CHANNEL_ID}>!")
            return

        user_id = message.author.id
        now = datetime.datetime.now()

        # Cooldown (Owner bypass)
        if user_id not in OWNER_IDS:
            last_use = cooldowns_nsfw.get(user_id)
            if last_use and (now - last_use).total_seconds() < COOLDOWN_NSFW:
                remaining = COOLDOWN_NSFW - (now - last_use).total_seconds()
                await channel.send(f"Bình tĩnh nào, chờ {remaining:.0f} giây nữa.")
                return
        cooldowns_nsfw[user_id] = now

        video_urls = load_paths(VIDEO_FILE)
        if not video_urls:
            print("[WARNING] Không có URL video NSFW")
            return

        # Owner bypass roll
        if user_id in OWNER_IDS:
            url = random.choice(video_urls)
            await channel.send("Thưa anh, sếch của anh đây ạ 🫡")
            await channel.send(f"[⬇]({url})")
        else:
            roll = random.uniform(0, 100)
            if roll <= 6.60:
                url = random.choice(video_urls)
                await channel.send("Sếch của mày đây")
                await channel.send(f"[⬇]({url})")
            else:
                await send_file_safe(channel, IMAGE_FILE)
        return

    if 'cafe' in msg:
        await channel.send('https://i.imgur.com/3tksAgI.gif')
        return

    if 'tài xỉu' in msg or 'xỉu tài' in msg or 'nổ hũ 64tr' in msg:
        await channel.send("tài hay xỉu???")
        await send_file_safe(channel, VIDEO_PATHS["taixiu"])
        return

    if 'địt mẹ thằng gay' in msg:
        await send_file_safe(channel, VIDEO_PATHS["tusena"], "Tú Sena solo với LBGT")
        return

    # FIX: 'gay' kiểm tra SAU 'địt mẹ thằng gay' để tránh match sai
    if 'gay' in msg:
        await send_file_safe(channel, VIDEO_PATHS["tusena"], "Tú Sena solo với LBGT")
        return

    # FIX: Kiểm tra 'cay' bằng word boundary để tránh match 'arcade', 'cayenne'...
    if any(word in ['cay', 'kay'] for word in msg.split()):
        await send_file_safe(channel, VIDEO_PATHS["cay"])
        return

    if 'uma musume' in msg or 'gái ngựa' in msg or 'mã nương' in msg:
        path = get_random_video_from_folder(VIDEO_FOLDER_UMA)
        if path:
            await send_file_safe(channel, path)
        else:
            await channel.send("Không có video Uma Musume.")
        return

    # FIX: 'uma' riêng kiểm tra SAU 'uma musume' 
    if 'uma' in msg:
        path = get_random_video_from_folder(VIDEO_FOLDER_UMA)
        if path:
            await send_file_safe(channel, path)
        else:
            await channel.send("Không có video Uma Musume.")
        return

    if 'dấu yêu học sinh' in msg or 'blue archive' in msg or 'học sinh' in msg:
        path = get_random_video_from_folder(VIDEO_FOLDER_BA)
        if path:
            await send_file_safe(channel, path)
        return

    # FIX: 'độ' quá chung, dễ trigger nhầm. Kiểm tra cụm từ cụ thể hơn
    if any(kw in msg for kw in ['bộ pc', 'độ pc', 'lộ pici', 'mixi']):
        await send_file_safe(channel, VIDEO_PATHS["dopc"])
        return

    # CUỐI CÙNG: Xử lý commands
    await bot.process_commands(message)

# ============================================================
# PHẦN 14: CHẠY BOT
# ============================================================

bot.run(DISCORD_TOKEN)