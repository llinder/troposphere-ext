#
#    Copyright (C) 2015 Lance Linder
#

import unittest


from troposphere import Tags
from troposphere.s3 import Bucket
from troposphere.ec2 import Tag, Instance, EIP

from troposphere_ext import Template, template


class TestTemplate(unittest.TestCase):

    # -- test register_resource

    def test_register_resource_no_tags_support(self):
        tpl = template('Test')

        eip = EIP('SomeEip',
                  InstanceId='Test',
                  Domain='Test')

        eip = tpl._register_resource(eip)[0]

        self.assertEquals(eip.title, 'TestSomeEip')
        self.assertFalse(hasattr(eip, 'Tags'))

    def test_register_resource_with_tags_Tag_support(self):
        tpl = template('Test')

        bucket = Bucket('SomeBucket',
                        BucketName='test')

        bucket = tpl._register_resource(bucket)[0]

        self.assertEquals(bucket.title, 'TestSomeBucket')
        self.assertTrue(hasattr(bucket, 'Tags'))
        self.assertTrue(isinstance(bucket.Tags, Tags))
        tag_dict = {tag['Key']: tag['Value'] for tag in bucket.Tags.tags}
        self.assertTrue('Name' in tag_dict)
        self.assertEquals(tag_dict['Name'], 'test_some_bucket')

    def test_register_resource_with_Tags_support_and_existing_tags(self):
        tpl = template('Test')

        bucket = Bucket('SomeBucket',
                        BucketName='test',
                        Tags=Tags(Test='test-tag'))

        bucket = tpl._register_resource(bucket)[0]

        self.assertEquals(bucket.title, 'TestSomeBucket')
        self.assertTrue(hasattr(bucket, 'Tags'))
        self.assertTrue(isinstance(bucket.Tags, Tags))
        tag_dict = {tag['Key']: tag['Value'] for tag in bucket.Tags.tags}
        self.assertTrue('Name' in tag_dict)
        self.assertEquals(tag_dict['Name'], 'test_some_bucket')
        self.assertTrue('Test' in tag_dict)
        self.assertEquals(tag_dict['Test'], 'test-tag')

    def test_register_resource_with_tags_list_support(self):
        tpl = template('Test')

        instance = Instance('SomeInstance',
                            ImageId='ami-test')

        instance = tpl._register_resource(instance)[0]

        self.assertEquals(instance.title, 'TestSomeInstance')
        self.assertTrue(hasattr(instance, 'Tags'))
        self.assertTrue(isinstance(instance.Tags, list))
        tag_dict = {tag.data['Key']: tag.data['Value']
                    for tag in instance.Tags}
        self.assertTrue('Name' in tag_dict)
        self.assertEquals(tag_dict['Name'], 'test_some_instance')

    def test_register_resource_with_tags_list_support_and_existing_tags(self):
        tpl = template('Test')

        instance = Instance('SomeInstance',
                            ImageId='ami-test',
                            Tags=[Tag('Test', 'test-tag')])

        instance = tpl._register_resource(instance)[0]

        self.assertEquals(instance.title, 'TestSomeInstance')
        self.assertTrue(hasattr(instance, 'Tags'))
        self.assertTrue(isinstance(instance.Tags, list))
        tag_dict = {tag.data['Key']: tag.data['Value']
                    for tag in instance.Tags}
        self.assertTrue('Name' in tag_dict)
        self.assertEquals(tag_dict['Name'], 'test_some_instance')
        self.assertEquals(tag_dict['Test'], 'test-tag')

    # -- test create_resource

    def test_create_resource_single(self):
        tpl = template('Test')

        self.assertTrue(isinstance(tpl, Template))

        resource = tpl._create_resource(EIP, 'SomeEip',
                                        InstanceId='Test',
                                        Domain='Test')

        self.assertTrue(len(resource), 1)

        resource = resource[0]

        self.assertTrue(isinstance(resource, EIP))
        self.assertEquals(resource.InstanceId, 'Test')
        self.assertEquals(resource.Domain, 'Test')

    def test_create_resource_instance(self):
        tpl = template('Test')

        self.assertTrue(isinstance(tpl, Template))

        resource = tpl._create_resource(EIP,
                                        EIP('SomeEip',
                                            InstanceId='Test',
                                            Domain='Test'))

        self.assertTrue(len(resource), 1)

        resource = resource[0]

        self.assertTrue(isinstance(resource, EIP))
        self.assertEquals(resource.InstanceId, 'Test')
        self.assertEquals(resource.Domain, 'Test')

    def test_create_resource_arg_list(self):
        tpl = template('Test')

        self.assertTrue(isinstance(tpl, Template))

        resource = tpl._create_resource(EIP,
                                        EIP('SomeEip1',
                                            InstanceId='Test1',
                                            Domain='Test1'),
                                        EIP('SomeEip2',
                                            InstanceId='Test2',
                                            Domain='Test2'))

        self.assertTrue(isinstance(resource, list))

    def test_create_resource_list(self):
        tpl = template('Test')

        self.assertTrue(isinstance(tpl, Template))

        resource = tpl._create_resource(EIP, [
                                                EIP('SomeEip1',
                                                    InstanceId='Test1',
                                                    Domain='Test1'),
                                                EIP('SomeEip2',
                                                    InstanceId='Test2',
                                                    Domain='Test2')])

        self.assertTrue(isinstance(resource, list))
