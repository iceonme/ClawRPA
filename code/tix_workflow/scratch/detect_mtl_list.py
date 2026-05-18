from playwright.sync_api import sync_playwright

def body_text_probe():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp('http://localhost:9222')
        context = browser.contexts[0]
        
        target_page = None
        for page in context.pages:
            if "seat-and-seatplan" in page.url:
                target_page = page
                break
        
        if not target_page:
            print("[Error] No price page found!")
            return

        print(f"[Probe] Inspecting Body of: {target_page.url}")
        
        # 1. 打印全文关键字搜索结果
        full_text = target_page.inner_text("body")
        print(f"Full Text Length: {len(full_text)}")
        if "票面" in full_text:
            print("FOUND keyword '票面' in body!")
        else:
            print("NOT FOUND '票面' in body. Page might be empty or loading.")

        # 2. 找到包含 '票面' 的元素的类名
        classes = target_page.evaluate("""() => {
            const results = [];
            const els = document.querySelectorAll('*');
            for(const el of els) {
                if(el.innerText && el.innerText.includes('票面') && el.innerText.length < 50) {
                    results.push({tag: el.tagName, cls: el.className, text: el.innerText});
                }
            }
            return results;
        }""")
        print(f"\nFound {len(classes)} elements with '票面':")
        for c in classes[:10]:
            print(f"<{c['tag']}> class='{c['cls']}' | Text: {c['text']}")

if __name__ == "__main__":
    body_text_probe()
