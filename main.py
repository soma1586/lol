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
    1523748305190912000,  # 2つ目のチャンネルID
    1523638969970196582   # 3つ目のチャンネルID
]

# 👑 テストコマンドの実行を許可するユーザーID
ALLOWED_USER_ID = 1260279278998913181

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
    if not daily_joke_loop.is_running():
        daily_joke_loop.start()

# ==========================================
# 2. 定期投稿タスク（【テスト用】毎日AM 4:00に自動でつぶやく）
# ==========================================
# 日本時間の朝4時00分を指定
TEST_TIME = time(hour=4, minute=0, second=0, tzinfo=JST)

@tasks.loop(time=TEST_TIME)
async def daily_joke_loop():
    joke = get_random_joke()
    await send_to_all_channels(f"ーー 今日のおもしろ話 ーー\n{joke}")

@daily_joke_loop.before_loop
async def before_daily_joke_loop():
    await bot.wait_until_ready()

# 共通の送信処理を関数化
async def send_to_all_channels(content):
    for channel_id in TARGET_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                await channel.send(content)
            except Exception as e:
                print(f"チャンネル {channel_id} への送信に失敗しました: {e}")

# ==========================================
# 3. コマンド（通常機能 ＆ 追加機能）
# ==========================================

# 「!joke」
@bot.command(name="joke")
async def send_joke(ctx):
    joke = get_random_joke()
    await ctx.send(joke)

# 「!lolbot」
@bot.command(name="lolbot")
async def send_lol_joke(ctx):
    joke = get_random_joke()
    await ctx.send(joke)

# 🔒 新機能①：「!lolbottest」（指定ユーザー以外は反応しない）
@bot.command(name="lolbottest")
async def test_lol_bot(ctx):
    if ctx.author.id != ALLOWED_USER_ID:
        return

    await ctx.send("📢 指定された3つのチャンネルへテスト送信を実行します...")
    joke = get_random_joke()
    await send_to_all_channels(f"ーー 【テスト配信】今日のおもしろ話 ーー\n{joke}")

# 🕶️ 新機能②：「!組長からの挑戦」で隠しメッセージを送信
@bot.command(name="組長からの挑戦")
async def boss_challenge(ctx):
    boss_quotes = [
        "組長「2度とオールしないと言って1日後にオールする今日この頃byおぼろん」",
        "組長「フッ…いい度胸だ。この俺にコマンドを打つとはな。…とりあえずお茶淹れてくれ。」",
        "組長「挑戦だと？ ならば次の動画のカット数を2倍にしてやろうかァ！？」",
        "組長「よくここまで辿り着いた。褒美として、ワイの厳選おもしろ話を授けよう。\n【悲報】ワイ、コンビニでドヤ顔でポイントカード出したらドラッグストアのやつだった。」"
    ]
    await ctx.send(random.choice(boss_quotes))

# ==========================================
# 4. Render用（Flask Webサーバー）
# ==========================================
app = Flask("")

@app.route("/")
def home():
    return "Joke Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 5. 起動
# ==========================================
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    bot.run(os.getenv("DISCORD_TOKEN"))
