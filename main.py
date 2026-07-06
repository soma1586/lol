import os
import random
import subprocess
import sys
from datetime import datetime, time, timedelta
from threading import Thread

# ==========================================
# 0. 必要なライブラリの自動インストール
# ==========================================
try:
    import discord
    from discord.ext import commands, tasks
    from flask import Flask
    import pytz
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "discord.py", "Flask", "pytz"])
    import discord
    from discord.ext import commands, tasks
    from flask import Flask
    import pytz

# ==========================================
# 1. Discord Botの設定
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 📢 おもしろ話を同時に投稿したい「3つのチャンネルID」をここに設定してください
TARGET_CHANNEL_IDS = [
    1523741885750050847,  # 1つ目のチャンネルID
    1523638969970196581,  # 2つ目のチャンネルID
    1523638969970196582   # 3つ目のチャンネルID
]

# タイムゾーンを日本時間に設定
JST = pytz.timezone("Asia/Tokyo")

# 直前に使ったネタを記憶する変数
last_joke = None

# ネタ帳ファイルから「前回と違うネタ」をランダムに1つ読み込む関数
def get_random_joke():
    global last_joke
    try:
        with open("jokes.txt", "r", encoding="utf-8") as f:
            jokes = [line.strip() for line in f.readlines() if line.strip()]
        
        if not jokes:
            return "ネタ帳（jokes.txt）が空っぽだよ！ネタを追加してね。"
        
        # ネタが2つ以上ある場合は、前回と同じネタを候補から外す
        if len(jokes) > 1 and last_joke in jokes:
            jokes.remove(last_joke)
            
        chosen_joke = random.choice(jokes)
        last_joke = chosen_joke  # 今回選んだネタを記憶
        return chosen_joke

    except FileNotFoundError:
        return "エラー：jokes.txt が見つかりません。GitHubにファイルを作ってね！"

@bot.event
async def on_ready():
    print(f"🎉 お笑いBotが起動しました: {bot.user.name}")
    # 毎日自動投稿するタイマーをスタート
    daily_joke_loop.start()

# ==========================================
# 2. 定期投稿タスク（毎日お昼の12:00に自動でつぶやく）
# ==========================================
# 日本時間の昼12時を指定
JST_12PM = time(hour=12, minute=0, second=0, tzinfo=JST)

@tasks.loop(time=JST_12PM)
async def daily_joke_loop():
    joke = get_random_joke()
    
    # 登録されたすべてのチャンネルIDに対してループ処理で送信
    for channel_id in TARGET_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                await channel.send(f"ーー 今日のおもしろ話 ーー\n{joke}")
            except Exception as e:
                print(f"チャンネル {channel_id} への送信に失敗しました: {e}")

@daily_joke_loop.before_loop
async def before_daily_joke_loop():
    await bot.wait_until_ready()

# ==========================================
# 3. コマンド（チャットで打つといつでも文章を返す）
# ==========================================

# 「!joke」で呼び出す場合
@bot.command(name="joke")
async def send_joke(ctx):
    joke = get_random_joke()
    await ctx.send(joke)

# 「!lolbot」で自由にいつでも呼び出す場合！
@bot.command(name="lolbot")
async def send_lol_joke(ctx):
    joke = get_random_joke()
    await ctx.send(joke)

# ==========================================
# 4. Render用（Flask Webサーバー）
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
# 5. 起動
# ==========================================
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
