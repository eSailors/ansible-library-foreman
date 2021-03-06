#!/usr/bin/env python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: foreman_compute_resource
short_description: Manage Foreman Compute resources using Foreman API v2
description:
- Create and delete Foreman Compute Resources using Foreman API v2
options:
  name:
    description: Compute Resource name
    required: true
    default: null
    aliases: []
  datacenter: Name of Datacenter (only for Vmware)
    required: false
    default: null
  password:
    description: Password for Ovirt, EC2, Vmware, Openstack. Secret key for EC2
    required: false
    default: null
  provider:
    description: Providers name (e.g. Ovirt, EC2, Vmware, Openstack, EC2, Google)
    required: false
    default: null
  server:
    description: Hostname of Vmware vSphere system
    required: false
    default: null
  state:
    description: Compute Resource state
    required: false
    default: present
    choices: ["present", "absent"]
  tenant:
    description: Tenant name for Openstack
  url:
    description: URL for Libvirt, Ovirt, and Openstack
    required: false
    default: null
  user:
    description: Username for Ovirt, EC2, Vmware, Openstack. Access Key for EC2.
    required: false
    default: null
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
- name: Ensure Vmware compute resource
  foreman_compute_resource:
    name: VMware
    datacenter: dc01
    provider: VMware
    server: vsphere.example.com
    url: vsphere.example.com
    user: domain\admin
    password: secret
    state: present
    foreman_user: admin
    foreman_pass: secret
- name: Ensure Openstack compute resource
  foreman_compute_resource:
    name: Openstack
    provider: OpenStack
    tenant: ExampleTenant
    url: https://compute01.example.com:5000/v2.0/tokens
    user: admin
'''

try:
    from foreman.foreman import *
except ImportError:
    foremanclient_found = False
else:
    foremanclient_found = True


def get_provider_params(provider):
    provider_name = provider.lower()

    if provider_name == 'docker':
        return ['password', 'url', 'user']
    elif provider_name == 'ec2':
        return ['access_key', 'password', 'region', 'url', 'user']
    elif provider_name == 'google':
        return ['email', 'key_path', 'project', 'url', 'zone']
    elif provider_name == 'libvirt':
        return ['display_type', 'url']
    elif provider_name == 'ovirt':
        return ['url', 'user', 'password']
    elif provider_name == 'openstack':
        return ['url', 'user', 'password', 'tenant']
    elif provider_name == 'vmware':
        return ['datacenter', 'user', 'password', 'server']
    else:
        return []


def ensure(module):
    name = module.params['name']
    state = module.params['state']
    provider = module.params['provider']

    foreman_host = module.params['foreman_host']
    foreman_port = module.params['foreman_port']
    foreman_user = module.params['foreman_user']
    foreman_pass = module.params['foreman_pass']

    theforeman = Foreman(hostname=foreman_host,
                         port=foreman_port,
                         username=foreman_user,
                         password=foreman_pass)

    data = dict(name=name)

    try:
        compute_resource = theforeman.search_compute_resource(data=data)
    except ForemanError as e:
        module.fail_json(msg='Could not get compute resource: {0}'.format(e.message))

    if state == 'absent':
        if compute_resource:
            try:
                compute_resource = theforeman.delete_compute_resource(id=compute_resource.get('id'))
            except ForemanError as e:
                module.fail_json(msg='Could not delete compute resource: {0}'.format(e.message))
            return True, compute_resource

    data['provider'] = provider
    provider_params = get_provider_params(provider=provider)
    for key in provider_params:
        data[key] = module.params[key]

    if state == 'present':
        if not compute_resource:
            try:
                compute_resource = theforeman.create_compute_resource(data=data)
            except ForemanError as e:
                module.fail_json(msg='Could not create compute resource: {0}'.format(e.message))
            return True, compute_resource

        return False, compute_resource

        if not all(data.get(key, None) == compute_resource.get(key, None) for key in provider_params):
            try:
                compute_resource = theforeman.update_compute_resource(id=compute_resource.get('id'), data=data)
            except ForemanError as e:
                module.fail_json(msg='Could not update compute resource: {0}'.format(e.message))
            return True, compute_resource

    return False, compute_resource


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            access_key=dict(type='str', requireD=False),
            datacenter=dict(type='str', required=False),
            display_type=dict(type='str', required=False),
            email=dict(type='str', required=False),
            key_path=dict(type='str', required=False),
            password=dict(type='str', required=False),
            provider=dict(type='str', required=False),
            region=dict(type='str', required=False),
            server=dict(type='str', required=False),
            url=dict(type='str', required=False),
            user=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            tenat=dict(type='str', required=False),
            foreman_host=dict(type='str', default='127.0.0.1'),
            foreman_port=dict(type='str', default='443'),
            foreman_user=dict(type='str', required=True),
            foreman_pass=dict(type='str', required=True)
        ),
    )

    if not foremanclient_found:
        module.fail_json(msg='python-foreman module is required. See https://github.com/Nosmoht/python-foreman.')

    changed, compute_resource = ensure(module)
    module.exit_json(changed=changed, compute_resource=compute_resource)

# import module snippets
from ansible.module_utils.basic import *

main()
