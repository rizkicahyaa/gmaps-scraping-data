from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

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
        "https://www.google.com/maps/place/Museum+Sonobudoyo+Unit+I/@-7.8002929,110.3558644,15z/data=!4m10!1m2!2m1!1smuseum+di+yogyakarta!3m6!1s0x2e7a578f83070a4f:0x9d10431ac43ec5ee!8m2!3d-7.802257!4d110.3639441!15sChRtdXNldW0gZGkgeW9neWFrYXJ0YZIBCmFydF9tdXNldW2qAUgQASoKIgZtdXNldW0oADIeEAEiGpOK9T_aCzU_-hEeoQ-wVlulzFcVFMxduoJ5MhgQAiIUbXVzZXVtIGRpIHlvZ3lha2FydGHgAQA!16s%2Fg%2F11h1v81d_?entry=ttu&g_ep=EgoyMDI1MTAyMC4wIKXMDSoASAFQAw%3D%3D",

        # kamu bisa tambahkan URL lain di sini:
        "https://www.google.com/maps/place/Vredeburg+Fort+Museum/@-7.8002929,110.3558644,15z/data=!4m10!1m2!2m1!1smuseum+di+yogyakarta!3m6!1s0x2e7a5788c0b3eecf:0xb9611ce0232a9ff8!8m2!3d-7.800293!4d110.3661642!15sChRtdXNldW0gZGkgeW9neWFrYXJ0YZIBDmhpc3RvcnlfbXVzZXVtqgFIEAEqCiIGbXVzZXVtKAAyHhABIhqTivU_2gs1P_oRHqEPsFZbpcxXFRTMXbqCeTIYEAIiFG11c2V1bSBkaSB5b2d5YWthcnRh4AEA!16zL20vMGJyZmY4?entry=ttu&g_ep=EgoyMDI1MTAyMC4wIKXMDSoASAFQAw%3D%3D",

        "https://www.google.com/maps/place/Monumen+Yogya+Kembali/@-7.7495904,110.3505524,15z/data=!4m10!1m2!2m1!1smuseum+yogyakarta!3m6!1s0x2e7a58f99013c989:0x2a96db25b8ff4333!8m2!3d-7.7495904!4d110.3696068!15sChFtdXNldW0geW9neWFrYXJ0YZIBDmhpc3RvcnlfbXVzZXVtqgFFEAEqCiIGbXVzZXVtKCYyHhABIhqTis0cXmnBX-QZNwwhxtnIR-OEp7aqTEZxwzIVEAIiEW11c2V1bSB5b2d5YWthcnRh4AEA!16s%2Fm%2F0gfgg53?entry=ttu&g_ep=EgoyMDI1MTAyMi4wIKXMDSoASAFQAw%3D%3D",
        
        "https://www.google.com/maps/place/Affandi+Museum/@-7.782713,110.3773426,15z/data=!4m10!1m2!2m1!1smuseum+yogyakarta!3m6!1s0x2e7a59c49f681dbd:0x3e9d55bf26695d4a!8m2!3d-7.782713!4d110.396397!15sChFtdXNldW0geW9neWFrYXJ0YZIBCmFydF9tdXNldW2qAUUQASoKIgZtdXNldW0oJjIeEAEiGpOKzRxeacFf5Bk3DCHG2chH44SntqpMRnHDMhUQAiIRbXVzZXVtIHlvZ3lha2FydGHgAQA!16s%2Fm%2F05b4x2q?entry=ttu&g_ep=EgoyMDI1MTAyMi4wIKXMDSoASAFQAw%3D%3D"
    ]

    semua_ulasan = []
    for url in urls:
        hasil = scrape_google_maps_reviews(url, max_reviews=50, lang='id')
        semua_ulasan.extend(hasil)

    df = pd.DataFrame(semua_ulasan)
    df.to_csv("data_museum4.csv", index=False, encoding="utf-8")
    print(f"\n[INFO] Total {len(df)} ulasan berhasil disimpan ke 'data_museum4.csv'")
