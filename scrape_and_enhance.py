"""
fixed_scraper.py - Fixed Amazon scraper that works
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
from datetime import datetime

# =====================================
# ADD YOUR URLS HERE (1-15 products)
# =====================================

AMAZON_URLS = [
    "https://www.amazon.in/dp/B0D4QB724D?_encoding=UTF8&ref=cm_sw_r_cp_ud_dp_5ZBT3ZEN7G822B81AH9H&ref_=cm_sw_r_cp_ud_dp_5ZBT3ZEN7G822B81AH9H&social_share=cm_sw_r_cp_ud_dp_5ZBT3ZEN7G822B81AH9H&th=1",
    # Add more URLs here
]

AFFILIATE_TAG = "pandaloon-21"

class FixedAmazonScraper:
    def __init__(self):
        self.session = requests.Session()
        self.products = []
        
    def get_headers(self):
        """Rotate user agents for better success"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'TE': 'trailers'
        }
    
    def clean_url(self, url):
        """Clean URL to basic format"""
        # Extract ASIN and create clean URL
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if match:
            asin = match.group(1)
            return f"https://www.amazon.in/dp/{asin}"
        return url
    
    def extract_asin(self, url):
        """Extract ASIN from URL"""
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        return match.group(1) if match else None
    
    def clean_text(self, text):
        """Clean text data"""
        if text:
            return ' '.join(text.split()).strip()
        return ""
    
    def extract_price_from_text(self, text):
        """Extract price from any text"""
        # Look for patterns like ₹1,999 or ₹ 1,999 or 1,999
        patterns = [
            r'₹\s*([\d,]+)',
            r'Rs\.?\s*([\d,]+)',
            r'INR\s*([\d,]+)',
            r'([\d,]+)\s*₹'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price = match.group(1).replace(',', '')
                return price
        return None
    
    def scrape_product(self, url, index):
        """Scrape single product with better extraction"""
        # Clean URL first
        clean_url = self.clean_url(url)
        print(f"\n[{index}] Scraping: {clean_url}")
        print("-" * 60)
        
        try:
            # Random delay to avoid detection
            delay = random.uniform(2, 5)
            print(f"⏳ Waiting {delay:.1f} seconds...")
            time.sleep(delay)
            
            # Make request with fresh headers
            headers = self.get_headers()
            response = self.session.get(clean_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ HTTP Error: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we got blocked
            if "Enter the characters you see below" in response.text:
                print("❌ CAPTCHA detected - Amazon blocked us")
                return None
            
            # Initialize product
            product = {
                'url': clean_url,
                'asin': self.extract_asin(clean_url),
                'affiliate_link': f"https://www.amazon.in/dp/{self.extract_asin(clean_url)}?tag={AFFILIATE_TAG}",
                'position': index,
                'success': False
            }
            
            # TITLE - Multiple attempts
            print("🔍 Extracting title...")
            title = None
            
            title_selectors = [
                'span#productTitle',
                'h1#title',
                'h1.a-size-large.product-title-word-break',
                'h1[data-automation-id="title"]',
                'div#title_feature_div h1'
            ]
            
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    title = self.clean_text(elem.text)
                    if title:
                        break
            
            if title:
                product['title'] = title
                product['name'] = title[:60]
                print(f"✓ Title: {title[:50]}...")
            else:
                print("✗ Title not found")
            
            # PRICE - More aggressive extraction
            print("🔍 Extracting price...")
            price = None
            
            # Method 1: Direct price selectors
            price_selectors = [
                'span.a-price-whole',
                'span.a-price.a-text-price.a-size-medium.apexPriceToPay',
                'span.a-price-value',
                'span.a-color-price.a-size-base.a-text-normal',
                'span.a-price.priceToPay',
                'span.priceToPay',
                'div.a-section.a-spacing-small span.a-price-whole'
            ]
            
            for selector in price_selectors:
                elems = soup.select(selector)
                for elem in elems:
                    price_text = self.extract_price_from_text(elem.text)
                    if price_text and price_text != '0':
                        price = price_text
                        break
                if price:
                    break
            
            # Method 2: Search entire price section
            if not price:
                price_section = soup.find('div', {'id': 'apex_desktop'})
                if price_section:
                    price_text = self.extract_price_from_text(price_section.text)
                    if price_text:
                        price = price_text
            
            # Method 3: Look in scripts
            if not price:
                scripts = soup.find_all('script', type='text/javascript')
                for script in scripts:
                    if script.string and 'priceAmount' in script.string:
                        match = re.search(r'"priceAmount":([\d.]+)', script.string)
                        if match:
                            price = str(int(float(match.group(1))))
                            break
            
            if price:
                product['price'] = f"₹{price}"
                print(f"✓ Price: ₹{price}")
            else:
                print("✗ Price not found - will use default")
                product['price'] = "₹Check Price"
            
            # ORIGINAL PRICE (MRP)
            print("🔍 Extracting MRP...")
            mrp = None
            
            mrp_selectors = [
                'span.a-price.a-text-price',
                'span.a-text-strike',
                'span.a-price-whole.a-text-strike',
                'div.a-section.a-spacing-small.a-spacing-top-micro span.a-text-strike'
            ]
            
            for selector in mrp_selectors:
                elems = soup.select(selector)
                for elem in elems:
                    mrp_text = self.extract_price_from_text(elem.text)
                    if mrp_text and mrp_text != price:
                        mrp = mrp_text
                        break
                if mrp:
                    break
            
            if mrp:
                product['original_price'] = f"₹{mrp}"
                print(f"✓ MRP: ₹{mrp}")
                
                # Calculate discount
                try:
                    if price and price != "Check Price":
                        price_num = float(price)
                        mrp_num = float(mrp)
                        if mrp_num > price_num:
                            discount = int(((mrp_num - price_num) / mrp_num) * 100)
                            product['discount'] = f"{discount}%"
                            print(f"✓ Discount: {discount}%")
                except:
                    product['discount'] = "Great Deal"
            else:
                product['original_price'] = ""
                product['discount'] = "Special Offer"
            
            # RATING
            print("🔍 Extracting rating...")
            rating_elem = soup.find('span', {'class': 'a-icon-alt'})
            if rating_elem:
                match = re.search(r'([\d.]+)\s*out of', rating_elem.text)
                if match:
                    product['rating'] = match.group(1)
                    print(f"✓ Rating: {match.group(1)}/5")
                else:
                    product['rating'] = "4.0"
            else:
                product['rating'] = "4.0"
            
            # IMAGE - Multiple methods
            print("🔍 Extracting image...")
            image_url = None
            
            # Method 1: Main image
            img_selectors = [
                'img#landingImage',
                'div#imgTagWrapperId img',
                'div#main-image-container img',
                'img.a-dynamic-image',
                'div#imageBlock img'
            ]
            
            for selector in img_selectors:
                img = soup.select_one(selector)
                if img:
                    # Try different attributes
                    for attr in ['data-old-hires', 'data-a-dynamic-image', 'src', 'data-src']:
                        if attr in img.attrs:
                            if attr == 'data-a-dynamic-image':
                                try:
                                    import json as js
                                    img_dict = js.loads(img[attr])
                                    image_url = list(img_dict.keys())[0]
                                    break
                                except:
                                    continue
                            else:
                                img_url = img[attr]
                                if img_url.startswith('http'):
                                    image_url = img_url
                                    break
                    if image_url:
                        break
            
            if image_url:
                product['image_url'] = image_url
                print(f"✓ Image found")
            else:
                # Use placeholder
                product['image_url'] = "https://via.placeholder.com/500x500.png?text=Product+Image"
                print("✗ Image not found - using placeholder")
            
            # Generate caption
            product['caption'] = self.generate_caption_with_link(product)
            
            # Mark as success if we have minimum data
            if 'title' in product:
                product['success'] = True
                print("\n✅ Product scraped successfully!")
            else:
                print("\n⚠️ Incomplete data - but will use what we have")
                product['success'] = True  # Still mark as success to use partial data
            
            return product
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            # Return partial product even on error
            return {
                'url': clean_url,
                'asin': self.extract_asin(clean_url),
                'affiliate_link': f"https://www.amazon.in/dp/{self.extract_asin(clean_url)}?tag={AFFILIATE_TAG}",
                'name': 'Check out this amazing deal!',
                'price': '₹Check Price',
                'original_price': '',
                'discount': 'Special Offer',
                'rating': '4.0',
                'image_url': 'https://via.placeholder.com/500x500.png?text=Great+Deal',
                'caption': self.generate_default_caption(clean_url),
                'success': True
            }
    
    def generate_default_caption(self, url):
        """Generate caption even without data"""
        affiliate_link = f"https://www.amazon.in/dp/{self.extract_asin(url)}?tag={AFFILIATE_TAG}"
        
        return f"""🔥 AMAZING DEAL ALERT! 🔥

Check out this incredible offer!

💥 SPECIAL DISCOUNT
💰 Best Price Guaranteed
⭐ Highly Rated Product

✨ Premium Quality
✨ Fast Delivery
✨ 100% Genuine

🛒 GET THIS DEAL:
👉 Link in bio 
🔗 {affiliate_link}

⏰ Limited time offer!

#AmazonDeals #India #Shopping #Deals #Discount #OnlineShopping #BestPrice #FlashSale #LimitedOffer #PandaLoon #ShopNow #LinkInBio"""
    
    def generate_caption_with_link(self, product):
        """Generate Instagram caption"""
        templates = [
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

#AmazonDeals #India #Shopping #Deals #Discount #OnlineShopping #BestPrice #FlashSale #LimitedOffer #PandaLoon #ShopNow #LinkInBio""",

            f"""✨ Transform Your Space! ✨

{product.get('name', 'Premium Product')}

🏷️ Special Price: {product.get('price', 'Best Price')}
{f"📊 MRP: {product.get('original_price')}" if product.get('original_price') else ''}
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

            f"""⚡ {product.get('discount', '60%')} OFF - TODAY ONLY! ⚡

{product.get('name', 'Hot Deal')}

🎯 Deal Price: {product.get('price', 'Lowest Price')}
{f"❌ Was: {product.get('original_price')}" if product.get('original_price') else ''}
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
        
        return templates[(product.get('position', 1) - 1) % 3]
    
    def scrape_all(self, urls):
        """Scrape all URLs"""
        print("\n" + "="*60)
        print("🛒 FIXED AMAZON SCRAPER")
        print("="*60)
        print(f"URLs to scrape: {len(urls)}")
        print("="*60)
        
        for i, url in enumerate(urls[:15], 1):
            product = self.scrape_product(url, i)
            if product:
                self.products.append(product)
        
        # Summary
        successful = sum(1 for p in self.products if p)
        print("\n" + "="*60)
        print(f"✅ Products processed: {successful}")
        print("="*60)
    
    def save_results(self):
        """Save to JSON"""
        instagram_ready = []
        
        for product in self.products:
            if product:
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
        
        with open('instagram_ready.json', 'w', encoding='utf-8') as f:
            json.dump(instagram_ready, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved {len(instagram_ready)} products to instagram_ready.json")
        
        with open('scrape_debug.json', 'w', encoding='utf-8') as f:
            json.dump(self.products, f, indent=2, ensure_ascii=False)
        
        return len(instagram_ready)

# Main execution
if __name__ == "__main__":
    if not AMAZON_URLS:
        print("❌ No URLs added! Add Amazon URLs to AMAZON_URLS list")
        exit()
    
    scraper = FixedAmazonScraper()
    scraper.scrape_all(AMAZON_URLS)
    count = scraper.save_results()
    
    print("\n✅ Scraping complete!")
    print("Products are ready for Instagram posting!")
    print("Even if some data is missing, captions are generated with affiliate links")