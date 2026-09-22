import json
import requests
from bs4 import BeautifulSoup

url = "https://cricgo.pro/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

matches_data = []

try:
    response = requests.get(url, headers=headers, timeout=10)
    print("Response Status:", response.status_code)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # সাইটের সব <a> ট্যাগ যেগুলো লিঙ্কের মাধ্যমে কার্ড হিসেবে আছে
        cards = soup.find_all('a', href=True)
        print(f"Total links found: {len(cards)}")

        for card in cards:
            # যে কার্ডগুলোতে ছবি বা লোগো আছে সেগুলোকে টার্গেট করা
            images = card.find_all('img')
            if len(images) > 0:
                href = card.get('href', '')
                
                # ফালতু বা হোম পেজের নিজস্ব লিংক বাদ দেওয়া
                if href in ["/", "#"] or href.startswith("/category") or href.startswith("/leagues"):
                    continue

                full_text = card.get_text(separator=" ", strip=True)

                # লোগো সংগ্রহ
                logo1 = ""
                logo2 = ""
                if len(images) == 1:
                    single_logo = images[0].get('src', '')
                    logo1 = single_logo
                    logo2 = single_logo # একটি লোগো থাকলে উভয় জায়গাতেই একই বসবে
                elif len(images) >= 2:
                    logo1 = images[0].get('src', '')
                    logo2 = images[1].get('src', '')

                # ম্যাচ টাইম বের করা
                match_time = ""
                if "at" in full_text:
                    try:
                        parts = full_text.split("at")
                        raw_time = parts[1].strip()
                        if "UTC" in raw_time:
                            match_time = raw_time.split("UTC")[0].strip() + " UTC"
                        else:
                            match_time = raw_time
                    except:
                        match_time = ""

                is_live = "live" in full_text.lower()

                match_entry = {
                    "eventTitle": "",
                    "matchTime": match_time,
                    "team1Logo": logo1,
                    "team2Logo": logo2,
                    "team1Title": "",
                    "team2Title": "",
                    "streamLink": href,
                    "isHot": is_live
                }

                # ডুপ্লিকেট এড়ানো
                if match_entry not in matches_data and (logo1 or logo2):
                    matches_data.append(match_entry)

        # JSON ফাইলে সেভ করা
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(matches_data, f, indent=4, ensure_ascii=False)
            
        print(f"Success! Total matches saved: {len(matches_data)}")

    else:
        print("Failed to load page.")

except Exception as e:
    print("Error:", str(e))
