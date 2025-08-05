"""
instagram_poster_updated.py - Posts every 1 minute, maximum 5 posts per run
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os

# =====================================
# INSTAGRAM CONFIGURATION
# =====================================

ACCESS_TOKEN = "EAAKkJ9FFnoQBPKdJGfJS0wnfnXEvGHSd8Kz9B1YSs8QD5lGp80200jeIgkE3l9wHNQVbnkc8Y3j57FfDMihuytmoPEkfk2uf9iU01j0vZBlL4ulYHaCtZBhfZCLUB2i8ZAZB9sQ3afsWo5W4GsfJqo1bSYWbP8ScLOMXZCqVd6AvGy7sGE010cnxyVCuRwNzqvKKzxhxAXvlAL1qkolZCLSoRyUcZB1ZBiaXhKAZDZD"
INSTAGRAM_ACCOUNT_ID = "17841476036673024"
BASE_URL = "https://graph.facebook.com/v18.0"

# Posting configuration
POSTING_INTERVAL_MINUTES = 1  # Time between posts (1 minute)
MAX_POSTS_PER_RUN = 5  # Maximum posts per execution
JSON_FILE = "instagram_ready.json"  # File created by scraper
POSTED_FILE = "posted_products.json"  # Track what's already posted

class InstagramAutoPoster:
    def __init__(self):
        self.products = []
        self.posted = []
        self.failed = []
        self.already_posted_asins = self.load_posted_history()
        
    def load_posted_history(self):
        """Load history of already posted products"""
        if os.path.exists(POSTED_FILE):
            with open(POSTED_FILE, 'r', encoding='utf-8') as f:
                posted_data = json.load(f)
                return set(posted_data.get('posted_asins', []))
        return set()
    
    def save_posted_history(self):
        """Save posted products history"""
        posted_data = {
            'posted_asins': list(self.already_posted_asins),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(POSTED_FILE, 'w', encoding='utf-8') as f:
            json.dump(posted_data, f, indent=2)
        
    def load_products(self):
        """Load products from JSON file"""
        if not os.path.exists(JSON_FILE):
            print(f"❌ Error: {JSON_FILE} not found!")
            print("Please run 'python final_scraper.py' first!")
            return False
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            all_products = json.load(f)
        
        # Filter out already posted products
        self.products = []
        for product in all_products:
            asin = product.get('asin', '')
            if asin and asin not in self.already_posted_asins:
                self.products.append(product)
        
        print(f"📊 Total products in file: {len(all_products)}")
        print(f"✅ New products to post: {len(self.products)}")
        print(f"⏭️  Already posted: {len(self.already_posted_asins)}")
        
        return True
    
    def test_connection(self):
        """Test Instagram connection"""
        url = f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}"
        params = {
            'fields': 'username,followers_count,media_count',
            'access_token': ACCESS_TOKEN
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connected to @{data.get('username', 'Unknown')}")
                print(f"   Followers: {data.get('followers_count', 'N/A')}")
                print(f"   Posts: {data.get('media_count', 'N/A')}")
                return True
            else:
                print(f"❌ Connection failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def post_to_instagram(self, product):
        """Post a single product to Instagram"""
        try:
            # Step 1: Create media container
            create_url = f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
            create_params = {
                'image_url': product['image_url'],
                'caption': product['caption'],
                'access_token': ACCESS_TOKEN
            }
            
            create_response = requests.post(create_url, data=create_params)
            
            if create_response.status_code != 200:
                return False, f"Media creation failed: {create_response.text}"
            
            creation_id = create_response.json().get('id')
            
            # Wait for processing
            time.sleep(5)
            
            # Step 2: Publish
            publish_url = f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
            publish_params = {
                'creation_id': creation_id,
                'access_token': ACCESS_TOKEN
            }
            
            publish_response = requests.post(publish_url, data=publish_params)
            
            if publish_response.status_code == 200:
                post_id = publish_response.json().get('id')
                return True, post_id
            else:
                return False, f"Publishing failed: {publish_response.text}"
                
        except Exception as e:
            return False, str(e)
    
    def run_auto_posting(self, test_mode=False):
        """Main auto-posting function - max 5 posts"""
        # Limit products to MAX_POSTS_PER_RUN
        products_to_post = self.products[:1] if test_mode else self.products[:MAX_POSTS_PER_RUN]
        
        if not products_to_post:
            print("\n📭 No new products to post!")
            print("All products have been posted already.")
            return
        
        total_products = len(products_to_post)
        total_time_minutes = (total_products - 1) * POSTING_INTERVAL_MINUTES
        
        print("\n" + "="*60)
        print("🚀 INSTAGRAM AUTO-POSTER (LIMITED RUN)")
        print("="*60)
        print(f"📦 Products to post: {total_products} (max {MAX_POSTS_PER_RUN} per run)")
        print(f"⏱️  Interval: {POSTING_INTERVAL_MINUTES} minute between posts")
        print(f"⏰ Total duration: {total_time_minutes} minutes")
        print(f"🕐 Start time: {datetime.now().strftime('%I:%M %p')}")
        print(f"🕘 End time: {(datetime.now() + timedelta(minutes=total_time_minutes)).strftime('%I:%M %p')}")
        print("="*60)
        
        # Show schedule
        print("\n📅 POSTING SCHEDULE:")
        print("-"*60)
        for i, product in enumerate(products_to_post, 1):
            post_time = datetime.now() + timedelta(minutes=(i-1)*POSTING_INTERVAL_MINUTES)
            print(f"{i}. {post_time.strftime('%I:%M %p')} - {product['name'][:50]}")
        print("-"*60)
        
        if test_mode:
            print("\n🔍 TEST MODE - Will only post first product")
            confirm = input("Continue with test? (yes/no): ")
        else:
            print(f"\n⚠️  QUICK POST MODE - {total_products} posts in {total_time_minutes} minutes")
            confirm = input("Start auto-posting? Type 'YES' in capitals: ")
            
        if test_mode and confirm.lower() != 'yes':
            print("❌ Test cancelled")
            return
        elif not test_mode and confirm != 'YES':
            print("❌ Auto-posting cancelled")
            return
        
        # Start posting
        for i, product in enumerate(products_to_post, 1):
            current_time = datetime.now().strftime('%I:%M %p')
            
            print(f"\n{'='*60}")
            print(f"📱 POST {i}/{len(products_to_post)} - {current_time}")
            print(f"Product: {product['name']}")
            print(f"Price: {product['price']} ({product.get('discount', 'Special Offer')})")
            print("="*60)
            
            # Show caption preview
            print("\n📝 Caption preview (first 150 chars):")
            print(product['caption'][:150] + "...")
            print(f"\n🔗 Affiliate link included in caption")
            
            # Post to Instagram
            print("\n📤 Posting to Instagram...")
            success, result = self.post_to_instagram(product)
            
            if success:
                print(f"✅ SUCCESS! Post ID: {result}")
                print(f"📱 View at: https://www.instagram.com/p/{result}/")
                
                # Track posted product
                asin = product.get('asin', '')
                if asin:
                    self.already_posted_asins.add(asin)
                
                self.posted.append({
                    'product': product['name'],
                    'asin': asin,
                    'post_id': result,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                print(f"❌ FAILED: {result}")
                self.failed.append({
                    'product': product['name'],
                    'error': result,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Wait for next post (except last one)
            if i < len(products_to_post):
                next_post_time = datetime.now() + timedelta(minutes=POSTING_INTERVAL_MINUTES)
                print(f"\n⏳ Next post at: {next_post_time.strftime('%I:%M:%S %p')}")
                print(f"Waiting {POSTING_INTERVAL_MINUTES} minute...")
                
                # Countdown timer (in seconds for 1 minute)
                for second in range(60, 0, -1):
                    print(f"\r⏱️  Time until next post: {second:2d} seconds ", end="", flush=True)
                    time.sleep(1)
                print()  # New line after countdown
        
        # Save posted history
        self.save_posted_history()
        
        # Final summary
        self.show_summary()
        self.save_results()
    
    def show_summary(self):
        """Show posting summary"""
        print("\n" + "="*60)
        print("📊 POSTING SUMMARY")
        print("="*60)
        print(f"✅ Successful: {len(self.posted)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"📋 Total posted (all time): {len(self.already_posted_asins)}")
        
        if self.posted:
            print("\n✅ Successfully posted:")
            for item in self.posted:
                print(f"   • {item['product'][:50]} - {item['time']}")
        
        if self.failed:
            print("\n❌ Failed posts:")
            for item in self.failed:
                print(f"   • {item['product'][:50]} - {item['error'][:30]}")
    
    def save_results(self):
        """Save posting results"""
        results = {
            'posted': self.posted,
            'failed': self.failed,
            'summary': {
                'total_attempted': len(self.posted) + len(self.failed),
                'successful': len(self.posted),
                'failed': len(self.failed),
                'success_rate': f"{(len(self.posted)/(len(self.posted)+len(self.failed))*100):.1f}%" if (self.posted or self.failed) else "0%"
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        filename = f"posting_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to {filename}")

# Main menu
def main():
    poster = InstagramAutoPoster()
    
    print("\n🎯 PANDALOON INSTAGRAM AUTO-POSTER")
    print("📋 Quick Post Mode: 1-minute intervals, max 5 posts")
    print("="*60)
    
    # Load products
    if not poster.load_products():
        return
    
    # Test connection
    print("\n🔌 Testing Instagram connection...")
    if not poster.test_connection():
        print("Please check your access token and account ID!")
        return
    
    print("\n" + "="*60)
    print("📋 OPTIONS:")
    print("="*60)
    print("1. TEST MODE - Post only first product")
    print("2. QUICK POST - Post up to 5 products (1 min intervals)")
    print("3. VIEW PRODUCTS - See what will be posted")
    print("4. RESET HISTORY - Clear posted products history")
    print("5. EXIT")
    print("="*60)
    
    choice = input("\nSelect option (1-5): ")
    
    if choice == "1":
        poster.run_auto_posting(test_mode=True)
    elif choice == "2":
        poster.run_auto_posting(test_mode=False)
    elif choice == "3":
        print("\n📦 NEW PRODUCTS TO POST:")
        print("-"*60)
        for i, product in enumerate(poster.products[:10], 1):
            print(f"{i}. {product['name']}")
            print(f"   Price: {product['price']} | Discount: {product.get('discount', 'N/A')}")
            print(f"   ASIN: {product.get('asin', 'N/A')}")
            print()
        if len(poster.products) > 10:
            print(f"... and {len(poster.products) - 10} more products")
    elif choice == "4":
        confirm = input("Reset posting history? This will allow re-posting all products. (yes/no): ")
        if confirm.lower() == 'yes':
            if os.path.exists(POSTED_FILE):
                os.remove(POSTED_FILE)
                print("✅ Posting history cleared!")
            else:
                print("No history to clear.")
    elif choice == "5":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid option!")

if __name__ == "__main__":
    main()