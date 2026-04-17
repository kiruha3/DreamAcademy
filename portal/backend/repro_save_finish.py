import sys, asyncio
sys.path.insert(0, '/app')
from jose import jwt
from datetime import datetime, timezone, timedelta
import httpx
from app.config import get_settings

async def main():
    settings = get_settings()
    uid = 2
    token = jwt.encode({"sub": str(uid), "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, settings.SECRET_KEY, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        # Start attempt for cmid 238 in course 4
        r1 = await client.post("http://localhost:8000/api/courses/4/modules/238/quiz/start", headers=headers)
        print(f"start status={r1.status_code} body={r1.text[:200]}")
        if r1.status_code != 200:
            return
        attempt_id = r1.json()["attempt"]["id"]
        # Save empty attempt
        r2 = await client.post(f"http://localhost:8000/api/courses/4/modules/238/quiz/attempt/{attempt_id}/save", json={"data": []}, headers=headers)
        print(f"save status={r2.status_code} body={r2.text[:200]}")
        # Finish attempt
        r3 = await client.post(f"http://localhost:8000/api/courses/4/modules/238/quiz/attempt/{attempt_id}/finish", headers=headers)
        print(f"finish status={r3.status_code} body={r3.text[:200]}")

asyncio.run(main())
