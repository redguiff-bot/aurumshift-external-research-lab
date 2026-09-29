import sys, asyncio, os
os.environ.setdefault("DB", sys.argv[1])
from app import app, flaky2
async def main():
    async with app.open_async():
        for n in sys.argv[2:]: await flaky2.defer_async(n=int(n))
asyncio.run(main())
