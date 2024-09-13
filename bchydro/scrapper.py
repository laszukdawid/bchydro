import logging
import os
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
from playwright.async_api import Playwright

ENUM_CURRENT_BILLING_PERIOD = "Current billing period"
ENUM_LAST_BILLING_PERIOD = "Last billing period"
ENUM_LAST_7_DAYS = "Last 7 days"
ENUM_LAST_30_DAYS = "Last 30 days"

URL_LOGIN_PAGE = "https://app.bchydro.com/BCHCustomerPortal/web/login.html"

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

supported_periods = (
    ENUM_CURRENT_BILLING_PERIOD,
    ENUM_LAST_BILLING_PERIOD,
    ENUM_LAST_7_DAYS,
    ENUM_LAST_30_DAYS,
)


class BCHydroScrapper:
    def __init__(
        self, username: str, password: str, browser_exec_path: Optional[str] = None
    ):
        """BC Hydro data accessor through headless browser.

        *Note* that username and password are stored in the object.
        Be sure you trust the environment where this object is created and instance is executed.

        Reduce your risks by creating a read-only BCHydro account following
        https://github.com/emcniece/bchydro?tab=readme-ov-file#-read-only-account-sharing.

        Args:
            username (str): BCHydro username
            password (str): BCHydro password
            browser_exec_path (str): Path to browser executabble. Useful if browser is not in PATH.

        """
        self.page = None
        self._username = username
        self._password = password
        self.browser_exec_path = browser_exec_path

    async def get_usage_table(
        self, p: Playwright, period: str = ENUM_CURRENT_BILLING_PERIOD
    ):
        # Navigate to Consumption page by clicking button:
        browser = await p.chromium.launch(slow_mo=200)
        page = await browser.new_page()

        logger.debug("Populating login form...")
        await page.goto(URL_LOGIN_PAGE)
        await page.fill("#email", self._username)
        await page.fill("#password", self._password)

        logger.debug("Clicking login button...")
        await page.locator("#submit-button").click()

        logger.debug("Clicking Detailed Consumption button...")
        await page.wait_for_selector("#detailCon:not([disabled])")
        await page.click("#detailCon")

        # Navigate to the table look
        logger.debug("Clicking Table button...")
        # await self.page.wait_for_selector("#tableBtnLabel", state="attached")

        await page.wait_for_timeout(1000)  # Wait for the table to load
        await page.click("#tableBtnLabel")

        # Wait until the table with id="consumptionTable" is present
        await page.wait_for_selector("table#consumptionTable")

        if period != ENUM_CURRENT_BILLING_PERIOD and period in supported_periods:
            try:
                await page.wait_for_selector("span#dateSelect-button", state="attached")
            except Exception:
                logger.info("No dropdown found for period selection")
                print("No dropdown found for period selection")
            await page.click("span#dateSelect-button")

            # Wait until the dropdown is present
            options = await page.query_selector_all("div.ui-menu-item-wrapper")
            for option in options:
                text = await page.evaluate("(el) => el.textContent", option)
                if text == period:
                    await option.click()
                    break

            # Wait until the table with id="consumptionTable" is present after changing the table
            try:
                await page.wait_for_selector("table#consumptionTable")
            except Exception:
                print("Table not found after changing period")

        # Download the whole table at id="consumptionTable"
        html_table = await page.evaluate(
            "document.querySelector('table#consumptionTable').outerHTML"
        )
        with open("table.html", "w") as f:
            f.write(html_table)

        table = self.__parse_consumption_table(html_table)
        with open("table.json", "w") as f:
            import json

            f.write(json.dumps(table, indent=4))

        return table

    def __parse_consumption_table(self, html_table: str):
        """Parse the consumption table from the HTML content.

        Converts <table>...</table> HTML content to a dictionary.
        It's expected that the table is a daily consumption with the day in the 'Date' column.
        Parsing converts Date into the key (`YYYY-MM-dd`) for the dictionary, and all columns are flatten into the dictionary per row.

        Args:
            html_table (str): HTML content of the table, i.e. <table>...</table>

        Returns:
            dict: Dictionary with the table data, where the keys are the date in short-ISO format (2024-09-01).

        """

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_table, "html.parser")

        # Find the table element
        table = soup.find("table")

        # Extract table rows
        rows = table.find_all("tr")

        # Initialize the dictionary to store the table data
        table_dict = {}

        # Extract the header row to get the field names
        headers = [
            header.get_text(strip=True) for header in rows[0].find_all(["td", "th"])
        ]

        # Iterate over the rows and populate the dictionary
        for row in rows[1:]:  # Skip the header row
            cells = row.find_all(["td", "th"])
            cell_data = [cell.get_text(strip=True) for cell in cells]
            row_dict = dict(zip(headers, cell_data))

            date_key = row_dict.get("Date")
            if date_key:
                date_obj = datetime.strptime(date_key, "%b %d, %Y")
                formatted_date = date_obj.strftime("%Y-%m-%d")
                row_dict["Date"] = formatted_date
                table_dict[formatted_date] = row_dict

        return table_dict
