"""
Stitch Screens and Assets Downloader for DP-Synth Health
========================================================
Downloads all 13 Stitch screens HTML code and preview screenshots.
"""

import os
import sys
import json
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_DIR, "web", "stitch_assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
SCREENS_DIR = os.path.join(ASSETS_DIR, "screens_code")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(SCREENS_DIR, exist_ok=True)

SCREENS_DATA = [
    {
        "id": "4206c636ea324ca1a24b0f02cd813fe3",
        "title": "DP-Synth Health | Project Overview",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLtM_nWPDs1i1MU2mpwpKcl7bUtqXXMWCg70cTuVlhsRWVip2KCgFvdc2FpGi433wVGqProivOZQsUp1efaxxZlkaDJfIi_V81-IUk7vAASWWNdZg5OPgEguRXjfUXtykVcTZW-F0yUbyNjAsopneuPFWSkrRwWVVbGa_RUzKHzQFWqcprgNM9XOokom9qabLHqzBBvclQfXd_HL7a_KwuompA1quowpfMKWWmIyVUTXABiHQMnT7YTBHQ",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTc1MGM2MTM5ZjEwOTEwN2M1Y2I2MTVlMDFjEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "DESKTOP"
    },
    {
        "id": "787196f7bd814c8d959b2e7ad6ed24df",
        "title": "DP-Synth Health | Compliance Reporting",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLtMVH71bPcBvq8O-aqA1Zfpl-sZ-o4Qdr8fjWhMCtGbTzCK_R_hniaATXsDrugIPubCy13YbR4nWHkzBFdff6OdWgK1uUA-x4xg8JnujpXAK2x-a3jOUPQXU9WmSb2BXaorwD0_YSinKEH1Vn8DYC1ZJrTWbb0JjCZuPWoc8eJbCyB3Vs6iTQT-thXnXEiTnpw_GxvaQeiTd-EXHseznhEIBN637AsKmgkpSCnI34OnP-XX0ywWhHe_Ew",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZDc4Mzg5N2IwOTI1ZDU5YmFlMDc2Mjc2EgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "DESKTOP"
    },
    {
        "id": "9223df06be3b40638d9004ca27f0f906",
        "title": "DP-Synth Health | Privacy Validation",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLtzwkJ1scyFAkakjuy7rw6OSIgwKoZxTvCyVM5fQhn2VlqQVUQLybWUWpmcXRk7AfUgclQ_l9a-HJjtH9WYH47SXuc_0ymZ8hrVfuzIN6j_SKdqjpHqs12iSBNqU5Mz53cuRkVbeI2XwJLBYfPCWSEnmJTAryWEOYVdxhkEdkZDr_6oswtg4qlujcbTzvCc_Mvlw4PPZunUdpfcAf3wIqDiVTI8eXtk_MzdTn5w7GwwFrLhgOSxxfdTGg",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2Y2FhZGUwZGQwMjJkNGVjNDY2MDk0ODVjEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "DESKTOP"
    },
    {
        "id": "afab65ca44ff4774875e25acada472db",
        "title": "DP-Synth Health | Results & Export (Mobile)",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLsYY_zuazsmPUB1GSt4hAq3Crfl-OXcSVApVs3UwT5hWUwKA4BTpHilOa7BAvQRjTDsDMhFzACOiaHQ8k2_4xiXeneKZrHcHZDFxjiMmAp_Qn54XU9ExPOmY_wVRfDs5vIezkSwvaRlDsLWc3qb1GBBzAn9NGsDU8KfLPeqADm1RSn8JPEcCQniWH8wjNN88WFBX-GgtFprWNrIVAYOxgIYcVdQPxl6cWUCd6ie5ZP8WVqx22uhmLX5PQ",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZWIzYTQxYmMwODlhZjUxMGQ5MTk2YTczEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "MOBILE"
    },
    {
        "id": "1b2228a467124cabb6a940a7be57c7b4",
        "title": "DP-Synth Health | Adversarial Playground",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLuM64LTSbJwAIKQny6ENWHvKzlQVsijoLLL6QEuWcZOrvzdS6LwKzA1p38bR8EH2cZSl7vmwIfTOYCPrtjcNCE5YhXIqfn7q2CHQwsFkMS26h3HxgGv6hXUYmtJGhTXNf5MBAIJQ2xosRPY7R9NELHjtyhfHGKo2rdGAGQBe4MloFaEvn32-Lw4wHG2Zct7au2BajdUO6oSVc7zUwPlZYQsQ4_72b51lCMYCTFuSYvlnV_svcL8S96OFg",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZGRhMGYzNzgwOTI1ZDRlZGFiMjBlNWQyEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "DESKTOP"
    },
    {
        "id": "50a4298e13bc4c22bb855a2cb9d4bf8b",
        "title": "DP-Synth Health | Generation Config",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLvKlb9BiKv8eBpiq6CT_WAd75BkjYFTdIDWpFFy6wbCvKNAKlBDTTqRTgr5DjpS_XUCDbk2LkIBqhsrjSqCgW1NK-OqLL7NzWbd9L_pV6DVK_MijkfXJnDRfycpL2wKlvxNWbI-Pf9Gbj_PcsI4eP5QzMv3zcoikikqW_JBHkzYl8w30tnOlj_z6bdyW-wWsIctJ8V1n8GzxPQoQk2Hq1e-y9JfA7tA_fC5axMIdMLVlqXPc3T0mYq_eQ",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2Y2FiOWExMjIwMWI0ZTc2NzdlMTI3NGM5EgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "DESKTOP"
    },
    {
        "id": "0b81e812882c48ddbeb6103b20f8da72",
        "title": "DP-Synth Health | Ensemble Orchestration",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLvRX1o8iVXc_mrlcLLpTx3nCO4rRdnP_wiedqPJr3lT_kqgTuplI0WNUYGQFTGauOx6VovNquD29NQcXTL9SUepsCHBptpjqOGl3U7eyMbIPvfDxGT2HbpUjSs2qmTE4ARlueKdID-_jT5K5S8KhGn7mNek_ABSV1sqlVSYS-EGtcSzfUUB4T062gwJqsaio-zKC16mlhtJLOVH1xr3sdVCsOrtyEwOOX1g10vGjWAii1h38RqZJxaVXg",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZDI1MzFjNTYwODlhZjUxMGQ5MTk2YTczEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "DESKTOP"
    },
    {
        "id": "883886c19dcd491386d3e5f01381d20b",
        "title": "DP-Synth Health | Mobile Dashboard",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLtDI1i2lCmtnxLOhFo30w-52O365YWPI9OPNmOtB3xj0-GOHUk--Xa9evaodPW1CV1WbfL7b7VdyFsKoQagpohBucXf_-lFd8QPm5U6MaefGRhBJxHKdMWc6wGvLHuaNtIbKrqxfL-IjsXXjzKckvSNvgH9gAakRm_KjzC277kLOmoIf8LvxdeI9HS_OJwxg3I14DCoUfHg4BzHCLuaf2Dt-50GGA80B6eFHnR3CYYU9Xei6btVgCBCKw",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZTFkYTdjYmMwODlhZjUxMGQ5MTk2YTczEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "MOBILE"
    },
    {
        "id": "5ed913b006a741c5b259601f31002f49",
        "title": "DP-Synth Health | Utility Validation",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLsE8v1BZtDkMOiizw24aonu0cHvJ3K3ywcKqwhhGYLd8oZ5MkxCqJtlYOdsoxsPqKiPTfWr0mynShDsdr-k1lVNTjpVkr_bC2y2tlq9TfHqNpJkxJXQqUyynDwu1Ik8H0UfPjzoIQ_C3Zf2bsprF6zwsZk6OLgUrUuSoutbHcqAl7XNucELJcaDSoTel_-Yp45AWVT1JNOcgvud9QEm8ATMnokd_4eU52Tps86hAqxW73Ixn8voxiIB",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTc1MGRjMGU5ODgwNzc5ODM5NGNkMzgzZWVkEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "DESKTOP"
    },
    {
        "id": "4bf2b27235b2456a85a56d1c53491b75",
        "title": "DP-Synth Health | Results & Export",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLuT3Z1jF9ItHAoE0ga6XQUwK5g8S0ld5mArvp6I5WcTPTbjyIFUvqL2-UjAH_JOqgQx8m_EcIPK3Piz0GOaNalajZus6IylljR_n_xM0fmtBc3KDsfMfbgsjU2modM9OqZPmviTm3t6jvaAXfFTf4NaTP3RHNOSxf6p6EEzDOAAnLIgFb1ZyMezM5tgT6AfY235J2bnZYxwAYc9FaH1Lw5Y0m1rsgpoqivfUBXqtolPNohWb2NLtdDvqw",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2Y2E5ZTZiMzUwNmYxYzliYzllMGVmMTIyEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "DESKTOP"
    },
    {
        "id": "d0428a3aefb74021b94c293304c585c4",
        "title": "DP-Synth Health | Alert Details",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLsBsnvTu6av71dbUZGITd7oBDjcBoYNvBSN03eACmnwB_HNoWhhaPZAt2Y1KvoZb2nQjoX9UyaiAyXDtEuWSWXR6u5ZiZPnV6PuwXJuZ5rYI2cORtvgRdgtsoyJiUz-EWwsO-MHq2aUIaZISy6Fqvn2EHtJgAZnyAawqkZszZfGVGLZ0K6RBZJ46llVM4ArYj2JPhR47jZR8xGvu3H4SU840f5VEQXnIqmwYU3WkZlmavyzQlodxjUOhA",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZTcyMGFiODcwNmYxYzliYzllMGVmMTIyEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "MOBILE"
    },
    {
        "id": "d58cc89bffa2431aa9731fb1b2452517",
        "title": "DP-Synth Health | Security Settings",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLvpkNTXDVg2ll4OeRa8DhgjQpBfISNaU1zltneEUX7GppCABoPYK4lfyl6YrSKMIzshic4hMaTcyguYWenRajdCHYV8SueVtGz4LOHa5GtpdFbcq-1RmTs4LR-Mtn_JTcq3WXZBtrzZeuhXMoEnTao8t0Jtob3tq1JvHxmWdzsS-SQNXPtHBGqEa8fB6GlEcJA2ALhOhc4TnorYL-lZsU1dLwuFqRGc6lVEM5ejM0Gmv4vpGfq3HUWzrw",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZTYwMzFhOWMwMWE2MzE2OGQ3MjA4NGMxEgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "MOBILE"
    },
    {
        "id": "8733f747543e4b6eb53613ac2918005b",
        "title": "DP-Synth Health | Ensemble Orchestration (Mobile)",
        "img_url": "https://lh3.googleusercontent.com/aida/AP1WRLuy-kNeXwBA4fPajUBNGktEQ-X36Halu47D5HcbTp8RktQdz6iXoWN9y14Mt-FYqrkxZqAVjQG0AKizn3QykfLsrv72CAvuSHtZaD6bRBALqAqdfmgqUtsXW5SHUnNg_NiDMWdidlElG-ClWTD_z_CCRh-8yxORilF3jpd_zvy5DHvsGstym6KHpOvJkFyGu3aQspEryBgLaaEnjuTCPI0LSgUNrFVGgX-Fo2lO8DSANgJRK6YIvuaO",
        "html_url": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1OTg2ZWZiMDU4NGMwMzM4NWM4Nzg2MWJjZjM3EgsSBxDegcztshgYAZIBIgoKcHJvamVjdF9pZBIUQhI1ODAyODg1MDUwNTc3MzQyNzI&filename=&opi=89354086",
        "device": "MOBILE"
    }
]


def download_all_assets():
    print("==================================================")
    print("🚀 Downloading Stitch Screens & Assets for DP-Synth Health")
    print("==================================================")

    manifest = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for idx, screen in enumerate(SCREENS_DATA, 1):
        clean_title = screen["title"].replace("DP-Synth Health | ", "").replace(" ", "_").replace("&", "and").replace("(", "").replace(")", "").replace("/", "_")
        img_filename = f"{screen['id']}_{clean_title}.png"
        html_filename = f"{screen['id']}_{clean_title}.html"

        img_path = os.path.join(IMAGES_DIR, img_filename)
        html_path = os.path.join(SCREENS_DIR, html_filename)

        print(f"[{idx:02d}/13] Downloading: {screen['title']} ({screen['device']})...")

        # Download Screenshot Image
        if screen.get("img_url"):
            try:
                req = urllib.request.Request(screen["img_url"], headers=headers)
                with urllib.request.urlopen(req, timeout=30) as resp, open(img_path, "wb") as out:
                    out.write(resp.read())
                print(f"  -> Saved Preview: {img_filename}")
            except Exception as e:
                print(f"  -> [Warning] Image download error: {e}")

        # Download HTML Code
        if screen.get("html_url"):
            try:
                req = urllib.request.Request(screen["html_url"], headers=headers)
                with urllib.request.urlopen(req, timeout=30) as resp, open(html_path, "wb") as out:
                    out.write(resp.read())
                print(f"  -> Saved HTML: {html_filename}")
            except Exception as e:
                print(f"  -> [Warning] HTML download error: {e}")

        manifest.append({
            "id": screen["id"],
            "title": screen["title"],
            "device": screen["device"],
            "image_file": img_filename,
            "html_file": html_filename
        })

    manifest_path = os.path.join(ASSETS_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n==================================================")
    print(f"✅ STITCH DOWNLOAD COMPLETE: 13/13 Screens Saved")
    print(f"   Manifest: {manifest_path}")
    print("==================================================")


if __name__ == "__main__":
    download_all_assets()
