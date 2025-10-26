from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# sesuaikan jumlah data yang ingin di scraping, contoh max_reviews=50
def scrape_google_maps_reviews(url, max_reviews=50, lang='id'):
    options = Options()
    options.add_argument("--headless=new")  # biar jalan di background
    options.add_argument(f"--lang={lang}")
    options.add_argument(f"accept-language={lang},{lang.upper()}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    print(f"[INFO] Membuka halaman: {url}")
    driver.get(url)
    time.sleep(5)

    # Ambil nama tempat
    try:
        nama_tempat_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "DUwDvf"))
        )
        nama_tempat = nama_tempat_el.text.strip()
    except:
        nama_tempat = "Unknown"

    print(f"[INFO] Mengambil ulasan untuk: {nama_tempat}")

    # Klik tombol “Ulasan lainnya”
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[.//span[contains(text(),'Ulasan lainnya')] or .//span[contains(text(),'More reviews')]]"
            ))
        )
        btn.click()
        time.sleep(3)
    except Exception as e:
        print(f"[WARNING] Tombol 'Ulasan lainnya' tidak ditemukan: {e}")

    reviews, seen = [], set()

    # Cari area scrollable (panel ulasan)
    try:
        scrollable_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "div.m6QErb.DxyBCb.kA9KIf.dS8AEf"
            ))
        )
    except:
        scrollable_div = driver.find_element(By.TAG_NAME, "body")

    scroll_count = 0
    max_scrolls = 500
    last_count = 0
    stagnation = 0

    while len(reviews) < max_reviews and scroll_count < max_scrolls:
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf, div.dS8AEf")

        for c in cards:
            try:
                user_el = c.find_element(By.CSS_SELECTOR, "div.d4r55")
                review_el = c.find_element(By.CSS_SELECTOR, "span.wiI7pd")
                rating_el = c.find_element(By.CSS_SELECTOR, "span.kvMYJc")
            except:
                continue

            review_text = review_el.text.strip()
            if not review_text:
                continue

            user = user_el.text.strip() if user_el else "Unknown"
            try:
                rating = rating_el.get_attribute("aria-label").split()[0]
            except:
                rating = "Unknown"

            key = (user, review_text)
            if key not in seen:
                seen.add(key)
                reviews.append({
                    "nama_tempat": nama_tempat,
                    "user": user,
                    "review": review_text,
                    "rating": rating
                })

                if len(reviews) % 100 == 0:
                    # Simpan checkpoint setiap 100 ulasan
                    pd.DataFrame(reviews).to_csv("ulasan_checkpoint.csv", index=False)
                    print(f"[INFO] Checkpoint: {len(reviews)} ulasan disimpan sementara.")

                if len(reviews) >= max_reviews:
                    break

        if len(reviews) >= max_reviews:
            break

        # Scroll ke bawah
        try:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
        except:
            driver.execute_script("window.scrollBy(0, window.innerHeight);")

        scroll_count += 1
        print(f"[INFO] Scroll ke-{scroll_count}, total ulasan: {len(reviews)}")

        time.sleep(3)

        # hentikan kalau tidak ada pertambahan ulasan dalam 5 kali scroll
        if len(reviews) == last_count:
            stagnation += 1
        else:
            stagnation = 0
        last_count = len(reviews)

        if stagnation >= 5:
            print("[INFO] Tidak ada ulasan baru, berhenti scroll.")
            break

    driver.quit()
    return reviews


# =============== MAIN PROGRAM ===============
if __name__ == "__main__":
    urls = [
        # masukkan url didalam string
        "",

        # bisa juga tambahkan URL lain di sini:
        "",

    ]

    semua_ulasan = []
    for url in urls:
        # sesuaikan jumlah data yang ingin di scraping, contoh max_reviews=50
        hasil = scrape_google_maps_reviews(url, max_reviews=50, lang='id')
        semua_ulasan.extend(hasil)

    df = pd.DataFrame(semua_ulasan)
    df.to_csv("hasil_scraping.csv", index=False, encoding="utf-8")
    print(f"\n[INFO] Total {len(df)} ulasan berhasil disimpan ke 'hasil_scraping.csv'")
