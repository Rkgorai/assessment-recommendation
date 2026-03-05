import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("1. Testing Health Check...")
health_response = requests.get(f"{BASE_URL}/health")
print(f"Status Code: {health_response.status_code}")
print(health_response.json())

print("\n2. Testing Recommendation Endpoint...")

input_query = input("Enter a job description or query for assessment recommendations: ")

if len(input_query.strip()) == 0:
    input_query = "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes."

payload = {
    "query": input_query
}
# Sending the POST request
response = requests.post(f"{BASE_URL}/recommend", json=payload)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("Success! Here are the recommendations:")
    print(json.dumps(response.json(), indent=4))
else:
    print("Failed:", response.text)