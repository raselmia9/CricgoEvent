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
        f.write("✦ CricGo Logos & Links Scraper Initialized ✦\n")

    update_status("blue", "হোমপেজ থেকে লোগো এবং স্ট্রিমিং লিংক সংগ্রহ করা হচ্ছে...")

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
                text = card.get_text(separator=" ", strip=True)
                # যে কার্ডগুলোতে লোগো বা ম্যাচ/ইভেন্ট সম্পর্কিত তথ্য আছে সেগুলোকে ফিল্টার করা
                if len(card.find_all('img')) > 0:
                    href = card.get('href', '')
                    # সাইডবার মেনু বা ক্যাটাগরি লিংক বাদ দেওয়া
                    if href not in ["/", "#"] and not href.startswith("/category") and not href.startswith("/leagues"):
                        if card not in valid_cards:
                            valid_cards.append(card)

            update_status("blue", f"মোট {len(valid_cards)} টি কার্ড পাওয়া গেছে, লোগো প্রসেস করা হচ্ছে...")

            for card in valid_cards:
                full_text = card.get_text(separator=" ", strip=True)
                
                # লোগোগুলো সংগ্রহ করা
                images = card.find_all('img')
                logo1 = ""
                logo2 = ""
                
                if len(images) == 1:
                    # যদি একটিমাত্র লোগো থাকে, তবে সেটি টিম ১ এবং টিম ২ উভয় জায়গাতেই বসে যাবে
                    single_logo = images[0].get('src', '')
                    logo1 = single_logo
                    logo2 = single_logo
                elif len(images) >= 2:
                    # যদি দুটি লোগো থাকে
                    logo1 = images[0].get('src', '')
                    logo2 = images[1].get('src', '')

                # ম্যাচ টাইম বা ডেট এক্সট্রাক্ট করা (যদি থাকে)
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
                stream_link = card.get('href', '')

                # টাইটেল ছাড়া শুধুমাত্র আপনার কাঙ্ক্ষিত ফিল্ডগুলো সাজানো
                match_entry = {
                    "eventTitle": "",
                    "matchTime": match_time,
                    "team1Logo": logo1,
                    "team2Logo": logo2,
                    "team1Title": "",
                    "team2Title": "",
                    "streamLink": stream_link,
                    "isHot": is_live
                }
                
                # শুধু লোগো বা স্ট্রিম লিংক থাকলেই সেভ করবে
                if (logo1 or logo2) and stream_link not in [item["streamLink"] for item in matches_data]:
                    matches_data.append(match_entry)

            if not matches_data:
                update_status("yellow", "সতর্কতা: কোনো লোগো ডেটা পাওয়া যায়নি।")
            else:
                update_status("green", f"সফলভাবে {len(matches_data)} টি কার্ডের লোগো ও লিংক প্রসেস করা হয়েছে!")

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
