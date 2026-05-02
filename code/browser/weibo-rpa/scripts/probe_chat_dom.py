#!/usr/bin/env python3
from __future__ import annotations

import json
from playwright.sync_api import sync_playwright

JS = r'''
() => {
  const els = Array.from(document.querySelectorAll('textarea,input,[contenteditable="true"],[role="textbox"],button,a,[role="button"]'));
  return els.slice(0, 500).map((el, i) => ({
    i,
    tag: el.tagName,
    type: el.getAttribute('type') || '',
    role: el.getAttribute('role') || '',
    cls: el.className || '',
    id: el.id || '',
    name: el.getAttribute('name') || '',
    placeholder: el.getAttribute('placeholder') || '',
    text: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 120),
    visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
  }));
}
'''

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0]
    data = page.evaluate(JS)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    browser.close()
