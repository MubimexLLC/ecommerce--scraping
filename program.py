from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime
from urllib.parse import urljoin
from db_connection import get_connection

INSERT_IN_DB = True
BASE_URL = "https://rainbowcc.com.pk"
CATEGORY_URLS = [
    "https://rainbowcc.com.pk/catalog/promotion-32963/promotion-64468/food-promotion-lhr-skp-grw-93136",
    "https://rainbowcc.com.pk/catalog/ultra-fresh-23408/ultra-fresh-53220/vegetables-72722",
    "https://rainbowcc.com.pk/catalog/dry-fruits-33249/dry-fruits-65946/dry-fruits-93216",
    "https://rainbowcc.com.pk/catalog/grocery-23411/grocery-65141",
    "https://rainbowcc.com.pk/catalog/breakfast--dairy-23412/breakfast--dairy-53224/liquid-milk--cream-72766",
    "https://rainbowcc.com.pk/catalog/frozen-food-23413/frozen-food-53225/frozen-items-72770",
    "https://rainbowcc.com.pk/catalog/baby-products-23410/baby-products-53222/baby-milk-93065",
    "https://rainbowcc.com.pk/catalog/health--beauty-23409/health--beauty-53221/soap-72727",
    "https://rainbowcc.com.pk/catalog/household-23414/household-53226/tissue-rolls--wipes-72776",
    "https://rainbowcc.com.pk/catalog/cosmetics-23415/cosmetics-53227/lip-stick-92722",
    "https://rainbowcc.com.pk/catalog/beverages-23407/beverages-53219/juice-91730",
    "https://rainbowcc.com.pk/catalog/sweets--confectioneries-23416/sweets--confectioneries-53228/chocolate-72791",
]

conn = get_connection()
cursor = conn.cursor()

insert_query = """
    INSERT INTO [dbo].[Products]
        (Name, CategoryName, Price, OrignialPrice, Unit, ImageUrl, IsOutofStock, CreatedDate, SKU, Url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

update_query = """
    UPDATE [dbo].[Products]
    SET Name=%s, CategoryName=%s, Price=%s, OrignialPrice=%s, Unit=%s, ImageUrl=%s, IsOutofStock=%s, CreatedDate=%s, Url=%s
    WHERE SKU=%s
"""

service = Service(executable_path="C:\\webdriver\\chromedriver.exe")
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 30)

def get_image_url(image_elem):
    img_attrs = ["src", "data-src", "data-original", "data-lazy", "data-srcset"]
    for attr in img_attrs:
        val = image_elem.get_attribute(attr)
        if val and not val.startswith("data:image/gif;base64") and val.strip():
            if attr == "data-srcset":
                val = val.split(",")[0].strip().split(" ")[0]
            return urljoin(BASE_URL, val)
    return None

def product_data_changed(db_row, scraped_data):
    fields = ['Name', 'CategoryName', 'Price', 'OrignialPrice', 'Unit', 'ImageUrl', 'IsOutofStock', 'Url']
    for idx, field in enumerate(fields):
        db_val = db_row[idx]
        scr_val = scraped_data[field]
        if field in ('Price', 'OrignialPrice'):
            try:
                scr_num = float(scr_val) if scr_val is not None else 0.0
                db_num = float(db_val) if db_val is not None else 0.0
                if abs(scr_num - db_num) > 0.001:
                    return True
            except (ValueError, TypeError):
                if str(scr_val or "").strip() != str(db_val or "").strip():
                    return True
        elif field == 'IsOutofStock':
            try:
                scr_int = int(scr_val)
                db_int = int(db_val)
                if scr_int != db_int:
                    return True
            except (ValueError, TypeError):
                if str(scr_val or "").strip() != str(db_val or "").strip():
                    return True
        else:
            if str(scr_val or "").strip() != str(db_val or "").strip():
                return True
    return False

def select_location():
    driver.get(BASE_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Select City / Region']"))).send_keys("Lahore")
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Select Area / Sub Region']"))).send_keys("Airline Society")
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Select' and not(@disabled)]"))).click()
    time.sleep(5)

def scrape_category(url):
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(3)
    try:
        category_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Categories']")))
        category_button.click()
        time.sleep(2)
    except:
        pass
    try:
        see_more_btn = driver.find_element(By.XPATH, "//a[contains(text(),'See more')]")
        driver.execute_script("arguments[0].click();", see_more_btn)
        time.sleep(3)
    except:
        pass
    subcategories = []
    for ul in driver.find_elements(By.CSS_SELECTOR, "ul.MuiList-root"):
        try:
            header = ul.find_element(By.CSS_SELECTOR, "li.MuiListSubheader-root span").text.strip()
            if header.lower() == "brands":
                continue
        except:
            pass
        subcategories += ul.find_elements(By.CSS_SELECTOR, "li.MuiListItem-root label")
    for label in subcategories:
        subcat_name = label.text.strip()
        try:
            driver.execute_script("arguments[0].click();", label)
            time.sleep(5)
        except:
            continue
        scrape_products(subcat_name)

def scrape_products(category_name):
    while True:
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h4[title]")))
            product_cards = driver.find_elements(By.CSS_SELECTOR, "h4[title]")
            if not product_cards:
                break
        except:
            break
        for elem in product_cards:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            time.sleep(0.2)
        for elem in product_cards:
            try:
                name = elem.get_attribute("title").strip()
                container = elem.find_element(By.XPATH, "./ancestor::div[contains(@class,'hazle-product-item')]")
                try:
                    qty_elem = elem.find_element(By.XPATH, "./following::p[contains(@class,'product_item_description')]")
                    unit = qty_elem.get_attribute("title").strip()
                except:
                    unit = "N/A"
                try:
                    price_block = container.find_element(By.CSS_SELECTOR, "div.hazle-product-item_product_item_price_label__ET_we")
                    price_text = price_block.text.replace("Rs.", "").replace(",", "")
                    prices = [float(p) for p in price_text.split() if p.replace('.', '', 1).isdigit()]
                    price = prices[-1] if prices else None
                    original_price = prices[0] if len(prices) == 2 else None
                except:
                    price = original_price = None
                try:
                    image_elem = container.find_element(By.CSS_SELECTOR, "div.hazle-product-item_product_item_image_container__OOD5L img")
                    image_url = get_image_url(image_elem) or "[NO_VALID_IMAGE]"
                except:
                    image_url = "[ERROR_IMAGE]"
                try:
                    sku = container.get_attribute("id").split("-")[-1]
                except:
                    sku = "N/A"
                try:
                    container.find_element(By.XPATH, ".//div[contains(text(),'Out of Stock')]")
                    is_out = 1
                except:
                    is_out = 0
                product_slug = name.lower().replace(" ", "-")
                product_url = f"https://rainbowcc.com.pk/product/{product_slug}-{sku}"
                now = datetime.datetime.now()
                scraped_data = {
                    "Name": name,
                    "CategoryName": category_name,
                    "Price": price,
                    "OrignialPrice": original_price,
                    "Unit": unit,
                    "ImageUrl": image_url,
                    "IsOutofStock": is_out,
                    "Url": product_url
                }
                cursor.execute("SELECT * FROM Products WHERE SKU = %s", (sku,))
                existing = cursor.fetchone()
                if existing:
                    if product_data_changed(existing, scraped_data):
                        cursor.execute(update_query, (
                            name, category_name, price, original_price, unit,
                            image_url, is_out, now, product_url, sku
                        ))
                else:
                    cursor.execute(insert_query, (
                        name, category_name, price, original_price, unit,
                        image_url, is_out, now, sku, product_url
                    ))
                if INSERT_IN_DB:
                    conn.commit()
            except Exception as e:
                print(f"[ERROR] Product scraping failed: {e}")
        try:
            next_btn = driver.find_element(By.XPATH, "//button[contains(., 'Next')]")
            if next_btn.get_attribute("disabled"):
                break
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(3)
        except:
            break

def main():
    select_location()
    for url in CATEGORY_URLS:
        scrape_category(url)
    driver.quit()
    conn.close()

if __name__ == "__main__":
    main()
