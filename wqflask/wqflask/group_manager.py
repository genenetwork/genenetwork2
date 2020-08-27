
from __future__ import print_function, division, absolute_import

import random, string

from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash)

from wqflask import app
from wqflask.user_login import send_verification_email, send_invitation_email, basic_info, set_password

from utility.redis_tools import get_user_groups, get_group_info, save_user, create_group, delete_group, add_users_to_group, remove_users_from_group, \
                                change_group_name, save_verification_code, check_verification_code, get_user_by_unique_column, get_resources, get_resource_info

from utility.logger import getLogger
logger = getLogger(__name__)

@app.route("/groups/manage", methods=('GET', 'POST'))
def manage_groups():
   params = request.form if request.form else request.args
   if "add_new_group" in params:
      return redirect(url_for('add_group'))
   else:
      admin_groups, member_groups = get_user_groups(g.user_session.user_id)
      return render_template("admin/group_manager.html", admin_groups=admin_groups, member_groups=member_groups)

@app.route("/groups/view", methods=('GET', 'POST'))
def view_group():
   params = request.form if request.form else request.args
   group_id = params['id']
   group_info = get_group_info(group_id)
   admins_info = []
   user_is_admin = False
   if g.user_session.user_id in group_info['admins']:
      user_is_admin = True
   for user_id in group_info['admins']:
      if user_id:
         user_info = get_user_by_unique_column("user_id", user_id)
         admins_info.append(user_info)
   members_info = []
   for user_id in group_info['members']:
      if user_id:
         user_info = get_user_by_unique_column("user_id", user_id)
         members_info.append(user_info)

   #ZS: This whole part might not scale well with many resources
   resources_info  = []
   all_resources = get_resources()
   for resource_id in all_resources:
      resource_info = get_resource_info(resource_id)
      group_masks = resource_info['group_masks']
      if group_id in group_masks:
         this_resource = {}
         privileges = group_masks[group_id]
         this_resource['id'] = resource_id
         this_resource['name'] = resource_info['name']
         this_resource['data'] = privileges['data']
         this_resource['metadata'] = privileges['metadata']
         this_resource['admin'] = privileges['admin']
         resources_info.append(this_resource)

   return render_template("admin/view_group.html", group_info=group_info, admins=admins_info, members=members_info, user_is_admin=user_is_admin, resources=resources_info)

@app.route("/groups/remove", methods=('POST',))
def remove_groups():
   group_ids_to_remove = request.form['selected_group_ids']
   for group_id in group_ids_to_remove.split(":"):
      delete_group(g.user_session.user_id, group_id)

   return redirect(url_for('manage_groups'))

@app.route("/groups/remove_users", methods=('POST',))
def remove_users():
   group_id = request.form['group_id']
   admin_ids_to_remove = request.form['selected_admin_ids']
   member_ids_to_remove = request.form['selected_member_ids']

   remove_users_from_group(g.user_session.user_id, admin_ids_to_remove.split(":"), group_id, user_type="admins")
   remove_users_from_group(g.user_session.user_id, member_ids_to_remove.split(":"), group_id, user_type="members")

   return redirect(url_for('view_group', id=group_id))

@app.route("/groups/add_<path:user_type>", methods=('POST',))
def add_users(user_type='members'):
   group_id = request.form['group_id']
   if user_type == "admins":
      user_emails = request.form['admin_emails_to_add'].split(",")
      add_users_to_group(g.user_session.user_id, group_id, user_emails, admins = True)
   elif user_type == "members":
      user_emails = request.form['member_emails_to_add'].split(",")
      add_users_to_group(g.user_session.user_id, group_id, user_emails, admins = False)

   return redirect(url_for('view_group', id=group_id))

@app.route("/groups/change_name", methods=('POST',))
def change_name():
   group_id = request.form['group_id']
   new_name = request.form['new_name']
   group_info = change_group_name(g.user_session.user_id, group_id, new_name)

   return new_name

@app.route("/groups/create", methods=('GET', 'POST'))
def add_or_edit_group():
   params = request.form if request.form else request.args
   if "group_name" in params:
      member_user_ids = set()
      admin_user_ids = set()
      admin_user_ids.add(g.user_session.user_id) #ZS: Always add the user creating the group as an admin
      if "admin_emails_to_add" in params:
         admin_emails = params['admin_emails_to_add'].split(",")
         for email in admin_emails:
            user_details = get_user_by_unique_column("email_address", email)
            if user_details:
               admin_user_ids.add(user_details['user_id'])
         #send_group_invites(params['group_id'], user_email_list = admin_emails, user_type="admins")
      if "member_emails_to_add" in params:
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
      else:
         temp_password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
         user_details = {
            'user_id': str(uuid.uuid4()),
            'email_address': user_email,
            'registration_info': basic_info(),
            'password': set_password(temp_password),
            'confirmed': 0
         }
         save_user(user_details, user_details['user_id'])
         send_invitation_email(user_email, temp_password)

#@app.route()