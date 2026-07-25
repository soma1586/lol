from datetime import datetime
import pytz

JST = pytz.timezone("Asia/Tokyo")

# 季節・行事イベント用のメッセージ定義
SEASONAL_EVENTS = {
    (1, 1): "元日",
    (2, 14): "バレンタインデー",
    (4, 1): "エイプリルフール",
    (10, 31): "ハロウィン",
    (12, 24): "クリスマス",
    (12, 25): "クリスマス",
}

EVENT_MESSAGES = {
    "元日": "🎍 あけましておめでとうございます！今年もたくさんの笑いをお届けします！",
    "バレンタインデー": "🍫 バレンタインデー！チョコよりも甘〜い（？）おもしろ話をお届け！",
    "エイプリルフール": "🃏 エイプリルフール！今日のお話は……もしかしたら全部嘘かも！？",
    "ハロウィン": "🎃 トリックオアトリート！お菓子をくれないタダでは済まさないぞ！",
    "クリスマス": "🎄 メリークリスマス！聖なる夜に笑いのプレゼントをお届け！",
}

def get_seasonal_event_message(month=None, day=None):
    """指定日付（未指定なら現在日付）のイベントメッセージを返す"""
    if month is None or day is None:
        now = datetime.now(JST)
        month, day = now.month, now.day
        
    event_name = SEASONAL_EVENTS.get((month, day))
    if event_name:
        return EVENT_MESSAGES.get(event_name)
    return None
