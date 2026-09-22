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

    update_status("blue", "হোমপেজ থেকে রিয়েল ম্যাচ কার্ড ডাটা ফেচ করা শুরু হয়েছে...")

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
            
            # সাইডবার মেনু বা ক্যাটাগরি বাদ দিয়ে মূল ম্যাচ কার্ডগুলো খোঁজার জন্য 
            # সাধারণ ম্যাচ কার্ডের ক্লাস বা কন্টেইনার (যেমন: match-card, match-box অথবা সরাসরি লিঙ্কের স্ট্রাকচার) টার্গেট করা
            # সাধারণত ম্যাচ কার্ডগুলোতে টিম ও সময়ের তথ্য থাকে
            
            # এখানে আপনার সাইটের ম্যাচ কার্ডগুলোর আসল ক্লাস বা কন্টেইনার ট্যাগ দিন (যেমন: 'match-card', 'card', ইত্যাদি)
            # নিচে একটি আদর্শ ম্যাচ কার্ড স্ট্রাকচার ফিল্টার করার লজিক দেওয়া হলো যা সাইডবার বাদ দেবে:
            cards = []
            
            # সম্ভাব্য ম্যাচ কার্ড বা ম্যাচ আইটেম কন্টেইনার খুঁজছি
            potential_cards = soup.find_all('div', class_=['match-card', 'card', 'match-item', 'live-match'])
            
            if not potential_cards:
                # যদি নির্দিষ্ট ক্লাস না পাওয়া যায়, তবে যে সমস্ত লিংকের মধ্যে একাধিক টিম লোগো বা 'vs' / সময় রয়েছে সেগুলোকে ফিল্টার করা হবে
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    # সাইডবার মেনুর লিংক যেমন /cricket বা /leagues বাদ দিয়ে শুধুমাত্র ম্যাচ বা স্ট্রিম লিংক ফিল্টার করা
                    if '/match/' in href or '/stream/' in href or len(link.find_all('img')) >= 2:
                        cards.append(link)
            else:
                cards = potential_cards

            update_status("blue", f"পাওয়া গেছে মোট {len(cards)} সম্ভাব্য কার্ড, ডেটা প্রসেস করা হচ্ছে...")

            for card in cards:
                # কার্ড থেকে লোগোগুলো সংগ্রহ করা
                images = card.find_all('img')
                logo1 = images[0]['src'] if len(images) > 0 else ""
                logo2 = images[1]['src'] if len(images) > 1 else ""
                
                # টিম বা ইভেন্টের শিরোনাম বের করা
                # সাইডবার বা ক্যাটাগরি টেক্সট বাদ দেওয়ার জন্য ন্যূনতম শর্ত রাখা হলো
                title_elem = card.find(['h3', 'h4', 'span', 'div'], class_=['title', 'match-title', 'team-name'])
                event_title = title_elem.get_text(strip=True) if title_elem else card.get_text(strip=True)
                
                # ম্যাচ টাইম বা স্ট্যাটাস (লাইভ বা টাইম) বের করা
                time_elem = card.find(['span', 'div'], class_=['time', 'match-time', 'badge'])
                match_time = time_elem.get_text(strip=True) if time_elem else ""
                
                stream_link = card.get('href', '') if card.name == 'a' else (card.find('a', href=True).get('href', '') if card.find('a', href=True) else "")

                # যদি এটি সাইডবার মেনু না হয়ে আসল ম্যাচ কার্ড হয় (যেমন লোগো আছে অথবা লিংকে নির্দিষ্ট প্যাটার্ন আছে)
                if logo1 or "vs" in event_title.lower() or "/match/" in stream_link:
                    match_entry = {
                        "eventTitle": event_title[:100],
                        "matchTime": match_time,
                        "team1Logo": logo1,
                        "team2Logo": logo2,
                        "team1Title": "", # প্রয়োজন অনুযায়ী আলাদা করতে পারেন
                        "team2Title": "",
                        "streamLink": stream_link,
                        "isHot": "live" in card.get_text().lower() or "live" in stream_link.lower()
                    }
                    if match_entry not in matches_data and stream_link:
                        matches_data.append(match_entry)

            if not matches_data:
                update_status("yellow", "সতর্কতা: সঠিক ফিল্টারে কোনো ম্যাচ কার্ড পাওয়া যায়নি। অনুগ্রহ করে ম্যাচ কার্ডের নির্দিষ্ট HTML ক্লাস নেম দিন।")
            else:
                update_status("green", f"সফলভাবে {len(matches_data)} টি রিয়েল ম্যাচ কার্ড এক্সট্রাক্ট করা হয়েছে!")

            # JSON ফাইলে সেভ করা
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(matches_data, f, indent=4, ensure_ascii=False)
                
            update_status("green", "সকল ম্যাচ কার্ডের রিয়েল ডাটা data.json ফাইলে সেভ করা হয়েছে!")

        else:
            update_status("red", f"সার্ভার এরর: স্ট্যাটাস কোড {response.status_code}")

    except Exception as e:
        update_status("red", f"ত্রুটি ঘটেছে: {str(e)}")

if __name__ == "__main__":
    scrape_cricgo()
