"""
Populates the app with realistic sample complaints for demo/viva purposes.

Run this AFTER the backend is running (uvicorn ... on port 8000) and AFTER
you've run seed_data.py at least once (needs the admin + officer accounts).

Usage:
    python populate_demo_data.py

This uses the real API (not direct DB writes), so it exercises the actual
AI analyzer, duplicate detection, and scoring — same as a real citizen
filing a complaint through the website.
"""
import requests
import random
import time

BASE_URL = "http://localhost:8000"

# A pool of demo citizens - script will register them if they don't exist
CITIZENS = [
    {"name": "Ravi Kumar", "email": "ravi.demo@example.com", "password": "demo1234"},
    {"name": "Priya Sharma", "email": "priya.demo@example.com", "password": "demo1234"},
    {"name": "Arjun Nair", "email": "arjun.demo@example.com", "password": "demo1234"},
    {"name": "Meena Iyer", "email": "meena.demo@example.com", "password": "demo1234"},
]

COMPLAINTS = [
    # Ward 1 - mostly bad (for a "Critical" health score)
    dict(title="Major pothole near school", complaint_type="road",
         description="There is a huge pothole right outside the government school gate on Ward 1 main road, two accidents have already happened this month.",
         area="Ward 1"),
    dict(title="Street light not working for months", complaint_type="street_light",
         description="The street light near the Ward 1 bus stop has not worked for over two months, it is very unsafe for women walking at night.",
         area="Ward 1"),
    dict(title="Garbage dumping near residential area", complaint_type="illegal_dumping",
         description="People are illegally dumping garbage on the empty plot in Ward 1 every week, it is causing a terrible smell and attracting stray dogs.",
         area="Ward 1"),
    dict(title="Water pipeline leaking badly", complaint_type="water_leakage",
         description="The water pipeline near Ward 1 market has been leaking for days, wasting a huge amount of water and flooding the road.",
         area="Ward 1"),

    # Ward 2 - mixed (some resolved, "Good" range)
    dict(title="Broken footpath tiles", complaint_type="road",
         description="Several footpath tiles are broken near the Ward 2 park entrance, elderly people have tripped and fallen there.",
         area="Ward 2"),
    dict(title="Flickering street light", complaint_type="street_light",
         description="The street light outside Ward 2 community hall keeps flickering on and off, needs to be checked by the electricity department.",
         area="Ward 2"),
    dict(title="Overflowing garbage bin", complaint_type="illegal_dumping",
         description="The public garbage bin in Ward 2 has been overflowing for a week, sanitation workers have not collected it recently.",
         area="Ward 2"),

    # Ward 3 - mostly good (for an "Excellent" health score)
    dict(title="Minor road crack", complaint_type="road",
         description="There is a small crack developing on the Ward 3 internal road near house number 45, would like it patched before monsoon.",
         area="Ward 3"),
    dict(title="Request for new street light", complaint_type="street_light",
         description="Ward 3 lane 4 does not have a street light at all, residents have requested one be installed for safety.",
         area="Ward 3"),

    # Corruption example (routed to Vigilance Cell)
    dict(title="Bribe demanded for water connection", complaint_type="corruption",
         description="A local official demanded extra payment beyond the official fee to approve a new water connection application in Ward 2.",
         area="Ward 2"),
]


def register_or_login(citizen):
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "name": citizen["name"], "email": citizen["email"],
        "password": citizen["password"], "role": "citizen"
    })
    if resp.status_code == 200:
        return resp.json()["access_token"]

    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": citizen["email"], "password": citizen["password"]
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def file_complaint(token, complaint):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "title": complaint["title"],
        "description": complaint["description"],
        "complaint_type": complaint["complaint_type"],
        "area": complaint["area"],
        "force_new": True,
    }
    resp = requests.post(f"{BASE_URL}/complaints", data=data, headers=headers)
    if resp.status_code != 200:
        print(f"  Failed to file '{complaint['title']}': {resp.status_code} {resp.text[:200]}")
        return None
    return resp.json()


def admin_login():
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@grievance.gov", "password": "admin123"
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_officers(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = requests.get(f"{BASE_URL}/officers", headers=headers)
    resp.raise_for_status()
    return resp.json()


def main():
    print("Checking backend is reachable...")
    try:
        requests.get(BASE_URL, timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: could not reach {BASE_URL}. Make sure uvicorn is running first.")
        return

    print("Logging in as admin...")
    admin_token = admin_login()
    officers = get_officers(admin_token)
    if not officers:
        print("ERROR: no officers found. Run seed_data.py first.")
        return

    print(f"Found {len(officers)} officer(s).\n")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    created = []
    for i, complaint in enumerate(COMPLAINTS):
        citizen = CITIZENS[i % len(CITIZENS)]
        token = register_or_login(citizen)
        print(f"Filing: {complaint['title']} ({complaint['area']}) as {citizen['name']}...")
        result = file_complaint(token, complaint)
        if result:
            created.append(result)
            print(f"  -> {result['complaint_code']} | priority={result['ai_priority']} | dept={result['ai_department']}")
        time.sleep(0.3)

    print(f"\nCreated {len(created)} complaints. Now simulating resolution progress...\n")

    for idx, complaint in enumerate(created):
        officer = officers[idx % len(officers)]
        assign_resp = requests.post(
            f"{BASE_URL}/complaints/{complaint['id']}/assign",
            params={"officer_id": officer["id"]},
            headers=admin_headers,
        )
        if assign_resp.status_code != 200:
            continue

        roll = random.random()

        officer_login = requests.post(f"{BASE_URL}/auth/login", json={
            "email": officer["email"], "password": "officer123"
        })
        if officer_login.status_code != 200:
            continue
        officer_token = officer_login.json()["access_token"]
        officer_headers = {"Authorization": f"Bearer {officer_token}"}

        stages = ["accepted", "in_progress", "completed"]
        if roll < 0.6:
            target_stages = stages
        elif roll < 0.85:
            target_stages = stages[:2]
        else:
            target_stages = []

        for stage in target_stages:
            requests.post(
                f"{BASE_URL}/complaints/{complaint['id']}/status",
                json={"status": stage, "remarks": "Demo data - auto progressed"},
                headers=officer_headers,
            )

        print(f"  {complaint['complaint_code']}: -> {target_stages[-1] if target_stages else 'assigned'}")

    print("\nDone! Refresh your Admin Dashboard and Constituency Health Score pages to see the data.")


if __name__ == "__main__":
    main()
