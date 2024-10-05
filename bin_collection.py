from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json
import requests
import constants

# Function to update a Home Assistant sensor
def update_ha_sensor(sensor_id, value):
    url = f"{constants.HA_URL}/api/states/{sensor_id}"
    headers = {
        "Authorization": f"Bearer {constants.HA_TOKEN}",
        "content-type": "application/json",
    }
    data = {
        "state": value
    }
    response = requests.post(url, headers = headers, json = data)
    if response.status_code == 200:
        print(f"Successfully updated {sensor_id} to {value}")
    else:
        print(f"Failed to update {sensor_id}. Response: {response.content}")

def parse_data() -> dict:
    driver = None
    try:
        data = []

        # Define Chrome options
        chrome_options = Options()
        #chrome_options.add_argument("--headless")  # Headless mode
        chrome_options.add_argument("--disable-cache")
        chrome_options.add_argument("--disk-cache-size=0")
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--aggressive-cache-discard")  # Discards old cache immediately
        chrome_options.add_argument("--incognito")

        # Create a new remote WebDriver instance
        driver = webdriver.Remote(
            command_executor = constants.SELENIUM_GRID_URL,
            options = chrome_options
        )

        driver.delete_all_cookies()

        # Open the target page
        driver.get('https://myselfservice.ne-derbyshire.gov.uk/service/Check_your_Bin_Day')
        driver.execute_script("location.reload(true);")

        # Wait for the iframe and switch to it
        iframe_presence = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "fillform-frame-1"))
        )
        driver.switch_to.frame(iframe_presence)

        # Wait for the postcode input and enter it
        wait = WebDriverWait(driver, 60)
        inputElement_postcodesearch = wait.until(
            EC.element_to_be_clickable((By.NAME, "postcode_search"))
        )
        inputElement_postcodesearch.send_keys(str(constants.USER_POSTCODE))

        # Wait for the dropdown to appear
        dropdown = wait.until(EC.element_to_be_clickable((By.NAME, "selAddress")))
        
        # Wait until the dropdown is populated with values (beyond just the default option)
        wait.until(lambda driver: len(Select(driver.find_element(By.NAME, "selAddress")).options) > 1)

        # Select the property using user UPRN
        drop_down_values = Select(dropdown)
        drop_down_values.select_by_value(str(constants.USER_UPRN))

        # Wait for the 'Waste Collection' table to appear
        timeout = 60
        h3_element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//th[contains(text(), 'Waste Collection')]"))
        )

        # Wait for JavaScript and page to fully load
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Wait for 10 seconds
        time.sleep(10)

        # Use BeautifulSoup to parse the table content
        soup = BeautifulSoup(driver.page_source, "html.parser")
        target_h3 = soup.find("h3", string="Collection Details")
        tables_after_h3 = target_h3.find_next("table")
        table_rows = tables_after_h3.find_all("tr")

        for row in table_rows:
            rowdata = row.find_all("td")
            if len(rowdata) == 3:
                labels = rowdata[0].find_all("label")
                if len(labels) >= 2:
                    date_label = labels[1]
                    datestring = date_label.text.strip()

                    # Define the date format
                    date_format = "%d/%m/%Y"

                    # Add the bin type and collection date to the 'data' dictionary
                    data.append(
                        {
                            "type": rowdata[2].text.strip(),
                            "collectionDate": datetime.strptime(
                                datestring, "%d/%m/%Y"
                            ).strftime(date_format),  # Format the date
                        }
                    )

    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        # Ensure the driver is closed
        if driver:
            driver.quit()

        jsonData = json.loads(data)

     # Update Home Assistant sensors
    update_ha_sensor('sensor.next_bin_collection', jsonData[0]['collectionDate'])
    update_ha_sensor('sensor.bin_colour', jsonData[0]['type'])

    return data

# This is how you would call the function
if __name__ == "__main__":
    scraped_data = parse_data()