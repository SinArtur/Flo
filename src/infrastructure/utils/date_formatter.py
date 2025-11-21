from datetime import date

MONTH_NAMES = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


def format_date_russian(d: date) -> str:
    """Format date in Russian format: '15 декабря 2024'"""
    return f"{d.day} {MONTH_NAMES[d.month]} {d.year}"

