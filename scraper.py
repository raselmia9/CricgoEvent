import json
import os
from datetime import datetime
import cloudscraper

STATUS_FILE = "status.txt"
OUTPUT_FILE = "data.json"

def update_status(dot_color, message):
    """
    স্ট্যাটাস ফাইলে রঙিন ডট এবং মেসেজ যুক্ত করে।
    🟢 সবুজ = সফল
    🔵 নীল = প্রসেসিং/শুরু
    🟡 হলুদ = সতর্কবার্তা
    🔴 লাল = এরর/ফেল
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dots = {
        "green": "🟢",
        "blue": "🔵",
        "yellow": "🟡",
        "red": "🔴"
    }
    emoji = dots.get(dot_color, "⚪")
    log_line = f"{emoji} [{timestamp}] {message}\n"
    
    print(log_line.strip())
    with open(STATUS_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

def main():
    # স্ট্যাটাস ফাইল রিসেট করা (প্রতি রান এ নতুন করে শুরু করার জন্য)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("--- Scraping Session Started ---\n")

    update_status("blue", "স্ক্রেপিং প্রক্রিয়া শুরু হয়েছে...")

    url = "https://cricgo.pro/"
    
    try:
        update_status("blue", "ক্লাউডফ্লেয়ার বাইপাস করার জন্য cloudscraper ব্যবহার করা হচ্ছে...")
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=30)
        
        if response.status_code == 200:
            update_status("green", "ওয়েবসাইট সফলভাবে লোড হয়েছে!")
            
            # TODO: এখানে আপনার BeautifulSoup বা lxml ব্যবহার করে 
            # ওয়েবসাইটের কার্ডগুলো থেকে তথ্য পার্স (Parse) করতে হবে 
            # এবং আপনার দেওয়া ডেমো ফরম্যাট অনুযায়ী ডিকশনারি তৈরি করতে হবে।
            
            # ডেমো ডেটা হিসেবে আপনার দেওয়া ফরম্যাটটি এখানে যুক্ত করা হলো:
            parsed_data = [
                {
                    "eventTitle": "CRICKET T20 | LANKA PREMIER LEAGUE 2026 | Match 15",
                    "matchTime": "2026-08-28 00:00:00",
                    "team1Logo": "https://cricketvectors.akamaized.net/Teams/G2.png",
                    "team2Logo": "https://cricketvectors.akamaized.net/Teams/G5.png",
                    "team1Title": "Colombo Kaps",
                    "team2Title": "Jaffna Kings",
                    "streamLink": "T Sports,,http://103.191.99.248:5550/102/tracks-v1a1/mono.m3u8,) iScreen,,https://c9wm5zqx2rt8vnj6lpl.rockstreamer.com/v1/019f325acf6615fc60e92c29383152/019f325bba0315fc600b2da99b6c8e/main.m3u8|Referer=https://iscreen.com.bd/",
                    "isHot": True
                }
            ]

            # JSON ফাইলে সেভ করা
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=4, ensure_ascii=False)
            
            update_status("green", f"তথ্য সফলভাবে {OUTPUT_FILE} ফাইলে সেভ করা হয়েছে!")

        else:
            update_status("red", f"ওয়েবসাইট থেকে রেসপন্স পেতে সমস্যা হয়েছে। স্ট্যাটাস কোড: {response.status_code}")

    except Exception as e:
        update_status("red", f"একটি ত্রুটি (Error) দেখা দিয়েছে: str({e})")

if __name__ == "__main__":
    main()
          
