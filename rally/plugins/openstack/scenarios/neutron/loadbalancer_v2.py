#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import random

from rally import consts
from rally.plugins.openstack import scenario
from rally.plugins.openstack.scenarios.neutron import utils
from rally.task import atomic
from rally.task import validation


class NeutronLoadbalancerV2(utils.NeutronScenario):
    """Benchmark scenarios for Neutron Loadbalancer v2."""

    @validation.restricted_parameters("subnet_id",
                                      subdict="lb_create_args")
    @validation.required_neutron_extensions("lbaasv2")
    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @validation.required_contexts("network")
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_delete_loadbalancer(self, lb_create_args=None):
        """Create a pool(v2) and then list pools(v2).

        Measure the "neutron lb-pool-list" command performance.
        The scenario creates a pool for every subnet and then lists pools.

        :param pool_create_args: dict, POST /lb/pools request options
        """
        lb_create_args = lb_create_args or {}
        networks = self.context.get("tenant", {}).get("networks", [])
        lbs = self._create_v2_loadbalancer(networks, **lb_create_args)
        for lb in lbs:
            self._delete_v2_loadbalancer(lb['loadbalancer']['id'])
        #self._list_v2_loadbalancer()


    @validation.restricted_parameters(["lb_id", "subnet_id"],
                                      subdict="listener_create_args")
    @validation.required_neutron_extensions("lbaasv2")
    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @validation.required_contexts("network")
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_delete_listener(self, lb_create_args=None,
                             listener_per_lb=1,
                             listener_create_args=None):
        """Create a vip(v2) and then list vips(v2).

        Measure the "neutron lb-vip-create" and "neutron lb-vip-list" command
        performance. The scenario creates a vip for every pool created and
        then lists vips.

        :param vip_create_args: dict, POST /lb/vips request options
        :param pool_create_args: dict, POST /lb/pools request options
        """
        listener_create_args = listener_create_args or {}
        lb_create_args = lb_create_args or {}
        networks = self.context.get("tenant", {}).get("networks", [])
        lbs = self._create_v2_loadbalancer(networks, **lb_create_args)
        with atomic.ActionTimer(self, "neutron.create_%s_loadbalancers" % len(lbs)):
            for lb in lbs:
                for listener in range(listener_per_lb):
                    lb['loadbalancer']['listeners'].append(self._create_v2_listener(lb, **listener_create_args))
        for lb in lbs:
            for listener in lb['loadbalancer']['listeners']:
                self._delete_v2_listener(listener['listener']['id'])
            self._delete_v2_loadbalancer(lb['loadbalancer']['id'])
        #self._list_v2_vips()

    @validation.restricted_parameters("listener_id",
                                      subdict="pool_create_args")
    @validation.required_neutron_extensions("lbaasv2")
    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @validation.required_contexts("network")
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_delete_v2pools(self, lb_create_args=None,
                              listener_per_lb=1,
                              listener_create_args=None,
                              pool_per_listener=1, pool_create_args=None):
        """Create a pool(v2) and then list pools(v2).

        Measure the "neutron lb-pool-list" command performance.
        The scenario creates a pool for every subnet and then lists pools.

        :param pool_create_args: dict, POST /lb/pools request options
        """
        lb_create_args = lb_create_args or {}
        listener_create_args = listener_create_args or {}
        pool_create_args = pool_create_args or {}
        networks = self.context.get("tenant", {}).get("networks", [])
        lbs = self._create_v2_loadbalancer(networks, **lb_create_args)
        with atomic.ActionTimer(self, "neutron.create_%s_loadbalancers" % len(lbs)):
            for lb in lbs:
                for listener in range(listener_per_lb):
                    lb['loadbalancer']['listeners'].append(self._create_v2_listener(lb, **listener_create_args))
                    lb['loadbalancer']['listeners'][listener]['listener']['pools'] = []
                    for pool in range(pool_per_listener):
                        lb['loadbalancer']['listeners'][listener]['listener']['pools'].append(self._create_v2_pool(lb['loadbalancer']['listeners'][listener], **pool_create_args))
        with atomic.ActionTimer(self, "neutron.delete_%s_loadbalancers" % len(lbs)):
            for lb in lbs:
                for listener in lb['loadbalancer']['listeners']:
                    for pool in listener['listener']['pools']:
                        self._delete_v2_pool(pool['pool']['id'])
                    self._delete_v2_listener(listener['listener']['id'])
                self._delete_v2_loadbalancer(lb['loadbalancer']['id'])
        #self._list_v2_pools()

    @validation.restricted_parameters("pool_id",
                                      subdict="mem_create_args")
    @validation.required_neutron_extensions("lbaasv2")
    @validation.required_services(consts.Service.NEUTRON)
    @validation.required_openstack(users=True)
    @validation.required_contexts("network")
    @scenario.configure(context={"cleanup": ["neutron"]})
    def create_and_delete_members(self, lb_create_args=None,
                                port_create_args=None,
                                listener_per_lb=1,
                                listener_create_args=None,
                                pool_create_args=None,
                                member_per_pool=1, mem_create_args=None):
        """Create a pool(v2) and then list pools(v2).

        Measure the "neutron lb-pool-list" command performance.
        The scenario creates a pool for every subnet and then lists pools.

        :param pool_create_args: dict, POST /lb/pools request options
        """
        lb_create_args = lb_create_args or {}
        listener_create_args = listener_create_args or {}
        pool_create_args = pool_create_args or {}
        mem_create_args = mem_create_args or {}
        networks = self.context.get("tenant", {}).get("networks", [])
        pool_per_listener=1
        ports = []
        for network in networks:
            ports.append(self._create_port({'network': network}, port_create_args or {}))
        lbs = self._create_v2_loadbalancer(networks, **lb_create_args)
        with atomic.ActionTimer(self, "neutron.create_%s_loadbalancers" % len(lbs)):
            for lb_idx, lb in enumerate(lbs):
                for listener in range(listener_per_lb):
                    listener_create_args['protocol_port']=listener+10
                    lb['loadbalancer']['listeners'].append(self._create_v2_listener(lb, **listener_create_args))
                    lb['loadbalancer']['listeners'][listener]['listener']['pools'] = []
                    for pool in range(pool_per_listener):
                        lb['loadbalancer']['listeners'][listener]['listener']['pools'].append(self._create_v2_pool(lb['loadbalancer']['listeners'][listener], **pool_create_args))
                        for mem in range(member_per_pool):
                            mem_create_args['address']=ports[lb_idx]['port']['fixed_ips'][0]['ip_address']
                            mem_create_args['protocol_port']=listener+10
                            lb['loadbalancer']['listeners'][listener]['listener']['pools'][pool]['pool']['members'].append(self._create_v2_pool_member(lb['loadbalancer']['vip_subnet_id'], 
                                lb['loadbalancer']['listeners'][listener]['listener']['pools'][pool], **mem_create_args))
        import pdb;pdb.set_trace()
        with atomic.ActionTimer(self, "neutron.delete_%s_loadbalancers" % len(lbs)):
            for lb in lbs:
                for listener in lb['loadbalancer']['listeners']:
                    for pool in listener['listener']['pools']:
                        for mem in pool['pool']['members']:
                            self._delete_v2_pool_member(mem['member']['id'], pool['pool']['id'])
                        self._delete_v2_pool(pool['pool']['id'])
                    self._delete_v2_listener(listener['listener']['id'])
                self._delete_v2_loadbalancer(lb['loadbalancer']['id'])
        #self._list_v2_pools()

