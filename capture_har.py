#!/usr/bin/env python3
"""Capture HAR from browser automation."""

import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def enable_har_logging(driver):
    """Enable HAR logging in Chrome DevTools."""
    # Enable Network and Performance domains for HAR capture
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Performance.enable", {})


def get_har_data(driver):
    """Extract HAR data from Chrome DevTools Protocol."""
    try:
        # Try to get performance metrics as HAR-like data
        performance_data = driver.execute_cdp_cmd("Performance.getMetrics", {})
        return performance_data
    except Exception as e:
        print(f"Could not extract HAR: {e}")
        return None


def capture_dummyjson_har(output_path: str):
    """Capture traffic from dummyjson.com API endpoints."""
    output_file = Path(output_path)
    
    # Setup Chrome options for DevTools Protocol access
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # Uncomment for headless
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Enable performance logging
    capabilities = {
        "goog:loggingPrefs": {"performance": "ALL", "browser": "ALL"}
    }
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    driver = None
    try:
        # Setup WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("Chrome started, enabling DevTools...")
        
        # Enable performance logging for network capture
        driver.execute_cdp_cmd("Performance.enable", {})
        driver.execute_cdp_cmd("Network.enable", {})
        
        # Visit API endpoints
        base_url = "https://dummyjson.com"
        endpoints = [
            "/products",
            "/products/1",
            "/products/2",
            "/products/3",
            "/products?limit=5",
            "/products/category/electronics",
            "/products/search?query=laptop",
        ]
        
        print(f"Navigating to {len(endpoints)} endpoints...")
        
        for endpoint in endpoints:
            url = base_url + endpoint
            print(f"  -> {url}")
            driver.get(url)
            time.sleep(1)  # Wait for response
        
        print("Capturing HAR data...")
        
        # Get performance logs
        logs = driver.get_log("performance")
        
        # Build HAR-like structure
        har = {
            "log": {
                "version": "1.2",
                "creator": {
                    "name": "API Behavior Learner - Browser Capture",
                    "version": "1.0"
                },
                "pages": [],
                "entries": []
            }
        }
        
        # Parse performance logs into HAR format
        for log in logs:
            message = json.loads(log["message"])
            method = message.get("message", {}).get("method", "")
            
            if method == "Network.responseReceived":
                params = message.get("message", {}).get("params", {})
                response = params.get("response", {})
                request_id = params.get("requestId", "")
                
                # Build entry
                entry = {
                    "startedDateTime": response.get("timestamp", 0) if isinstance(response.get("timestamp"), (int, float)) else "2026-11-01T08:00:00.000Z",
                    "time": 100,  # Approximate
                    "request": {
                        "method": "GET",
                        "url": response.get("url", ""),
                        "headers": response.get("headers", {}),
                        "queryString": [],
                        "cookies": [],
                        "headersSize": -1,
                        "bodySize": -1
                    },
                    "response": {
                        "status": response.get("status", 200),
                        "statusText": "",
                        "headers": response.get("headers", {}),
                        "cookies": [],
                        "content": {
                            "size": response.get("mimeType", ""),
                            "mimeType": response.get("mimeType", "application/json")
                        },
                        "redirectURL": "",
                        "headersSize": -1,
                        "bodySize": -1
                    },
                    "cache": {},
                    "timings": {
                        "send": -1,
                        "wait": -1,
                        "receive": -1
                    },
                    "serverIPAddress": "",
                    "connection": "0"
                }
                
                har["log"]["entries"].append(entry)
        
        # Write HAR file
        output_file.write_text(json.dumps(har, indent=2))
        print(f"HAR written to: {output_file}")
        print(f"Total entries: {len(har['log']['entries'])}")
        
        return har
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        if driver:
            driver.quit()
            print("Chrome closed")


if __name__ == "__main__":
    har_path = r"D:\api-behavior-learner\samples\dummyjson.har"
    capture_dummyjson_har(har_path)
