import os
import random
import subprocess
import sys
from threading import Thread

# ==========================================
# 0. 必要なライブラリの自動インストール
# ==========================================
try:
    import discord
    from discord.ext import commands, tasks
    from flask import Flask
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "discord.py", "Flask"])
    import discord
    from discord.ext import commands, tasks
    from flask import Flask

# ==========================================
# 1. Discord Botの設定
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 📢 おもしろ話を投稿したいチャンネルのIDを設定してください
TARGET_CHANNEL_ID = 1523638969970196580

# ネタ帳ファイルからランダムに1つおもしろ話を読み込む関数
def get_random_joke():
    try:
        with open("jokes.txt", "r", encoding="utf-8") as f:
            jokes = [line.strip() for line in f.readlines() if line.strip()]
        if jokes:
            return random.choice(jokes)
        return "ネタ帳（jokes.txt）が空っぽだよ！ネタを追加してね。"
    except FileNotFoundError:
        return "エラー：jokes.txt が見つかりません。GitHubにファイルを作ってね！"

@bot.event
async def on_ready():
    print(f"🎉 お笑いBotが起動しました: {bot.user.name}")
    # 毎日自動投稿するタイマーをスタート
    daily_joke_loop.start()

# ==========================================
# 2. 定期投稿タスク（1日に1回自動でつぶやく）
# ==========================================
@tasks.loop(hours=24)
async def daily_joke_loop():
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        joke = get_random_joke()
        await channel.send(f"ーー 今日のおもしろ話 ーー\n{joke}")

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
