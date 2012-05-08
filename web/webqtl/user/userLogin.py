# Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# This program is available from Source Forge: at GeneNetwork Project
# (sourceforge.net/projects/genenetwork/).
#
# Contact Drs. Robert W. Williams and Xiaodong Zhou (2010)
# at rwilliams@uthsc.edu and xzhou15@uthsc.edu
#
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2010/08/10
#
# Last updated by GeneNetwork Core Team 2010/10/20

#Xiaodong changed the independancy structure

from htmlgen import HTMLgen2 as HT
import os

from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil
from search import IndexPage
from base.myCookie import myCookie

class userLogin(templatePage):

	def __init__(self, fd):	

		templatePage.__init__(self, fd)

		if not self.updMysql():
			return

		try:	
			user = fd.formdata.getvalue('user').strip()
			password = fd.formdata.getvalue('password').strip()
		except:
			user = password = ''

		if user and password:
			try:
				if user == password:
					raise 'identError'
				privilege, id, account_name, encrypt_password, grpName = webqtlUtil.authUser(user, password, self.cursor)

				if encrypt_password:
					self.session_data_changed['user'] = user
					self.session_data_changed['privilege'] = privilege

					self.cursor.execute("""update User set user_ip=%s,lastlogin=Now() where name=%s""",(fd.remote_ip,user))

					myPage = IndexPage.IndexPage(fd)
					self.dict['title'] = myPage.dict['title']
					self.dict['body'] = myPage.dict['body']
					self.dict['js1'] = myPage.dict['js1']
					self.dict['js2'] = myPage.dict['js2']
					return
				else:
					result = HT.Blockquote(HT.Font('Error: ',color='red'),HT.Font('You entered wrong user name or password. Please try it again.',color='black'))
			except 'identError':
				result = HT.Blockquote(HT.Font('Error: ',color='red'),HT.Font('User name and password are the same, modify you password before login.',color='black'))
			except:
				result = HT.Blockquote(HT.Font('Error: ',color='red'),HT.Font('User database is not ready yet. Try again later.',color='black'))
		else:
			result = HT.Blockquote(HT.Font('Error: ',color='red'),HT.Font('No user name or password was entered, Please try it again.',color='black'))
		
		result.__setattr__("class","subtitle")
		self.dict['title'] = 'User Login Result'
		self.dict['body'] = HT.TD(result,colspan=2,height=200,width="100%",bgColor='#eeeeee')
		LOGOUT = HT.Href(text = "Logout",Class="small", target="_blank",url=os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE) + "?FormID=userLogoff")
		self.dict['login'] = LOGOUT
