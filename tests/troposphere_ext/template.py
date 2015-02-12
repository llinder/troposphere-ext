import unittest

import troposphere.ec2
import troposphere.s3
import troposphere_ext

from troposphere_ext.template import Template


class TestTemplate(unittest.TestCase):

    # -- test register_resource

    def test_register_resource_no_tags_support(self):
        template = troposphere_ext.template.template('Test')

        eip = troposphere.ec2.EIP('SomeEip',
            InstanceId = 'Test',
            Domain = 'Test')

        eip = template._register_resource(eip)[0]

        self.assertEquals(eip.title, 'TestSomeEip')
        self.assertFalse(hasattr(eip, 'Tags'))

    def test_register_resource_with_tags_Tag_support(self):
        template = troposphere_ext.template.template('Test')

        bucket = troposphere.s3.Bucket('SomeBucket',
            BucketName = 'test')

        bucket = template._register_resource(bucket)[0]

        self.assertEquals(bucket.title, 'TestSomeBucket')
        self.assertTrue(hasattr(bucket, 'Tags'))
        self.assertTrue(isinstance(bucket.Tags, troposphere.Tags))
        tag_dict = {tag['Key']: tag['Value'] for tag in bucket.Tags.tags}
        self.assertTrue('Name' in tag_dict)
        self.assertEquals(tag_dict['Name'], 'TestSomeBucket')

    def test_register_resource_with_Tags_support_and_existing_tags(self):
        template = troposphere_ext.template.template('Test')

        bucket = troposphere.s3.Bucket('SomeBucket',
            BucketName = 'test',
            Tags = troposphere.Tags(Test='test-tag'))

        bucket = template._register_resource(bucket)[0]

        self.assertEquals(bucket.title, 'TestSomeBucket')
        self.assertTrue(hasattr(bucket, 'Tags'))
        self.assertTrue(isinstance(bucket.Tags, troposphere.Tags))
        tag_dict = {tag['Key']: tag['Value'] for tag in bucket.Tags.tags}
        self.assertTrue('Name' in tag_dict)
        self.assertEquals(tag_dict['Name'], 'TestSomeBucket')
        self.assertTrue('Test' in tag_dict)
        self.assertEquals(tag_dict['Test'], 'test-tag')

    def test_register_resource_with_tags_list_support(self):
        template = troposphere_ext.template.template('Test')

        instance = troposphere.ec2.Instance('SomeInstance',
            ImageId = 'ami-test')

        instance = template._register_resource(instance)[0]

        self.assertEquals(instance.title, 'TestSomeInstance')
        self.assertTrue(hasattr(instance, 'Tags'))
        self.assertTrue(isinstance(instance.Tags, list))
        tag_dict = {tag.data['Key']: tag.data['Value'] for tag in instance.Tags}
        self.assertTrue('Name' in tag_dict)
        self.assertEquals(tag_dict['Name'], 'TestSomeInstance')

    def test_register_resource_with_tags_list_support_and_existing_tags(self):
        template = troposphere_ext.template.template('Test')

        instance = troposphere.ec2.Instance('SomeInstance',
            ImageId = 'ami-test',
            Tags = [troposphere.ec2.Tag('Test', 'test-tag')])

        instance = template._register_resource(instance)[0]

        self.assertEquals(instance.title, 'TestSomeInstance')
        self.assertTrue(hasattr(instance, 'Tags'))
        self.assertTrue(isinstance(instance.Tags, list))
        tag_dict = {tag.data['Key']: tag.data['Value'] for tag in instance.Tags}
        self.assertTrue('Name' in tag_dict)
        self.assertEquals(tag_dict['Name'], 'TestSomeInstance')
        self.assertEquals(tag_dict['Test'], 'test-tag')

    # -- test create_resource

    def test_create_resource_single(self):
        template = troposphere_ext.template.template('Test')

        self.assertTrue(isinstance(template, Template))

        resource = template._create_resource(troposphere.ec2.EIP, 'SomeEip',
            InstanceId = 'Test',
            Domain = 'Test')

        self.assertTrue(len(resource), 1)

        resource = resource[0]

        self.assertTrue(isinstance(resource, troposphere.ec2.EIP))
        self.assertEquals(resource.InstanceId, 'Test')
        self.assertEquals(resource.Domain, 'Test')

    def test_create_resource_instance(self):
        template = troposphere_ext.template.template('Test')

        self.assertTrue(isinstance(template, Template))

        resource = template._create_resource(troposphere.ec2.EIP, 
            troposphere.ec2.EIP('SomeEip',
                InstanceId = 'Test',
                Domain = 'Test'))

        self.assertTrue(len(resource), 1)

        resource = resource[0]

        self.assertTrue(isinstance(resource, troposphere.ec2.EIP))
        self.assertEquals(resource.InstanceId, 'Test')
        self.assertEquals(resource.Domain, 'Test')

    def test_create_resource_arg_list(self):
        template = troposphere_ext.template.template('Test')

        self.assertTrue(isinstance(template, Template))                      

        resource = template._create_resource(troposphere.ec2.EIP, 
            troposphere.ec2.EIP('SomeEip1',
                InstanceId = 'Test1',
                Domain = 'Test1'),
            troposphere.ec2.EIP('SomeEip2',
                InstanceId = 'Test2',
                Domain = 'Test2'))

        self.assertTrue(isinstance(resource, list))


    def test_create_resource_list(self):
        template = troposphere_ext.template.template('Test')

        self.assertTrue(isinstance(template, Template))                      

        resource = template._create_resource(troposphere.ec2.EIP, 
            [troposphere.ec2.EIP('SomeEip1',
                InstanceId = 'Test1',
                Domain = 'Test1'),
            troposphere.ec2.EIP('SomeEip2',
                InstanceId = 'Test2',
                Domain = 'Test2')])

        self.assertTrue(isinstance(resource, list))

   
        