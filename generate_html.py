from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

class WebsiteUpdater:
    def __init__(self):
        self.html_file = "index.html"
        self.json_file = "insta_ready.json"
        self.existing_asins = set()
        # Define valid categories
        self.valid_categories = ["Electronics", "Home & Decor", "Fitness"]
        
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
        """Create new HTML structure with category sections"""
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
h2 { color: #6b4c3b; border-bottom: 2px solid #c7a17a; padding-bottom: 10px; margin-top: 30px; }
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
<!-- Category sections will be added here -->
<div class="updated">Last updated: <span id="update-time"></span></div>
</body>
</html>"""
        soup = BeautifulSoup(html_template, 'html.parser')
        
        # Create sections for each category
        timestamp = soup.find('div', class_='updated')
        for category in self.valid_categories:
            section = soup.new_tag('section')
            h2 = soup.new_tag('h2')
            h2.string = category
            section.append(h2)
            timestamp.insert_before(section)
        
        return soup
    
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
    
    def get_or_create_category_section(self, soup, category):
        """Get existing category section or create new one"""
        # Normalize category name
        if category not in self.valid_categories:
            print(f"⚠️ Unknown category '{category}', defaulting to 'Home & Decor'")
            category = "Home & Decor"
        
        # Look for existing category section
        for section in soup.find_all('section'):
            h2 = section.find('h2')
            if h2 and h2.text == category:
                return section
        
        # Create new category section if not found
        print(f"📁 Creating new section for category: {category}")
        new_section = soup.new_tag('section')
        h2 = soup.new_tag('h2')
        h2.string = category
        new_section.append(h2)
        
        # Insert before the timestamp div
        timestamp = soup.find('div', class_='updated')
        if timestamp:
            timestamp.insert_before(new_section)
        else:
            soup.body.append(new_section)
        
        return new_section
    
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
        """Main function to update HTML with new products organized by category"""
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
        
        # Track added products by category
        category_counts = {cat: 0 for cat in self.valid_categories}
        category_counts['Other'] = 0
        added_count = 0
        
        for product in new_products:
            asin = product.get('asin', '')
            category = product.get('category', 'Home & Decor')  # Default category if not specified
            
            print(f"🔍 Checking product: {product.get('name', '')[:30]}... (Category: {category})")
            
            # Skip if already exists
            if asin in self.existing_asins:
                print(f"⏭️  Skipping duplicate: {product.get('name', '')[:40]}...")
                continue
            
            # Get or create the appropriate category section
            target_section = self.get_or_create_category_section(soup, category)
            
            # Create product element
            product_elem = self.create_product_element(product)
            
            # Find the h2 tag and add product after it (newest first)
            h2_tag = target_section.find('h2')
            if h2_tag:
                # Insert right after the h2 tag (newest products at top)
                next_sibling = h2_tag.next_sibling
                if next_sibling and next_sibling.name == 'div':
                    # There are existing products, insert before the first one
                    h2_tag.insert_after(product_elem)
                else:
                    # No products yet in this category
                    target_section.append(product_elem)
            else:
                target_section.append(product_elem)
            
            added_count += 1
            
            # Track category counts
            if category in self.valid_categories:
                category_counts[category] += 1
            else:
                category_counts['Other'] += 1
            
            print(f"✅ Added to {category}: {product.get('name', '')[:40]}...")
        
        # Update timestamp
        time_elem = soup.find('span', id='update-time')
        if not time_elem:
            # Find or create timestamp
            timestamp_div = soup.find('div', class_='updated')
            if not timestamp_div:
                timestamp_div = soup.new_tag('div', class_='updated')
                timestamp_div.string = "Last updated: "
                span = soup.new_tag('span', id='update-time')
                span.string = datetime.now().strftime('%Y-%m-%d %I:%M %p')
                timestamp_div.append(span)
                soup.body.append(timestamp_div)
            else:
                span = soup.new_tag('span', id='update-time')
                span.string = datetime.now().strftime('%Y-%m-%d %I:%M %p')
                timestamp_div.clear()
                timestamp_div.string = "Last updated: "
                timestamp_div.append(span)
        else:
            time_elem.string = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        
        # Save updated HTML
        with open(self.html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        
        print(f"\n📊 Summary:")
        print(f"✅ Added {added_count} new products")
        for cat, count in category_counts.items():
            if count > 0:
                print(f"   - {cat}: {count} products")
        print(f"📄 Updated {self.html_file}")
        
        return True

# Main execution
if __name__ == "__main__":
    print("🌐 PANDALOON WEBSITE UPDATER WITH CATEGORIES")
    print("="*60)
    
    updater = WebsiteUpdater()
    success = updater.update_html()
    
    if success:
        print("\n✅ Website updated successfully!")
        print(f"📄 Open {updater.html_file} in your browser")
    else:
        print("\n❌ Update failed!")
