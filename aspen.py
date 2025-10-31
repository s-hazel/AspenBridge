import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from selenium.webdriver.support.ui import Select

# Find the select element
load_dotenv()

def get_schedule():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)

    def getColumnOne(row):
        return f"/html/body/form/table/tbody/tr[2]/td/div/table[2]/tbody/tr[1]/td[2]/table[2]/tbody/tr[6]/td/div/table/tbody/tr/td/table/tbody/tr[{row}]/td[1]/table/tbody/tr[2]/td"
    def getBlock(row):
        return f"/html/body/form/table/tbody/tr[2]/td/div/table[2]/tbody/tr[1]/td[2]/table[2]/tbody/tr[6]/td/div/table/tbody/tr/td/table/tbody/tr[{row}]/td[2]/table/tbody/tr[2]/td"

    times = []
    blocks = []
    
    try:
        driver.get("https://ma-melrose.myfollett.com/aspen-login/?deploymentId=ma-melrose")

        wait = WebDriverWait(driver, 10)
        
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_field = driver.find_element(By.ID, "password")
        
        # Credentials
        username_field.send_keys(os.environ.get("ASPEN_USERNAME"))
        password_field.send_keys(os.environ.get("ASPEN_PASSWORD"))
        
        login_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/go-root/go-login/go-login-container/div/div/div/go-default-login/form/div[4]/div/button"))
        )
        login_button.click()

        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "navTab"))
        )
        
        my_info = driver.find_element(By.XPATH, "/html/body/div[3]/div/table[2]/tbody[3]/tr/td[3]/a")
        my_info.click()

        current_schedule = driver.find_element(By.XPATH, "/html/body/form/table/tbody/tr[2]/td/div/table[2]/tbody/tr[1]/td[1]/div/table/tbody/tr[3]/td/div")
        current_schedule.click()

        # Select today
        select_element = driver.find_element(By.ID, "selectedTermOid")
        dropdown = Select(select_element)
        dropdown.select_by_visible_text("Today")

        # Length of schedule
        table = driver.find_element(By.XPATH, "/html/body/form/table/tbody/tr[2]/td/div/table[2]/tbody/tr[1]/td[2]/table[2]/tbody/tr[6]/td/div/table/tbody/tr/td/table")
        length = table.find_elements(By.XPATH, "./tbody/tr")
        length = len(length) + 1
        print(length)

        # Get schedule times
        for i in range(2, length):
            element = driver.find_element(By.XPATH, getColumnOne(i))
            times.append(element.text)

        # Get schedule blocks
        for i in range(2, length):
            element = driver.find_element(By.XPATH, getBlock(i))
            blocks.append(element.text)
        
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}
    finally:
        driver.quit()
    
    return times, blocks

times, blocks = get_schedule()

print(
    {
        "schedule": {
            "times": times,
            "blocks": blocks
        }
    }
)