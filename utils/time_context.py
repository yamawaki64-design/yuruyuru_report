from datetime import datetime


def get_time_context() -> str | None:
    """
    現在の時刻・曜日を判定してコンテキスト文字列を返す。
    平日18時未満は通常モードのためNoneを返す。
    """
    now = datetime.now()
    is_weekend = now.weekday() >= 5  # 5=土, 6=日

    if is_weekend:
        return "今日は休日なんだからこれ終わったら休んで。"
    elif now.hour >= 18:
        return f"もう{now.hour}時だ。定時も過ぎてるし早く帰るように。"
    return None
