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

from base.templatePage import templatePage
from utility import webqtlUtil


#########################################
#      User Password Page
#########################################

class userPasswd(templatePage):
	def __init__(self, fd):	

		templatePage.__init__(self, fd)

		if not self.updMysql():
			return

		try:	
			user = fd.formdata.getvalue('user')
			password = fd.formdata.getvalue('password')
			newpassword = fd.formdata.getvalue('newpassword')
			retypepassword = fd.formdata.getvalue('retypepassword')
		except:
			user = ''
		
		if newpassword != retypepassword:
			result = HT.Blockquote(HT.Font('Error: ',color='red'),HT.Font('The new passwords you just entered are inconsistent. Please try it again',color='black'))
		elif user and password and newpassword:
			try:
				encrypt_password = webqtlUtil.authUser(user,password,self.cursor)[3]
				if encrypt_password:
					self.cursor.execute("""update User set password=SHA(%s) where name=%s""",(newpassword,user))
					result = HT.Blockquote(HT.Font('Change Result: ',color='green'),HT.Font('You have succesfully changed your password. You may continue to use WebQTL.',color='black'))
				else:
					result = HT.Blockquote(HT.Font('Error: ',color='red'),HT.Font('You entered wrong user name or password. Please try it again.',color='black'))
			except:
				result = HT.Blockquote(HT.Font('Error: ',color='red'),HT.Font('User database is not ready yet. Try again later.',color='black'))
		else:
			result = HT.Blockquote(HT.Font('Error: ',color='red'),HT.Font('No user name or password or new password was entered, Please try it again.',color='black'))
		
		result.__setattr__("class","subtitle")
		self.dict['title'] = 'Change Password Result'
		self.dict['body'] = HT.TD(result,colspan=2,height=200,width="100%",bgColor='#eeeeee')

