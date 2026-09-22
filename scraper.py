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

    update_status("blue", "হোমপেজ থেকে ম্যাচ কার্ডগুলোর ডেটা নিখুঁতভাবে সংগ্রহ করা হচ্ছে...")

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
                
                # লোগোগুলো সংগ্রহ করা
                images = card.find_all('img')
                logo1 = ""
                logo2 = ""
                if len(images) == 1:
                    # যদি একটিমাত্র লোগো থাকে (যেমন টুর্নামেন্ট লোগো)
                    logo1 = images[0].get('src', '')
                elif len(images) >= 2:
                    # যদি দুটি টিম লোগো থাকে
                    logo1 = images[0].get('src', '')
                    logo2 = images[1].get('src', '')

                # ইভেন্ট টাইটেল ডাবল আসা রোধ করে পরিচ্ছন্ন করা
                # সাধারণত ওয়েবসাইটের টেক্সটে নাম দুইবার থাকে, তাই লজিক দিয়ে ইউনিক অংশ বের করা
                cleaned_title = full_text
                for status_word in ["LIVE", "Starting Soon", "UTC"]:
                    cleaned_title = cleaned_title.replace(status_word, "")
                
                # ডেট বা টাইম বাদ দিয়ে শুধু মূল নাম রাখা
                if " at " in cleaned_title:
                    cleaned_title = cleaned_title.split(" at ")[0]
                
                # যদি টেক্সট ডাবল হয়ে থাকে (যেমন "England vs Sri Lanka England vs Sri Lanka") তবে মাঝখান থেকে অর্ধেক কেটে নেওয়া
                length = len(cleaned_title)
                half = length // 2
                if length > 10 and cleaned_title[:half].strip() == cleaned_title[half:].strip():
                    event_title = cleaned_title[:half].strip()
                else:
                    event_title = cleaned_title.strip()

                # 'vs' বা 'VS' দিয়ে টিম ওয়ান এবং টিম টু আলাদা করা
                team1_title = ""
                team2_title = ""
                if " vs " in event_title.lower():
                    parts = event_title.lower().split(" vs ")
                    if len(parts) >= 2:
                        # মূল নামের কেস ঠিক রেখে স্প্লিট করা
                        split_idx = event_title.lower().find(" vs ")
                        team1_title = event_title[:split_idx].strip()
                        team2_title = event_title[split_idx + 4:].strip()
                else:
                    # যদি vs না থাকে (যেমন Asian Games 2026), তবে পুরোটা টিম ওয়ান টাইটেলে বা ইভেন্ট টাইটেলে থাকবে
                    team1_title = event_title

                # ম্যাচ টাইম বের করা
                match_time = ""
                if "at" in full_text:
                    try:
                        match_time = full_text.split("at")[1].split("UTC")[0].strip() + " UTC"
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
                update_status("yellow", "সতর্কতা: কোনো কার্ড ডাটা পাওয়া যায়নি।")
            else:
                update_status("green", f"সফলভাবে {len(matches_data)} টি কার্ডের ডেটা ফিল্টার করা হয়েছে!")

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
