#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import luna


def luna_node_present(data):
    name = data.pop('name')
    changed = False
    ret = True

    try:
        node = luna.Node(name=name)
    except RuntimeError:
        if data['group'] is None:
            err_msg = "Group needs to be specified to create the node"
            return True, changed, err_msg
        args = {
            'name': name,
            'create': True,
            'group': data['group'],
            'localboot': data['localboot'],
            'setupbmc': data['setupbmc'],
            'service': data['service'],
            'comment': data['comment'],
        }
        node = luna.Node(**args)
        changed = True

    ansible_ifs = [e['name'] for e in data['interfaces']]
    node_ifs = node.list_ifs().keys()
    undefined_ifs = [e for e in ansible_ifs if e not in node_ifs]

    if undefined_ifs:
        err_msg = ("Node does not have {} interfaces configured."
                   .format(" ".join(undefined_ifs)))
        return True, changed, err_msg

    keys = ['localboot', 'setupbmc', 'service', 'port', 'comment']
    for key in keys:
        if data[key] is None:
            continue
        if node.get(key) == data[key]:
            continue
        ret &= node.set(key, data[key])
        changed = True

    node_show = node.show()
    keys = ['group', 'switch']
    for key in keys:
        if (data[key] is not None
                and node_show[key] != '[' + data[key] + ']'):
            ret &= getattr(node, "set_%s" % key)(data[key])
            changed = True

    if (data['mac'] is not None
            and node.get_mac != data['mac']):
        ret &= node.set_mac(data['mac'])
        changed = True

    for e in data['interfaces']:
        ifname = e['name']
        ansible_ips = e['ips']
        conf_ips = []  # configured IPs

        for i in [4, 6]:
            ip = node.get_ip(ifname, version=i, quiet=True)

            if ip is None:
                continue

            conf_ips.append(ip)

        ips_to_change = [i for i in ansible_ips if i not in conf_ips]
        for ip in ips_to_change:

            ret &= node.set_ip(
                interface_name=ifname,
                ip=ip)

            changed = True

    return not ret, changed, str(node)


def luna_node_absent(data):
    name = data['name']
    try:
        node = luna.Node(name=name)
    except RuntimeError:
        return False, False, name

    return not node.delete(), True, name


def main():
    module = AnsibleModule(
        argument_spec={
            'name': {
                'type': 'str', 'default': None, 'required': True},
            'group': {
                'type': 'str', 'default': None, 'required': False},
            'comment': {
                'type': 'str', 'default': None, 'required': False},
            'interfaces': {
                'type': 'list', 'default': [], 'required': False},
            'localboot': {
                'type': 'bool', 'default': None, 'required': False},
            'setupbmc': {
                'type': 'bool', 'default': None, 'required': False},
            'service': {
                'type': 'bool', 'default': None, 'required': False},
            'mac': {
                'type': 'str', 'default': None, 'required': False},
            'switch': {
                'type': 'str', 'default': None, 'required': False},
            'port': {
                'type': 'int', 'default': None, 'required': False},
            'state': {
                'type': 'str', 'default': 'present',
                'choices': ['present', 'absent']}
        }
    )

    choice_map = {
        'present': luna_node_present,
        'absent': luna_node_absent,
    }

    is_error, has_changed, result = choice_map.get(
        module.params['state'])(module.params)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg='Error node changing', meta=result)


if __name__ == '__main__':
    main()
