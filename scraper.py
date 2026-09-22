import json
import requests
from bs4 import BeautifulSoup

url = "https://cricgo.pro/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

running_matches = []

try:
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # পেজের সব কার্ড বা লিংকগুলো চেক করা
        cards = soup.find_all('a', href=True)
        
        for card in cards:
            full_text = card.get_text(separator=" ", strip=True).lower()
            
            # যে কার্ডগুলোতে 'live' লেখা আছে সেগুলোকে রানিং ম্যাচ হিসেবে ধরবো
            if "live" in full_text:
                href = card.get('href', '')
                
                # যদি লিংকটি সঠিক হয় এবং লিস্টে আগে থেকে না থাকে
                if href and href not in ["/", "#"] and href not in running_matches:
                    running_matches.append(href)
        
        # বর্তমানে রানিং থাকা ম্যাচগুলোর লিংক প্রিন্ট করা
        print(f"রানিং ম্যাচ পাওয়া গেছে: {len(running_matches)} টি")
        for link in running_matches:
            print("Link:", link)

        # JSON ফাইলে সেভ করা (শুধু লিংকগুলো)
        output_data = [{"streamLink": link} for link in running_matches]
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
            
        print("সফলভাবে data.json ফাইলে সেভ করা হয়েছে!")

    else:
        print("পেজ লোড করতে সমস্যা হয়েছে। স্ট্যাটাস কোড:", response.status_code)

except Exception as e:
    print("ত্রুটি:", str(e))
