from datetime import datetime
def parse_date(date_str):
    if date_str:
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.000Z')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"❌ Date parse error: {e}")
            return None
    return None