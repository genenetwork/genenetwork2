import json

from flask import (Flask, g, render_template, url_for, request, make_response,
                   redirect, flash)

from wqflask import app

from utility.authentication_tools import check_owner_or_admin
from utility.redis_tools import get_resource_info, get_group_info, get_groups_like_unique_column, get_user_id, get_user_by_unique_column, get_users_like_unique_column, add_access_mask, add_resource, change_resource_owner

from utility.logger import getLogger
logger = getLogger(__name__)


@app.route("/resources/manage", methods=('GET', 'POST'))
def manage_resource():
    params = request.form if request.form else request.args
    if 'resource_id' in request.args:
        resource_id = request.args['resource_id']
        admin_status = check_owner_or_admin(resource_id=resource_id)

        resource_info = get_resource_info(resource_id)
        group_masks = resource_info['group_masks']
        group_masks_with_names = get_group_names(group_masks)
        default_mask = resource_info['default_mask']['data']
        owner_id = resource_info['owner_id']

        owner_display_name = None
        if owner_id != "none":
            try:  # ZS: User IDs are sometimes stored in Redis as bytes and sometimes as strings, so this is just to avoid any errors for the time being
                owner_id = str.encode(owner_id)
            except:
                pass
            owner_info = get_user_by_unique_column("user_id", owner_id)
            if 'name' in owner_info:
                owner_display_name = owner_info['full_name']
            elif 'user_name' in owner_info:
                owner_display_name = owner_info['user_name']
            elif 'email_address' in owner_info:
                owner_display_name = owner_info['email_address']

        return render_template("admin/manage_resource.html", owner_name=owner_display_name, resource_id=resource_id, resource_info=resource_info, default_mask=default_mask, group_masks=group_masks_with_names, admin_status=admin_status)


@app.route("/search_for_users", methods=('POST',))
def search_for_user():
    params = request.form
    user_list = []
    user_list += get_users_like_unique_column("full_name", params['user_name'])
    user_list += get_users_like_unique_column(
        "email_address", params['user_email'])

    return json.dumps(user_list)


@app.route("/search_for_groups", methods=('POST',))
def search_for_groups():
    params = request.form
    group_list = []
    group_list += get_groups_like_unique_column("id", params['group_id'])
    group_list += get_groups_like_unique_column("name", params['group_name'])

    user_list = []
    user_list += get_users_like_unique_column("full_name", params['user_name'])
    user_list += get_users_like_unique_column(
        "email_address", params['user_email'])
    for user in user_list:
        group_list += get_groups_like_unique_column("admins", user['user_id'])
        group_list += get_groups_like_unique_column("members", user['user_id'])

    return json.dumps(group_list)


@app.route("/resources/change_owner", methods=('POST',))
def change_owner():
    resource_id = request.form['resource_id']
    if 'new_owner' in request.form:
        admin_status = check_owner_or_admin(resource_id=resource_id)
        if admin_status == "owner":
            new_owner_id = request.form['new_owner']
            change_resource_owner(resource_id, new_owner_id)
            flash("The resource's owner has beeen changed.", "alert-info")
            return redirect(url_for("manage_resource", resource_id=resource_id))
        else:
            flash("You lack the permissions to make this change.", "error")
            return redirect(url_for("manage_resource", resource_id=resource_id))
    else:
        return render_template("admin/change_resource_owner.html", resource_id=resource_id)


@app.route("/resources/change_default_privileges", methods=('POST',))
def change_default_privileges():
    resource_id = request.form['resource_id']
    admin_status = check_owner_or_admin(resource_id=resource_id)
    if admin_status == "owner" or admin_status == "edit-admins":
        resource_info = get_resource_info(resource_id)
        default_mask = resource_info['default_mask']
        if request.form['open_to_public'] == "True":
            default_mask['data'] = 'view'
        else:
            default_mask['data'] = 'no-access'
        resource_info['default_mask'] = default_mask
        add_resource(resource_info)
        flash("Your changes have been saved.", "alert-info")
        return redirect(url_for("manage_resource", resource_id=resource_id))
    else:
        return redirect(url_for("no_access_page"))


@app.route("/resources/add_group", methods=('POST',))
def add_group_to_resource():
    resource_id = request.form['resource_id']
    admin_status = check_owner_or_admin(resource_id=resource_id)
    if admin_status == "owner" or admin_status == "edit-admins" or admin_status == "edit-access":
        if 'selected_group' in request.form:
            group_id = request.form['selected_group']
            resource_info = get_resource_info(resource_id)
            default_privileges = resource_info['default_mask']
            return render_template("admin/set_group_privileges.html", resource_id=resource_id, group_id=group_id, default_privileges = default_privileges)
        elif all(key in request.form for key in ('data_privilege', 'metadata_privilege', 'admin_privilege')):
            group_id = request.form['group_id']
            group_name = get_group_info(group_id)['name']
            access_mask = {
                'data': request.form['data_privilege'],
                'metadata': request.form['metadata_privilege'],
                'admin': request.form['admin_privilege']
            }
            add_access_mask(resource_id, group_id, access_mask)
            flash("Privileges have been added for group {}.".format(
                group_name), "alert-info")
            return redirect(url_for("manage_resource", resource_id=resource_id))
        else:
            return render_template("admin/search_for_groups.html", resource_id=resource_id)
    else:
        return redirect(url_for("no_access_page"))


def get_group_names(group_masks):
    group_masks_with_names = {}
    for group_id, group_mask in list(group_masks.items()):
        this_mask = group_mask
        group_name = get_group_info(group_id)['name']
        this_mask['name'] = group_name
        group_masks_with_names[group_id] = this_mask
    
    return group_masks_with_names
