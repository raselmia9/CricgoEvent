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
        f.write("✦ CricGo Real Data Scraper Initialized ✦\n")

    update_status("blue", "হোমপেজ থেকে রিয়েল ডাটা ফেচ করা শুরু হয়েছে...")

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
            
            # ওয়েবসাইটের ম্যাচ কার্ড বা কন্টেইনারগুলো খুঁজে বের করার লজিক
            # আপনার সাইটের নির্দিষ্ট HTML ট্যাগ বা ক্লাস অনুযায়ী এটি পরিবর্তন করতে হতে পারে
            cards = soup.find_all('div', class_='card') # অথবা সঠিক এলিমেন্ট/ক্লাস নাম দিন
            
            if not cards:
                update_status("yellow", "নির্দিষ্ট ক্লাস না পাওয়ায় সকল লিঙ্ক বা ব্লক চেক করা হচ্ছে...")
                cards = soup.find_all('a', href=True)

            for card in cards:
                card_text = card.get_text(strip=True)
                
                # উদাহরণস্বরূপ: যে কার্ডগুলোতে লাইভ বা ম্যাচ সম্পর্কিত তথ্য আছে
                if card_text and len(card_text) > 3:
                    images = card.find_all('img')
                    logo1 = images[0]['src'] if len(images) > 0 else ""
                    logo2 = images[1]['src'] if len(images) > 1 else ""
                    
                    match_entry = {
                        "eventTitle": card_text[:100],
                        "matchTime": "",
                        "team1Logo": logo1,
                        "team2Logo": logo2,
                        "team1Title": "",
                        "team2Title": "",
                        "streamLink": card.get('href', ''),
                        "isHot": "live" in card_text.lower()
                    }
                    if match_entry not in matches_data:
                        matches_data.append(match_entry)

            if not matches_data:
                update_status("yellow", "সতর্কতা: কোনো ম্যাচ ডাটা ফিল্টার করা যায়নি। অনুগ্রহ করে সাইটের সঠিক এইচটিএমএল ক্লাস বা ট্যাগ দিন।")
            else:
                update_status("green", f"মোট {len(matches_data)} টি রিয়েল ম্যাচ ডাটা পাওয়া গেছে!")

            # JSON ফাইলে সেভ করা
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(matches_data, f, indent=4, ensure_ascii=False)
                
            update_status("green", "সকল রিয়েল ডাটা সফলভাবে data.json ফাইলে সেভ করা হয়েছে!")

        else:
            update_status("red", f"সার্ভার এরর: স্ট্যাটাস কোড {response.status_code}")

    except Exception as e:
        update_status("red", f"ত্রুটি ঘটেছে: {str(e)}")

if __name__ == "__main__":
    scrape_cricgo()
