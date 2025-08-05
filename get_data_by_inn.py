import requests
import time

def get_data(INN):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://egrul.nalog.ru/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    session = requests.Session()
    session.headers.update(HEADERS)

    # get cookies
    session.get("https://egrul.nalog.ru")

    # send INN
    response = session.post(
        "https://egrul.nalog.ru", 
        data={"query": INN, "captcha": "", "captchaToken": ""}
    )
    print(response)
    search_token = response.json()["t"]

    # get org data
    org_data = session.get(f"https://egrul.nalog.ru/search-result/{search_token}").json()
    if len(org_data["rows"]) > 0:
        org_name = org_data["rows"][0]["n"]
        download_token = org_data["rows"][0]["t"]
        print(f"Found: {org_name}")

        # make pdf
        pdf_request_url = f"https://egrul.nalog.ru/vyp-request/{download_token}?r=1&_={int(time.time() * 1000)}"
        pdf_response = session.get(pdf_request_url)
        
        # if not pdf make another request with new token
        if pdf_response.headers.get("Content-Type") != "application/pdf":
            new_token = pdf_response.json()["t"]
            pdf_url = f"https://egrul.nalog.ru/vyp-download/{new_token}"
            pdf_response = session.get(pdf_url)
        
        # save
        if pdf_response.headers.get("Content-Type") == "application/pdf":
            with open(f"egrul_{INN}.pdf", "wb") as file:
                file.write(pdf_response.content)
            print("DONE")
            
        else:
            print("ERR:")
            print(pdf_response.text)
    else:
        print("Org not found")


INN1 = "4205254853"
INN2 = "7710137066"
INN3 = "4207012578"

inns = [INN1, INN2, INN3]
for i in inns:
    get_data(i)
    time.sleep(1)
