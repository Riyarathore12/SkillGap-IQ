from playwright.sync_api import sync_playwright
from pathlib import Path
Path('screenshots').mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(args=['--no-sandbox']); page=browser.new_page(viewport={'width':1440,'height':1000}); page.goto('http://localhost:8501',timeout=90000); page.get_by_text('Postings',exact=True).first.wait_for(timeout=90000); page.wait_for_timeout(3000)
 for i,t in enumerate(['Market overview','Skill gap','SQL lab','Findings'],1):
  page.get_by_role('tab',name=t).click();page.wait_for_timeout(1500);page.screenshot(path=f'screenshots/{i:02}.png',full_page=True)
 browser.close()
