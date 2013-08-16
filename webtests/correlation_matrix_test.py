"""

Test Correlation matrix

>>> test = Test()
>>> test.get("http://genenetwork.org/")
title: GeneNetwork

Choose the type
>>> test.click_option('''//*[@id="tissue"]''', 'Hippocampus mRNA')

Enter the Get Any
>>> test.enter_text('''//*[@id="tfor"]''', 'grin2b')
text: grin2b

Search
>>> test.click('//*[@id="btsearch"]')

Select the first 4 records
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/p/table/tbody/tr[3]/td/div/table/tbody/tr[2]/td/input''')
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/p/table/tbody/tr[3]/td/div/table/tbody/tr[3]/td/input''')
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/p/table/tbody/tr[3]/td/div/table/tbody/tr[4]/td/input''')
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/p/table/tbody/tr[3]/td/div/table/tbody/tr[5]/td/input''')

>>> sleep(5)

Add to collection page
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/p/table/tbody/tr[1]/td/table/tbody/tr[1]/td[4]/a''')

>>> sleep(5)

A new window is created, so we switch to it
>>> test.switch_window()
title: BXD Trait Collection

Select all records
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/a/img''')


Click Matrix
>>> test.click('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td[2]/a/img''')

Another new window
>>> test.switch_window()
title: Correlation Matrix

Sleep a bunch because this can take a while
>>> sleep(10)

Ensure that the correlation between Trait3 (HC_M2_0606_P::1457003_at) and Trait4 (HC_M2_0606_P::1422223_at) is 0.608
>>> test.get_text('''/html/body/table/tbody/tr[3]/td/table/tbody/tr/td/form/blockquote/table/tbody/tr[5]/td[5]/a/font''')
text: 0.608\n71

"""

from __future__ import print_function, division, absolute_import

from browser_test import Test

if __name__ == '__main__':
    import doctest
    doctest.testmod()
