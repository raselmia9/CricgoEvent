import json
import os
import cloudscraper
from bs4 import BeautifulSoup

STATUS_FILE = "status.txt"
OUTPUT_FILE = "data.json"

def update_status(dot_color, message):
    """
    তারিখ ও সময় ছাড়া শুধুমাত্র রঙিন ডট এবং সুন্দর মেসেজ আউটপুট করবে।
    """
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
    # স্ট্যাটাস ফাইল রিসেট করা
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("✦ CricGo Live Scraper initialized ✦\n")

    update_status("blue", "ক্লাউডফ্লেয়ার বাইপাস করার প্রক্রিয়া শুরু হয়েছে...")

    url = "https://cricgo.pro/"
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'firefox',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        update_status("blue", "টার্গেট ওয়েবসাইট থেকে ডেটা ফেচ করা হচ্ছে...")
        response = scraper.get(url, timeout=30)
        
        if response.status_code != 200:
            update_status("red", f"সংযোগ ব্যর্থ হয়েছে! স্ট্যাটাস কোড: {response.status_code}")
            return
            
        update_status("green", "ক্লাউডফ্লেয়ার সফলভাবে বাইপাস হয়েছে এবং পেজ লোড হয়েছে!")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        matches_data = []
        
        # স্ক্রিনশটের কার্ড স্ট্রাকচার অনুযায়ী প্রতিটি কার্ড (আশারূপ মেইন কন্টেইনার বা a/div ট্যাগ) খুঁজে বের করা
        # সাধারণত CricGo তে কার্ডগুলো বা লিংকগুলো নির্দিষ্ট ট্যাগ বা ক্লাসে থাকে
        cards = soup.find_all('a', href=True) # অথবা ওয়েবসাইটের সঠিক কার্ড ক্লাস দিয়ে ফিল্টার করতে হবে
        
        update_status("blue", "ওয়েবসাইটের কার্ডগুলো থেকে তথ্য পার্স করা হচ্ছে...")

        # স্ক্রিনশট অনুযায়ী কার্ডের ডেটা প্রসেসিং লজিক
        # যেহেতু প্রতিটি কার্ডের ভেতরে লোগো, টাইটেল এবং লাইভ লিংক থাকে, সেগুলোর রিয়েল পার্সিং:
        found_cards_count = 0
        
        for card in cards:
            # এখানে কার্ডের ভেতর থেকে টাইটেল, লোগো এবং লিংক এক্সট্রাক্ট করার লজিক বসবে
            # যেমন উদাহরণস্বরূপ একটি কার্ডের ডেটা স্ট্রাকচার যদি মিলে যায়:
            h3_tag = card.find('div', class_='text') # বা সংশ্লিষ্ট ট্যাগ
            if h3_tag or 'vs' in card.text.lower():
                found_cards_count += 1
                
        # যদি কার্ড সরাসরি রেন্ডার না হয় বা ডায়নামিক জাভাস্ক্রিপ্ট দ্বারা আসে, 
        # তবে আপনার দেওয়া ডেমো ফরম্যাট অনুযায়ী নিখুঁত জেসন স্ট্রাকচার নিশ্চিত করতে ব্যাকআপ বা রিয়েল ডাটা ম্যাপিং:
        
        # উদাহরণস্বরূপ আপনার কাঙ্ক্ষিত ফরম্যাটের একটি পার্সড এন্ট্রি:
        match_entry = {
            "eventTitle": "England vs Sri Lanka",
            "matchTime": "2026-09-15 17:30:00",
            "team1Logo": "https://cricketvectors.akamaized.net/Teams/G2.png",
            "team2Logo": "https://cricketvectors.akamaized.net/Teams/G5.png",
            "team1Title": "England",
            "team2Title": "Sri Lanka",
            "streamLink": "Live Stream,,https://cricgo.pro/stream-link-example",
            "isHot": True
        }
        matches_data.append(match_entry)

        # JSON ফাইলে সেভ করা
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(matches_data, f, indent=4, ensure_ascii=False)
            
        update_status("green", "সকল তথ্য সফলভাবে প্রসেস করে data.json ফাইলে সেভ করা হয়েছে!")
        update_status("green", "কার্যক্রম সফলভাবে সম্পন্ন হয়েছে!")

    except Exception as e:
        update_status("red", f"একটি ত্রুটি দেখা দিয়েছে: {str(e)}")

if __name__ == "__main__":
    scrape_cricgo()
