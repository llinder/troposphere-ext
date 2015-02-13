#
#    Copyright (C) 2015 Lance Linder
#

import troposphere
import troposphere.autoscaling

from troposphere import Ref
from troposphere.autoscaling import AutoScalingGroup as TropAutoScalingGroup


class AutoScalingGroup(TropAutoScalingGroup):

    def __init__(self, title, template=None, **kwargs):
        helper_keys = ['LaunchConfiguration']
        clean_kwargs = {k: v for k, v in kwargs.iteritems()
                        if k not in helper_keys}

        self._launch_config = kwargs.get('LaunchConfiguration', None)

        if template is not None:
            if self.launch_config is not None:
                launch_config = \
                    template._register_resource(self.launch_config)
                clean_kwargs['LaunchConfigurationName'] = Ref(launch_config[0])

        super(AutoScalingGroup, self).__init__(title, template, **clean_kwargs)

    @property
    def launch_config(self):
        return self._launch_config
