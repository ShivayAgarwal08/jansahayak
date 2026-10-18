"""
JanSahayak Complete Live Production Verification Script
Tests all requirements against the deployed Render production instance.
"""
import urllib.request
import urllib.error
import json
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_URL = "https://jansahayak-backend-kvuq.onrender.com"

def request_json(path, method="GET", payload=None, headers=None):
    if headers is None:
        headers = {}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body
    except Exception as e:
        return 500, {"error": str(e)}

def main():
    results = {}
    print("=== LIVE PRODUCTION AUDIT START ===")

    # 1. Health checks
    status_health, data_health = request_json("/api/health")
    status_db, data_db = request_json("/api/health/db")
    results["health"] = {"status": status_health, "body": data_health}
    results["health_db"] = {"status": status_db, "body": data_db}
    print(f"1. /api/health: {status_health} -> {data_health}")
    print(f"   /api/health/db: {status_db} -> {data_db}")

    # 2. OpenAPI inspection
    status_openapi, data_openapi = request_json("/openapi.json")
    if status_openapi == 200:
        paths = list(data_openapi.get("paths", {}).keys())
        expected_routes = [
            "/api/assistant/documents",
            "/api/assistant/search-documents",
            "/api/voice/status",
            "/api/voice/languages",
            "/api/voice/stt",
            "/api/voice/tts",
            "/api/voice/translate",
            "/api/whatsapp/status",
            "/api/whatsapp/webhook"
        ]
        registered = {r: (r in paths) for r in expected_routes}
        results["routes"] = {"total_paths": len(paths), "registered_expected": registered}
        print(f"2. OpenAPI Routes (Total {len(paths)}): {registered}")
    else:
        results["routes"] = {"status": status_openapi}

    # 3. Documents endpoint
    status_docs, docs_data = request_json("/api/assistant/documents")
    results["documents"] = {
        "status": status_docs,
        "count": len(docs_data) if isinstance(docs_data, list) else 0,
        "docs_summary": [
            {
                "scheme_slug": d.get("scheme_slug"),
                "authority": d.get("authority"),
                "ref": d.get("document_reference"),
                "pages": d.get("total_pages"),
                "chunks": d.get("chunks_count"),
                "url": d.get("source_url")
            } for d in (docs_data if isinstance(docs_data, list) else [])
        ]
    }
    print(f"3. Seeded Documents in DB: {results['documents']['count']} official documents")

    # 4. Search documents endpoint
    status_search, search_data = request_json("/api/assistant/search-documents?query=farmer%20eligibility&limit=5")
    results["search_documents"] = {
        "status": status_search,
        "query": search_data.get("query") if isinstance(search_data, dict) else None,
        "total_results": search_data.get("total_results") if isinstance(search_data, dict) else None,
        "top_result": (search_data.get("results")[0] if isinstance(search_data, dict) and search_data.get("results") else None)
    }
    print(f"4. Search Documents: status={status_search}, total_results={results['search_documents']['total_results']}")
    if results["search_documents"]["top_result"]:
        top = results["search_documents"]["top_result"]
        print(f"   Top Result: scheme={top.get('scheme_slug')}, title={top.get('document_title')}, score={top.get('similarity_score')}, page={top.get('page_number')}")

    # 5. Assistant status & WhatsApp status
    status_asst, data_asst = request_json("/api/assistant/status")
    status_wa, data_wa = request_json("/api/whatsapp/status")
    status_voice, data_voice = request_json("/api/voice/status")
    results["assistant_status"] = {"status": status_asst, "body": data_asst}
    results["whatsapp_status"] = {"status": status_wa, "body": data_wa}
    results["voice_status"] = {"status": status_voice, "body": data_voice}
    print(f"5. Assistant status: {status_asst} -> {data_asst}")
    print(f"   WhatsApp status: {status_wa} -> {data_wa}")
    print(f"   Voice status: {status_voice} -> {data_voice}")

    # 6. Test PM-KISAN question via POST /api/assistant/chat
    pm_kisan_query = {
        "query": "I am a farmer from Bihar with 1.5 acres of agricultural land. Am I eligible for PM-KISAN?",
        "preferred_language": "en"
    }
    print("\n6. Testing PM-KISAN query through /api/assistant/chat ...")
    status_chat, data_chat = request_json("/api/assistant/chat", method="POST", payload=pm_kisan_query)
    results["pm_kisan_chat"] = {
        "status": status_chat,
        "ai_provider": data_chat.get("ai_provider") if isinstance(data_chat, dict) else None,
        "is_fallback": data_chat.get("is_fallback") if isinstance(data_chat, dict) else None,
        "answer": data_chat.get("answer") if isinstance(data_chat, dict) else None,
        "citations_count": len(data_chat.get("citations", [])) if isinstance(data_chat, dict) else 0,
        "citations": data_chat.get("citations") if isinstance(data_chat, dict) else [],
        "extracted_profile": data_chat.get("extracted_profile") if isinstance(data_chat, dict) else {},
        "missing_criteria": data_chat.get("missing_criteria") if isinstance(data_chat, dict) else [],
        "eligibility_results": data_chat.get("eligibility_results") if isinstance(data_chat, dict) else [],
        "follow_up_prompt": data_chat.get("follow_up_prompt") if isinstance(data_chat, dict) else None
    }
    print(f"   Status: {status_chat}")
    print(f"   AI Provider: {results['pm_kisan_chat']['ai_provider']}, Is Fallback: {results['pm_kisan_chat']['is_fallback']}")
    print(f"   Citations Count: {results['pm_kisan_chat']['citations_count']}")
    for c in results['pm_kisan_chat']['citations']:
        print(f"     - Title: {c.get('title')}, Page: {c.get('page_number')}, Ref: {c.get('document_reference')}, URL: {c.get('url')}")
    ans = results['pm_kisan_chat']['answer'] or ""
    print(f"   Answer Preview: {ans[:200]}...")

    # Save complete structured results to file
    with open("artifacts_live_verification.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nVerification complete. Structured data saved to artifacts_live_verification.json")

if __name__ == "__main__":
    main()
