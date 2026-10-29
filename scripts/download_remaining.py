"""
Reliable Downloader for Remaining Stitch Screens
"""
import os
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_DIR, "web", "stitch_assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
SCREENS_DIR = os.path.join(ASSETS_DIR, "screens_code")

REMAINING_SCREENS = [
    {
        "id": "4206c636ea324ca1a24b0f02cd813fe3",
        "title": "Project_Overview",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLtM_nWPDs1i1MU2mpwpKcl7bUtqXXMWCg70cTuVlhsRWVip2KCgFvdc2FpGi433wVGqProivOZQsUp1efaxxZlkaDJfIi_V81-IUk7vAASWWNdZg5OPgEguRXjfUXtykVcTZW-F0yUbyNjAsopneuPFWSkrRwWVVbGa_RUzKHzQFWqcprgNM9XOokom9qabLHqzBBvclQfXd_HL7a_KwuompA1quowpfMKWWmIyVUTXABiHQMnT7YTBHQ",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTc1MGM2MTM5ZjEwOTEwN2M1Y2I2MTVlMDFjEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086"
    },
    {
        "id": "787196f7bd814c8d959b2e7ad6ed24df",
        "title": "Compliance_Reporting",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLtMVH71bPcBvq8O-aqA1Zfpl-sZ-o4Qdr8fjWhMCtGbTzCK_R_hniaATXsDrugIPubCy13YbR4nWHkzBFdff6OdWgK1uUA-x4xg8JnujpXAK2x-a3jOUPQXU9WmSb2BXaorwD0_YSinKEH1Vn8DYC1ZJrTWbb0JjCZuPWoc8eJbCyB3Vs6iTQT-thXnXEiTnpw_GxvaQeiTd-EXHseznhEIBN637AsKmgkpSCnI34OnP-XX0ywWhHe_Ew",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZDc4Mzg5N2IwOTI1ZDU5YmFlMDc2Mjc2EgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086"
    },
    {
        "id": "9223df06be3b40638d9004ca27f0f906",
        "title": "Privacy_Validation",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLtzwkJ1scyFAkakjuy7rw6OSIgwKoZxTvCyVM5fQhn2VlqQVUQLybWUWpmcXRk7AfUgclQ_l9a-HJjtH9WYH47SXuc_0ymZ8hrVfuzIN6j_SKdqjpHqs12iSBNqU5Mz53cuRkVbeI2XwJLBYfPCWSEnmJTAryWEOYVdxhkEdkZDr_6oswtg4qlujcbTzvCc_Mvlw4PPZunUdpfcAf3wIqDiVTI8eXtk_MzdTn5w7GwwFrLhgOSxxfdTGg",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2Y2FhZGUwZGQwMjJkNGVjNDY2MDk0ODVjEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086"
    },
    {
        "id": "afab65ca44ff4774875e25acada472db",
        "title": "Results_and_Export_Mobile",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLsYY_zuazsmPUB1GSt4hAq3Crfl-OXcSVApVs3UwT5hWUwKA4BTpHilOa7BAvQRjTDsDMhFzACOiaHQ8k2_4xiXeneKZrHcHZDFxjiMmAp_Qn54XU9ExPOmY_wVRfDs5vIezkSwvaRlDsLWc3qb1GBBzAn9NGsDU8KfLPeqADm1RSn8JPEcCQniWH8wjNN88WFBX-GgtFprWNrIVAYOxgIYcVdQPxl6cWUCd6ie5ZP8WVqx22uhmLX5PQ",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZWIzYTQxYmMwODlhZjUxMGQ5MTk2YTczEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086"
    },
    {
        "id": "1b2228a467124cabb6a940a7be57c7b4",
        "title": "Adversarial_Playground",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLuM64LTSbJwAIKQny6ENWHvKzlQVsijoLLL6QEuWcZOrvzdS6LwKzA1p38bR8EH2cZSl7vmwIfTOYCPrtjcNCE5YhXIqfn7q2CHQwsFkMS26h3HxgGv6hXUYmtJGhTXNf5MBAIJQ2xosRPY7R9NELHjtyhfHGKo2rdGAGQBe4MloFaEvn32-Lw4wHG2Zct7au2BajdUO6oSVc7zUwPlZYQsQ4_72b51lCMYCTFuSYvlnV_svcL8S96OFg",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZGRhMGYzNzgwOTI1ZDRlZGFiMjBlNWQyEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086"
    }
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for item in REMAINING_SCREENS:
    html_f = os.path.join(SCREENS_DIR, f"{item['id']}_{item['title']}.html")
    img_f = os.path.join(IMAGES_DIR, f"{item['id']}_{item['title']}.png")

    print(f"[*] Downloading {item['title']}...")
    if not os.path.exists(html_f):
        for attempt in range(3):
            try:
                req = urllib.request.Request(item["html_url"], headers=headers)
                with urllib.request.urlopen(req, timeout=30) as r, open(html_f, "wb") as out:
                    out.write(r.read())
                print(f"  -> Saved HTML: {os.path.basename(html_f)}")
                break
            except Exception as e:
                print(f"  -> Attempt {attempt+1} HTML error: {e}")
                time.sleep(2)

    if not os.path.exists(img_f):
        for attempt in range(3):
            try:
                req = urllib.request.Request(item["img_url"], headers=headers)
                with urllib.request.urlopen(req, timeout=30) as r, open(img_f, "wb") as out:
                    out.write(r.read())
                print(f"  -> Saved PNG: {os.path.basename(img_f)}")
                break
            except Exception as e:
                print(f"  -> Attempt {attempt+1} Image error: {e}")
                time.sleep(2)

print("\nDone downloading remaining assets!")
