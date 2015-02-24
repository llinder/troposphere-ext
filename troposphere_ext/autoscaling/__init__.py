#
#    Copyright (C) 2015 Lance Linder
#

import troposphere
import troposphere.autoscaling

from troposphere import Ref
from troposphere.autoscaling import AutoScalingGroup as TropAutoScalingGroup


class AutoScalingGroup(TropAutoScalingGroup):

    def __init__(self, title, template=None, **kwargs):
        helper_keys = ['LaunchConfiguration', 'LoadBalancers']
        clean_kwargs = {k: v for k, v in kwargs.iteritems()
                        if k not in helper_keys}

        self._launch_config = kwargs.get('LaunchConfiguration', None)
        self._load_balancers = kwargs.get('LoadBalancers', None)

        super(AutoScalingGroup, self).__init__(title, template, **clean_kwargs)

    @property
    def launch_config(self):
        return self._launch_config

    def set_template(self, template):
        self.template = template

        if isinstance(self._load_balancers, list):
            lb_names = [Ref(template._register_resource(lb)[0]) for lb in self._load_balancers]
            self.__setattr__('LoadBalancerNames', lb_names)

        if self._launch_config is not None:
            template._register_resource(self._launch_config)
            self.__setattr__('LaunchConfigurationName', 
                             Ref(self._launch_config))
