import asyncio
import os

from playwright.async_api import async_playwright

from bchydro.scrapper import ENUM_LAST_7_DAYS, BCHydroScrapper


async def main(bep=None):
    scrape = BCHydroScrapper(
        os.environ.get("BCH_USER"), os.environ.get("BCH_PASS"), browser_exec_path=bep
    )
    async with async_playwright() as p:
        usage = await scrape.get_usage_table(p, period=ENUM_LAST_7_DAYS)

    print(usage)


if __name__ == "__main__":
    asyncio.run(main())
