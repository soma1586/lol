from datetime import datetime
import pytz

JST = pytz.timezone("Asia/Tokyo")

# 季節・行事イベント用のメッセージ定義
SEASONAL_EVENTS = {
    (1, 1): "🎍 あけましておめでとうございます！今年もたくさんの笑いをお届けします！",
    (2, 14): "🍫 バレンタインデー！チョコよりも甘〜い（？）おもしろ話をお届け！",
    (4, 1): "🃏 エイプリルフール！今日のお話は……もしかしたら全部嘘かも！？",
    (10, 31): "🎃 トリックオアトリート！お菓子をくれないタダでは済まさないぞ！",
    (12, 24): "🎄 メリークリスマス・イブ！聖なる夜に笑いのプレゼント！",
    (12, 25): "🎁 メリークリスマス！今日も楽しく過ごそう！",
}

def get_seasonal_event_message():
    """今日が特定のイベント日であれば、そのメッセージを返す"""
    now = datetime.now(JST)
    key = (now.month, now.day)
    return SEASONAL_EVENTS.get(key, None)
