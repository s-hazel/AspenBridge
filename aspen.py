import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="AspenBridge", version="1.0.0")

# Enable CORS if you need to call this from a frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScheduleResponse(BaseModel):
    times: List[str]
    blocks: List[str]

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
        
        # Get credentials from environment variables
        username = os.environ.get("ASPEN_USERNAME")
        password = os.environ.get("ASPEN_PASSWORD")
        
        if not username or not password:
            raise ValueError("ASPEN_USERNAME and ASPEN_PASSWORD environment variables must be set")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
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
        length = len(table.find_elements(By.XPATH, "./tbody/tr")) + 1

        # Get schedule times
        for i in range(2, length):
            element = driver.find_element(By.XPATH, getColumnOne(i))
            times.append(element.text)

        # Get schedule blocks
        for i in range(2, length):
            element = driver.find_element(By.XPATH, getBlock(i))
            blocks.append(element.text)
        
    except Exception as e:
        raise Exception(f"Error scraping schedule: {str(e)}")
    finally:
        driver.quit()
    
    return times, blocks

@app.get("/")
def root():
    return {"message": "Schedule API is running", "endpoints": ["/schedule", "/docs"]}

@app.get("/schedule", response_model=ScheduleResponse)
def get_schedule_endpoint():
    """Get today's schedule from Aspen"""
    try:
        times, blocks = get_schedule()
        return {"times": times, "blocks": blocks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}