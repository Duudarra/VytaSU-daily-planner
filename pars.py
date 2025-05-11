import asyncio

from models import async_main
from parsing import start_parsing


async def main():
    await async_main()  # Initialize the database
    await start_parsing()  # Start the parsing loop


if __name__ == "__main__":
    asyncio.run(main())