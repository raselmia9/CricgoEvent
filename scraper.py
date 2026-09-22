import json
import os
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

def scrape_cricgo():
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("✦ CricGo Match Cards Scraper Initialized ✦\n")

    update_status("blue", "হোমপেজ থেকে ম্যাচ কার্ডগুলোর ডেটা সঠিকভাবে পার্স করা হচ্ছে...")

    url = "https://cricgo.pro/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    matches_data = []

    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            update_status("green", "হোমপেজ সফলভাবে লোড হয়েছে!")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.find_all('a', href=True)
            
            valid_cards = []
            for card in cards:
                href = card.get('href', '')
                if '/events/' in href or '/match/' in href:
                    if card not in valid_cards:
                        valid_cards.append(card)

            update_status("blue", f"মোট {len(valid_cards)} টি কার্ড প্রসেস করা হচ্ছে...")

            for card in valid_cards:
                full_text = card.get_text(separator=" ", strip=True)
                
                # লোগো সংগ্রহ করা
                images = card.find_all('img')
                logo1 = ""
                logo2 = ""
                if len(images) == 1:
                    logo1 = images[0].get('src', '')
                elif len(images) >= 2:
                    logo1 = images[0].get('src', '')
                    logo2 = images[1].get('src', '')

                # ১. প্রথমে টাইম এবং লাইভ স্ট্যাটাস অংশটুকু আলাদা করে ফেলা
                # যেমন: "England vs Sri Lanka England vs Sri Lanka Live at 2026-09-15 17:30:00 UTC"
                clean_base = full_text
                for word in ["LIVE", "Starting Soon", "UTC"]:
                    clean_base = clean_base.replace(word, "")
                
                if " at " in clean_base:
                    event_part = clean_base.split(" at ")[0].strip()
                else:
                    event_part = clean_base.strip()

                # ২. ডাবল টেক্সট দূর করা (যেমন একই নাম দুইবার থাকলে মাঝখান থেকে কেটে একবার করা)
                length = len(event_part)
                half = length // 2
                if length > 10 and event_part[:half].strip().lower() == event_part[half:].strip().lower():
                    event_title = event_part[:half].strip()
                else:
                    # যদি হুবহু দুই ভাগ না হয়, তবে 'vs' এর আগের অংশ দুইবার থাকলে তা ঠিক করা
                    if " vs " in event_part.lower():
                        parts = event_part.split(" vs ")
                        if len(parts) >= 2 and parts[0].strip().lower() == parts[1].strip().lower()[:len(parts[0])]:
                            event_title = parts[0].strip() + " vs " + parts[1].strip().replace(parts[0].strip(), "").strip()
                        else:
                            event_title = event_part
                    else:
                        event_title = event_part

                # পরিষ্কার ইভেন্ট টাইটেল থেকে "vs" বা "VS" এর ভিত্তিতে টিম ওয়ান ও টিম টু টাইটেল আলাদা করা
                team1_title = ""
                team2_title = ""
                
                # কেস-সেন্সিটিভ সমস্যা এড়াতে ছোট হাতের করে ইনডেক্স বের করা
                lower_title = event_title.lower()
                if " vs " in lower_title:
                    idx = lower_title.find(" vs ")
                    team1_title = event_title[:idx].strip()
                    team2_title = event_title[idx + 4:].strip() # " vs " এর পরের অংশ
                else:
                    team1_title = event_title

                # ম্যাচ টাইম নিখুঁতভাবে এক্সট্রাক্ট করা
                match_time = ""
                if "at" in full_text:
                    try:
                        # "2026-09-15 17:30:00 UTC" ফরম্যাট বের করা
                        parts_time = full_text.split("at")
                        raw_time = parts_time[1].strip()
                        if "UTC" in raw_time:
                            match_time = raw_time.split("UTC")[0].strip() + " UTC"
                        else:
                            match_time = raw_time
                    except:
                        match_time = ""

                is_live = "live" in full_text.lower()

                match_entry = {
                    "eventTitle": event_title,
                    "matchTime": match_time,
                    "team1Logo": logo1,
                    "team2Logo": logo2,
                    "team1Title": team1_title,
                    "team2Title": team2_title,
                    "streamLink": card.get('href', ''),
                    "isHot": is_live
                }
                
                if match_entry not in matches_data and event_title:
                    matches_data.append(match_entry)

            if not matches_data:
                update_status("yellow", "সতর্কতা: কোনো ম্যাচ ডেটা পাওয়া যায়নি।")
            else:
                update_status("green", f"সফলভাবে {len(matches_data)} টি কার্ডের ডেটা প্রসেস করা হয়েছে!")

            # JSON ফাইলে সেভ করা
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(matches_data, f, indent=4, ensure_ascii=False)
                
            update_status("green", "সংশোধিত ডেটা সফলভাবে data.json ফাইলে সেভ করা হয়েছে!")

        else:
            update_status("red", f"সার্ভার এরর: স্ট্যাটাস কোড {response.status_code}")

    except Exception as e:
        update_status("red", f"ত্রুটি ঘটেছে: {str(e)}")

if __name__ == "__main__":
    scrape_cricgo()
