from __future__ import print_function, division, absolute_import

from time import sleep

import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException
from selenium.webdriver.common.keys import Keys

class Test(object):
    def __init__(self):
        self.browser = webdriver.Chrome('/home/gn2/gn2/webtests/chromedriver')

    def get(self, url):
        self.browser.get(url)
        sleep(5)
        self.title()

    def click(self, xpath_selector):
        el = self.browser.find_element_by_xpath(xpath_selector)
        if el.text:
            text = el.text.strip()
        elif el.get_attribute("value"):
            text = el.get_attribute("value").strip()
        else:
            text = "Notext"
        el.click()
        print("clicked:", text)
        sleep(2)

    def click_option(self, xpath_selector, option_text):
        el = self.browser.find_element_by_xpath(xpath_selector)
        for option in el.find_elements_by_tag_name('option'):
            if option.text == option_text:
                option.click() # select() in earlier versions of webdriver
                break
        sleep(2)

    def enter_text(self, xpath_selector, text):
        el = self.browser.find_element_by_xpath(xpath_selector)
        sleep(10)
        el.send_keys(text)
        sleep(5)
        # Just in case things get mangled by JavaScript, etc. we print the text for testing
        self.get_text(xpath_selector)

    def get_text(self, xpath_selector):
        el = self.browser.find_element_by_xpath(xpath_selector)
        text = el.text.strip() or el.get_attribute("value").strip()
        print("text:", text)

    def switch_window(self):
        self.browser.switch_to_window(self.browser.window_handles[-1])
        sleep(2)
        self.title()
        sleep(2)


    def title(self):
        print("title:", self.browser.title)


#if __name__ == '__main__':
#    import doctest
#    doctest.testmod()