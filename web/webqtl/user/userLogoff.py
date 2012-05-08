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
from base.myCookie import myCookie

#########################################
#      User Logoff Page
#########################################

class userLogoff(templatePage):
	def __init__(self, fd):	

		templatePage.__init__(self, fd)

		self.session_data_changed['user'] = 'Guest'
		self.session_data_changed['privilege'] = 'guest'

		#self.cookie.append(myCookie('user',' ',0))
		#self.cookie.append(myCookie('password',' ',0))
		result = HT.Blockquote(HT.Font('Logout Result: ',color='green'),HT.Font('You have been succesfully logged out. ',color='black'))
		result.__setattr__("class","subtitle")
		self.dict['title'] = 'User Logoff Result'
		self.dict['body'] = HT.TD(result,colspan=2,height=200,width="100%",bgColor='#eeeeee')
		LOGIN = HT.Href(text = "Login",Class="small", target="_blank",url="account.html")
		self.dict['login'] = LOGIN
			
