import json
import requests
from bs4 import BeautifulSoup

# মূল হোম ইউআরএল
BASE_URL = "https://cricgo.pro"
url = BASE_URL + "/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

matches_data = []

try:
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.find_all('a', href=True)
        
        seen_links = set()
        
        for card in cards:
            full_text = card.get_text(separator=" ", strip=True).lower()
            
            # রানিং ম্যাচ বা 'live' লেখা কার্ডগুলো ফিল্টার করা
            if "live" in full_text:
                href = card.get('href', '')
                
                if href and href not in ["/", "#"]:
                    # পূর্ণাঙ্গ লিংক তৈরি করা (যদি অলরেডি https না থাকে)
                    if href.startswith("http"):
                        full_stream_link = href
                    else:
                        full_stream_link = BASE_URL + href if href.startswith("/") else BASE_URL + "/" + href
                    
                    # ডুপ্লিকেট এড়ানো
                    if full_stream_link not in seen_links:
                        seen_links.add(full_stream_link)
                        
                        # আপনার কাঙ্ক্ষিত ফরম্যাট অনুযায়ী ট্যাগগুলো খালি রেখে ডাটা স্ট্রাকচার তৈরি
                        match_entry = {
                            "eventTitle": "",
                            "matchTime": "",
                            "team1Logo": "",
                            "team2Logo": "",
                            "team1Title": "",
                            "team2Title": "",
                            "streamLink": full_stream_link,
                            "isHot": True
                        }
                        
                        matches_data.append(match_entry)

        # JSON ফাইলে সেভ করা
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(matches_data, f, indent=4, ensure_ascii=False)
            
        print(f"সফলভাবে {len(matches_data)} টি ম্যাচের সম্পূর্ণ লিংকসহ ডেটা data.json ফাইলে সেভ করা হয়েছে!")

    else:
        print("পেজ লোড করতে সমস্যা হয়েছে। স্ট্যাটাস কোড:", response.status_code)

except Exception as e:
    print("ত্রুটি:", str(e))
