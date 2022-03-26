
import traceback
import os
from datetime import datetime
from tempfile import NamedTemporaryFile
from time import sleep

import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait


def get_new_tab():
    opts = Options()
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.binary_location = os.environ.get("GOOGLE_CHROME_BIN")    
    opts.add_argument('--disable-cached')
    opts.add_argument('--disable-dev-shm-usage')  
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-application-cache")
    opts.add_experimental_option("windowTypes", ["webview"])
    opts.add_argument("accept-language=en-GB,en;q=0.9,en-US;q=0.8")
    #opts.add_argument("cache-control=no-cache")
    #opts.add_argument("pragma=no-cache")
    opts.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36')
    opts.add_argument("--start-maximized")
    opts.add_argument("--headless")
    opts.add_argument("--window-size=1920,1080")

    service = Service(executable_path=os.environ.get("CHROMEDRIVER_PATH"))
    web_browser = webdriver.Chrome(service=service, options=opts)
    return web_browser


def check_and_create_folder(drive, folderName, parentID):
    folderlist = (drive.ListFile({'q': f"'{parentID}' in parents and trashed=false"}).GetList())
    titlelist = [x['title'] for x in folderlist]
    if str(folderName) in titlelist:
        print('folder exists')
        for item in folderlist:
            if item['title'] == str(folderName):
                return item['id']
    else:
        print('new folder created')
        file_metadata = {
            'title': folderName,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{"id": parentID}]
        }
        file0 = drive.CreateFile(file_metadata)
        file0.Upload()
        return file0['id']


# Upload screenshot images into Google Drive
def upload_into_drive(folder_name, image_filename, imageBytes):
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)
    p_folder_id = '1Rm1XX04Y0anFNoqfTtoxm3fnTBsx554a'
    f_id = check_and_create_folder(drive, folder_name, p_folder_id)
    gd_file = drive.CreateFile({'title': image_filename, 'parents': [{'id': f_id}]})
    tmp_name = None
    with NamedTemporaryFile(delete=False, mode='w+b') as tf:
        tf.write(imageBytes)
        tmp_name = tf.name
    if tmp_name is not None:
        gd_file.SetContentFile(tmp_name)
        gd_file.Upload()


# program starts from here
if __name__ == '__main__':

    base_url = 'https://trade.mql5.com/trade'

    account_details = pd.read_csv('login_details.csv')

    login_css = '[id="login"]'
    pass_css = '[id="password"]'
    server_css = 'input[id="server"]'
    platform_mt4_css = 'input[type="radio"][id="mt4-platform"]'
    platform_mt5_css = 'input[type="radio"][id="mt5-platform"]'
    ok_button_xpath = '//button[text()="OK"]'

    while True:
        for login_details in account_details.values:
            sleep(1)
            browser = get_new_tab()
            try:
                browser.get(base_url)
                sleep(0.5)
                if login_details[3] == 'MT4':
                    print('MT4')
                    platform4 = WebDriverWait(browser, 20).until(
                        ec.element_to_be_clickable((By.CSS_SELECTOR, platform_mt4_css)))
                    ActionChains(browser).move_to_element(platform4).click().perform()
                    print('MT4 clicked.')
                    sleep(0.5)
                if login_details[3] == 'MT5':
                    print('MT5')
                    platform5 = WebDriverWait(browser, 20).until(
                        ec.element_to_be_clickable((By.CSS_SELECTOR, platform_mt5_css)))
                    browser.execute_script("arguments[0].click();", platform5)
                    sleep(3.5)
                    print('mt5 clicked.')
                sleep(0.5)
                WebDriverWait(browser, 20).until(ec.presence_of_element_located((By.CSS_SELECTOR, login_css))).send_keys(
                    login_details[0])
                sleep(0.5)
                WebDriverWait(browser, 20).until(ec.presence_of_element_located((By.CSS_SELECTOR, pass_css))).send_keys(
                    login_details[1])
                sleep(0.5)
                server_input = WebDriverWait(browser, 20).until(
                    ec.presence_of_element_located((By.CSS_SELECTOR, server_css)))
                server_input.clear()
                sleep(0.5)
                server_input.send_keys(login_details[2])
                sleep(0.5)
                login_button = WebDriverWait(browser, 20).until(ec.element_to_be_clickable((By.XPATH, ok_button_xpath)))
                ActionChains(browser).move_to_element(login_button).click().perform()
                print(f'Login Account: {login_details[0]} logged in.')
                datetime_now_mt4 = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
                image_name = f"{login_details[0]}-{datetime_now_mt4}.png"
                sleep(8)
                result_save = browser.get_screenshot_as_png()
                if result_save:
                    sleep(0.5)
                    image = browser.get_screenshot_as_png()                    
                    upload_into_drive(login_details[0], image_name, result_save)
                    print('Image Saved.')
                else:
                    print("Sorry image couldn't upload into drive")
                sleep(0.5)
                file_btn = WebDriverWait(browser, 20).until(ec.presence_of_element_located((By.XPATH, '//*[text()="File"]')))
                ActionChains(browser).move_to_element(file_btn).click().perform()
                sleep(0.5)
                logout_menu_btn = WebDriverWait(browser, 20).until(ec.presence_of_element_located((By.XPATH, '//*[text()="Logout"]')))
                ActionChains(browser).move_to_element(logout_menu_btn).click().perform()
                sleep(0.5)
                logout_confirm_checkbox = WebDriverWait(browser, 20).until(ec.presence_of_element_located((By.CSS_SELECTOR, '[id="logout-confirm"]')))
                ActionChains(browser).move_to_element(logout_confirm_checkbox).click().perform()
                sleep(0.5)
                logout_btn = WebDriverWait(browser, 20).until(ec.element_to_be_clickable((By.XPATH, '//button[text()="Logout"]')))
                ActionChains(browser).move_to_element(logout_btn).click().perform()
                print('Logging out..')
                browser.close()
            except Exception as e:
                print(e)
                #print(traceback.print_tb(e.__traceback__))
