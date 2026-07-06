"""
Run this once after starting the app for the first time:
    python seed_data.py

Creates a default admin and a couple of officer accounts so you don't have
to manually register them through the API for your demo.
"""
from app.database import SessionLocal, Base, engine
from app import models, auth

Base.metadata.create_all(bind=engine)
db = SessionLocal()

seed_users = [
    {"name": "Admin", "email": "admin@grievance.gov", "password": "admin123", "role": "admin", "department": None},
    {"name": "Officer - Public Works", "email": "officer.pwd@grievance.gov", "password": "officer123", "role": "officer", "department": "Public Works"},
    {"name": "Officer - Sanitation", "email": "officer.sanitation@grievance.gov", "password": "officer123", "role": "officer", "department": "Sanitation Department"},
]

for u in seed_users:
    existing = db.query(models.User).filter(models.User.email == u["email"]).first()
    if existing:
        print(f"Skipping (already exists): {u['email']}")
        continue
    user = models.User(
        name=u["name"],
        email=u["email"],
        hashed_password=auth.hash_password(u["password"]),
        role=u["role"],
        department=u["department"],
    )
    db.add(user)
    print(f"Created: {u['email']} / {u['password']} (role={u['role']})")

db.commit()
db.close()
print("\nSeeding complete.")
