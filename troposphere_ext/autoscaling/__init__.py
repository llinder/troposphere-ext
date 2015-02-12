# vi: set ts=4 expandtab:
#
#    Copyright (C) 2015 Lance Linder
#

import troposphere
import troposphere.autoscaling


class AutoScalingGroup(troposphere.autoscaling.AutoScalingGroup):

    def __init__(self, title, template=None, **kwargs):
        helper_keys = ['LaunchConfiguration']
        clean_kwargs = { k:v for k, v in kwargs.iteritems() if not k in helper_keys }

        self._launch_config = kwargs.get('LaunchConfiguration', None)

        if template is not None:
            if self.launch_config is not None:
                launch_config = template._register_resource(self.launch_config)
                clean_kwargs['LaunchConfigurationName'] = troposphere.Ref(launch_config[0])

        super(AutoScalingGroup, self).__init__(title, template, **clean_kwargs)

    @property
    def launch_config(self):
        return self._launch_config