# vi: set ts=4 expandtab:
#
#    Copyright (C) 2015 Lance Linder
#

import re

import troposphere
import troposphere.ec2
import troposphere_ext
import collections
import yaml


class VPC(troposphere.ec2.VPC):

    def __init__(self, title, template=None, **kwargs):
        helper_keys = ['NetworkAclEntries', 'NetworkAcls', 'Subnets', 'AttachGateway', 'RouteTables', 'SecurityGroups']
        clean_kwargs = { k:v for k, v in kwargs.iteritems() if not k in helper_keys }

        self._network_acl_entries = kwargs.get('NetworkAclEntries', [])
        self._network_acls = kwargs.get('NetworkAcls', [])
        self._subnets = kwargs.get('Subnets', [])
        self._attach_gateway = kwargs.get('AttachGateway')
        self._route_tables = kwargs.get('RouteTables', [])
        self._security_groups = kwargs.get('SecurityGroups', [])

        super(VPC, self).__init__(title, template, **clean_kwargs)

        if template is not None:

            # gatey attachment
            if self._attach_gateway is not None:
                attachment = self._attach_gateway
                attachment.title = '{}{}'.format(self.title, attachment.title)
                attachment.VpcId = troposphere.Ref(self)
                template._register_resource(attachment)

            # network ACLs
            for acl in self._network_acls:
                acl.title = '{}{}'.format(self.title, acl.title)
                acl.VpcId = troposphere.Ref(self)

                # network ACL entries
                for entry in acl.network_acl_entries:
                    entry.title = '{}{}'.format(acl.title, entry.title)
                    entry.NetworkAclId = troposphere.Ref(acl)
                    template._register_resource(entry)

                template._register_resource(acl)

            # route tables
            for route_table in self._route_tables:
                route_table.title = '{}{}'.format(self.title, route_table.title)
                route_table.VpcId = troposphere.Ref(self)

                # routes
                for route in route_table.routes:
                    route.title = '{}{}'.format(route_table.title, route.title)
                    route.RouteTableId = troposphere.Ref(route_table)
                    template._register_resource(route)

                template._register_resource(route_table)

            # subnets
            for subnet in self._subnets:
                subnet.title = '{}{}'.format(self.title, subnet.title)
                subnet.VpcId = troposphere.Ref(self)

                # route table associations
                for route_table in subnet.route_tables:
                    route_table_assoc = troposphere.ec2.SubnetRouteTableAssociation(
                        '{}{}Assoc'.format(subnet.title, route_table.get_ref().title),
                        SubnetId = troposphere.Ref(subnet),
                        RouteTableId = route_table)
                    template._register_resource(route_table_assoc)

                # network ACL associations
                for acl in subnet.network_acls:
                    network_acl_assoc = troposphere.ec2.SubnetNetworkAclAssociation(
                        '{}{}Assoc'.format(subnet.title, acl.get_ref().title),
                        SubnetId = troposphere.Ref(subnet),
                        NetworkAclId = acl)
                    template._register_resource(network_acl_assoc)

                template._register_resource(subnet)

            # security groups
            for security_group in self._security_groups:
                security_group.VpcId = troposphere.Ref(self)
                template._register_resource(security_group)



    @property
    def network_acl_entries(self):
        return self._network_acl_entries

    @property
    def network_acls(self):
        return self._network_acls

    @property
    def subnets(self):
        return self._subnets

    @property
    def attach_gateway(self):
        return self._attach_gateway

    @property
    def route_table(self):
        return self._route_table

    @property
    def security_groups(self):
        return self._security_groups
    

class RouteTable(troposphere.ec2.RouteTable):

    def __init__(self, title, template=None, **kwargs):
        helper_keys = ['Routes']
        clean_kwargs = { k:v for k, v in kwargs.iteritems() if not k in helper_keys }
        
        self._routes = kwargs.get('Routes', [])
        super(RouteTable, self).__init__(title, template, **clean_kwargs)

    @property
    def routes(self):
        return self._routes


class Route(troposphere.ec2.Route):

    def JSONrepr(self):
        depends_on = self.resource.get('DependsOn')
        if isinstance(depends_on, troposphere_ext.TRef):
            self.resource['DependsOn'] = depends_on.get_ref().title
                
        return super(Route, self).JSONrepr()


class Subnet(troposphere.ec2.Subnet):

    def __init__(self, title, template=None, **kwargs):
        helper_keys = ['NetworkAcls', 'RouteTables']
        clean_kwargs = { k:v for k, v in kwargs.iteritems() if not k in helper_keys }

        self._network_acls = kwargs.get('NetworkAcls', [])
        self._route_tables = kwargs.get('RouteTables', [])

        super(Subnet, self).__init__(title, template, **clean_kwargs)

    @property
    def network_acls(self):
        return self._network_acls

    @property
    def route_tables(self):
        return self._route_tables


class NetworkAcl(troposphere.ec2.NetworkAcl):
    
    def __init__(self, title, template=None, **kwargs):
        helper_keys = ['NetworkAclEntries']
        clean_kwargs = { k:v for k, v in kwargs.iteritems() if not k in helper_keys }
        
        self._network_acl_entries = kwargs.get('NetworkAclEntries', [])
        
        super(NetworkAcl, self).__init__(title, template, **clean_kwargs)

    @property
    def network_acl_entries(self):
        return self._network_acl_entries

class CloudConfig(troposphere.AWSHelperFn):

    def __init__(self, config):
        self.config = config

    def JSONrepr(self):
        result = yaml.dump(self.config, default_flow_style=False)
        result = '#cloud-config\n' + result
        return troposphere.Base64(result)

class UserData(troposphere.AWSHelperFn):

    def __init__(self, *args):
        self.data = args

    def _strip_margin(self, value):
        return re.sub('\n[ \t]*\|', '\n', value)

    def JSONrepr(self):
        # flatten array
        data = [x for y in self.data for x in (y if isinstance(y, list) else [y])]
        # strip margin from the strings
        data = [ self._strip_margin(v) if isinstance(v, str) else v for v in data]
        return troposphere.Base64(troposphere.Join('', data))




