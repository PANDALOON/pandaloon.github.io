"""
final_scraper.py - Working Amazon scraper with affiliate links in captions
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime

# =====================================
# ADD YOUR URLS HERE (1-15 products)
# =====================================

AMAZON_URLS = [
    "https://www.amazon.in/FILLISKA%C2%AE-Luxurious-Adjustable-Changing-Gold-7716/dp/B0D76SL1MK/ref=srd_d_psims_d_sccl_1_1/258-2002287-9195660?pd_rd_w=WcyvT&content-id=amzn1.sym.6b3aa144-fd3f-4cac-9ae1-ac2407bcccc2&pf_rd_p=6b3aa144-fd3f-4cac-9ae1-ac2407bcccc2&pf_rd_r=5ZBT3ZEN7G822B81AH9H&pd_rd_wg=YKHhr&pd_rd_r=f2142fe9-0ce3-4f71-ae6a-df8bd91334c1&pd_rd_i=B0D76SL1MK&th=1",
    "https://www.amazon.in/dp/B0DW13XKQZ?ref=cm_sw_r_cso_wa_apin_dp_FSWEN81T2YPWZJ7SP5PB&ref_=cm_sw_r_cso_wa_apin_dp_FSWEN81T2YPWZJ7SP5PB&social_share=cm_sw_r_cso_wa_apin_dp_FSWEN81T2YPWZJ7SP5PB&th=1",
    "https://www.amazon.in/dp/B0DDXHZXDK?ref=cm_sw_r_cso_wa_apin_dp_1E8598QGK07RCZ2M0GVJ&ref_=cm_sw_r_cso_wa_apin_dp_1E8598QGK07RCZ2M0GVJ&social_share=cm_sw_r_cso_wa_apin_dp_1E8598QGK07RCZ2M0GVJ&th=1",
    "https://www.amazon.in/dp/B0DW13XKQZ?ref=cm_sw_r_cso_wa_apin_dp_FSWEN81T2YPWZJ7SP5PB&ref_=cm_sw_r_cso_wa_apin_dp_FSWEN81T2YPWZJ7SP5PB&social_share=cm_sw_r_cso_wa_apin_dp_FSWEN81T2YPWZJ7SP5PB&th=1",
    # Add more URLs here (up to 15)
]

AFFILIATE_TAG = "pandaloon-21"

class WorkingAmazonScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        self.products = []
    
    def clean_text(self, text):
        """Clean text data"""
        if text:
            return ' '.join(text.split()).strip()
        return ""
    
    def extract_asin(self, url):
        """Extract ASIN from URL"""
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        return match.group(1) if match else None
    
    def scrape_product(self, url, index):
        print(f"\n[{index}] Scraping: {url[:60]}...")
        print("-" * 60)
        
        try:
            # Make request
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ HTTP Error: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Initialize product
            product = {
                'url': url,
                'asin': self.extract_asin(url),
                'affiliate_link': f"https://www.amazon.in/dp/{self.extract_asin(url)}?tag={AFFILIATE_TAG}",
                'position': index,
                'success': False
            }
            
            # TITLE - Try multiple methods
            print("🔍 Extracting title...")
            title = None
            
            # Method 1: ID selector
            title_elem = soup.find('span', {'id': 'productTitle'})
            if title_elem:
                title = self.clean_text(title_elem.text)
            
            # Method 2: Class selectors
            if not title:
                for selector in ['h1.a-size-large', 'h1#title', 'div#centerCol h1']:
                    elem = soup.select_one(selector)
                    if elem:
                        title = self.clean_text(elem.text)
                        break
            
            if title:
                product['title'] = title
                product['name'] = title[:60]
                print(f"✓ Title: {title[:50]}...")
            else:
                print("✗ Title not found")
            
            # PRICE - Enhanced detection
            print("🔍 Extracting price...")
            price = None
            
            # Method 1: Price whole span
            price_elem = soup.find('span', {'class': 'a-price-whole'})
            if price_elem:
                price = self.clean_text(price_elem.text).replace(',', '').replace('.', '')
                
            # Method 2: Look for any price pattern
            if not price:
                price_pattern = re.compile(r'₹\s*[\d,]+')
                # Search in specific price areas
                price_areas = soup.find_all(['span', 'div'], class_=re.compile('price'))
                for area in price_areas:
                    match = price_pattern.search(area.text)
                    if match:
                        price = match.group().replace('₹', '').replace(',', '').strip()
                        break
            
            # Method 3: Meta tags
            if not price:
                meta_price = soup.find('meta', {'property': 'product:price:amount'})
                if meta_price:
                    price = meta_price.get('content', '').replace(',', '')
            
            if price:
                product['price'] = f"₹{price}"
                print(f"✓ Price: ₹{price}")
            else:
                print("✗ Price not found")
            
            # ORIGINAL PRICE (MRP)
            print("🔍 Extracting MRP...")
            mrp = None
            
            # Look for strike-through prices
            strike_elems = soup.find_all(['span', 'div'], class_=re.compile('strike|list-price|was-price'))
            for elem in strike_elems:
                text = elem.text
                match = re.search(r'₹\s*([\d,]+)', text)
                if match:
                    mrp_value = match.group(1).replace(',', '')
                    if mrp_value != price:  # Make sure it's different from current price
                        mrp = mrp_value
                        break
            
            if mrp:
                product['original_price'] = f"₹{mrp}"
                print(f"✓ MRP: ₹{mrp}")
                
                # Calculate discount
                try:
                    price_num = float(price) if price else 0
                    mrp_num = float(mrp)
                    if mrp_num > price_num and price_num > 0:
                        discount = int(((mrp_num - price_num) / mrp_num) * 100)
                        product['discount'] = f"{discount}%"
                        print(f"✓ Discount: {discount}%")
                except:
                    pass
            
            # RATING
            print("🔍 Extracting rating...")
            rating_elem = soup.find('span', {'class': 'a-icon-alt'})
            if rating_elem:
                match = re.search(r'([\d.]+)\s*out of', rating_elem.text)
                if match:
                    product['rating'] = match.group(1)
                    print(f"✓ Rating: {match.group(1)}/5")
            
            # IMAGE
            print("🔍 Extracting image...")
            image_found = False
            
            # Method 1: landingImage
            img_elem = soup.find('img', {'id': 'landingImage'})
            if img_elem:
                for attr in ['data-old-hires', 'data-a-dynamic-image', 'src']:
                    if attr in img_elem.attrs:
                        if attr == 'data-a-dynamic-image':
                            try:
                                img_data = json.loads(img_elem[attr])
                                product['image_url'] = list(img_data.keys())[0]
                                image_found = True
                                break
                            except:
                                pass
                        else:
                            product['image_url'] = img_elem[attr]
                            image_found = True
                            break
            
            # Method 2: Main image container
            if not image_found:
                img_container = soup.find('div', {'id': 'main-image-container'})
                if img_container:
                    img = img_container.find('img')
                    if img and img.get('src'):
                        product['image_url'] = img['src']
                        image_found = True
            
            if image_found:
                print(f"✓ Image found")
            
            # FEATURES
            print("🔍 Extracting features...")
            features = []
            feature_div = soup.find('div', {'id': 'feature-bullets'})
            if feature_div:
                bullets = feature_div.find_all('span', {'class': 'a-list-item'})
                for bullet in bullets[:4]:
                    text = self.clean_text(bullet.text)
                    if text and len(text) > 10 and not text.startswith('Make sure'):
                        features.append(text[:80])
            
            if features:
                product['features'] = features
                print(f"✓ Features: {len(features)} found")
            
            # Generate caption with affiliate link
            product['caption'] = self.generate_caption_with_link(product)
            
            # Check success
            if 'title' in product and ('price' in product or 'image_url' in product):
                product['success'] = True
                print("\n✅ Product scraped successfully!")
            else:
                print("\n⚠️ Incomplete data")
                
            return product
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None
    
    def generate_caption_with_link(self, product):
        """Generate Instagram caption with affiliate link (NO search instructions)"""
        
        templates = [
            # Template 1: Deal Focus
            f"""🔥 MEGA DEAL ALERT! 🔥

{product.get('name', 'Amazing Product')}

💥 {product.get('discount', 'HUGE')} DISCOUNT
💰 Just {product.get('price', '₹XXX')}
⭐ Rated {product.get('rating', '4.5')}/5

✨ Premium Quality
✨ Fast Delivery
✨ 100% Genuine

🛒 GET THIS DEAL:
👉 Link in bio 
🔗 {product.get('affiliate_link', '')}

⏰ Limited stock! Order now!

#AmazonDeals #India #Shopping #Deals #Discount #OnlineShopping #BestPrice #FlashSale #LimitedOffer #PandaLoon #ShopNow #AmazonFinds #DealOfTheDay #LinkInBio""",

            # Template 2: Product Focus
            f"""✨ Transform Your Space! ✨

{product.get('name', 'Premium Product')}

🏷️ Special Price: {product.get('price', 'Best Price')}
📊 MRP: {product.get('original_price', 'Higher Price')}
💯 Save {product.get('discount', 'Big')} Today!

Why customers love it:
• Top-rated with {product.get('rating', '4.5')}/5 stars
• Premium quality guaranteed
• Fast Amazon delivery
• Easy returns

📱 SHOP NOW:
🔗 Link in bio 
👇 Direct link:
{product.get('affiliate_link', '')}

#HomeDecor #Amazon #OnlineShoppingIndia #InteriorDesign #HomeStyling #Decor #BestDeals #QualityProducts #PandaLoon #LinkInBio #ShopNow""",

            # Template 3: Urgency Focus
            f"""⚡ {product.get('discount', '60%')} OFF - TODAY ONLY! ⚡

{product.get('name', 'Hot Deal')}

🎯 Deal Price: {product.get('price', 'Lowest Price')}
❌ Was: {product.get('original_price', 'Original Price')}
⭐ Customer Rating: {product.get('rating', '4.5')}/5

🚀 Why Buy Now?
✅ Limited time offer
✅ Authentic product
✅ Prime delivery
✅ Thousands sold

👇 GRAB THIS DEAL NOW
📱 Link in bio
🔗 {product.get('affiliate_link', '')}

#FlashSale #TodayOnly #AmazonSale #LimitedTime #HurryUp #DealAlert #Discounts #ShoppingIndia #BestPrice #PandaLoon #LinkInBio #OrderNow"""
        ]
        
        # Rotate templates based on position
        return templates[(product.get('position', 1) - 1) % 3]
    
    def scrape_all(self, urls):
        """Scrape all URLs"""
        print("\n" + "="*60)
        print("🛒 AMAZON PRODUCT SCRAPER")
        print("="*60)
        print(f"URLs to scrape: {len(urls)}")
        print("="*60)
        
        for i, url in enumerate(urls[:15], 1):  # Max 15
            product = self.scrape_product(url, i)
            if product:
                self.products.append(product)
            
            if i < len(urls):
                print("\n⏳ Waiting 3 seconds...")
                time.sleep(3)
        
        # Summary
        successful = sum(1 for p in self.products if p and p.get('success'))
        print("\n" + "="*60)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {len(urls) - successful}")
        print("="*60)
    
    def save_results(self):
        """Save to JSON"""
        instagram_ready = []
        
        for product in self.products:
            if product and product.get('success'):
                instagram_ready.append({
                    'name': product.get('name', 'Product'),
                    'asin': product.get('asin'),
                    'image_url': product.get('image_url', ''),
                    'caption': product.get('caption'),
                    'price': product.get('price', ''),
                    'original_price': product.get('original_price', ''),
                    'discount': product.get('discount', ''),
                    'rating': product.get('rating', ''),
                    'affiliate_link': product.get('affiliate_link'),
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Save Instagram-ready file
        with open('instagram_ready.json', 'w', encoding='utf-8') as f:
            json.dump(instagram_ready, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved {len(instagram_ready)} products to instagram_ready.json")
        
        # Save detailed results for debugging
        with open('scrape_debug.json', 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        
        return len(instagram_ready)

# Main execution
if __name__ == "__main__":
    if not AMAZON_URLS:
        print("❌ No URLs added! Add Amazon URLs to AMAZON_URLS list")
        exit()
    
    scraper = WorkingAmazonScraper()
    scraper.scrape_all(AMAZON_URLS)
    count = scraper.save_results()
    
    if count > 0:
        print("\n✅ Ready for Instagram posting!")
        print("Next steps:")
        print("1. Run: python instagram_poster_updated.py")
        print("2. Run: python update_website.py")
    else:
        print("\n❌ No products scraped successfully")
        print("Check scrape_debug.json for details")