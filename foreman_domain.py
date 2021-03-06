#!/usr/bin/env python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: foreman_domain
short_description: Manage Foreman Domains using Foreman API v2
description:
- Create and delete Foreman Domain using Foreman API v2
options:
  name:
    description: Domain name
    required: true
    default: null
    aliases: []
  fullname:
    description: Description of the domain
    required: false
    default: null
  state:
    description: Domain state
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
- name: Ensure example.com
  foreman_domain:
    name: example.com
    fullname: Example domain
    state: present
    foreman_host: 127.0.0.1
    foreman_port: 443
    foreman_user: admin
    foreman_pass: secret
'''

try:
    from foreman.foreman import *
except ImportError:
    foremanclient_found = False
else:
    foremanclient_found = True


def ensure(module):
    name = module.params['name']
    fullname = module.params['fullname']
    state = module.params['state']

    foreman_host = module.params['foreman_host']
    foreman_port = module.params['foreman_port']
    foreman_user = module.params['foreman_user']
    foreman_pass = module.params['foreman_pass']

    theforeman = Foreman(hostname=foreman_host,
                         port=foreman_port,
                         username=foreman_user,
                         password=foreman_pass)

    data = {'name': name}

    try:
        domain = theforeman.search_domain(data=data)
    except ForemanError as e:
        module.fail_json(msg='Could not get domain: {0}'.format(e.message))

    data['fullname'] = fullname

    if not domain and state == 'present':
        try:
            domain = theforeman.create_domain(data=data)
            return True, domain
        except ForemanError as e:
            module.fail_json(msg='Could not create domain: {0}'.format(e.message))

    if domain:
        if state == 'absent':
            try:
                domain = theforeman.delete_domain(id=domain.get('id'))
                return True, domain
            except ForemanError as e:
                module.fail_json(msg='Could not delete domain: {0}'.format(e.message))

        if not all(data[key] == domain[key] for key in data):
            try:
                domain = theforeman.update_domain(id=domain.get('id'), data=data)
                return True, domain
            except ForemanError as e:
                module.fail_json(msg='Could not update domain: {0}'.format(e.message))

    return False, domain


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            fullname=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            foreman_host=dict(type='str', default='127.0.0.1'),
            foreman_port=dict(type='str', default='443'),
            foreman_user=dict(type='str', required=True),
            foreman_pass=dict(type='str', required=True)
        ),
    )

    if not foremanclient_found:
        module.fail_json(msg='python-foreman module is required. See https://github.com/Nosmoht/python-foreman.')

    changed, domain = ensure(module)
    module.exit_json(changed=changed, domain=domain)

# import module snippets
from ansible.module_utils.basic import *

main()
