import boto
import json
import troposphere
import troposphere.ec2
import troposphere.route53
import troposphere.elasticloadbalancing
import troposphere_ext.ec2
import troposphere_ext.autoscaling
import re
import collections
import yaml

from troposphere import BaseAWSObject, AWSHelperFn

from troposphere_ext import utils

_template = None

def template(name):
    troposphere_ext._template = Template(name)
    return troposphere_ext._template


class Template(object):

    def __init__(self, name):
        self._name = name
        self._version = None
        self._description = None
        self._conditions = dict()
        self._mappings = dict()
        self._outputs = dict()
        self._parameters = dict()
        self._resources = dict()

    def version(self, version):
        self._version = version
        return self

    def description(self, description):
        self._description = description
        return self

    def parameter(self, title, **kwargs):
        self._update(self._parameters, troposphere.Parameter(
            title, **kwargs
        ))
        return self

    def mapping(self, title, mapping):
        self._mappings[title] = mapping
        return self

    # ------------------
    #  S3
    # ------------------

    def bucket(self, *args, **kwargs):
        self._create_resource(troposphere.s3.Bucket, *args, **kwargs)
        return self

    # -------------------
    #  IAM
    # -------------------

    def role(self, *args, **kwargs):
        self._create_resource(troposphere.iam.Role, *args, **kwargs)
        return self

    def instance_profile(self, *args, **kwargs):
        self._create_resource(troposphere.iam.InstanceProfile, *args, **kwargs)
        return self

    # -------------------
    #  Network
    # -------------------

    def internet_gateway(self, *args, **kwargs):
        self._create_resource(troposphere.ec2.InternetGateway, *args, **kwargs)
        return self

    def vpc(self, *args, **kwargs):
        self._create_resource(troposphere_ext.ec2.VPC, *args, **kwargs)
        return self

    # -------------------
    #  Auto Scaling
    # -------------------

    def auto_scaling_group(self, *args, **kwargs):
        self._create_resource(troposphere_ext.autoscaling.AutoScalingGroup, *args, **kwargs)
        return self

    # -------------------
    #  ELB
    # -------------------

    def load_balancer(self, *args, **kwargs):
        self._create_resource(troposphere.elasticloadbalancing.LoadBalancer, *args, **kwargs)
        return self

    # -------------------
    #  EC2
    # -------------------

    def eip(self, *args, **kwargs):
        self._create_resource(troposphere.ec2.EIP, *args, **kwargs)
        return self

    def instance(self, *args, **kwargs):
        self._create_resource(troposphere.ec2.Instance, *args, **kwargs)
        return self

    def security_group(self, *args, **kwargs):
        self._create_resource(troposphere.ec2.SecurityGroup, *args, **kwargs)
        return self

    # -------------------
    #  Route53
    # -------------------    

    def record_set(self, *args, **kwargs):
        self._create_resource(troposphere.route53.RecordSetType, *args, **kwargs)
        return self        


    # ----------------------------------
    #  Template APIs and helper methods
    # ----------------------------------


    def get_resource(self, resource):

        regex = resource.title if isinstance(resource, BaseAWSObject) else resource
        if isinstance(resource, BaseAWSObject):
            matches = [v for k,v in self._resources.iteritems() if resource.type is v.type and re.search(regex, k)]
        else:
            matches = [v for k,v in self._resources.iteritems() if re.search(regex, k)]

        if len(matches) > 1:
            titles = [r.title for r in matches]
            raise LookupError('More than one match found in "{}" for regex "{}".'.format(titles, regex))
        elif len(matches) > 0:
            return matches[0]
        else:
            return None

    def add_resource(self, resource):
        return self._register_resource(resource)[0]

    def _register_resource(self, resources):

        # ensure resources is iterable
        resources = resources if isinstance(resources, collections.Iterable) else (resources,)

        def _r(accu, r_resources):
            value = r_resources[0]
            # prefix resource title with the template name
            if not self._name in value.title:
                value.title = '{}{}'.format(self._name, value.title)
            # add a name tag to the resource for better visibility in the AWS web console
            if 'Tags' in value.props:
                # convert camel case title to snake case
                name_tag = utils.camel_to_snake(value.title) #'_'.join(filter(None, re.split(r'([A-Z][^A-Z]*)', value.title))).lower()
                # sometimes troposphere entities use Tags and other times they use a list of Tag
                is_tags_type = value.props['Tags'][0] is troposphere.Tags
                if not hasattr(value, 'Tags'):
                    # no tags defined so create new instance and set it
                    if is_tags_type:
                        # handle Tags type
                        tags = troposphere.Tags(Name=name_tag)
                    else:
                        # handle list type
                        if value.type == 'AWS::AutoScaling::AutoScalingGroup':
                            tags = [troposphere.autoscaling.Tag('Name', name_tag, True)]
                        else:
                            tags = [troposphere.ec2.Tag('Name', name_tag)]
                    value.Tags = tags
                else:
                    # already has tags so we need to merge the name tag in
                    if isinstance(value.Tags, troposphere.Tags):
                        # handle Tags type
                        value.Tags.tags.append({'Key': 'Name', 'Value': name_tag})
                    else:
                        # handle list 
                        if value.type == 'AWS::AutoScaling::AutoScalingGroup':
                            value.Tags.append(troposphere.autoscaling.Tag('Name', name_tag, True))
                        else:
                            value.Tags.append(troposphere.ec2.Tag('Name', name_tag))

            accu.append(self._update(self._resources, value))
            return accu if len(r_resources) < 2 else _r(accu, r_resouces[1:])

        return _r([], resources)

    def _create_resource(self, clazz, *args, **kwargs):
        """Creates a resource or list of resources. If the resource is already created then it will just be returned."""

        # recursive function for creating resources
        def _r(accu, *r_args, **r_kwargs):
            if len(r_args) is 1:
                arg = r_args[0]
                # TODO remove this as it shouldn't be necessary
                # handle lists by recursion
                # if isinstance(arg, list):
                #     print 'is list'
                #     if len(arg) is 0:
                #         return accu
                #     else:
                #         accu.extend(_r(accu, *arg[1:], **r_kwargs))
                #         return accu
                # if first argument is a string then treat it as the title and instantiate the clazz
                if isinstance(arg, str):
                    accu.append(clazz(arg, template=self, **r_kwargs))
                    return accu
                # if the first argument is already an instance of the class then just return it.
                elif isinstance(arg, clazz):
                    self._register_resource(arg)
                    accu.append(arg)
                    return accu
                else:
                    raise TypeError('Unknown argument type "{}"'.format(type(arg)))
            elif len(r_args) > 1:
                accu.extend(_r(accu, *r_args[1:], **r_kwargs))
                return accu

        # support lists by flatten the arguments.
        # this will make ([1,2,3]) into [1,2,3] or ('abc',1,2,3,[4,5]) into ['abc',1,2,3,4,5]
        args = [x for y in args for x in (y if isinstance(y, list) or isinstance(y, tuple) else (y,))]

        return _r([], *args, **kwargs)
                
    def _handle_duplicate_key(self, key):
        raise ValueError('duplicate key "%s" detected' % key)

    def _update(self, d, values):
        if isinstance(values, list):
            for v in values:
                if v.title in d:
                    self._handle_duplicate_key(values.title)
                d[v.title] = v
        else:
            if values.title in d:
                self._handle_duplicate_key(values.title)
            d[values.title] = values
        return values


    def to_json(self, indent=2, sort_keys=True, separators=(', ', ': ')):
        t = dict()
        if self._description:
            t['Description'] = self._description

        if self._version:
            t['AWSTemplateFormatVersion'] = self._version
        
        t['Conditions'] = self._conditions
        t['Mappings'] = self._mappings
        t['Outputs'] = self._outputs
        t['Parameters'] = self._parameters
        t['Resources'] = self._resources

        return json.dumps(t, cls=troposphere.awsencode, indent=indent, sort_keys=sort_keys, separators=separators)	


class TGetAtt(troposphere.GetAtt):

    def __init__(self, resource, attribute):
        self._resource = resource
        self._attribute = attribute
        self._resource_name = resource.title if isinstance(resource, BaseAWSObject) else resource
        # super(TGetAtt, self).__init__(self._resource_name, attribute)

    def JSONrepr(self):
        # resolve the resource and return the json representation object
        ref = self.get_ref()
        return {'Fn::GetAtt': [ref.title, self._attribute]}

    def get_ref(self):
        # resolve the resource and return the json representation object
        template = troposphere_ext._template
        ref = template.get_resource(self._resource)
        if ref is None:
            raise LookupError('Resource with matching regex "{}" was not found in template "{}"'.format(self._resource_name, template._name))
        else:
            return ref


class Ref(troposphere.Ref):

    def __init__(self, data):
        self._title = self.getdata(data)
        super(Ref, self).__init__(data)

    @property
    def title(self):
        return self._title


class TRef(Ref):
    """allows late binding of template resources by name"""

    def __init__(self, resource):
        self._resource = resource
        self._resource_name = resource.title if isinstance(resource, BaseAWSObject) else resource
        super(TRef, self).__init__(self._resource_name)

    def JSONrepr(self):
        # resolve the resource and return the json representation object
        ref = self.get_ref()
        return {'Ref': ref.title}

    def get_ref(self):
        # resolve the resource and return the json representation object
        template = troposphere_ext._template
        ref = template.get_resource(self._resource)
        if ref is None:
            raise LookupError('Resource with matching regex "{}" was not found in template "{}"'.format(self._resource_name, template._name))
        else:
            return ref


class SRef(AWSHelperFn):

    __resources = None
    __conn = None

    @staticmethod
    def yaml_reper(dumper, data):
        '''yaml representation function'''
        return dumper.represent_scalar('tag:yaml.org,2002:str', data.JSONrepr())

    @staticmethod
    def resources(region, stack_name):
        if SRef.__resources is None:
            if SRef.__conn is None:
                SRef.__conn = boto.cloudformation.connect_to_region(region)

            SRef.__resources = SRef.__conn.describe_stack_resources(stack_name)

        return [] if SRef.__resources is None else SRef.__resources

    def __init__(self, region, stack_name, resource):
        self._region = region
        self._stack_name = stack_name
        self._resource = resource
        self._resource_name = resource.title if isinstance(resource, BaseAWSObject) else resource

    def JSONrepr(self):

        resources = SRef.resources(self._region, self._stack_name)

        regex = self._resource.title+'$' if isinstance(self._resource, BaseAWSObject) else self._resource
        if isinstance(self._resource, BaseAWSObject):
            matches = [res for res in resources if res.resource_type == self._resource.type and re.search(regex, res.logical_resource_id)]
        else:
            matches = [res for res in resources if re.search(regex, res.logical_resource_id)]

        # # create list of matching resources from the given stack
        # matches = [res for res in resources if res.resource_type == self._resource.type and re.search(self._resource.title, res.logical_resource_id)]

        if len(matches) > 1:
            titles = [r.logical_resource_id for r in matches]
            raise LookupError('Found multiple matchings resources for {} in stack {}:{}'.format(
                self._resource_name, self._region, self._stack_name))
        elif len(matches) > 0:
            return matches[0].physical_resource_id
        else:
            raise LookupError('Unable to find matching resource for {} in stack {}:{}'.format(
                self._resource_name, self._region, self._stack_name))


# initialize yaml representation handlers for Cloud Config user data
yaml.add_representer(SRef, SRef.yaml_reper)

