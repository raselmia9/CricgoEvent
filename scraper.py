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

    update_status("blue", "হোমপেজ থেকে ম্যাচ কার্ডগুলোর ডেটা সংগ্রহ করা হচ্ছে...")

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
            
            # স্ক্রিনশট অনুযায়ী প্রতিটি ম্যাচ কার্ড সাধারণত একটি নির্দিষ্ট ট্যাগ বা লিঙ্কের মধ্যে থাকে
            # আমরা সরাসরি মূল কার্ডের কন্টেইনার বা a ট্যাগগুলো খুঁজব যেগুলোতে ম্যাচ বা ইভেন্ট আছে
            cards = soup.find_all('a', href=True)
            
            valid_cards = []
            for card in cards:
                href = card.get('href', '')
                # শুধুমাত্র ইভেন্ট বা ম্যাচ সম্পর্কিত লিংকগুলো ফিল্টার করা (যেমন /events/ বা অনুরূপ)
                if '/events/' in href or '/match/' in href:
                    if card not in valid_cards:
                        valid_cards.append(card)

            update_status("blue", f"মোট {len(valid_cards)} টি ম্যাচ কার্ড পাওয়া গেছে, ডেটা প্রসেস করা হচ্ছে...")

            for card in valid_cards:
                # কার্ডের ভেতরের সমস্ত টেক্সট পরিষ্কারভাবে নেওয়া
                full_text = card.get_text(separator=" ", strip=True)
                
                # লোগোগুলো সংগ্রহ করা
                images = card.find_all('img')
                logo1 = images[0]['src'] if len(images) > 0 else ""
                logo2 = images[1]['src'] if len(images) > 1 else ""
                
                # ইভেন্ট বা ম্যাচের শিরোনাম আলাদা করা (রিপিট হওয়া টেক্সট রোধ করতে সুনির্দিষ্ট ক্লিনিং)
                # যেমন স্ক্রিনশটের হেডিং বা টিম নাম আলাদা করা
                event_title = full_text.split("Live at")[0].replace("LIVE", "").replace("Starting Soon", "").strip()
                if not event_title:
                    event_title = full_text[:60]

                # ম্যাচ সময় বা ডেট বের করা
                match_time = ""
                if "at" in full_text:
                    try:
                        match_time = full_text.split("at")[1].split("UTC")[0].strip() + " UTC"
                    except:
                        match_time = ""

                # লাইভ স্ট্যাটাস চেক করা
                is_live = "live" in full_text.lower()

                match_entry = {
                    "eventTitle": event_title,
                    "matchTime": match_time,
                    "team1Logo": logo1,
                    "team2Logo": logo2,
                    "team1Title": "",
                    "team2Title": "",
                    "streamLink": card.get('href', ''),
                    "isHot": is_live
                }
                
                if match_entry not in matches_data and event_title:
                    matches_data.append(match_entry)

            if not matches_data:
                update_status("yellow", "সতর্কতা: কোনো কার্ড ফিল্টার করা যায়নি।")
            else:
                update_status("green", f"সফলভাবে {len(matches_data)} টি কার্ডের সঠিক ডেটা এক্সট্রাক্ট করা হয়েছে!")

            # JSON ফাইলে সেভ করা
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(matches_data, f, indent=4, ensure_ascii=False)
                
            update_status("green", "সকল ডেটা সফলভাবে data.json ফাইলে সেভ করা হয়েছে!")

        else:
            update_status("red", f"সার্ভার এরর: স্ট্যাটাস কোড {response.status_code}")

    except Exception as e:
        update_status("red", f"ত্রুটি ঘটেছে: {str(e)}")

if __name__ == "__main__":
    scrape_cricgo()
