import webqtlConfig

footer_html = open(webqtlConfig.HTMLPATH + 'footer.html', 'r').read()
footer = footer_html.replace('%"','%%"')

footer_string = footer.replace('<!-- %s -->', '%s')
