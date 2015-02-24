#
#    Copyright (C) 2015 Lance Linder
#


import re
import os
import importlib
import logging
import difflib
import boto.cloudformation
import time
import json

from boto.exception import BotoServerError


class Tropext(object):

    def __init__(self, log, stack_name, namespace, region='us-west-2'):
        self._region = region
        self._stack_name = stack_name
        self._namespace = namespace
        self._conn = boto.cloudformation.connect_to_region(region)
        self._log = log

    def generate(self, template_name, template_args):
        """Creates a Cloud Formation JSON file from a Troposphere template"""
        try:
            self._log.debug("Loading template '{}'".format(template_name))

            # attempt to an existing template module by name
            template = importlib.import_module(template_name)

            # get matching namespaced stack name for parent
            # if the parent name was specified
            template_args['parent_stack'] = None \
                if 'parent_stack' not in template_args \
                else self.__get_fq_stack_name(template_args['parent_stack'])

            # add stack name to template args
            template_args['stack_name'] = self._stack_name

            # add namespace to template args
            template_args['namespace'] = self._namespace

            # create stack prefix. this is used for naming stack resource.
            template_args['stack_prefix'] = \
                '{}{}'.format(self._namespace.capitalize(),
                              self._stack_name.capitalize())

            # add region to the template args
            template_args['region'] = self._region

            self._log.debug("Generating template '{}' for stack '{}' "
                            "with prefix '{}' and template args '{}'"
                            .format(template_name, self._stack_name,
                                    self._namespace, template_args))

            # generate cloud formation JSON string from Troposphere DSL
            return template.create(**template_args).to_json()

        except ImportError as e:
            self._log.exception("Unable to load specified template '{}'"
                                .format(template_name))

        return None

    def diff(self, template_name, template_args=None):
        """Creates differences between the current
            and previous stack"""

        template_args = {} if template_args is None else template_args

        existing_stack = self.__get_existing_stack()
        if existing_stack is None:
            self._log.warn("Stack '{}' doesn't, nothing to diff."
                           .format(self.__get_fq_stack_name()))
        else:
            prev_template = existing_stack.get_template() \
                .get('GetTemplateResponse') \
                .get('GetTemplateResult') \
                .get('TemplateBody')

            current_template = self.generate(template_name, template_args)
            return [line for line in
                    difflib.unified_diff(prev_template.splitlines(),
                                         current_template.splitlines(),
                                         fromfile='original',
                                         tofile='current',
                                         lineterm='')]

    def create(self, creator, template_name, template_args=None,
               template_params=None):
        """Creates a stack and returns the stack ID or
            None if there was an error"""

        template_args = {} if template_args is None else template_args
        template_params = [] if template_params is None \
            else [(k, v) for k, v in template_params.iteritems()]

        fq_stack_name = self.__get_fq_stack_name()
        existing = self.__get_existing_stack()
        if existing is not None:
            self._log.warn("Stack '{}' already exists.".format(fq_stack_name))
            return None
        else:
            try:
                template_body = self.generate(template_name, template_args)
                self._log.debug('Creating stack {} from template {}, '
                                'body is:\n{}'.format(fq_stack_name,
                                                      template_name,
                                                      template_body))

                return self._conn.create_stack(fq_stack_name,
                                               template_body=template_body,
                                               parameters=template_params,
                                               capabilities=['CAPABILITY_IAM'],
                                               tags={'creator': creator})
            except Exception as e:
                self._log.exception("Error creating stack '{}' from template "
                                    "'{}', error was '{}'"
                                    .format(fq_stack_name,
                                            template_name,
                                            str(e)))

            return None

    def update(self, template_name, template_args=None,
               template_params=None):
        """Updates a stack and returns the stack ID or None
           if there was an error"""

        template_args = {} if template_args is None else template_args
        template_params = [] if template_params is None \
            else [(k, v) for k, v in template_params.iteritems()]

        fq_stack_name = self.__get_fq_stack_name()
        existing = self.__get_existing_stack()
        if existing is None:
            self._log.warn("Stack '{}' doesn't exist yet."
                           .format(fq_stack_name))
            return None
        else:
            try:
                template_body = self.generate(template_name, template_args)
                self._log.debug('Updating stack {} from template {}, '
                                'body is:\n{}'.format(fq_stack_name,
                                                      template_name,
                                                      template_body))
                return self._conn.update_stack(fq_stack_name,
                                               template_body=template_body,
                                               parameters=template_params,
                                               capabilities=['CAPABILITY_IAM'])
            except BotoServerError as be:
                error = json.loads(be.body)['Error']
                code = error['Code']
                message = error['Message']
                self._log.warn('{code}: {message}'.format(**locals()))
            except Exception as e:
                self._log.exception("Error updating stack '{}' from template "
                                    "'{}', error was '{}'"
                                    .format(fq_stack_name, template_name, 
                                            str(e)))

            return None

    def get_events(self):
        """Get the events in batches and return in
           chronological order"""
        next = None
        event_list = []
        fq_stack_name = self.__get_fq_stack_name()
        while 1:
            events = self._conn.describe_stack_events(fq_stack_name, next)
            event_list.append(events)
            if events.next_token is None:
                break
            next = events.next_token
            time.sleep(1)

        return reversed(sum(event_list, []))

    def watch(self, fetch):
        """Watches a Cloud Formation stack for events and
           returns a Generator for consuming the events."""
        seen = set()
        if fetch:
            # fetch previous events
            initial_events = self.get_events()
            for e in initial_events:
                yield e
                seen.add(e.event_id)

        # start looping and dump the new events
        complete = False
        while 1:
            events = self.get_events()
            for e in events:
                if e.event_id not in seen:
                    yield e
                    seen.add(e.event_id)

            # exit loop on cloud formation complete or failed event
            if (e.resource_type == 'AWS::CloudFormation::Stack'
                and ('COMPLETE' in e.resource_status 
                    or 'FAILED' in e.resource_status)):
                break

            time.sleep(5)

    def __get_existing_stack(self):
        fq_stack_name = self.__get_fq_stack_name()
        try:
            stack = [stack for stack in
                     self._conn.describe_stacks()
                     if stack.stack_name == fq_stack_name]
            return stack[0] if len(stack) > 0 else None
        except:
            self._log.exception("Unable to get existing stack '{}'"
                                .format(fq_stack_name))

        return None

    def __get_template_path(self):
        return os.path.join(self._template_dir,
                            '{}.json'.format(self.__get_fq_stack_name()))

    def __get_fq_stack_name(self, stack_name=None, namespace=None):
        if namespace is None:
            namespace = self._namespace
        if stack_name is None:
            stack_name = self._stack_name

        return '{}-{}'.format(namespace, stack_name)


def camel_to_snake(value):
    split = re.split(r'([A-Z][^A-Z]*)', value)
    return '_'.join(filter(None, split)).lower()
