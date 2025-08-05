"""
update_website.py - Adds new products from instagram_ready.json to existing HTML
"""

from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

class WebsiteUpdater:
    def __init__(self):
        self.html_file = "index.html"
        self.json_file = "insta_ready_2.json"
        self.existing_asins = set()
        
    def load_existing_html(self):
        """Load existing HTML or create new one"""
        if os.path.exists(self.html_file):
            print(f"📄 Loading existing {self.html_file}")
            with open(self.html_file, 'r', encoding='utf-8') as f:
                return BeautifulSoup(f.read(), 'html.parser')
        else:
            print(f"🆕 Creating new {self.html_file}")
            return self.create_new_html()
    
    def create_new_html(self):
        """Create new HTML structure matching your template"""
        html_template = """<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<title>PandaLoon Deals</title>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<style>
body { background-color: #f9f3e7; color: #3d2b1f; font-family: 'Segoe UI', sans-serif; margin: 0; }
header { background-color: #b08968; padding: 20px; text-align: center; }
header img { height: 60px; }
h1 { color: white; font-size: 28px; margin: 10px 0; }
section { padding: 20px; }
h2 { color: #6b4c3b; border-bottom: 2px solid #c7a17a; }
.product { background: #fff9f1; border: 1px solid #e1cdb5; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
.product img { width: 220px; height: auto; border-radius: 8px;}
.product .title { font-weight: bold; margin: 10px 0 5px; }
.product .price { color: #a86e39; font-weight: bold; }
.product a { background: #a86e39; color: white; padding: 8px 12px; display: inline-block; margin-top: 10px; text-decoration: none; border-radius: 4px; }
.updated { text-align: center; color: #888; font-size: 14px; margin: 20px; }
</style>
</head>
<body>
<header>
  <img src='https://pandaloon.in/logo.png' alt='PandaLoon Logo'>
  <h1>PandaLoon Curated Deals</h1>
</header>
<section><h2>Today's Deals</h2>
</section>
<section><h2>Home Decor</h2>
</section>
<section><h2>Electronics</h2>
</section>
<section><h2>Fashion</h2>
</section>
<div class="updated">Last updated: <span id="update-time"></span></div>
</body>
</html>"""
        return BeautifulSoup(html_template, 'html.parser')
    
    def get_existing_asins(self, soup):
        """Extract ASINs from existing products to avoid duplicates"""
        asins = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/dp/' in href:
                # Extract ASIN from URL
                parts = href.split('/dp/')
                if len(parts) > 1:
                    asin = parts[1].split('?')[0]
                    asins.add(asin)
        return asins
    
    def categorize_product(self, product_name):
        """Categorize product based on name"""
        name_lower = product_name.lower()
        
        # Category keywords
        home_keywords = ['lamp', 'light', 'decor', 'wall', 'ceiling', 'tissue', 'holder', 'painting', 'furniture', 'curtain', 'cushion', 'rug', 'vase']
        electronics_keywords = ['phone', 'laptop', 'headphone', 'speaker', 'charger', 'cable', 'mouse', 'keyboard', 'monitor', 'tablet']
        fashion_keywords = ['shirt', 'dress', 'shoe', 'bag', 'watch', 'jacket', 'jeans', 'saree', 'kurta', 'jewelry']
        
        for keyword in home_keywords:
            if keyword in name_lower:
                return "Home Decor"
        
        for keyword in electronics_keywords:
            if keyword in name_lower:
                return "Electronics"
                
        for keyword in fashion_keywords:
            if keyword in name_lower:
                return "Fashion"
        
        return "Today's Deals"  # Default category
    
    def create_product_element(self, product):
        """Create product HTML element"""
        product_html = f"""
<div class="product">
  <img src="{product.get('image_url', '')}" alt="{product.get('name', '')[:60]}">
  <div class="title">{product.get('name', 'Product')[:60]}</div>
  <div class="price">{product.get('price', '')} <small>(was {product.get('original_price', '')})</small></div>
  <a href="{product.get('affiliate_link', '')}" target="_blank">View Deal</a>
</div>
"""
        return BeautifulSoup(product_html, 'html.parser').find('div', class_='product')
    
    def update_html(self):
        """Main function to update HTML with new products"""
        # Load existing HTML
        soup = self.load_existing_html()
        
        # Get existing ASINs to avoid duplicates
        self.existing_asins = self.get_existing_asins(soup)
        print(f"📊 Found {len(self.existing_asins)} existing products")
        print(f"📝 Existing ASINs: {self.existing_asins}")
        
        # Load new products from JSON
        if not os.path.exists(self.json_file):
            print(f"❌ {self.json_file} not found!")
            return False
        
        with open(self.json_file, 'r', encoding='utf-8') as f:
            new_products = json.load(f)
        
        print(f"📦 Found {len(new_products)} products in {self.json_file}")
        
        # Add new products
        added_count = 0
        
        for product in new_products:
            asin = product.get('asin', '')
            print(f"🔍 Checking product: {product.get('name', '')[:30]}...")
            print(f"   ASIN: {asin}")
            print(f"   Is it in existing? {asin in self.existing_asins}")
            
            # Skip if already exists
            if asin in self.existing_asins:
                print(f"⏭️  Skipping duplicate: {product.get('name', '')[:40]}...")
                continue
            
            # Determine category
            category = self.categorize_product(product.get('name', ''))
            print(f"   Category determined: {category}")
            
            # Debug: Show all h2 tags
            all_h2 = soup.find_all('h2')
            print(f"   Available sections: {[h2.text for h2 in all_h2]}")
            
            # Find the section - look for exact text match
            section = None
            for h2 in soup.find_all('h2'):
                if h2.text.strip() == category:
                    section = h2.parent
                    print(f"   Found section: {category}")
                    break
            
            # If section doesn't exist, use Today's Deals
            if not section:
                print(f"   Section '{category}' not found, looking for 'Today's Deals'")
                for h2 in soup.find_all('h2'):
                    if h2.text.strip() == "Today's Deals":
                        section = h2.parent
                        print(f"   Found 'Today's Deals' section")
                        break
            
            # Last resort - use first section
            if not section and len(all_h2) > 0:
                print(f"   Using first available section as fallback")
                section = all_h2[0].parent
            
            if section:
                print(f"   Adding product to section...")
                # Create product element
                product_elem = self.create_product_element(product)
                
                # Add to the beginning of the section (newest first)
                h2_tag = section.find('h2')
                if h2_tag:
                    h2_tag.insert_after(product_elem)
                else:
                    section.append(product_elem)
                
                added_count += 1
                print(f"✅ Added to {category}: {product.get('name', '')[:40]}...")
            else:
                print(f"❌ ERROR: Could not find any section to add product!")
        
        # Update timestamp
        time_elem = soup.find('span', id='update-time')
        if time_elem:
            time_elem.string = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        
        # Save updated HTML
        with open(self.html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        print(f"\n📊 Summary:")
        print(f"✅ Added {added_count} new products")
        print(f"📄 Updated {self.html_file}")
        
        return True

# Main execution
if __name__ == "__main__":
    print("🌐 PANDALOON WEBSITE UPDATER")
    print("="*60)
    
    updater = WebsiteUpdater()
    success = updater.update_html()
    
    if success:
        print("\n✅ Website updated successfully!")
        print(f"📄 Open {updater.html_file} in your browser")
    else:
        print("\n❌ Update failed!")