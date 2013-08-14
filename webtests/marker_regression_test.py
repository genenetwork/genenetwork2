"""
Test calculate correlations

>>> test = Test()
>>> test.get("http://genenetwork.org")
title: GeneNetwork

Choose the type
>>> test.click_option('''//*[@id="tissue"]''', 'Liver mRNA')

Enter the Get Any
>>> test.enter_text('''//*[@id="tfor"]''', 'grin2b')
text: grin2b

Search
>>> test.click('//*[@id="btsearch"]')
clicked: Search

Choose the second result
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/p/table/tbody/tr[3]/td/div/table/tbody/tr[3]/td[2]/a''')
clicked: 1431700_at_A

A new window is created, so we switch to it
>>> test.switch_window()
title: GSE16780 UCLA Hybrid MDP Liver Affy HT M430A (Sep11) RMA : 1431700_at_A: Display Trait

Click on Mapping Tools
>>> test.click('''//*[@id="title4"]''')
clicked: Mapping Tools

Click on Marker Regression tab
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/p[8]/table/tbody/tr/td/div/ul/li[2]/a''')
clicked: Marker Regression

Click on Compute
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/p[8]/table/tbody/tr/td/div/div[2]/span/table/tbody/tr/td/input''')
clicked: Compute

Another new window
>>> test.switch_window()
title: Genome Association Result

Sleep a bunch because this can take a while
>>> sleep(60)

Ensure that the LRS of the top record is the exepcted value
>>> test.get_text('''/html/body/table/tbody/tr[3]/td/table/tbody/tr[4]/td/table/tbody/tr/td/div/table/tbody/tr[2]/td[2]''')
text: 11.511

"""

from __future__ import print_function, division, absolute_import

from browser_test import Test

#
#from time import sleep
#
#
#import selenium
#from selenium import webdriver
#from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException
#from selenium.webdriver.common.keys import Keys
#
#
#class Test(object):
#    def __init__(self):
#        self.browser = webdriver.Chrome('/home/gn2/gn2/webtests/chromedriver')
#
#    def get(self, url):
#        self.browser.get(url)
#        sleep(5)
#        self.title()
#
#    def click(self, xpath_selector):
#        el = self.browser.find_element_by_xpath(xpath_selector)
#        text = el.text.strip() or el.get_attribute("value").strip()
#        el.click()
#        print("clicked:", text)
#        sleep(2)
#
#    def click_option(self, xpath_selector, option_text):
#        el = self.browser.find_element_by_xpath(xpath_selector)
#        for option in el.find_elements_by_tag_name('option'):
#            if option.text == option_text:
#                option.click() # select() in earlier versions of webdriver
#                break
#        sleep(2)
#
#    def enter_text(self, xpath_selector, text):
#        el = self.browser.find_element_by_xpath(xpath_selector)
#        sleep(10)
#        el.send_keys(text)
#        sleep(5)
#        # Just in case things get mangled by JavaScript, etc. we print the text for testing
#        self.get_text(xpath_selector)
#
#    def get_text(self, xpath_selector):
#        el = self.browser.find_element_by_xpath(xpath_selector)
#        text = el.text.strip() or el.get_attribute("value").strip()
#        print("text:", text)
#
#    def switch_window(self):
#        self.browser.switch_to_window(self.browser.window_handles[-1])
#        sleep(2)
#        self.title()
#        sleep(2)
#
#
#    def title(self):
#        print("title:", self.browser.title)



if __name__ == '__main__':
    import doctest
    doctest.testmod()
