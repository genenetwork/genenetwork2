
from __future__ import print_function, division, absolute_import

from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash)

from wqflask import app
from wqflask.user_login import send_verification_email

from utility.redis_tools import get_user_groups, get_group_info, create_group, delete_group, add_users_to_group, remove_users_from_group, \
                                change_group_name, save_verification_code, check_verification_code, get_user_by_unique_column

from utility.logger import getLogger
logger = getLogger(__name__)

@app.route("/groups/manage", methods=('GET', 'POST'))
def manage_groups():
   params = request.form if request.form else request.args
   if "add_new_group" in params:
      return redirect(url_for('add_group'))
   else:
      admin_groups, user_groups = get_user_groups(g.user_session.user_id)
      return render_template("admin/group_manager.html", admin_groups=admin_groups, user_groups=user_groups)

@app.route("/groups/remove", methods=('POST',))
def remove_groups():
   group_ids_to_remove = request.form['selected_group_ids']
   for group_id in group_ids_to_remove.split(":"):
      delete_group(g.user_session.user_id, group_id)

   return redirect(url_for('manage_groups'))

@app.route("/groups/create", methods=('GET', 'POST'))
def add_group():
   params = request.form if request.form else request.args
   if "group_name" in params:
      member_user_ids = set()
      admin_user_ids = set()
      admin_user_ids.add(g.user_session.user_id) #ZS: Always add the user creating the group as an admin
      if "admin_emails" in params:
         admin_emails = params['admin_emails_to_add'].split(",")
         for email in admin_emails:
            user_details = get_user_by_unique_column("email_address", email)
            if user_details:
               admin_user_ids.add(user_details['user_id'])
         #send_group_invites(params['group_id'], user_email_list = admin_emails, user_type="admins")
      if "user_emails" in params:
         member_emails = params['member_emails_to_add'].split(",")
         for email in member_emails:
            user_details = get_user_by_unique_column("email_address", email)
            if user_details:
               member_user_ids.add(user_details['user_id'])
         #send_group_invites(params['group_id'], user_email_list = user_emails, user_type="members")

      create_group(list(admin_user_ids), list(member_user_ids), params['group_name'])
      return redirect(url_for('manage_groups'))
   else:
      return render_template("admin/create_group.html")

#ZS: Will integrate this later, for now just letting users be added directly
def send_group_invites(group_id, user_email_list = [], user_type="members"):
   for user_email in user_email_list:
      user_details = get_user_by_unique_column("email_address", user_email)
      if user_details:
         group_info = get_group_info(group_id)
         #ZS: Probably not necessary since the group should normally always exist if group_id is being passed here,
         #    but it's technically possible to hit it if Redis is cleared out before submitting the new users or something
         if group_info:
            #ZS: Don't add user if they're already an admin or if they're being added a regular user and are already a regular user,
            #    but do add them if they're a regular user and are added as an admin
            if (user_details['user_id'] in group_info['admins']) or \
               ((user_type == "members") and (user_details['user_id'] in group_info['members'])):
               continue
            else:
               send_verification_email(user_details, template_name = "email/group_verification.txt", key_prefix = "verification_code", subject = "You've been invited to join a GeneNetwork user group")

#@app.route()