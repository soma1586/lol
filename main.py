import os
import random
import subprocess
import sys
from datetime import datetime, time
from threading import Thread

# 📦 ライブラリ自動インストール
try:
    import discord
    from discord import app_commands
    from discord.ext import commands, tasks
    from flask import Flask
    import pytz
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "discord.py", "Flask", "pytz"])
    import discord
    from discord import app_commands
    from discord.ext import commands, tasks
    from flask import Flask
    import pytz

# 季節イベントモジュールの読み込み
import events

# ==========================================
# ⚙️ Discord Bot & 設定
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 📢 通知チャンネルIDリスト
TARGET_CHANNEL_IDS = [
    1523741885750050847,
    1523748305190912000,
    1523638969970196582
]

ALLOWED_USER_ID = 1260279278998913181
JST = pytz.timezone("Asia/Tokyo")

# 状態保持用変数
last_joke = None
today_joke_cache = {"date": None, "joke": None}  # /today 用のキャッシュ

def get_random_joke():
    """jokes.txt からランダムに1個取得"""
    global last_joke
    try:
        with open("jokes.txt", "r", encoding="utf-8") as f:
            jokes = [line.strip() for line in f.readlines() if line.strip()]
        
        if not jokes:
            return "ネタ帳（jokes.txt）が空っぽだよ！ネタを追加してね。"
        
        if len(jokes) > 1 and last_joke in jokes:
            jokes.remove(last_joke)
            
        chosen_joke = random.choice(jokes)
        last_joke = chosen_joke
        return chosen_joke
    except FileNotFoundError:
        return "エラー：jokes.txt が見つかりません。GitHubにファイルを作ってね！"

def get_or_create_today_joke():
    """今日の面白い話を保持・取得（日付が変わると自動で新しくなる）"""
    global today_joke_cache
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    
    if today_joke_cache["date"] != today_str or today_joke_cache["joke"] is None:
        today_joke_cache["date"] = today_str
        today_joke_cache["joke"] = get_random_joke()
        
    return today_joke_cache["joke"]

def do_coin_flip():
    """コイン投げの判定処理"""
    rand = random.random()
    if rand < 0.01:
        return "🤯 **奇跡！コインが横向きに立ちました！！ (レア演出: 1%)**"
    elif rand < 0.505:
        return "🪙 コインの結果は... **【 表 (Heads) 】** です！"
    else:
        return "🪙 コインの結果は... **【 裏 (Tails) 】** です！"

def create_today_embed():
    """/today および !today 用のエムベッド作成"""
    joke = get_or_create_today_joke()
    event_msg = events.get_seasonal_event_message()
    
    embed = discord.Embed(
        title="📅 本日のおもしろ話",
        description=joke,
        color=discord.Color.gold(),
        timestamp=datetime.now(JST)
    )
    if event_msg:
        embed.add_field(name="🎉 本日の特別イベント", value=event_msg, inline=False)
        
    embed.set_footer(text="日付が変わると新しく更新されます！")
    return embed

# 全チャンネル送信関数
async def send_to_all_channels(content=None, embed=None):
    for channel_id in TARGET_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                await channel.send(content=content, embed=embed)
            except Exception as e:
                print(f"チャンネル {channel_id} への送信失敗: {e}")

@bot.event
async def on_ready():
    print(f"🎉 lolbot が正常に起動しました: {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 {len(synced)} 個のスラッシュコマンドを同期しました")
    except Exception as e:
        print(f"同期エラー: {e}")
    daily_joke_loop.start()

# ==========================================
# ⏰ 定期投稿タスク（毎日12:00）
# ==========================================
JST_12PM = time(hour=12, minute=0, second=0, tzinfo=JST)

@tasks.loop(time=JST_12PM)
async def daily_joke_loop():
    joke = get_or_create_today_joke()
    event_msg = events.get_seasonal_event_message()
    
    msg_content = "ーー 今日のおもしろ話 ーー\n"
    if event_msg:
        msg_content = f"✨ **【イベントメッセージ】** ✨\n{event_msg}\n\n" + msg_content
    msg_content += joke
    
    await send_to_all_channels(content=msg_content)

@daily_joke_loop.before_loop
async def before_daily_joke_loop():
    await bot.wait_until_ready()

# ==========================================
# 💬 スラッシュコマンド (`/`)
# ==========================================

# 🪙 コイン投げコマンド (/coin)
@bot.tree.command(name="coin", description="コインを投げて表か裏を判定します（超レア演出あり！？）")
async def coin_flip_slash(interaction: discord.Interaction):
    await interaction.response.send_message(do_coin_flip())

# 📜 今日の面白い話を再表示 (/today)
@bot.tree.command(name="today", description="今日のおもしろ話をもう一度確認します")
async def today_joke_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=create_today_embed())

# ==========================================
# 🛠️ 通常のプレフィックスコマンド (`!`)
# ==========================================

# 🪙 コイン投げコマンド (!coin, !コイン)
@bot.command(name="coin", aliases=["コイン"])
async def send_coin(ctx):
    await ctx.send(do_coin_flip())

# 📜 今日の面白い話を再表示 (!today)
@bot.command(name="today")
async def send_today(ctx):
    await ctx.send(embed=create_today_embed())

@bot.command(name="joke")
async def send_joke(ctx):
    await ctx.send(get_random_joke())

@bot.command(name="lolbot")
async def send_lol_joke(ctx):
    await ctx.send(get_random_joke())

@bot.command(name="lolbottest")
async def test_lol_bot(ctx):
    if ctx.author.id != ALLOWED_USER_ID:
        return
    await ctx.send("📢 指定された3つのチャンネルへテスト送信を実行します...")
    joke = get_random_joke()
    await send_to_all_channels(content=f"ーー 【テスト配信】今日のおもしろ話 ーー\n{joke}")

@bot.command(name="組長からの挑戦")
async def boss_challenge(ctx):
    boss_quotes = [
        "組長「2度とオールしないと言って1日後にオールする今日この頃byおぼろん」",
        "組長「フッ…いい度胸だ。この俺にコマンドを打つとはな。…とりあえずお茶淹れてくれ。」",
        "組長「挑戦だと？ ならば次の動画のカット数を2倍にしてやろうかァ！？」",
        "組長「よくここまで辿り着いた。褒美として、ワイの厳選おもしろ話を授けよう。\n【悲報】ワイ、コンビニでドヤ顔でポイントカード出したらドラッグストアのやつだった。」"
    ]
    await ctx.send(random.choice(boss_quotes))

@bot.command(name="up")
async def update_patch(ctx):
    if ctx.author.id != ALLOWED_USER_ID:
        return

    await ctx.send("📝 **アップデートパッチの内容を入力してください。**\n（例：自動送信の不具合修正、新コマンドの追加 など）")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=120.0)
        update_content = msg.content

        now = datetime.now(JST)
        version_str = f"v{now.year}-{now.month}"

        embed = discord.Embed(
            title="📢 lolbot リリースノート！",
            description=f"**バージョン:** `{version_str}`",
            color=discord.Color.green(),
            timestamp=now
        )
        embed.add_field(name="🛠️ アップデート内容", value=update_content, inline=False)
        embed.add_field(name="👤 変更者", value="soma1586", inline=False)
        embed.set_footer(text="lolbotは日々進化しています✊")

        await send_to_all_channels(embed=embed)
        await ctx.send("✅ アップデートパッチをすべてのチャンネルに送信しました！")

    except TimeoutError:
        await ctx.send("❌ 時間切れです。もう一度 `!up` をやり直してください。")

# ==========================================
# 🌐 Render用（Flask Webサーバー）
# ==========================================
app = Flask("")

@app.route("/")
def home():
    return "Joke Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 🚀 起動処理
# ==========================================
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
