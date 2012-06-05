import webqtlConfig

header_string = open(webqtlConfig.HTMLPATH + 'header.html', 'r').read()
header_string = header_string.replace("\\'", "'")
header_string = header_string.replace('%"','%%"')
header_string = header_string.replace('<!-- %s -->', '%s')
