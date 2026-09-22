import json
import os
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

STATUS_FILE = "status.txt"
OUTPUT_FILE = "data.json"

def update_status(dot_color, message):
    dots = {
        "green": "🟢",
        "blue": "🔵",
        "yellow": "🟡",
        "red": "🔴"
    }
    emoji = dots.get(dot_color, "⚪")
    log_line = f"{emoji} {message}\n"
    print(log_line.strip())
    with open(STATUS_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

def convert_to_numeric_bd_time(time_str):
    """সময়কে বাংলাদেশ সময় (UTC+6)-এ কনভার্ট করে সংখ্যাভিত্তিক ফরম্যাটে রূপান্তর করবে"""
    try:
        if "UTC" in time_str:
            clean_time_str = time_str.replace("UTC", "").strip()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    dt_utc = datetime.strptime(clean_time_str, fmt).replace(tzinfo=timezone.utc)
                    bd_time = dt_utc.astimezone(timezone(timedelta(hours=6)))
                    return bd_time.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
        return time_str
    except Exception:
        return time_str

def scrape_match_details():
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("✦ Phase 2: Detailed Scraper Initialized ✦\n")

    update_status("blue", "data.json থেকে লিঙ্কগুলো লোড করা হচ্ছে...")

    if not os.path.exists(OUTPUT_FILE):
        update_status("red", "ত্রুটি: data.json ফাইল পাওয়া যায়নি!")
        return

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        matches = json.load(f)

    if not matches:
        update_status("yellow", "সতর্কতা: ফাইলে কোনো লিঙ্ক নেই।")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    updated_matches = []

    for index, match in enumerate(matches, start=1):
        stream_link = match.get("streamLink", "")
        if not stream_link:
            continue

        update_status("blue", f"[{index}/{len(matches)}] পেজ ভিজিট করা হচ্ছে: {stream_link}")

        try:
            res = requests.get(stream_link, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # ১. ইভেন্ট টাইটেল সংগ্রহ
                event_title = ""
                small_heading = soup.find('div', class_='text-sm')
                if small_heading:
                    event_title = small_heading.get_text(strip=True)
                if not event_title:
                    event_title = "INTERNATIONAL CRICKET"

                # ২. লোগো এবং টিম নাম সংগ্রহ
                logo1, logo2 = "", ""
                team1_title, team2_title = "", ""

                images = soup.find_all('img')
                team_images = [img.get('src', '') for img in images if 'team' in img.get('src', '')]

                if len(team_images) >= 2:
                    logo1 = team_images[0]
                    logo2 = team_images[1]
                elif len(team_images) == 1:
                    logo1 = team_images[0]
                    logo2 = team_images[0]

                # স্লগ থেকে টিম নাম বের করা (যেমন /events/england-vs-sri-lanka)
                slug = stream_link.split("/events/")[-1]
                if "-vs-" in slug:
                    parts = slug.split("-vs-")
                    team1_title = parts[0].replace("-", " ").title()
                    team2_title = parts[1].replace("-", " ").title()

                # ৩. সময় এক্সট্রাক্ট করা
                raw_time_str = ""
                page_text = soup.get_text(separator=" ", strip=True)
                if "UTC" in page_text:
                    try:
                        parts = page_text.split("UTC")[0].split("at")
                        raw_time_str = parts[-1].strip() + " UTC"
                    except:
                        pass

                final_match_time = convert_to_numeric_bd_time(raw_time_str) if raw_time_str else ""

                # ৪. লাইভ স্ট্যাটাস চেক
                is_live = "live" in page_text.lower()

                match_entry = {
                    "eventTitle": event_title,
                    "matchTime": final_match_time,
                    "team1Logo": logo1,
                    "team2Logo": logo2,
                    "team1Title": team1_title,
                    "team2Title": team2_title,
                    "streamLink": stream_link,
                    "isHot": is_live
                }

                updated_matches.append(match_entry)
                update_status("green", f"সফল: {team1_title} vs {team2_title}")

            else:
                update_status("red", f"ফেইলড (স্ট্যাটাস: {res.status_code}): {stream_link}")
                updated_matches.append(match)

        except Exception as e:
            update_status("red", f"ত্রুটি: {str(e)}")
            updated_matches.append(match)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_matches, f, indent=4, ensure_ascii=False)

    update_status("green", "সকল ডেটা সফলভাবে প্রসেস করে data.json ফাইলে সেভ করা হয়েছে!")

if __name__ == "__main__":
    scrape_match_details()
