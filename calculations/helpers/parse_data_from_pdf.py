import pdfplumber

def parse_egrul_pdf(pdf_path):
    data = {
        "name": None,
        "ogrn": None,
        "kpp": None,
        "address": None,
    }

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            for row in table:
                if None not in data.values():
                    return data
                if row[1] == None:
                    continue
                elif row[1].replace("\n", " ").strip() == "Полное наименование на русском языке":
                    data["name"] = row[2].replace("\n", " ").strip()
                elif row[1].replace("\n", " ").strip() == "ОГРН":
                    data["ogrn"] = row[2].replace("\n", " ").strip()
                elif row[1].replace("\n", " ").strip() == "КПП юридического лица":
                    data["kpp"] = row[2].replace("\n", " ").strip()
                elif row[1].replace("\n", " ").strip() == "Адрес юридического лица":
                    data["address"] = row[2].replace("\n", " ").strip()
    return data

