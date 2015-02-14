#!/usr/bin/env python
#
#    Copyright (C) 2015 Lance Linder
#


import sys
import argparse
import logging
import os
import yaml

from troposphere_ext.utils import Tropext

log = logging.getLogger('tropext')
log.addHandler(logging.StreamHandler())


def generate(args):
    log.info('Starting template generate command.')

    try:
        trop = Tropext(log, args.stack, args.namespace, args.region)
        print trop.generate(args.template, args.template_args)
        return 0
    except:
        log.exception('Unexpected error while generating "{}" template'
                      .format(args.template))
        return 1


def create(args):
    log.info('Starting stack create command.')
    try:
        tropext = Tropext(log, args.stack, args.namespace, args.region)
        stack_id = tropext.create(args.creator, args.template,
                                  args.template_args, args.template_params)

        if stack_id is not None:
            log.info('Stack creation started with id "{}" for "{}"'
                     .format(stack_id, args.template))

            if args.watch:
                __watch(args.no_color, args.stack,
                        args.namespace, args.region, False)

            return 0
        else:
            log.warn('Stack creation failed.')
            return 1

    except Exception as e:
        log.exception('Stack creation failed for template "{}" with an '
                      'unexpected error: "{}"'.format(args.template, str(e)))
        return 1


def update(args):
    log.info('Starting stack update command.')
    try:
        tropext = Tropext(log, args.stack, args.namespace, args.region)
        stack_id = tropext.update(args.template, args.template_args,
                                  args.template_params)

        if stack_id is not None:
            log.info('Stack update started with id "{}" for "{}"'
                     .format(stack_id, args.template))

            if args.watch:
                __watch(args.no_color, args.stack, args.namespace,
                        args.region, False)

            return 0
        else:
            log.warn('Stack update failed.')
            return 1

    except Exception as e:
        log.exception('Stack update failed for template "{}" with an '
                      'unexpected error: "{}"'.format(args.template, str(e)))
        return 1


def delete(args):
    log.info('Starting stack delete command.')
    return 0


def watch(args):
    log.info('Starting stack event watch command.')

    result = __watch(args.no_color, args.stack, args.namespace, args.region)
    return 0 if result else 1


def diff(args):
    log.info('Starting stack diff command.')
    try:
        tropext = Tropext(log, args.stack, args.namespace, args.region)
        diff_result = tropext.diff(args.template, args.template_args)
        if len(diff_result) is 0:
            log.warn('Current template does not differ from '
                     'previous stack template.')
        else:
            print '\n'.join(diff_result)

        return 0
    except:
        log.exception('Unexpected error while generating "{}" template'
                      .format(args.template))
        return 1


def cost(args):
    log.info('Starting calculate stack costs command.')

    return 0


def __watch(no_color, stack_name, namespace, region, fetch=True):
    try:
        color_map = {
            'CREATE_IN_PROGRESS': '\033[93m',
            'CREATE_FAILED': '\033[91m',
            'CREATE_COMPLETE': '\033[92m',
            'UPDATE_IN_PROGRESS': '\033[93m',
            'UPDATE_FAILED': '\033[91m',
            'UPDATE_COMPLETE': '\033[92m',
            'UPDATE_ROLLBACK_IN_PROGRESS': '\033[93m',
            'UPDATE_ROLLBACK_FAILED': '\033[91m',
            'UPDATE_ROLLBACK_COMPLETE': '\033[92m',
            'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS': '\033[93m',
            'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS': '\033[93m',
            'DELETE_IN_PROGRESS': '\033[93m',
            'DELETE_FAILED': '\033[91m',
            'DELETE_COMPLETE': '\033[92m',
            'ROLLBACK_IN_PROGRESS': '\033[93m',
            'ROLLBACK_FAILED': '\033[91m',
            'ROLLBACK_COMPLETE': '\033[92m'
        }

        tropext = Tropext(log, stack_name, namespace, region)
        for e in tropext.watch(fetch):
            if no_color:
                if 'FAILED' in e.resource_status:
                    print ('{} {} {} {}'
                           .format(e.resource_status, e.resource_type,
                                   e.logical_resource_id,
                                   e.resource_status_reason))
                else:
                    print ('{} {} {}'
                           .format(e.resource_status, e.resource_type,
                                   e.logical_resource_id))
            else:
                if 'FAILED' in e.resource_status:
                    print ('{}{} {} {} {}{}'
                           .format(color_map[e.resource_status],
                                   e.resource_status, e.resource_type,
                                   e.logical_resource_id,
                                   e.resource_status_reason, '\033[0m'))
                else:
                    print ('{}{} {} {}{}'
                           .format(color_map[e.resource_status],
                                   e.resource_status, e.resource_type,
                                   e.logical_resource_id, '\033[0m'))

    except Exception as e:
        log.exception('Watching stack events failed with '
                      'unexpected error: "{}"'.format(str(e)))
        return False

    return True


def main():
    def is_valid_dir(parser, arg):
        if not os.path.isdir(arg):
            parser.error("The directory '{0}' does not exist.".format(arg))
        else:
            return arg

    p = argparse.ArgumentParser()

    p.add_argument('-d', '--debug', action='store_const', dest='log_level',
                   const=logging.DEBUG, default=logging.WARNING,
                   help='Print debug logs')
    p.add_argument('-v', '--verbose', action='store_const', dest='log_level',
                   const=logging.INFO, help='Print info logs')

    sp = p.add_subparsers()

    # generate
    pg = sp.add_parser('generate', help='Generate Cloud Formation '
                                        'templates from Troposphere DSL.')
    pg.set_defaults(func=generate)
    pg.add_argument('template', help='Troposphere DSL to execute')
    pg.add_argument('--access-key-id', help='AWS Access Key ID.')
    pg.add_argument('--secret-key', help='AWS Secret Access Key.')
    pg.add_argument('--stack', '-s', required=True, metavar='STACK_NAME',
                    help='AWS Cloud Formation stack name.')
    pg.add_argument('--namespace', '-n', required=True,
                    help='AWS Cloud Formation stack name namespace prefix.')
    pg.add_argument('--region', '-r', required=True,
                    help='AWS Cloud Formation region to creat the stack in.')
    pg.add_argument('--template-args', '-a', type=yaml.load, default=dict(),
                    help='AWS Cloud Formation stack factory arguments.')
    # pg.add_argument('--output', '-o', default='/tmp',
    #                 type=lambda x: is_valid_dir(parser, x),
    #                 metavar='DIRECTORY',
    #                 help='Cloud Formation JSON output location.')

    # create
    pg = sp.add_parser('create',
                       help='Creates a Cloud Formation stack from '
                            'Troposphere DSL.')
    pg.set_defaults(func=create)
    pg.add_argument('template', help='Troposphere DSL to execute')
    pg.add_argument('--access-key-id', help='AWS Access Key ID.')
    pg.add_argument('--secret-key', help='AWS Secret Access Key.')
    pg.add_argument('--stack', '-s', required=True, metavar='STACK_NAME',
                    help='AWS Cloud Formation stack name.')
    pg.add_argument('--namespace', '-n', required=True,
                    help='AWS Cloud Formation stack name namespace prefix.')
    pg.add_argument('--creator', '-c',
                    help='The creator (username) used for tagging the '
                         'newly created stack.')
    pg.add_argument('--region', '-r', required=True,
                    help='AWS Cloud Formation region to creat the stack in.')
    pg.add_argument('--template-args', '-a', type=yaml.load, default=dict(),
                    help='AWS Cloud Formation stack factory arguments.')
    pg.add_argument('--template-params', '-p', type=yaml.load, default=dict(),
                    help='AWS Cloud Formation stack template parameters.')
    pg.add_argument('--watch', '-w', action='store_true',
                    help='AWS Cloud Formation stack parameters.')
    pg.add_argument('--no-color', dest='no_color', action='store_true',
                    help='AWS Cloud Formation stack name namespace prefix.')
    # pg.add_argument('--output', '-o', default='/tmp',
    #    type=lambda x: is_valid_dir(parser, x), metavar='DIRECTORY',
    #    help='Cloud Formation JSON output location.')

    # update
    pg = sp.add_parser('update',
                       help='Updates a Cloud Formation stack from '
                            'Troposphere DSL.')
    pg.set_defaults(func=update)
    pg.add_argument('template', help='Troposphere DSL to execute')
    pg.add_argument('--access-key-id', help='AWS Access Key ID.')
    pg.add_argument('--secret-key', help='AWS Secret Access Key.')
    pg.add_argument('--stack', '-s', required=True, metavar='STACK_NAME',
                    help='AWS Cloud Formation stack name.')
    pg.add_argument('--namespace', '-n', required=True,
                    help='AWS Cloud Formation stack name namespace prefix.')
    pg.add_argument('--region', '-r', required=True,
                    help='AWS Cloud Formation region to creat the stack in.')
    pg.add_argument('--template-args', '-a', type=yaml.load, default=dict(),
                    help='AWS Cloud Formation stack factory arguments.')
    pg.add_argument('--template-params', '-p', type=yaml.load, default=dict(),
                    help='AWS Cloud Formation stack template parameters.')
    pg.add_argument('--watch', '-w', action='store_true',
                    help='AWS Cloud Formation stack parameters.')
    pg.add_argument('--no-color', dest='no_color', action='store_true',
                    help='AWS Cloud Formation stack name namespace prefix.')

    # delete

    # watch
    pg = sp.add_parser('watch', help='Watches Cloud Formation events.')
    pg.set_defaults(func=watch)
    pg.add_argument('--access-key-id', help='AWS Access Key ID.')
    pg.add_argument('--secret-key', help='AWS Secret Access Key.')
    pg.add_argument('--stack', '-s', required=True, metavar='STACK_NAME',
                    help='AWS Cloud Formation stack name.')
    pg.add_argument('--namespace', '-n', required=True,
                    help='AWS Cloud Formation stack name namespace prefix.')
    pg.add_argument('--region', '-r', default='us-west-2',
                    help='AWS Cloud Formation stack name namespace prefix.')
    pg.add_argument('--no-color', dest='no_color', action='store_true',
                    help='AWS Cloud Formation stack name namespace prefix.')

    # diff
    pg = sp.add_parser('diff',
                       help='Diffs the Cloud Formation templates from '
                            'Troposphere DSL against an existing stack.')
    pg.set_defaults(func=diff)
    pg.add_argument('template', help='Troposphere DSL to execute')
    pg.add_argument('--access-key-id', help='AWS Access Key ID.')
    pg.add_argument('--secret-key', help='AWSi Secret Access Key.')
    pg.add_argument('--stack', '-s', required=True, metavar='STACK_NAME',
                    help='AWS Cloud Formation stack name.')
    pg.add_argument('--namespace', '-n', required=True,
                    help='AWS Cloud Formation stack name namespace prefix.')
    pg.add_argument('--region', '-r', default='us-west-2',
                    help='AWS Cloud Formation stack name namespace prefix.')
    pg.add_argument('--template-args', '-a', type=yaml.load, default=dict(),
                    help='AWS Cloud Formation stack factory arguments.')

    # cost

    args = p.parse_args()

    # log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]

    log.setLevel(args.log_level)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
