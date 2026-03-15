import requests
from concurrent.futures import ThreadPoolExecutor
import time

URL = "http://localhost:5000/scan"
IMAGE = "test.jpg"

TOTAL_REQUESTS = 20

def send_request(i):
    with open(IMAGE, "rb") as f:
        img = f.read()

    headers = {
        "Content-Type": "image/jpeg",
        "X-File-Name": f"test_{i}.jpg"
    }

    start = time.time()

    try:
        r = requests.post(URL, data=img, headers=headers)
        latency = time.time() - start
        print(f"{i} | {r.status_code} | {latency:.2f}s")
    except Exception as e:
        print(f"{i} ERROR {e}")


def main():
    start = time.time()

    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(send_request, range(TOTAL_REQUESTS))

    print("Finished in", time.time() - start)


if __name__ == "__main__":
    main()