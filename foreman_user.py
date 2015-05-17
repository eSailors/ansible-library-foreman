#!/usr/bin/env python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: foreman_user
short_description: Manage Foreman Users using Foreman API v2
description:
- Manage Foreman Architectures using Foreman API v2
options:
  admin:
    description: Is an admin account
    required: false
    default: False
    choices: [True, False]
  auth:
    description: Authorization method
    required: false
    default: 'Internal'
  login:
    description: Name of architecture
    required: true
    default: null
    aliases: ['name']
  firstname:
    description: User's firstname
    required: false
    default: null
  lastname:
    description: User's lastname
    required: false
    default: null
  mail:
    description: Mail address
    required: false
    default: null
  password:
    description: Password
    required: false
    default: null
  roles:
    description: Roles assigned to the user
    required: false
    default: null
  state:
    description: State of architecture
    required: false
    default: present
    choices: ["present", "absent"]
  foreman_host:
    description: Hostname or IP address of Foreman system
    required: false
    default: 127.0.0.1
  foreman_port:
    description: Port of Foreman API
    required: false
    default: 443
  foreman_user:
    description: Username to be used to authenticate on Foreman
    required: true
    default: null
  foreman_pass:
    description: Password to be used to authenticate user on Foreman
    required: true
    default: null
notes:
- Requires the python-foreman package to be installed. See https://github.com/Nosmoht/python-foreman.
author: Thomas Krahn
'''

EXAMPLES = '''
- name: Ensure ARM Architecture is present
  foreman_architecture:
    name: ARM
    state: present
    foreman_user: admin
    foreman_pass: secret
'''

try:
    from foreman.foreman import *

    foremanclient_found = True
except ImportError:
    foremanclient_found = False


def get_roles(module, theforeman, roles):
    result = list()
    for item in roles:
        search_data = dict()
        if isinstance(item, dict):
            search_data = item
        else:
            search_data['name'] = item
        try:
            role = theforeman.search_role(data=search_data)
            if not role:
                module.fail_json(msg='Could not find role {0}'.format(item))
            result.append(role)
        except ForemanError as e:
            module.fail_json(msg='Could not search role {0}: {1}'.format(item, e.message))
    return result


def extract_key_value_from_dict_array(a, key):
    result = list()
    for d in a:
        result.append(d.get(key, None))
    return result


def equal_roles(assigned_roles, defined_roles):
    ar = set(extract_key_value_from_dict_array(assigned_roles, 'name'))
    dr = set(extract_key_value_from_dict_array(defined_roles, 'name'))
    return ar.issubset(dr) and dr.issubset(ar)


def ensure(module):
    login = module.params['login']
    state = module.params['state']
    roles = module.params['roles']

    foreman_host = module.params['foreman_host']
    foreman_port = module.params['foreman_port']
    foreman_user = module.params['foreman_user']
    foreman_pass = module.params['foreman_pass']

    user_options = ['admin', 'auth_source_name', 'firstname', 'lastname', 'mail']

    theforeman = Foreman(hostname=foreman_host,
                         port=foreman_port,
                         username=foreman_user,
                         password=foreman_pass)

    data = dict(login=login)

    try:
        # Search the user. If it does exist get detailed information
        found = theforeman.search_user(data=data)
        if found:
            user = theforeman.get_user(id=found.get('id'))
        else:
            user = None
    except ForemanError as e:
        module.fail_json(msg='Could not get user: {0}'.format(e.message))

    # Compare assigned values. password is not returned by Foreman and must be handled different
    for key in user_options:
        if key in module.params:
            data[key] = module.params[key]

    if roles:
        data['roles'] = get_roles(module, theforeman, roles)
    else:
        data['roles'] = []

    if not user and state == 'present':
        try:
            data['password'] = module.params['password']
            user = theforeman.create_user(data=data)
            return True, user
        except ForemanError as e:
            module.fail_json(msg='Could not create user: {0}'.format(e.message))

    if user:
        if state == 'absent':
            try:
                user, theforeman.delete_user(id=user.get('id'))
                return True, user
            except ForemanError as e:
                module.fail_json(msg='Could not delete user: {0}'.format(e.message))

        if (not all(user.get(key, data[key]) == data[key] for key in user_options)) or (
                not equal_roles(defined_roles=data.get('roles'), assigned_roles=user.get('roles'))):
            try:
                # module.fail_json(msg='{0}\n{1}'.format(user.get('roles'), data.get('roles')))
                user = theforeman.update_user(id=user.get('id'), data=data)
                return True, user
            except ForemanError as e:
                module.fail_json(msg='Could not update user: {0}'.format(e.message))

    return False, user


def main():
    module = AnsibleModule(
        argument_spec=dict(
            admin=dict(type='str', required=False),
            auth_source_name=dict(type='str', default='Internal', aliases=['auth']),
            login=dict(type='str', required=True, aliases=['name']),
            firstname=dict(type='str', required=False),
            lastname=dict(type='str', required=False),
            mail=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            password=dict(type='str', required=False),
            roles=dict(type='list', required=False),
            foreman_host=dict(type='str', default='127.0.0.1'),
            foreman_port=dict(type='str', default='443'),
            foreman_user=dict(type='str', required=True),
            foreman_pass=dict(type='str', required=True)
        ),
    )

    if not foremanclient_found:
        module.fail_json(msg='python-foreman module is required. See https://github.com/Nosmoht/python-foreman.')

    changed, user = ensure(module)
    module.exit_json(changed=changed, user=user)

# import module snippets
from ansible.module_utils.basic import *

main()
