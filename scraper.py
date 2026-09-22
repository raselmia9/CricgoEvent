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
    """সময়কে বাংলাদেশ সময় (UTC+6)-এ কনভার্ট করে সংখ্যাভিত্তিক ফরম্যাটে (YYYY-MM-DD HH:MM:SS) রূপান্তর করবে"""
    try:
        # যদি পেজে UTC ফরম্যাট থাকে
        if "UTC" in time_str:
            clean_time_str = time_str.replace("UTC", "").strip()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    dt_utc = datetime.strptime(clean_time_str, fmt).replace(tzinfo=timezone.utc)
                    # বাংলাদেশ সময় (UTC +6)
                    bd_time = dt_utc.astimezone(timezone(timedelta(hours=6)))
                    # শুধুমাত্র সংখ্যাভিত্তিক ফরম্যাট (অতিরিক্ত কোনো লেখা ছাড়া)
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
                
                # ১. ইভেন্ট টাইটেল (যেমন: INTERNATIONAL CRICKET) নিখুঁতভাবে সংগ্রহ
                event_title = ""
                # পেজের ওপরের ক্যাটাগরি টেক্সট টার্গেট করা
                possible_titles = soup.find_all(['div', 'span', 'p', 'h3'])
                for tag in possible_titles:
                    txt = tag.get_text(strip=True)
                    if txt in ["INTERNATIONAL CRICKET", "DOMESTIC CRICKET", "T20 LEAGUE", "ODI SERIES", "TEST MATCH"]:
                        event_title = txt
                        break
                if not event_title:
                    # ফলব্যাক হিসেবে ওপরের প্রথম ছোট হেডিং
                    small_heading = soup.find('div', class_='text-sm')
                    if small_heading:
                        event_title = small_heading.get_text(strip=True)

                # ২. টিম লোগো এবং টিম নাম সুনির্দিষ্টভাবে সংগ্রহ
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

                # লোগোর ঠিক নিচের টেক্সট বা টিম নামগুলো বের করা
                # স্ক্রিনশট অনুযায়ী লোগোর নিচে টিমগুলোর নাম থাকে
                text_elements = soup.find_all(['div', 'span'])
                collected_teams = []
                for el in text_elements:
                    t = el.get(text=True, strip=True) if hasattr(el, 'get_text') else ""
                    # সাধারণ টিম নাম ফিল্টার (যেমন England, Sri Lanka ইত্যাদি)
                    if el.get('class') and any('text-' in c for c in el.get('class')):
                        txt = el.get_text(strip=True)
                        if txt and len(txt) <= 20 and txt not in ["LIVE", "VS", "vs", "Watch", event_title]:
                            if txt not in collected_teams and not txt.isdigit():
                                collected_teams.append(txt)

                # যদি সুনির্দিষ্ট টিম নাম না পাওয়া যায়, তবে স্ট্রিম লিংকের স্লগ থেকে নাম বের করা
                if len(collected_teams) >= 2:
                    team1_title = collected_teams[0]
                    team2_title = collected_teams[1]
                else:
                    # স্লগ যেমন /events/england-vs-sri-lanka থেকে নাম বের করা
                    slug = stream_link.split("/events/")[-1]
                    if "-vs-" in slug:
                        parts = slug.split("-vs-")
                        team1_title = parts[0].replace("-", " ").title()
                        team2_title = parts[1].replace("-", " ").title()

                # ৩. সময় এক্সট্রাক্ট করা এবং সংখ্যাভিত্তিক ফরম্যাটে রূপান্তর
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
                    "eventTitle": event_title if event_title else "INTERNATIONAL CRICKET",
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
