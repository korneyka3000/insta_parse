import contextlib
import time

from pydantic import ConfigDict, Field, HttpUrl, constr
from pydantic_settings import BaseSettings
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


class Settings(BaseSettings):
    password: constr(min_length=6, max_length=100, strip_whitespace=True) = Field(alias='INST_PASS')
    username: constr(
        min_length=1,
        max_length=100,
        strip_whitespace=True
    ) = Field(alias='INST_LOGIN')
    base_url: str = Field(default='https://www.instagram.com/', alias='INST_URL')

    model_config = ConfigDict(extra="allow")


def get_settings():
    return Settings(_env_file='.env')


class SeleniumWorker:
    SCROLL_PAUSE_TIME = 2

    def __init__(self, base_url: HttpUrl, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.driver = None
        self.driver_options = None
        self.wait = None
        self.result = []

    @contextlib.contextmanager
    def get_driver(self):
        self.driver_options = webdriver.ChromeOptions()
        self.driver_options.add_argument("--headless")
        self.driver_options.add_argument('--no-sandbox')
        self.driver_options.add_argument('--disable-gpu')
        self.driver_options.add_argument("--disable-dev-shm-usage")
        self.driver_options.add_argument('--start-maximized')
        # self.driver_options.binary_location = '/usr/bin/chromedriver'
        # print(self.driver_options.binary_location)
        # service = Service(executable_path='/usr/bin/chromedriver')
        # self.driver = webdriver.Chrome(options=self.driver_options)
        self.driver = webdriver.Remote(
            "http://chrome:4444/wd/hub",
            options=self.driver_options,
            keep_alive=True
        )
        self.wait = WebDriverWait(self.driver, 10)
        yield self.driver
        self.driver.quit()

    # unused here but could be used if login needed
    @contextlib.contextmanager
    def login(self, username):
        try:
            self.driver.get(self.base_url)
            self.driver.implicitly_wait(3)
            self.wait.until(
                expected_conditions.element_to_be_clickable(
                    (By.XPATH,
                     "//input[@name='username']")
                )
            )
            username_field = self.driver.find_element(By.NAME, value='username')
            password_field = self.driver.find_element(By.NAME, value='password')
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)
            self.wait.until(expected_conditions.presence_of_element_located(
                (By.XPATH, f'//img[contains(@alt,{username})]')
            ))
            yield
        finally:
            self.driver.close()

    def get_url(self, username, max_count=1):
        # with self.login(username):
        with self.get_driver():
            self.driver.get(self.base_url + username)
            # self.wait.until(expected_conditions.presence_of_element_located(
            #     (By.XPATH, f'//img[contains(@alt,{username})]')
            # ))
            div_elements = list()

            last_height = self.driver.execute_script("return document.body.scrollHeight")

            while len(div_elements) < max_count:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.SCROLL_PAUSE_TIME)
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                div_elements = self.wait.until(
                    expected_conditions.presence_of_all_elements_located(
                        (By.CLASS_NAME, '_aagu')
                    )
                )

                if new_height == last_height:
                    break

                last_height = new_height

            for div_element in div_elements:
                img_element = div_element.find_element(By.TAG_NAME, 'img')
                img_src = img_element.get_attribute('src')
                self.result.append(img_src)

            return self.result[:max_count]
