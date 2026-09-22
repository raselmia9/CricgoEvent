import json
import os
import re
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

def main():
    # স্ট্যাটাস ফাইল নতুন করে ইনিশিয়ালাইজ করা
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("✦ Scraper Initialized ✦\n")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # -------------------------------------------------------------
    # Phase 1: হোমপেজ থেকে ম্যাচ বা ইভেন্টের লিঙ্কগুলো সংগ্রহ করা
    # -------------------------------------------------------------
    update_status("blue", "হোমপেজ থেকে লাইভ ম্যাচ ও ইভেন্ট লিঙ্ক সংগ্রহ করা হচ্ছে...")
    base_url = "https://cricgo.pro/"
    match_links = []

    try:
        res = requests.get(base_url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href', '')
                if "/events/" in href:
                    full_link = href if href.startswith("http") else "https://cricgo.pro" + href
                    if full_link not in [m['streamLink'] for m in match_links]:
                        match_links.append({"streamLink": full_link})
            
            # সাময়িকভাবে লিঙ্কগুলো data.json এ সেভ করা
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(match_links, f, indent=4, ensure_ascii=False)
            update_status("green", f"মোট {len(match_links)} টি লিঙ্ক হোমপেজ থেকে সংগ্রহ করা হয়েছে।")
        else:
            update_status("red", f"হোমপেজ লোড করতে ব্যর্থ, স্ট্যাটাস কোড: {res.status_code}")
            return
    except Exception as e:
        update_status("red", f"হোমপেজ স্ক্রেপ করার সময় ত্রুটি: {str(e)}")
        return

    # -------------------------------------------------------------
    # Phase 2: প্রতিটি লিঙ্কে প্রবেশ করে বিস্তারিত ডেটা ও চ্যানেল সংগ্রহ করা
    # -------------------------------------------------------------
    if not os.path.exists(OUTPUT_FILE):
        update_status("red", "ত্রুটি: data.json ফাইল পাওয়া যায়নি!")
        return

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        matches = json.load(f)

    if not matches:
        update_status("yellow", "সতর্কতা: কোনো ম্যাচ লিঙ্ক পাওয়া যায়নি।")
        return

    updated_matches = []
    seen_links = set()

    for index, match in enumerate(matches, start=1):
        stream_link = match.get("streamLink", "")
        if not stream_link or stream_link in seen_links:
            continue
        seen_links.add(stream_link)

        update_status("blue", f"[{index}/{len(matches)}] পেজ ভিজিট করা হচ্ছে: {stream_link}")

        try:
            res = requests.get(stream_link, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # ১. ইভেন্ট টাইটেল সংগ্রহ
                event_title = "INTERNATIONAL CRICKET"
                small_heading = soup.find('div', class_='text-sm')
                if small_heading and small_heading.get_text(strip=True):
                    event_title = small_heading.get_text(strip=True)

                # ২. লোগো নিখুঁতভাবে সংগ্রহ (পূর্ণাঙ্গ লিংক সহ)
                images = soup.find_all('img')
                logos = []
                for img in images:
                    src = img.get('src', '')
                    if src:
                        if src.startswith('/'):
                            src = "https://cricgo.pro" + src
                        elif not src.startswith('http'):
                            src = "https://cricgo.pro/" + src
                        
                        if src not in logos:
                            logos.append(src)

                logo1, logo2 = "", ""
                team1_title, team2_title = "", ""

                if "asian-games" in stream_link:
                    event_title = "ASIAN GAMES 2026"
                    valid_logo = ""
                    for l in logos:
                        if 'team' in l or 'logo' in l or 'cdn' in l:
                            valid_logo = l
                            break
                    if not valid_logo and logos:
                        valid_logo = logos[0]
                    
                    logo1 = valid_logo
                    logo2 = valid_logo
                    team1_title = ""
                    team2_title = ""
                else:
                    team_logos = [l for l in logos if 'team' in l]
                    if len(team_logos) >= 2:
                        logo1 = team_logos[0]
                        logo2 = team_logos[1]
                    elif len(logos) >= 2:
                        logo1 = logos[0]
                        logo2 = logos[1]
                    elif len(logos) == 1:
                        logo1 = logos[0]
                        logo2 = logos[0]

                    slug = stream_link.split("/events/")[-1]
                    if "-vs-" in slug:
                        parts = slug.split("-vs-")
                        team1_title = parts[0].replace("-", " ").title()
                        team2_title = parts[1].replace("-", " ").title()

                # ৩. চ্যানেলের সঠিক নাম এবং মাল্টি-লিংক সংগ্রহ (ওয়াচ বা প্রতীক ফিল্টার করে)
                channels = []
                channel_rows = soup.find_all('a', href=True)
                
                for ch in channel_rows:
                    ch_text = ch.get_text(separator=" ", strip=True)
                    if "watch" in ch_text.lower():
                        # 'watch' শব্দের আগের অংশটুকু আলাদা করা
                        name_part = re.split(r'watch', ch_text, flags=re.IGNORECASE)[0]
                        # টিকমার্ক, তীরচিহ্ন ও অতিরিক্ত প্রতীকগুলো পরিষ্কার করা
                        name_part = re.sub(r'[✓↗\|\-\—\–]+', '', name_part).strip()
                        
                        if not name_part or len(name_part) < 2:
                            name_part = "Stream Link"
                        
                        ch_href = ch.get('href', '')
                        full_ch_link = ch_href if ch_href.startswith("http") else "https://cricgo.pro" + ch_href
                        
                        channel_obj = {
                            "channelName": name_part,
                            "channelLink": full_ch_link
                        }
                        
                        if channel_obj not in channels:
                            channels.append(channel_obj)

                # ৪. সময় এক্সট্রাক্ট করা
                raw_time_str = ""
                page_text = soup.get_text(separator=" ", strip=True)
                if "UTC" in page_text:
                    try:
                        parts = page_text.split("UTC")[0].split("at")
                        raw_time_str = parts[-1].strip() + " UTC"
                    except:
                        pass

                final_match_time = convert_to_numeric_bd_time(raw_time_str) if raw_time_str else ""
                is_live = "live" in page_text.lower()

                match_entry = {
                    "eventTitle": event_title,
                    "matchTime": final_match_time,
                    "team1Logo": logo1,
                    "team2Logo": logo2,
                    "team1Title": team1_title,
                    "team2Title": team2_title,
                    "streamLinks": channels,
                    "streamLink": stream_link,
                    "isHot": is_live
                }

                updated_matches.append(match_entry)
                update_status("green", f"সফল: {stream_link} (চ্যানেল পাওয়া গেছে: {len(channels)} টি)")

            else:
                update_status("red", f"ফেইলড (স্ট্যাটাস: {res.status_code}): {stream_link}")

        except Exception as e:
            update_status("red", f"ত্রুটি: {str(e)}")

    # চূড়ান্ত ফলাফল data.json এ সেভ করা
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_matches, f, indent=4, ensure_ascii=False)

    update_status("green", "সব কাজ সফলভাবে সম্পন্ন হয়েছে এবং data.json আপডেট করা হয়েছে!")

if __name__ == "__main__":
    main()
