import requests
import gzip
import json

def get_data(INN):
    url = f"https://egrul.itsoft.ru/{INN}.json.gz"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    try:
        raw = gzip.decompress(response.content)
        data = json.loads(raw)
    except gzip.BadGzipFile:
        data = response.json()

    return parse_egrul_json(data)


def parse_egrul_json(data):
    result = {
        "name": None,
        "ogrn": None,
        "kpp": None,
        "address": None,
    }

    try:
        ul = data["СвЮЛ"]
        attrs = ul["@attributes"]
        result["ogrn"] = attrs.get("ОГРН")
        result["kpp"] = attrs.get("КПП")

        result["name"] = (ul.get("СвНаимЮЛ", {}).get("@attributes", {}).get("НаимЮЛПолн"))
        result["address"] = parse_address(ul)
        print(result["address"])

    except KeyError:
        return "Ошибка структуры данных ЕГРЮЛ"

    return result


def parse_address(svul):
    # --- ФИАС формат ---
    fias = svul.get("СвАдресЮЛ", {}).get("СвАдрЮЛФИАС")
    if fias:
        parts = []

        region = fias.get("НаимРегион")
        if region:
            parts.append(region)

        city = fias.get("НаселенПункт", {}).get("@attributes")
        if city:
            parts.append(f"{city.get('Вид', '')}. {city.get('Наим', '')}".strip())

        street = fias.get("ЭлУлДорСети", {}).get("@attributes")
        if street:
            parts.append(f"{street.get('Тип', '')}. {street.get('Наим', '')}".strip())

        building = fias.get("Здание", {}).get("@attributes")
        if building:
            parts.append(f"{building.get('Тип', '')} {building.get('Номер', '')}".strip())

        room = fias.get("ПомещЗдания", {}).get("@attributes")
        if room:
            parts.append(f"{room.get('Тип', '')} {room.get('Номер', '')}".strip())

        return ", ".join(parts) if parts else None

    # --- Старый формат ---
    addr = svul.get("СвАдресЮЛ", {}).get("АдресРФ")
    if addr:
        parts = []

        region = addr.get("Регион", {}).get("@attributes", {}).get("НаимРегион")
        if region:
            parts.append(region)

        city = addr.get("Город", {}).get("@attributes")
        if city:
            parts.append(f"{city.get('ТипГород', '')} {city.get('НаимГород', '')}".strip())

        street = addr.get("Улица", {}).get("@attributes")
        if street:
            parts.append(f"{street.get('ТипУлица', '')} {street.get('НаимУлица', '')}".strip())

        house = addr.get("@attributes", {}).get("Дом")
        if house:
            parts.append(house)

        return ", ".join(parts) if parts else None

    return None

