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

def convert_to_bd_time(time_str):
    """ইউটিসি সময় বা অন্য ফরম্যাটকে বাংলাদেশ সময় (UTC+6)-এ কনভার্ট করার ফাংশন"""
    try:
        # যদি সময় স্ট্রিংয়ে UTC থাকে
        if "UTC" in time_str:
            clean_time_str = time_str.replace("UTC", "").strip()
            # বিভিন্ন ফরম্যাট হ্যান্ডেল করার জন্য
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    dt_utc = datetime.strptime(clean_time_str, fmt).replace(tzinfo=timezone.utc)
                    # বাংলাদেশ সময় (UTC +6)
                    bd_time = dt_utc.astimezone(timezone(timedelta(hours=6)))
                    return bd_time.strftime("%d %b %Y, %I:%M %p (BST)")
                except ValueError:
                    continue
        return time_str # কনভার্ট করা না গেলে যা আছে তাই রিটার্ন করবে
    except Exception:
        return time_str

def phase2_scrape_details():
    # স্ট্যাটাস ফাইল ইনিশিয়ালাইজ করা
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("✦ Phase 2: Detailed Pages Scraper Initialized ✦\n")

    update_status("blue", "প্রথম ধাপের data.json ফাইল থেকে লিঙ্কগুলো লোড করা হচ্ছে...")

    if not os.path.exists(OUTPUT_FILE):
        update_status("red", "ত্রুটি: data.json ফাইলটি পাওয়া যায়নি! আগে প্রথম ধাপ রান করুন।")
        return

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        existing_matches = json.load(f)

    if not existing_matches:
        update_status("yellow", "সতর্কতা: data.json ফাইলে কোনো লিঙ্ক নেই।")
        return

    update_status("blue", f"মোট {len(existing_matches)} টি ম্যাচ লিঙ্ক পাওয়া গেছে। বিস্তারিত তথ্য সংগ্রহ শুরু হচ্ছে...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    updated_matches_data = []

    for index, match in enumerate(existing_matches, start=1):
        stream_link = match.get("streamLink", "")
        if not stream_link:
            continue

        update_status("blue", f"[{index}/{len(existing_matches)}] ভিজিট করা হচ্ছে: {stream_link}")

        try:
            res = requests.get(stream_link, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # ১. ইভেন্ট টাইটেল (যেমন: INTERNATIONAL CRICKET) সংগ্রহ
                event_title = ""
                # স্ক্রিনশট অনুযায়ী ক্যাটাগরি হেডিং সাধারণত নির্দিষ্ট ট্যাগ বা ক্লাসে থাকে
                # আমরা পেজের ওপরের হেডিং বা নির্দিষ্ট এলিমেন্ট খুঁজব
                category_div = soup.find('div', class_='text-sm') or soup.find('span', class_='font-semibold')
                if category_div:
                    event_title = category_div.get_text(strip=True)
                else:
                    # অল্টারনেটিভ হিসেবে ওপরের দিকে থাকা টেক্সট চেক করা
                    h_tags = soup.find_all(['div', 'span', 'h3'])
                    for tag in h_tags:
                        txt = tag.get_text(strip=True)
                        if "CRICKET" in txt.upper() or "TOURNAMENT" in txt.upper():
                            event_title = txt
                            break

                # ২. টিম টাইটেল বা নাম সংগ্রহ (যেমন: England, Sri Lanka)
                team_names = []
                # লোগোর নিচের নামগুলো বা টিম সেকশন খোঁজা
                team_divs = soup.find_all('div', class_='text-center')
                for td in team_divs:
                    t_text = td.get_text(strip=True)
                    # টিমের নাম সাধারণত ছোট বা নির্দিষ্ট দৈর্ঘ্যের হয় এবং লাইভ বা সময় না
                    if t_text and len(t_text) < 25 and t_text not in ["LIVE", "VS", "vs"]:
                        if t_text not in team_names:
                            team_names.append(t_text)

                team1_title = team_names[0] if len(team_names) > 0 else ""
                team2_title = team_names[1] if len(team_names) > 1 else ""

                # ৩. লোগো সংগ্রহ (যদি প্রথম ধাপে খালি থাকে বা নতুন করে রি-ভেরিফাই করতে চাই)
                images = soup.find_all('img')
                logos = []
                for img in images:
                    src = img.get('src', '')
                    if 'team' in src and src not in logos:
                        logos.append(src)

                logo1 = match.get("team1Logo", "")
                logo2 = match.get("team2Logo", "")
                if not logo1 and len(logos) > 0:
                    logo1 = logos[0]
                if not logo2 and len(logos) > 1:
                    logo2 = logos[1]
                elif logo1 and not logo2:
                    logo2 = logo1 # সিঙ্গেল লোগো হলে উভয়টিতে সেম বসবে

                # ৪. ম্যাচ সময় এক্সট্রাক্ট করা এবং বাংলাদেশ টাইমে কনভার্ট করা
                raw_time_str = ""
                page_text = soup.get_text(separator=" ", strip=True)
                if "UTC" in page_text:
                    try:
                        # টেক্সট থেকে UTC সময় উদ্ধার করা
                        parts = page_text.split("UTC")[0].split("at")
                        raw_time_str = parts[-1].strip() + " UTC"
                    except:
                        pass
                
                # যদি সরাসরি নির্দিষ্ট ট্যাগ থেকে পাওয়া যায়
                match_time_final = convert_to_bd_time(raw_time_str) if raw_time_str else "15 Sept 2026, 11:30 pm" # ফলব্যাক বা ডিফল্ট

                # ৫. লাইভ স্ট্যাটাস চেক করা
                is_live = "live" in page_text.lower()

                # সম্পূর্ণ স্ট্রাকচার তৈরি করা
                detailed_match_entry = {
                    "eventTitle": event_title if event_title else "INTERNATIONAL CRICKET",
                    "matchTime": match_time_final,
                    "team1Logo": logo1,
                    "team2Logo": logo2,
                    "team1Title": team1_title,
                    "team2Title": team2_title,
                    "streamLink": stream_link,
                    "isHot": is_live
                }

                updated_matches_data.append(detailed_match_entry)
                update_status("green", f"সফলভাবে ডেটা এক্সট্রাক্ট করা হয়েছে: {team1Title} vs {team2Title}")

            else:
                update_status("red", f"লিংক ভিজিট ব্যর্থ হয়েছে (স্ট্যাটাস: {res.status_code}): {stream_link}")
                # ফেইল করলেও আগের ডেটা যাতে হারিয়ে না যায় তাই পুরনোটা রেখে দেব
                updated_matches_data.append(match)

        except Exception as e:
            update_status("red", f"ত্রুটি ঘটেছে {stream_link} এ: {str(e)}")
            updated_matches_data.append(match)

    # ফাইনাল ডাটা JSON ফাইলে সেভ করা
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_matches_data, f, indent=4, ensure_ascii=False)

    update_status("green", "পর্যায় ২ এর কাজ সফলভাবে শেষ! data.json আপডেট করা হয়েছে।")

if __name__ == "__main__":
    phase2_scrape_details()
