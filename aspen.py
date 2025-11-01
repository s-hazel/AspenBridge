import os
import secrets
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="AspenBridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Authentication Setup
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable must be set")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key"
        )
    return api_key

class ScheduleItem(BaseModel):
    time: str
    block: str
    meets: Optional[str] = None

class ScheduleResponse(BaseModel):
    schedule: List[ScheduleItem]

def parse_block(block_text):
    match = re.match(r'([A-Z])(\([^)]+\))', block_text)
    if match:
        return match.group(1), match.group(2)
    # If no parentheses, return the text
    return block_text, None

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

    schedule_items = []
    
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

        # Get schedule data
        for i in range(2, length):
            time_element = driver.find_element(By.XPATH, getColumnOne(i))
            block_element = driver.find_element(By.XPATH, getBlock(i))
            
            time = time_element.text
            block_text = block_element.text
            
            block, meets = parse_block(block_text)
            
            schedule_items.append({
                "block": block,
                "time": time,
                "meets": meets
            })
        
    except Exception as e:
        raise Exception(f"Error scraping schedule: {str(e)}")
    finally:
        driver.quit()
    
    return schedule_items

@app.get("/")
def root():
    return {"message": "AspenBridge - Melrose Public Schools", "endpoints": ["/schedule", "/docs"]}

@app.get("/schedule", response_model=ScheduleResponse)
def get_schedule_endpoint(api_key: str = Depends(verify_api_key)):
    try:
        schedule = get_schedule()
        return {"schedule": schedule}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}