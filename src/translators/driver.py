import sys 
import atexit
import re
import subprocess
from typing import Literal

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager



class Browsers:
    
    __edge_key = "HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    __chrome_key = "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon"
    __firefox_key = "HKEY_LOCAL_MACHINE\SOFTWARE\Mozilla\Mozilla Firefox"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._edge_version = cls.__extract_browser_version(cls.__edge_key, 'pv')
            cls._instance._chrome_version = cls.__extract_browser_version(cls.__chrome_key, 'version')
            cls._instance._firefox_version = cls.__extract_browser_version(cls.__firefox_key, 'CurrentVersion')
        return cls._instance
    

    @staticmethod
    def __extract_browser_version(key, value):
        try:
            output = subprocess.check_output(f'reg query "{key}" /v {value}', shell=True, universal_newlines=True)
            if value == 'CurrentVersion':
                match = re.search(r'(\d+\.\d+\.\d+)', output)
            else:    
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', output)
            if match:
                return match.group(1)
        except Exception as e:
            print(f'Error getting browser version: {e}')
        return None
    
    
    @staticmethod
    def get_edge_version():
        return Browsers()._edge_version
    
    
    @staticmethod
    def get_chrome_version():
        return Browsers()._chrome_version
    
    
    @staticmethod
    def get_firefox_version():
        return Browsers()._firefox_version
    
    
    @staticmethod
    def is_edge_installed():
        return bool(Browsers()._edge_version)
    
    
    @staticmethod
    def is_chrome_installed():
        return bool(Browsers()._chrome_version)


    @staticmethod
    def is_firefox_installed():
        return bool(Browsers()._firefox_version)
    

class WebDriverManager():
    _instance = None

    def __new__(cls, browser: Literal['edge', 'chrome', 'firefox'] = 'edge'):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
            browsers = {
                'edge': {
                    'is_installed': Browsers.is_edge_installed(), 
                    'options': webdriver.EdgeOptions,
                    'driver': webdriver.Edge,
                    'service': EdgeService,
                    'manager': EdgeChromiumDriverManager
                },
                'chrome': {
                    'is_installed': Browsers.is_chrome_installed(), 
                    'options': webdriver.ChromeOptions,
                    'driver': webdriver.Chrome,
                    'service': ChromeService,
                    'manager': ChromeDriverManager
                },
                'firefox': {
                    'is_installed': Browsers.is_firefox_installed(), 
                    'options': webdriver.FirefoxOptions,
                    'driver': webdriver.Firefox,
                    'service': FirefoxService,
                    'manager': GeckoDriverManager                    
                },
            }
            
            installed_browsers = [b for b, value in browsers.items() if value['is_installed']]
            if not installed_browsers:
                raise ValueError('No installed browsers found')
            
            browser = browser if browser in installed_browsers else installed_browsers[0]
            driver = browsers[browser]['driver']
            service = browsers[browser]['service']
            driver_manager = browsers[browser]['manager']
            
            options = browsers[browser]['options']()
            options.page_load_strategy = 'eager'
            options.add_argument('--blink-settings=imagesEnabled=false')
            options.add_argument('--disable-infobars')
            if browser != 'chrome':
                options.add_argument("--headless")
            else:
                options.add_argument("--headless=new")
                
            cls._instance.driver = driver(service=service(driver_manager().install()), options=options)
            # cls._instance.driver.set_window_position(-2000, 0)
            atexit.register(WebDriverManager.close_instance)
        return cls._instance
    
    
    def __getattr__(self, name):
        return getattr(self.driver, name)
        
        
    @staticmethod
    def close_instance():
        if WebDriverManager._instance:
            WebDriverManager._instance.driver.quit()
            WebDriverManager._instance = None
                
                
# This is a bad, but I haven’t figured out how to close the webdriver for any exceptions
def exception_handler(type, value, traceback):
    WebDriverManager.close_instance()
    sys.__excepthook__(type, value, traceback)
    sys.exit(0)
    
sys.excepthook = exception_handler
