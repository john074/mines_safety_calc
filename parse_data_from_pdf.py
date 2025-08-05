import pdfplumber

def parse_egrul_pdf(pdf_path):
    data = {
        "full_name": None,
        "ogrn": None,
        "kpp": None,
        "reg_date": None,
        "address": None,
        "director": None,
    }

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            current_section = ""
            for row in table:
                if None not in data.values():
                    return data
                if row[1] == None:
                    if row[0] != "":
                        current_section = row[0].replace("\n", " ").strip()
                    continue
                elif row[1].replace("\n", " ").strip() == "Полное наименование на русском языке":
                    data["full_name"] = row[2].replace("\n", " ").strip()
                elif row[1].replace("\n", " ").strip() == "ОГРН":
                    data["ogrn"] = row[2].replace("\n", " ").strip()
                elif row[1].replace("\n", " ").strip() == "КПП юридического лица":
                    data["kpp"] = row[2].replace("\n", " ").strip()
                elif row[1].replace("\n", " ").strip() == "Дата присвоения ОГРН" or row[1].replace("\n", " ") == "Дата регистрации":
                    data["reg_date"] = row[2].replace("\n", " ").strip()
                elif row[1].replace("\n", " ").strip() == "Адрес юридического лица":
                    data["address"] = row[2].replace("\n", " ").strip()
                elif row[1].replace("\n", " ") == "Фамилия Имя Отчество" and current_section == "Сведения о лице, имеющем право без доверенности действовать от имени юридического лица":
                    data["director"] = row[2].replace("\n", " ").strip()
                elif row[1].replace("\n", " ") == "Должность" and current_section == "Сведения о лице, имеющем право без доверенности действовать от имени юридического лица":
                    data["director"] += f"({row[2].replace('\n', ' ').strip()})"
                elif row[1].replace("\n", " ") == "Полное наименование" and current_section == "Сведения о лице, имеющем право без доверенности действовать от имени юридического лица":
                    data["director"] = row[2].replace("\n", " ").strip()
    return data


def start(file):
    data = parse_egrul_pdf(file)
    for i in data:
        print(i, data[i])


for i in ["egrul_4207012578.pdf", "egrul_7710137066.pdf", "egrul_4205254853.pdf"]:
    start(i)
    print()
    print()
