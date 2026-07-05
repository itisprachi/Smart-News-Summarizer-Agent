import asyncio
from services import auth_service, newsletter_job
import logging

logging.basicConfig(level=logging.INFO)

async def test_run():
    # Force a subscription for the first user
    users = auth_service.get_all_users()
    if users:
        email = users[0]["email"]
        print(f"Subscribing {email} to 'Space' for testing...")
        auth_service.subscribe_topic(email, "Space")
        
    print("Triggering newsletter job...")
    await newsletter_job.run_daily_newsletter()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(test_run())
