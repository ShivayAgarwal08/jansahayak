import urllib.request
import re

url = "https://jansahayak-two.vercel.app"
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as res:
        print("Vercel HTTP Status:", res.status)
        content = res.read().decode("utf-8")
        match = re.search(r'src="(/assets/index-[^"]+\.js)"', content)
        if match:
            asset_path = match.group(1)
            print("Live Vercel JS asset:", asset_path)
            js_url = "https://jansahayak-two.vercel.app" + asset_path
            js_req = urllib.request.Request(js_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(js_req, timeout=15) as js_res:
                js_content = js_res.read().decode("utf-8")
                print("Has 'Extracted Citizen Facts':", "Extracted Citizen Facts" in js_content)
                print("Has 'Prepare Application Draft for':", "Prepare Application Draft for" in js_content)
                print("Has 'Rule Engine Active':", "Rule Engine Active" in js_content)
                print("Has 'Phase 1 Grounded RAG':", "Phase 1 Grounded RAG" in js_content)
                backend_matches = re.findall(r'https://jansahayak-backend-[^"\',;)]+', js_content)
                print("Backend URL references found in live bundle:", set(backend_matches))
        else:
            print("No main JS bundle found in index.html")
except Exception as e:
    print("Vercel verification error:", e)
