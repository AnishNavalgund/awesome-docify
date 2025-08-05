import requests

# Test the RAG engine with the query API
url = "http://localhost:8000/api/v1/query"
headers = {"Content-Type": "application/json"}

# Test queries
test_queries = [
    "add a new function to handle user authentication",
    "update the documentation for the API endpoints",
    "fix the error handling in the database connection",
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Testing query: {query}")
    print(f"{'='*60}")

    data = {"query": query}

    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"Suggested Diff: {result.get('suggested_diff', 'N/A')}")
            print(f"Confidence: {result.get('confidence', 'N/A')}")
            print(f"Fallback Used: {result.get('fallback_used', 'N/A')}")
        else:
            print(f"Error Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

    print()
