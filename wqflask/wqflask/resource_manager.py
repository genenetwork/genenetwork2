from __future__ import print_function, division, absolute_import

from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash)

from wqflask import app

from utility.authentication_tools import check_owner
from utility.redis_tools import get_resource_info, get_group_info, get_group_by_unique_column, get_user_id

from utility.logger import getLogger
logger = getLogger(__name__)

@app.route("/resources/manage", methods=('GET', 'POST'))
def view_resource():
    params = request.form if request.form else request.args
    if 'resource_id' in request.args:
        resource_id = request.args['resource_id']
        if check_owner(resource_id=resource_id):
            resource_info = get_resource_info(resource_id)
            group_masks = resource_info['group_masks']
            group_masks_with_names = get_group_names(group_masks)
            default_mask = resource_info['default_mask']['data']
            return render_template("admin/manage_resource.html", resource_id = resource_id, resource_info=resource_info, default_mask=default_mask, group_masks=group_masks_with_names)
        else:
            return redirect(url_for("no_access_page"))
        
@app.route("/resources/add_group", methods=('POST',))
def add_group_to_resource():
    resource_id = request.form['resource_id']
    if check_owner(resource_id=resource_id):
        if all(key in request.form for key in ('group_id', 'group_name', 'user_name', 'user_email')):
            group_list = []
            if request.form['group_id'] != "":
                the_group = get_group_info(request.form['group_id'])
                if the_group:
                    group_list.append(the_group)
            if request.form['group_name'] != "":
                matched_groups = get_group_by_unique_column("name", request.form['group_name'])
                for group in matched_groups:
                    group_list.append(group)
            if request.form['user_name'] != "":
                user_id = get_user_id("user_name", request.form['user_name'])
                if user_id:
                    matched_groups = get_group_by_unique_column("admins", user_id)
                    matched_groups += get_group_by_unique_column("members", user_id)
                    for group in matched_groups:
                        group_list.append(group)
            if request.form['user_email'] != "":
                user_id = get_user_id("email_address", request.form['user_email'])
                if user_id:
                    matched_groups = get_group_by_unique_column("admins", user_id)
                    matched_groups += get_group_by_unique_column("members", user_id)
                    for group in matched_groups:
                        group_list.append(group)
            return render_template("admin/select_group_to_add.html", group_list=group_list, resource_id = resource_id)
        elif 'selected_group' in request.form:
            group_id = request.form['selected_group']
            return render_template("admin/set_group_privileges.html", resource_id = resource_id, group_id = group_id)
        else:
            return render_template("admin/search_for_groups.html", resource_id = resource_id)
    else:
        return redirect(url_for("no_access_page"))

def get_group_names(group_masks):
    group_masks_with_names = {}
    for group_id, group_mask in group_masks.iteritems():
        this_mask = group_mask
        group_name = get_group_info(group_id)['name']
        this_mask['name'] = group_name
    
    return group_masks_with_names