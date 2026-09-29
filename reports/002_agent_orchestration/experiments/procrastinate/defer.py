import sys, asyncio, os
os.environ.setdefault("DB", sys.argv[1])
from app import app, work, flaky2
async def main():
    async with app.open_async():
        if sys.argv[2] == "work":
            for i in range(int(sys.argv[3])): await work.defer_async(n=i)
        else:
            await flaky2.defer_async(n=int(sys.argv[3]))
asyncio.run(main())
