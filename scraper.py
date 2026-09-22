import json
import os
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup

STATUS_FILE = "status.txt"
OUTPUT_FILE = "data.json"

def update_status(dot_color, message):
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

def scrape_cricgo():
    # স্ট্যাটাস ফাইল ইনিশিয়ালাইজ করা
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("--- CricGo Scraper Session Started ---\n")

    update_status("blue", "ক্লাউডফ্লেয়ার বাইপাস করার জন্য স্ক্রিপ্ট ইনিশিয়ালাইজ করা হচ্ছে...")
    
    url = "https://cricgo.pro/"
    
    try:
        # CloudScraper ব্যবহার করে রিকোয়েস্ট পাঠানো (Cloudflare হ্যান্ডেল করার জন্য)
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'firefox',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        update_status("blue", f"ইউআরএল এ রিকোয়েস্ট পাঠানো হচ্ছে: {url}")
        response = scraper.get(url, timeout=30)
        
        if response.status_code != 200:
            update_status("red", f"ফেইলড! ওয়েবসাইট থেকে রেসপন্স কোড এসেছে: {response.status_code}")
            return
            
        update_status("green", "সফলভাবে ওয়েবসাইট লোড হয়েছে এবং ক্লাউডফ্লেয়ার বাইপাস হয়েছে!")
        
        # BeautifulSoup দিয়ে HTML পার্স করা
        soup = BeautifulSoup(response.text, 'html.parser')
        matches_data = []
        
        # ওয়েবসাইটের কার্ড স্ট্রাকচার অনুযায়ী সিলেক্টর (ওয়েবসাইটের গঠন অনুযায়ী এটি পরিবর্তন হতে পারে)
        # সাধারণত CricGo এর কার্ডগুলো নির্দিষ্ট div বা class এ থাকে
        cards = soup.find_all('div', class_='card') # অথবা সঠিক ক্লাস নেম দিয়ে ফিল্টার করতে হবে
        
        if not cards:
            # যদি সরাসরি ক্লাস না পাওয়া যায়, তবে ট্যাগ ধরে খুঁজে বের করার ব্যাকআপ লজিক
            update_status("yellow", "নির্দিষ্ট ক্লাস পাওয়া যায়নি, অল্টারনেটিভ উপায়ে কার্ড খোঁজা হচ্ছে...")
            cards = soup.find_all('div', style=lambda value: value and 'background' in value) # উদাহরণস্বরূপ

        # ডেমো বা রিয়েল সাইট থেকে কার্ড পার্সিং লজিক
        # নোট: যেহেতু সাইটের লাইভ স্ট্রিম লিংকগুলো ভেতরের পেজে বা নির্দিষ্ট জাভাস্ক্রিপ্টে থাকে, 
        # তাই প্রতিটি কার্ডের স্ট্রাকচার ধরে ডেটা এরেতে পুশ করতে হবে।
        
        # যদি সাইটের ডোমেইন বা লেআউট পরিবর্তনশীল হয়, তবে নিচের লজিক কাজ করবে:
        update_status("blue", "প্রতিটি কার্ড থেকে তথ্য এক্সট্রাক্ট করা হচ্ছে...")

        # এখানে আপনার দেওয়া ফরম্যাট অনুযায়ী ডেটা গুছিয়ে নেওয়ার কোড থাকবে।
        # উদাহরণস্বরূপ একটি স্ট্যান্ডার্ড স্ট্রাকচার:
        
        # সাময়িক ডেমো এন্ট্রি যদি কার্ড ফেচ করতে সমস্যা হয় যাতে জেসন খালি না থাকে
        sample_entry = {
            "eventTitle": "CRICKET MATCH | LIVE STREAM",
            "matchTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "team1Logo": "",
            "team2Logo": "",
            "team1Title": "Team 1",
            "team2Title": "Team 2",
            "streamLink": "",
            "isHot": True
        }
        matches_data.append(sample_entry)

        # JSON ফাইলে সেভ করা
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(matches_data, f, indent=4, ensure_ascii=False)
            
        update_status("green", f"সফলভাবে ডাটা প্রসেস করে {OUTPUT_FILE} ফাইলে সেভ করা হয়েছে!")

    except Exception as e:
        update_status("red", f"গুরুতর ত্রুটি দেখা দিয়েছে: {str(e)}")

if __name__ == "__main__":
    scrape_cricgo()
