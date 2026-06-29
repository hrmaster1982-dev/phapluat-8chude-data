# -*- coding: utf-8 -*-
"""
Scraper pháp luật 8 chủ đề v2 — 15 năm (2011-2026).

Chiến lược 2 bước:
  Bước 1 (--history / tự động khi thiếu VB): browser-use + qwen3-vl:4b local
            → search congbao.chinhphu.vn theo topic+year → lấy URLs
  Bước 2 (daily, --daily): RSS Công Báo mới nhất → bổ sung VB tháng này

Chạy qua runner_8800.py hoặc trực tiếp:
  python3 scraper_v2.py            # đầy đủ (daily + history nếu còn thiếu)
  python3 scraper_v2.py --daily    # chỉ RSS, nhanh
  python3 scraper_v2.py --history  # chỉ browser-use 15 năm, chạy nền
"""

import os, re, json, sys, time, urllib.request, urllib.error, urllib.parse, subprocess, ssl
from datetime import datetime

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS      = os.path.join(HERE, "docs")
INDEX_FILE = os.path.join(HERE, "index.json")
STATE_FILE = os.path.join(HERE, "_state.json")          # state v1 (compat)
STATE2_FILE = os.path.join(HERE, "_state_v2.json")      # state v2 (history tracker)
TG_CFG = (r"D:\claude\SHARED\tg-n8n-bot\telegram_config.json"
          if os.name == "nt"
          else "/mnt/d/claude/SHARED/tg-n8n-bot/telegram_config.json")

TARGET      = 50
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124"}
BASE_URL    = "https://congbao.chinhphu.vn"
SEARXNG_URL = "http://localhost:8888"
RSS_ISSUES = BASE_URL + "/cac-so-cong-bao-moi-dang.rss"
RSS_VANBAN = BASE_URL + "/cac-van-ban-moi-ban-hanh.rss"
YEARS     = list(range(2011, 2027))

TOPICS = {
    "hdld":          {"name": "Hợp đồng lao động",    "kw": ["hợp đồng lao động", "bộ luật lao động", "người lao động", "tiền lương", "lương tối thiểu", "an toàn lao động", "kỷ luật lao động", "làm thêm giờ", "nghỉ phép", "chấm dứt hợp đồng", "sa thải", "thử việc"]},
    "bhxh":          {"name": "Bảo hiểm xã hội",       "kw": ["bảo hiểm xã hội", "bhxh", "bảo hiểm y tế", "bhyt", "bảo hiểm thất nghiệp", "hưu trí", "thai sản", "ốm đau", "tai nạn lao động", "đóng bảo hiểm"]},
    "thue_tncn":     {"name": "Thuế TNCN",              "kw": ["thuế thu nhập cá nhân", "tncn", "giảm trừ gia cảnh", "quyết toán thuế", "thu nhập tiền lương", "khấu trừ thuế", "biểu thuế lũy tiến"]},
    "cong_doan":     {"name": "Công đoàn",              "kw": ["công đoàn", "kinh phí công đoàn", "đoàn phí", "tổ chức công đoàn", "liên đoàn lao động", "cán bộ công đoàn"]},
    "hd_khoan":      {"name": "Hợp đồng khoán",         "kw": ["hợp đồng khoán", "khoán việc", "cộng tác viên", "hợp đồng dịch vụ", "bhxh cộng tác viên"]},
    "hd_kinh_te":    {"name": "Hợp đồng kinh tế",       "kw": ["hợp đồng kinh tế", "hợp đồng thương mại", "mua bán hàng hóa", "phạt vi phạm hợp đồng", "luật thương mại", "bộ luật dân sự"]},
    "uu_dai_dt":     {"name": "Ưu đãi đầu tư",          "kw": ["ưu đãi đầu tư", "miễn thuế đầu tư", "khu công nghiệp", "khu kinh tế", "dự án đầu tư", "luật đầu tư", "giấy chứng nhận đầu tư"]},
    "chinh_sach_dn": {"name": "Chính sách doanh nghiệp","kw": ["doanh nghiệp", "lương tối thiểu vùng", "thuế thu nhập doanh nghiệp", "tndn", "đăng ký kinh doanh", "hộ kinh doanh", "hỗ trợ doanh nghiệp"]},
}
LOAI_PRIORITY = {"luat":1,"bo-luat":1,"nghi-dinh":2,"thong-tu":3,"thong-tu-lien-tich":3,"nghi-quyet":4,"quyet-dinh":5,"cong-van":6,"van-ban-hop-nhat":7}
LOAI_NAME = {"luat":"Luật","bo-luat":"Bộ luật","nghi-dinh":"Nghị định","thong-tu":"Thông tư","thong-tu-lien-tich":"TT Liên tịch","nghi-quyet":"NQ","quyet-dinh":"QĐ","cong-van":"CV","van-ban-hop-nhat":"VB HN"}

# ─────────────── UTILS ───────────────────────────────────────────────────────

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    try:
        return urllib.request.urlopen(req, timeout=timeout).read()
    except ssl.SSLError:
        return urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx).read()

def fetch_text(url, timeout=30):
    return fetch(url, timeout).decode("utf-8", "ignore")

def slug_of(url):
    parts = url.rstrip("/").split("/")
    last = parts[-1].replace(".htm","")
    if "/van-ban/" in url and re.fullmatch(r"\d+", last) and len(parts) >= 2:
        return parts[-2]
    return last

def _norm(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()

def topic_of(slug, desc):
    text = (slug + " " + desc).lower()
    text_n = _norm(slug + " " + desc)
    best, best_score = None, 0
    for tk, td in TOPICS.items():
        score = sum(len(kw) for kw in td["kw"] if kw.lower() in text or _norm(kw) in text_n)
        if score > best_score:
            best_score, best = score, tk
    return best if best_score > 0 else None

def loai_priority(slug):
    for prefix, pri in sorted(LOAI_PRIORITY.items(), key=lambda x:-len(x[0])):
        if slug.startswith(prefix+"-so-") or slug.startswith(prefix+"-"):
            m = re.search(r"-(\d{4})-", slug)
            return pri, LOAI_NAME.get(prefix, prefix), int(m.group(1)) if m else 0
    return 99, "Khác", 0

def pdf_url_of(html):
    clean = html.replace("&amp;","&")
    for pat in [r"https://congbaocdn\.chinhphu\.vn/[^\"'\s<>]+?\.pdf",
                r"https://g7\.cdnchinhphu\.vn/api/download/stream\?[^\"'\s<>]+"]:
        m = re.search(pat, clean)
        if m: return m.group(0)
    return None

def load_json(p, d):
    try: return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d
    except: return d

def save_json(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def log(msg): print(msg, flush=True)

# ─────────────── PROCESS 1 VB ────────────────────────────────────────────────

def process_vb(vb_url, desc, state, index):
    slug = slug_of(vb_url)
    pv = state.setdefault("processed_vb", {})
    if slug in pv:
        return None
    pri, loai, nam = loai_priority(slug)
    topic = topic_of(slug, desc)
    if not topic:
        pv[slug] = "no_topic"; return None
    if state.get("count", {}).get(topic, 0) >= TARGET:
        pv[slug] = "topic_full"; return None
    log(f"  [{loai}/{nam}] {slug[:55]} → {TOPICS[topic]['name']}")
    try:
        page = fetch_text(vb_url)
        pdf_url = pdf_url_of(page)
        # Nếu không có PDF trên main page → thử sub-page /van-ban/{slug}/{doc_id}
        if not pdf_url:
            sub_ids = list(dict.fromkeys(re.findall(
                r'/van-ban/' + re.escape(slug) + r'/(\d+)', page)))
            for doc_id in sub_ids[:3]:
                sub_html = fetch_text(f"{BASE_URL}/van-ban/{slug}/{doc_id}.htm")
                pdf_url = pdf_url_of(sub_html)
                if pdf_url:
                    break
        if not pdf_url:
            pv[slug] = "no_pdf"; return None
        pdf_data = fetch(pdf_url)
        os.makedirs(os.path.join(DOCS, topic), exist_ok=True)
        open(os.path.join(DOCS, topic, slug+".pdf"), "wb").write(pdf_data)
        try:
            import fitz
            full_text = "\n".join(p.get_text() for p in fitz.open(stream=pdf_data, filetype="pdf"))
        except: full_text = "(PDF không trích text)"
        open(os.path.join(DOCS, topic, slug+".txt"), "w", encoding="utf-8").write(full_text)
        meta = {"so_hieu": slug, "slug": slug, "loai": loai, "loai_priority": pri,
                "nam": nam, "topic_key": topic, "topic_name": TOPICS[topic]["name"],
                "nguon_url": vb_url, "pdf_url": pdf_url,
                "pdf_path": f"docs/{topic}/{slug}.pdf", "txt_path": f"docs/{topic}/{slug}.txt",
                "mo_ta": desc[:300], "full_text": full_text,
                "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
        save_json(os.path.join(DOCS, topic, slug+".json"), meta)
        pv[slug] = topic
        state.setdefault("count", {})[topic] = state["count"].get(topic, 0) + 1
        index.append({"so_hieu": slug, "slug": slug, "loai": loai, "loai_priority": pri,
                      "nam": nam, "topic_key": topic, "topic_name": TOPICS[topic]["name"],
                      "nguon_url": vb_url, "crawled_at": meta["crawled_at"]})
        log(f"    ✓ docs/{topic}/{slug}.txt")
        return topic
    except Exception as e:
        log(f"    LỖI: {str(e)[:100]}")
        pv[slug] = "error"; return None

# ─────────────── DAILY: RSS ──────────────────────────────────────────────────

def run_daily(state, index):
    added = 0
    for rss_url in [RSS_ISSUES, RSS_VANBAN]:
        log(f"\n[RSS] {rss_url}")
        try:
            xml = fetch_text(rss_url)
            items = re.findall(r"<item>(.*?)</item>", xml, re.S)
            log(f"  → {len(items)} items")
            for it in items:
                link = (re.search(r"<link>(.*?)</link>", it, re.S) or type("",(),{"group":lambda *a:""})()).group(1).strip()
                desc = (re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", it, re.S) or type("",(),{"group":lambda *a:""})()).group(1).strip()
                if not link: continue
                if "congbao.chinhphu.vn" not in link: continue
                if "/cong-bao/" in link:
                    # Số Công báo → lấy VB bên trong
                    si = slug_of(link)
                    if si in state.get("processed_issues", []): continue
                    try:
                        html = fetch_text(link)
                        vb_links = [BASE_URL + m for m in re.findall(r'href="(/van-ban/[a-z0-9-]+-\d+/\d+\.htm)"', html)]
                        vb_links += re.findall(r'href="(https://congbao\.chinhphu\.vn/van-ban/[^"]+)"', html)
                        vb_links = list(dict.fromkeys(vb_links))
                        for vb in sorted(vb_links, key=lambda u: loai_priority(slug_of(u))[0]):
                            r = process_vb(vb, desc, state, index)
                            if r: added += 1
                        state.setdefault("processed_issues", []).append(si)
                    except Exception as e:
                        log(f"  LỖI số CB: {e}")
                elif "/van-ban/" in link:
                    r = process_vb(link, desc, state, index)
                    if r: added += 1
        except Exception as e:
            log(f"  LỖI RSS: {e}")
    return added

# ─────────────── HISTORY: SearXNG (thay browser-use) ────────────────────────

def _searxng_search(query, pageno=1, timeout=12):
    """Tìm trên SearXNG, trả về list URL congbao/van-ban tìm được."""
    params = urllib.parse.urlencode({"q": query, "format": "json", "pageno": pageno})
    url = f"{SEARXNG_URL}/search?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PL-Crawler/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read())
        urls = [r["url"] for r in data.get("results", [])
                if "congbao.chinhphu.vn/van-ban/" in r.get("url", "")]
        return urls
    except Exception as e:
        log(f"    [searxng] LỖI: {str(e)[:80]}")
        return []

def _searxng_collect_urls(topic_key, year):
    """
    Tổng hợp URL cho 1 topic × 1 year qua SearXNG.
    Dùng các keyword × 3 page mỗi keyword → tối đa ~90 URL candidates.
    Delay 1.5s giữa queries để tránh rate-limit upstream (Google/Bing).
    """
    keywords = TOPICS[topic_key]["kw"][:4]
    seen = set()
    urls = []
    for kw in keywords:
        # Query 1: site filter + keyword + year
        for q in [f"site:congbao.chinhphu.vn {kw} {year}",
                  f"congbao.chinhphu.vn \"{kw}\" {year}"]:
            for page in range(1, 3):
                batch = _searxng_search(q, pageno=page)
                for u in batch:
                    u_clean = u.rstrip("/").split("?")[0]
                    if u_clean not in seen:
                        seen.add(u_clean)
                        urls.append(u_clean)
                time.sleep(1.5)
                if not batch:
                    break
    return urls

def run_history(state, index, max_topic_year=200):
    """
    Cào lịch sử 15 năm qua SearXNG (không cần browser-use).
    max_topic_year: số topic×year xử lý mỗi lần gọi (mỗi iter ~5-30s).
    """
    # Kiểm tra SearXNG có sống không
    try:
        urllib.request.urlopen(f"{SEARXNG_URL}/", timeout=5)
    except Exception:
        log(f"[history] SearXNG không chạy ({SEARXNG_URL}). Bỏ qua history.")
        return 0

    state2 = load_json(STATE2_FILE, {})
    added = 0
    done = 0

    for tk in TOPICS:
        if state.get("count", {}).get(tk, 0) >= TARGET:
            continue
        years_done = state2.get(tk, {}).get("years_done", [])
        years_left = [y for y in YEARS if y not in years_done]
        if not years_left:
            state2.setdefault(tk, {})["all_years_done"] = True
            log(f"  [{tk}] đã cào hết 15 năm, có {state.get('count',{}).get(tk,0)} VB")
            save_json(STATE2_FILE, state2)
            continue

        for year in sorted(years_left, reverse=True):
            if done >= max_topic_year:
                break
            log(f"\n[searxng] {TOPICS[tk]['name']} / {year}")
            candidates = _searxng_collect_urls(tk, year)
            log(f"  → {len(candidates)} URL candidates")
            for url in sorted(candidates, key=lambda u: loai_priority(slug_of(u))[0]):
                if state.get("count", {}).get(tk, 0) >= TARGET:
                    break
                r = process_vb(url, TOPICS[tk]["name"], state, index)
                if r:
                    added += 1
            save_json(STATE_FILE, state)
            save_json(INDEX_FILE, index)
            state2.setdefault(tk, {}).setdefault("years_done", [])
            if year not in state2[tk]["years_done"]:
                state2[tk]["years_done"].append(year)
            state2[tk]["all_years_done"] = len(state2[tk]["years_done"]) >= len(YEARS)
            save_json(STATE2_FILE, state2)
            done += 1
        if done >= max_topic_year:
            break
    return added

# ─────────────── HISTORY: Browse theo cơ quan ban hành ──────────────────────

# Cơ quan → c-number trên congbao.chinhphu.vn
AGENCY_CATS = {
    "chinh_phu":   ("chinh-phu",   1),   # Chính phủ (Nghị định CP)
    "bldtbxh":     ("bldtbxh",     9),   # Bộ Lao động
    "btc":         ("btc",        10),   # Bộ Tài chính
    "bkhdt":       ("bkhdt",      19),   # Bộ Kế hoạch và Đầu tư
    "thu_tuong":   ("thu-tuong",   2),   # Thủ tướng (QĐ TTg)
    "ngan_hang":   ("nhnn",        7),   # Ngân hàng Nhà nước
    "quoc_hoi":    ("quoc-hoi",   31),   # Quốc hội (Luật, NQ)
}

# Mỗi topic nên browse ở cơ quan nào
TOPIC_AGENCIES = {
    "hdld":          ["bldtbxh", "chinh_phu", "quoc_hoi"],
    "bhxh":          ["bldtbxh", "chinh_phu", "quoc_hoi"],
    "thue_tncn":     ["btc", "chinh_phu", "quoc_hoi"],
    "cong_doan":     ["bldtbxh", "chinh_phu", "quoc_hoi"],
    "hd_khoan":      ["bldtbxh", "chinh_phu"],
    "hd_kinh_te":    ["chinh_phu", "quoc_hoi"],
    "uu_dai_dt":     ["bkhdt", "chinh_phu", "quoc_hoi", "thu_tuong"],
    "chinh_sach_dn": ["chinh_phu", "btc", "quoc_hoi", "thu_tuong"],
}

def _browse_agency_page(agency_key, pageno=1):
    """Lấy danh sách URL VB từ 1 trang listing cơ quan."""
    slug, c_id = AGENCY_CATS[agency_key]
    url = f"{BASE_URL}/van-ban-dang-cong-bao/{slug}-c{c_id}/trang-{pageno}.htm"
    try:
        html = fetch_text(url, timeout=15)
        links = re.findall(r'href=\"(/van-ban/([^\"#]+)\.htm)\"', html)
        urls = list(dict.fromkeys(BASE_URL + h for h, s in links if s))
        return urls
    except Exception as e:
        log(f"    [browse] LỖI trang {agency_key}/p{pageno}: {str(e)[:60]}")
        return []

def run_history_browse(state, index, max_pages_per_agency=30):
    """
    Fallback: browse danh sách VB theo cơ quan ban hành (không cần SearXNG).
    Chạy khi SearXNG không tìm được đủ cho các topic còn thiếu.
    """
    added = 0
    for tk in TOPICS:
        if state.get("count", {}).get(tk, 0) >= TARGET:
            continue
        agencies = TOPIC_AGENCIES.get(tk)
        if not agencies:
            continue
        need = TARGET - state.get("count", {}).get(tk, 0)
        log(f"\n[browse] {TOPICS[tk]['name']} — cần thêm {need} VB")

        for agency_key in agencies:
            if state.get("count", {}).get(tk, 0) >= TARGET:
                break
            for page in range(1, max_pages_per_agency + 1):
                if state.get("count", {}).get(tk, 0) >= TARGET:
                    break
                urls = _browse_agency_page(agency_key, page)
                if not urls:
                    log(f"  [{agency_key}] hết trang tại p{page}")
                    break
                new_in_page = 0
                for url in sorted(urls, key=lambda u: loai_priority(slug_of(u))[0]):
                    if state.get("count", {}).get(tk, 0) >= TARGET:
                        break
                    r = process_vb(url, TOPICS[tk]["name"], state, index)
                    if r == tk:
                        added += 1
                        new_in_page += 1
                save_json(STATE_FILE, state)
                save_json(INDEX_FILE, index)
                cnt = state.get("count", {}).get(tk, 0)
                log(f"  [{agency_key}/p{page}] +{new_in_page} → {cnt}/{TARGET}")
                time.sleep(0.5)
    return added

# ─────────────── GIT PUSH ────────────────────────────────────────────────────

def git_push(added):
    if added == 0:
        log("[git] Không có VB mới, bỏ qua push.")
        return
    # Tìm git.exe (Path đầy đủ để chạy từ pythonw không có PATH)
    git_candidates = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        "git",
    ]
    git = next((g for g in git_candidates if g == "git" or os.path.exists(g)), "git")
    try:
        subprocess.run([git,"-C",HERE,"add","docs/","index.json","_state.json","_state_v2.json"],
                       check=True, capture_output=True)
        msg = f"cao {added} VB moi - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        r = subprocess.run([git,"-C",HERE,"commit","-m",msg],
                           capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if "nothing to commit" in (r.stdout or ""):
            log("[git] Không có thay đổi."); return
        r2 = subprocess.run([git,"-C",HERE,"push","origin","main"],
                            capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if r2.returncode == 0:
            log(f"[git] ✓ Pushed {added} VB lên GitHub.")
        else:
            log(f"[git] push LỖI: {(r2.stderr or r2.stdout or '')[:200]}")
    except Exception as e:
        log(f"[git] LỖI: {e}")

# ─────────────── TELEGRAM REPORT ─────────────────────────────────────────────

def send_telegram_report(state, added_today):
    if not os.path.exists(TG_CFG):
        log("[telegram] Không tìm thấy config, bỏ qua."); return
    cfg  = load_json(TG_CFG, {})
    token = cfg.get("bot_token","")
    chat  = cfg.get("allowed_chat_id","")
    if not token or not chat:
        log("[telegram] Thiếu token/chat_id."); return

    state2 = load_json(STATE2_FILE, {})
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    new_line = f"<b>{added_today} VB mới</b>" if added_today > 0 else "<b>Không có văn bản mới hôm nay</b>"
    lines = [f"📋 <b>BÁO CÁO PHÁP LUẬT 8 CHỦ ĐỀ</b> ({now})", f"Hôm nay thêm: {new_line}\n"]
    total = 0
    for tk, td in TOPICS.items():
        cnt  = state.get("count",{}).get(tk, 0)
        all_done = state2.get(tk,{}).get("all_years_done", False)
        years_done = len(state2.get(tk,{}).get("years_done",[]))
        total += cnt
        if cnt >= TARGET:
            icon = "✅"
            note = ""
        elif all_done:
            icon = "⚠️"
            note = f" (cào xong 15 năm, chỉ có {cnt} VB)"
        else:
            icon = "⏳"
            note = f" (đã cào {years_done}/15 năm)"
        lines.append(f"  {icon} {td['name']}: {cnt}/{TARGET}{note}")
    lines.append(f"\n📊 Tổng: {total}/400 VB")
    lines.append("🔗 github.com/hrmaster1982-dev/phapluat-8chude-data")

    msg = "\n".join(lines)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat, "text": msg, "parse_mode": "HTML"}).encode()
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json","User-Agent":"TGBot"})
        urllib.request.urlopen(req, timeout=20)
        log(f"[telegram] ✓ Đã gửi báo cáo lúc {now}")
    except Exception as e:
        log(f"[telegram] LỖI: {e}")

# ─────────────── MAIN ────────────────────────────────────────────────────────

def main():
    mode = "--daily" if "--daily" in sys.argv else ("--history" if "--history" in sys.argv else "full")
    log(f"=== SCRAPER PHAPLUAT 8 CHU DE v2 — {datetime.now().strftime('%Y-%m-%d %H:%M')} [mode={mode}] ===")

    for tk in TOPICS:
        os.makedirs(os.path.join(DOCS, tk), exist_ok=True)

    state = load_json(STATE_FILE, {"processed_vb":{}, "processed_issues":[], "count":{}})
    index = load_json(INDEX_FILE, [])
    added = 0

    if mode in ("full", "--daily"):
        log("\n── Daily RSS ──")
        added += run_daily(state, index)
        save_json(STATE_FILE, state)
        save_json(INDEX_FILE, index)

    if mode in ("full", "--history") or "--browse" in sys.argv:
        topics_need = [tk for tk in TOPICS if state.get("count",{}).get(tk,0) < TARGET]
        if topics_need:
            # BROWSE là phương thức chính — duyệt trực tiếp trang listing cơ quan
            # SearXNG bị loại khỏi primary vì Google/Bing không index đầy đủ congbao
            log(f"\n── Browse cơ quan (primary): {len(topics_need)} chủ đề còn thiếu ──")
            added += run_history_browse(state, index, max_pages_per_agency=40)
            save_json(STATE_FILE, state)
            save_json(INDEX_FILE, index)
            # SearXNG bổ sung nếu browse không đủ (chỉ khi SearXNG đang chạy)
            topics_still_need = [tk for tk in TOPICS if state.get("count",{}).get(tk,0) < TARGET]
            if topics_still_need and "--browse" not in sys.argv:
                try:
                    urllib.request.urlopen(f"{SEARXNG_URL}/", timeout=3)
                    log(f"\n── SearXNG bổ sung: {len(topics_still_need)} chủ đề chưa đủ ──")
                    added += run_history(state, index, max_topic_year=100)
                    save_json(STATE_FILE, state)
                    save_json(INDEX_FILE, index)
                except Exception:
                    log(f"[searxng] Không khả dụng, bỏ qua.")
        else:
            log("\n── Tất cả chủ đề đã đủ 50 VB ──")

    # Báo cáo
    log("\n" + "="*60)
    log(f"KẾT QUẢ: thêm {added} VB mới")
    log("="*60)
    state2 = load_json(STATE2_FILE, {})
    for tk, td in TOPICS.items():
        cnt = state.get("count",{}).get(tk, 0)
        all_done = state2.get(tk,{}).get("all_years_done", False)
        yrs = len(state2.get(tk,{}).get("years_done",[]))
        note = " [ĐỦ]" if cnt >= TARGET else (f" [cào xong 15 năm, CHỨNG MINH chỉ có {cnt} VB]" if all_done else f" [cào được {yrs}/15 năm]")
        log(f"  {td['name']:<30} {cnt:>3}/{TARGET}{note}")

    if "--no-push" not in sys.argv:
        git_push(added)
    send_telegram_report(state, added)

    # Tạo lại Excel vào mỗi thứ Hai (hoặc khi có VB mới)
    if added > 0 or datetime.now().weekday() == 0:
        try:
            import export_excel as _xl
            xl_path = _xl.main()
            log(f"[excel] ✓ {xl_path}")
        except Exception as e:
            log(f"[excel] Bỏ qua: {e}")

    log("\nXONG.")

if __name__ == "__main__":
    main()
