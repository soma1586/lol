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

# 📢 通知を飛ばしたい「3つのチャンネルID」
TARGET_CHANNEL_IDS = [
    1523741885750050847,  # 1つ目のチャンネルID
    1523748305190912000,  # 2つ目のチャンネルID
    1523638969970196582   # 3つ目のチャンネルID
]

# 👑 権限を持つユーザーID（soma1586さん）
ALLOWED_USER_ID = 1260279278998913181

# タイムゾーンを日本時間に設定
JST = pytz.timezone("Asia/Tokyo")

# 直前に使ったネタを記憶する変数
last_joke = None

def get_random_joke():
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

@bot.event
async def on_ready():
    print(f"🎉 お笑いBotが起動しました: {bot.user.name}")
    daily_joke_loop.start()

# ==========================================
# 2. 定期投稿タスク（毎日お昼の12:00）
# ==========================================
JST_12PM = time(hour=12, minute=0, second=0, tzinfo=JST)

async def send_to_all_channels(content=None, embed=None):
    for channel_id in TARGET_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                await channel.send(content=content, embed=embed)
            except Exception as e:
                print(f"チャンネル {channel_id} への送信に失敗しました: {e}")

@tasks.loop(time=JST_12PM)
async def daily_joke_loop():
    joke = get_random_joke()
    await send_to_all_channels(content=f"ーー 今日のおもしろ話 ーー\n{joke}")

@daily_joke_loop.before_loop
async def before_daily_joke_loop():
    await bot.wait_until_ready()

# ==========================================
# 3. コマンド機能
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

# 🔒 「!lolbottest」
@bot.command(name="lolbottest")
async def test_lol_bot(ctx):
    if ctx.author.id != ALLOWED_USER_ID:
        return
    await ctx.send("📢 指定された3つのチャンネルへテスト送信を実行します...")
    joke = get_random_joke()
    await send_to_all_channels(content=f"ーー 【テスト配信】今日のおもしろ話 ーー\n{joke}")

# 🕶️ 「!組長からの挑戦」
@bot.command(name="組長からの挑戦")
async def boss_challenge(ctx):
    boss_quotes = [
        "組長「2度とオールしないと言って1日後にオールする今日この頃byおぼろん」",
        "組長「フッ…いい度胸だ。この俺にコマンドを打つとはな。…とりあえずお茶淹れてくれ。」",
        "組長「挑戦だと？ ならば次の動画のカット数を2倍にしてやろうかァ！？」",
        "組長「よくここまで辿り着いた。褒美として、ワイの厳選おもしろ話を授けよう。\n【悲報】ワイ、コンビニでドヤ顔でポイントカード出したらドラッグストアのやつだった。」"
    ]
    await ctx.send(random.choice(boss_quotes))

# 🚀 新機能：アップデート通知コマンド「!up」
@bot.command(name="up")
async def update_patch(ctx):
    # soma1586さん以外は実行できないようにロック
    if ctx.author.id != ALLOWED_USER_ID:
        return

    # ユーザーに変更内容を入力してもらう案内
    await ctx.send("📝 **アップデートパッチの内容を入力してください。**\n（例：自動送信の不具合修正、新コマンドの追加 など）")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        # ユーザーからのメッセージを待つ（制限時間2分）
        msg = await bot.wait_for("message", check=check, timeout=120.0)
        update_content = msg.content

        # 現在の年月を取得 (例: v2026-7)
        now = datetime.now(JST)
        version_str = f"v{now.year}-{now.month}"

        # 綺麗なリリースノート（Embed）を作成
        embed = discord.Embed(
            title="📢 lolbot リリースノート！",
            description=f"**バージョン:** `{version_str}`",
            color=discord.Color.green(),
            timestamp=now
        )
        embed.add_field(name="🛠️ アップデート内容", value=update_content, inline=False)
        embed.add_field(name="👤 変更者", value="soma1586", inline=False)
        embed.set_footer(text="lolbotは日々進化しています✊")

        # 3つのチャンネルに送信
        await send_to_all_channels(embed=embed)
        await ctx.send("✅ アップデートパッチをすべてのチャンネルに送信しました！")

    except TimeoutError:
        await ctx.send("❌ 時間切れです。もう一度 `!up` をやり直してください。")

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
