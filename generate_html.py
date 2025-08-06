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
        self.json_file = "insta_ready.json"
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
  <img src='Pandaloon_logo.png' alt='PandaLoon Logo'>
  <h1>PandaLoon Curated Deals</h1>
</header>
<section>
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
            
            # Skip if already exists
            if asin in self.existing_asins:
                print(f"⏭️  Skipping duplicate: {product.get('name', '')[:40]}...")
                continue
            
            # Find the LAST section (which has all the products)
            all_sections = soup.find_all('section')
            
            if len(all_sections) >= 2:  # Skip header, use the main product section
                target_section = all_sections[1]  # Second section has all products
            elif len(all_sections) >= 1:
                target_section = all_sections[0]  # Fallback to first section
            else:
                print("❌ No sections found! Creating new section...")
                # Create a new section if none exist
                new_section = soup.new_tag('section')
                soup.body.append(new_section)
                target_section = new_section
            
            print(f"✅ Adding product to main section...")
            
            # Create product element
            product_elem = self.create_product_element(product)
            
            # Add to the beginning of the section (newest first)
            if target_section.contents:
                target_section.insert(0, product_elem)
            else:
                target_section.append(product_elem)
            
            added_count += 1
            print(f"✅ Added: {product.get('name', '')[:40]}...")
        
        # Update timestamp - create if doesn't exist
        time_elem = soup.find('span', id='update-time')
        if not time_elem:
            # Create timestamp section if it doesn't exist
            timestamp_div = soup.new_tag('div', class_='updated')
            timestamp_div.string = f"Last updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}"
            soup.body.append(timestamp_div)
        else:
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