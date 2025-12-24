import requests
import gzip
import json
import pandas as pd

FILE = "OKVED_primer.xlsx"

def main():
    df = pd.read_excel(FILE)

    for idx, row in df.iterrows():
        inn = pick_inn(row)
        print(inn)
        if not inn:
            continue

        json_data = load_egrul_json(inn)
        if not json_data:
            continue

        okved = parse_okved(json_data)
        if not okved:
            continue

        df.at[idx, "Реквизит: ОКВЭД"] = okved

    df.to_excel(FILE, index=False)


def pick_inn(row):
    for col in ("Реквизит: ИНН", "ИНН_1", "ИНН_2"):
        val = row.get(col)

        if pd.isna(val):
            continue
        if isinstance(val, float):
            val = str(int(val))

        val = str(val).strip()
        if val.isdigit() and len(val) in (10, 12):
            return val

    return None

def load_egrul_json(inn):
    url = f"https://egrul.itsoft.ru/{inn}.json.gz"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        try:
            data = gzip.decompress(r.content)
            return json.loads(data)
        except gzip.BadGzipFile:
            return r.json()

    except Exception:
        return None


def parse_okved(data):
    try:
        key = "СвИП" if "СвИП" in data.keys() else "СвЮЛ"
        okved = (
            data[key]
            ["СвОКВЭД"]
            ["СвОКВЭДОсн"]
            ["@attributes"]
        )
        code = okved.get("КодОКВЭД")
        name = okved.get("НаимОКВЭД")

        if code and name:
            return f"{code} {name}"
    except KeyError:
        pass

    return None

main()
