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
>>> test.click('''//*[@id="mapping_tabs"]/ul/li[2]/a''')
clicked: Marker Regression

Click on Compute
>>> test.click('''//*[@id="mappingtabs-2"]/span/table/tbody/tr[1]/td/input''')
clicked: Compute

Another new window
>>> test.switch_window()
title: Genome Association Result

Sleep a bunch because this can take a while
>>> sleep(60)

Ensure that the LRS of the top record is the exepcted value
>>> test.get_text('''//*[@id="1"]/td[2]''')
text: 11.511

"""

from __future__ import print_function, division, absolute_import

from browser_test import Test

if __name__ == '__main__':
    import doctest
    doctest.testmod()
