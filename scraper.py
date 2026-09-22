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

    update_status("blue", "হোমপেজ থেকে ম্যাচ কার্ডগুলোর ডেটা ফেচ করা হচ্ছে...")

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
            
            # সাইডবার বা ফুটার বাদ দিয়ে হোমপেজের মূল ম্যাচ কার্ডগুলো বা কন্টেইনারগুলো খোঁজা
            # সাধারণত যে ট্যাগ বা লিংকের ভেতরে লোগো এবং 'vs' বা সময় থাকে সেগুলোই ম্যাচ কার্ড
            cards = soup.find_all('a', href=True)
            
            valid_cards = []
            for card in cards:
                text = card.get_text(separator=" ", strip=True)
                # যে কার্ডগুলোতে খেলার নাম, 'vs', অথবা সময়/লাইভ লেখা আছে সেগুলোকে টার্গেট করা
                if len(text) > 5 and ('vs' in text.lower() or 'at' in text.lower() or len(card.find_all('img')) > 0):
                    # সাইডবার মেনুর লিংকগুলো (যেমন শুধু /cricket বা /leagues) বাদ দেওয়া
                    href = card.get('href', '')
                    if href not in ["/", "#"] and not href.startswith("/category") and not href.startswith("/leagues"):
                        if card not in valid_cards:
                            valid_cards.append(card)

            update_status("blue", f"মোট {len(valid_cards)} টি সম্ভাব্য ম্যাচ কার্ড পাওয়া গেছে...")

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

                # টেক্সট থেকে অপ্রয়োজনীয় শব্দ পরিষ্কার করা
                clean_base = full_text
                for word in ["LIVE", "Starting Soon", "UTC"]:
                    clean_base = clean_base.replace(word, "")
                
                if " at " in clean_base:
                    event_part = clean_base.split(" at ")[0].strip()
                else:
                    event_part = clean_base.strip()

                # ডাবল টেক্সট বা রিপিট হওয়া নাম ঠিক করা
                length = len(event_part)
                half = length // 2
                if length > 10 and event_part[:half].strip().lower() == event_part[half:].strip().lower():
                    event_title = event_part[:half].strip()
                else:
                    event_title = event_part

                # টিম ওয়ান এবং টিম টু টাইটেল আলাদা করা
                team1_title = ""
                team2_title = ""
                lower_title = event_title.lower()
                
                if " vs " in lower_title:
                    idx = lower_title.find(" vs ")
                    team1_title = event_title[:idx].strip()
                    team2_title = event_title[idx + 4:].strip()
                else:
                    team1_title = event_title

                # ম্যাচ টাইম বা ডেট এক্সট্রাক্ট করা
                match_time = ""
                if "at" in full_text:
                    try:
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
                update_status("yellow", "সতর্কতা: কোনো ম্যাচ ডেটা ফিল্টার করা যায়নি।")
            else:
                update_status("green", f"সফলভাবে {len(matches_data)} টি ম্যাচ কার্ডের ডেটা প্রসেস করা হয়েছে!")

            # JSON ফাইলে সেভ করা
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(matches_data, f, indent=4, ensure_ascii=False)
                
            update_status("green", "সফলভাবে data.json ফাইলে ডেটা সেভ করা হয়েছে!")

        else:
            update_status("red", f"সার্ভার এরর: স্ট্যাটাস কোড {response.status_code}")

    except Exception as e:
        update_status("red", f"ত্রুটি ঘটেছে: {str(e)}")

if __name__ == "__main__":
    scrape_cricgo()
