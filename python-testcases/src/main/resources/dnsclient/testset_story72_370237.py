#!/usr/bin/env python

'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Sept 2014, Sept 2019
@author:    Maria, Karen Flannery
@summary:   Integration tests to model nameservers,
            so that a user can configure resolv.conf
            for name resolution on my servers
            Agile: STORY LITPCDS-72
            Added to existing test case to cover
            create/update/remove nameserver with
            IPv6 address containing CIDR prefix
            Agile: TORF-370237
'''

from litp_cli_utils import CLIUtils
from xml_utils import XMLUtils
from redhat_cmd_utils import RHCmdUtils
from litp_generic_test import GenericTest, attr
import test_constants
import os


class Story72(GenericTest):

    '''
    As a LITP User I want to model nameservers, so that I can
    configure resolv.conf for name resolution on my servers
    As a LITP engineer, I need to update a number of properties so
    that they support dual stack with a CIDR prefix
    '''

    def setUp(self):
        """
        Description:
            Runs before every single test
        Actions:
            1. Call the super class setup method
            2. Set up variables used in the tests
        Results:
            The super class prints out diagnostics and variables
            common to all tests are available.
        """
        # 1. Call super class setup
        super(Story72, self).setUp()
        self.test_ms = self.get_management_node_filename()
        self.test_nodes = self.get_managed_node_filenames()
        self.test_node1 = None
        self.test_node2 = None
        self.cli = CLIUtils()
        self.xml = XMLUtils()
        self.redhatutils = RHCmdUtils()

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Actions:
            1. Perform Test Cleanup
        Results:
            Items used in the test are cleaned up and the
            super class prints out end test diagnostics
        """
        super(Story72, self).tearDown()

    def _get_managed_nodes(self):
        """
        Description:
            Function that gets the managed nodes
        Actions:
            1. Find the nodes path
            2. Ensure there are at least 2 nodes defined
            3. Set node1 path in model
            4. Set node2 path in model
            5. Get node1
            6. Get node2
        Result:
             node1 and node2
        """
        # 1. Find the nodes path
        nodes_path = self.find(self.test_ms, "/deployments", "node", True)

        # 2. Enusre there are at least 2 nodes defined
        self.assertTrue(
            len(nodes_path) > 1,
            "The LITP Tree has less than 2 nodes defined")

        # 3. Set node1 path in model
        node1_path = nodes_path[0]

        # 4. Set node2 path in model
        node2_path = nodes_path[1]

        # 5. Get node1
        self.test_node1 = self.get_node_filename_from_url(
            self.test_ms, node1_path)

        # 6. Get node2
        self.test_node2 = self.get_node_filename_from_url(
            self.test_ms, node2_path)

    def _create_dns_client(self, config_path, dns_name, **kwargs):
        """
        Description:
            Creates dns-client
        Args:
            config_path(str): config_path
            dns_name(str): dns client name
        Actions:
            1. Create dns-client collection
        Results:
            dns-client collection is successfully created
        """
        # Create a dns-client
        dns_url = config_path + "/{0}".format(dns_name)
        pairs = ["=".join([name, value]) for name, value in kwargs.iteritems()]
        props = " ".join(pairs)
        self.execute_cli_create_cmd(
            self.test_ms, dns_url, "dns-client", props)
        return dns_url

    def _update_dns_client(self, config_path, props):
        """
        Description:
            Add/update the search property in the dns-client
        Args:
            config_path (str): config path
            dns_name (str): dns client name
            props (str): properties to be updated
        Actions:
            1. Add/update search property
        Results:
            Search property is added/updated
        """
        self.execute_cli_update_cmd(
            self.test_ms, config_path, props)

    def _update_dns_client_remove_search_prop(self, config_path):
        """
        Description:
            Update dns-client to remove search property
        Args:
            config_path (str): config path
        Actions:
            1. Update dns-client to remove search property
        Results:
            Search property has been removed
        """
        self.execute_cli_update_cmd(
            self.test_ms, config_path, "search", action_del=True)

    def _create_nameserver(self, dns_path, nameserver_name, props):
        """
        Description:
            Create a nameserver item-type
        Args:
            dns_path (str): dns path
            nameserver_name (str): nameserver name
            props (str): properties to be created

        Actions:
            1. Create nameserver item-type

        Results:
            system-param item-type is successfully created
        """

        nameserver_path = dns_path + "/nameservers/{0}".format(nameserver_name)
        self.execute_cli_create_cmd(
            self.test_ms, nameserver_path, "nameserver", props)
        return nameserver_path

    def _update_nameserver_props(self, nameserver_path, props):
        """
        Description:
            Updates a nameserver item-type
        Args:
            nameserver_path (str): nameserver path
            props (str): properties to be updated
        Actions:
            1. Update the nameserver item-type
        Results:
            nameserver item-type is successfully updated
        """
        self.execute_cli_update_cmd(
            self.test_ms, nameserver_path, props)

    def _remove_nameserver(self, nameserver_path):
        """
        Description:
            removes a nameserver item-type
        Args:
            nameserver_path (str): path to nameserver
        Actions:
            1. Remove nameserver item-type
        Results:
             nameserver item-type is successfully removed
        """
        self.execute_cli_remove_cmd(
            self.test_ms, nameserver_path)

    def _find_line_in_resolv_conf(self, node, search_val, positive=True):
        """
        Description:
            Function to find a specific value
            in the resolv.conf file.
        Args:
            node (str) : The node to find the file on.
            search_val (str): value to search for
            positive (bool): If set to true,
                             expects to find search value in file,
                             else does not expect to find value in file
        Actions:
            1. Greps for the value in the file
        Results:
             if positive=True
             Successfully finds search value in resolv.conf
        """
        cmd = self.redhatutils.get_grep_file_cmd(
            test_constants.RESOLV_CFG_FILE, search_val)
        std_out, std_err, rc = self.run_command(node, cmd, su_root=True)
        if positive is True:
            self.assertEquals([], std_err)
            self.assertNotEqual([], std_out)
            self.assertEquals(0, rc)
        else:
            self.assertEquals([], std_err)
            self.assertEquals([], std_out)
            self.assertEquals(1, rc)

    def _assert_cli_error_message(self, err_list, result):
        """
        Description:
            Check whether 'ensure_not_found' property is enabled

        Args:
            err_list (list): list of error messages and paths
            result (dict):  dictionary of error data
        """

        if result.get('ensure_not_found') == True:
            self._assert_cli_error_message_not_found(err_list, result)
        else:
            self._assert_cli_error_message_found(err_list, result)

    def _assert_cli_error_message_found(self, err_list, result):
        """
        Description:
            Check that give path and message pair is found in error messages
        Args:
            err_list (list): list of error messages and paths
            result (dict):  dictionary of error data
        """

        self.assertTrue('msg' in result,
            'Required expected error message missing in "result"')

        found = False
        if result.get('path') != None:
            path_assert_msg = '\n{0}'.format(result['path'])
            for i in xrange(len(err_list) - 1):
                if err_list[i] == result.get('path') and \
                    err_list[i + 1] == result['msg']:
                    found = True
                    break
        else:
            path_assert_msg = ''
            for line in err_list:
                if line == result['msg']:
                    found = True
                    break

        assert_msg = (
        '\nExpected error message:{0}\n{1}\nNOT found in:\n{2}'
        .format(path_assert_msg, result['msg'], '\n'.join(err_list)))
        self.assertTrue(found, assert_msg)

    def _assert_cli_error_message_not_found(self, err_list, result):

        """
        Description:
            Check that give path and message pair is not found in
            error messages
        Args:
            err_list (list): list of error messages and paths
            result (dict):  dictionary of error data
        """

        self.assertTrue('msg' in result,
            'Required expected error message missing in "result"')

        if result.get('path') != None:
            path_assert_msg = '\n{0}'.format(result['path'])
            for i in xrange(len(err_list) - 1):
                if err_list[i] == result.get('path') and \
                    err_list[i + 1] == result['msg']:
                    found = True
                    break

        else:
            path_assert_msg = ''
            for line in err_list:
                if line == result['msg']:
                    found = True
                    break

        assert_msg = (
        '\nExtra error message:{0}\n{1}\nfound in:\n{2}'
        .format(path_assert_msg, result['msg'], '\n'.join(err_list)))
        self.assertFalse(found, assert_msg)

    def _execute_createplan_cmd_and_verify_msg(self, rule_sets):
        """
        Description:
            Function that executes the "createplan_cmd"
            and verifies the error messages
        Args:
            rule_sets: (dict) Dictionary containing rule sets
                       necessary for verifying error messages
        """
        for rule in rule_sets:
            self.log("info", "\n*** Starting test for invalid dnsclient "
                     "rules data set : {0}"
                     .format(rule['description']))

            _, stderr, _ = self.execute_cli_createplan_cmd(
                    self.test_ms, expect_positive=False)

            for result in rule['results']:
                self._assert_cli_error_message(stderr, result)

    def _execute_create_cmd_and_verify_msg(self, rule_sets, url_link,
                                           alias_name):
        """
        Description:
            Function that executes "cli_create_cmd" and
            verifies the error messages.
        Args:
            rule_sets:   (dict) Dictionary containing rule sets
                          necessary for verifying error messages
            url_link:    (str) The url link
            alias_name : (str) The name of the alias
        """
        for rule in rule_sets:

            self.log("info", "\n*** Starting test for invalid dnsclient "
                     "rules data set : {0}"
                     .format(rule['description']))

            _, stderr, _ = self.execute_cli_create_cmd(
                           self.test_ms, url_link, alias_name,
                           rule['param'], expect_positive=False)

            for result in rule['results']:
                self._assert_cli_error_message(stderr, result)

    def _execute_update_cmd_and_verify_msg(self, rule_sets, alias):
        """
        Description:
            Function that executes "cli_update_cmd" and
            verifies the error messages
         Args:
            rule_sets:  (dict) Dictionary containing rule sets
                   necessary for verifying error messages
            alias_item: (str) The name of the alias (path)
        """
        for rule in rule_sets:
            self.log("info", "\n*** Starting test for invalid dnsclient "
                     "rules data set : {0}"
                     .format(rule['description']))

            _, stderr, _ = self.execute_cli_update_cmd(
                    self.test_ms, alias, rule['param'],
                    expect_positive=False)

            for result in rule['results']:
                self._assert_cli_error_message(stderr, result)

    def _execute_remove_cmd_and_verify_msg(self, rule_sets, item_path):
        """
        Description:
            Function that executes "cli_remove_cmd" and
            verifies the error messages.
        Args:
        rule_sets: (dict) Dictionary containing rule sets
                   necessary for verifying error messages
        """
        for rule in rule_sets:
            self.log("info", "\n*** Starting test for invalid dnsclient "
                     "rules data set : {0}"
                     .format(rule['description']))

            _, stderr, _ = self.execute_cli_remove_cmd(
                    self.test_ms, item_path, expect_positive=False)

            for result in rule['results']:
                self._assert_cli_error_message(stderr, result)

    @attr('all', 'non-revert', 'story72', 'story72_tc01', 'story370237',
          'story370237_tc14', 'story370237_tc15', 'story370237_tc17')
    def test_01_p_create_update_remove_nameserver(self):
        """
        @tms_id: litpcds_72_tc01
        @tms_requirements_id: LITPCDS-72, TORF-370237
        @tms_title: test_01_p_create_update_remove_nameserver
        @tms_description: A node's resolve.conf can be (de)configured to use
                          IPv4 or IPv6 as DNS server.
        @tms_test_steps:
            @step:      Create dns-client on the MS with a search property set
                        to "foo.com".
            @result:    The dns-client is created on MS with search property
                        set to "foo.com".
            @step:      Create a gateway name server on the MS with the ip
                        property set to 2.
            @result:    Gateway name server created on the MS with the ip
                        property set to 2.
            @step:      Create nameserver1 on the MS with the ip property set
                        to the IPV4 address and the position property set to 3.
            @result:    Item nameserver1 created with ip property IPv4 and
                        position set to 3.
            @step:      Create dns-client on nodeX with the search property
                        defined with 6 domains.
            @result:    NodeX dns-client created with search property defined
                        with 6 domains.
            @step:      Create nameserver1 on nodeX with the ip property set
                        to gateway address and the position property set to 1.
            @result:    nameserver1 created on nodeX with ip property set to
                        gateway address and position set to 1.
            @step:      Create nameserver2 on nodeX with the ip property set
                        to an IPv6 address and the position property set to 3.
            @result:    nameserver2 created on nodeX with ip property set to
                        IPv6 address and position set to 3.
            @step:      Create nameserver3 on nodeX with the ip property set
                        to an IPv4 address and the position property set to 2.
            @result:    nameserver3 created on nodeX with with IPv4 and
                        position set to 2.
            @step:      Create dns-client on nodeY without the search property
                        defined.
            @result:    dns-client created for nodeY and search property
                        empty.
            @step:      Create nameserver1 on nodeY with the ip property set
                        to an IPv6 address with prefix and the position
                        property set to 3.
            @result:    nameserver1 created on nodeY with IPv6 address with
                        prefix and position 3.
            @step:      Create nameserver2 on nodeY with the ip property set
                        to an IPv4 address and the position property set to 2.
            @result:    nameserver2 created on nodeY with IPv4 address and
                        position 2.
            @step:      Create LITP plan.
            @result:    LITP plan created.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check resolv.conf on MS domain and nameserver added.
            @result:    MS domain and namserver added to resolv.conf on MS.
            @step:      Check resolv.conf on nodeX domains added in order
                        specified by position.
            @result:    NodeX domains and nameservers added to resolv.conf on
                        nodeX in the specified order.
            @step:      Check resolv.conf on nodeY domains added in order
                        specified by position.
            @result:    NodeY domains and nameservers added to resolv.conf on
                        nodeY in the specified order.
            @step:      Add nameserver3 on nodeY with the ip property set to
                        an IPv6 address and the position property set to 2.
            @result:    nameserver3 added to nodeY with IPv6 and positon 2.
            @step:      Update the the position property on nameserver2 on
                        nodeY set to 1.
            @result:    nameserver2 position updated (changed from 2 to 1).
            @step:      Update the search property on the MS to "bar.com"
            @result:    MS domain updated to "bar.com"
            @step:      Update ip property to an ipv4 address nameserver1 on
                        MS.
            @result:    nameserver1 IPv4 address updated for MS.
            @step:      Update ip property to an ipv6 address with prefix
                        nameserver1 on nodeX.
            @result:    nodeX ip property updated to IPv6 with prefix for
                        nameserver1.
            @step:      Add a search property on nodeY, amm.com.
            @result:    Search property amm.com added to nodeY
            @step:      Shuffle the 6 domains on nodeX.
            @result:    nodeX domains shuffled around.
            @step:      Create LITP plan.
            @result:    LITP plan created.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check MS resolv.conf line changed to "search bar.com"
            @result:    MS resolv.conf updated and line changed to
                        "search bar.com".
            @step:      Check nodeX resolv.conf domains added and in specified
                        order.
            @result:    nodeX resolv.conf domains added and in specified order
            @step:      Check the resolv.conf on nodeY nameservers added and
                        in specified order.
            @result:    nodeY resolv.conf nameservers added in specified
                        order.
            @step:      Check resolv.conf on nodeY has line "search amm.com"
            @result:    Line "search amm.com" added to nodeY resolv.conf.
            @step:      Remove nameserver1 from nodeX
            @result:    namserver1 on nodeX in ForRemoval
            @step:      Remove search property from dns-client on nodeX.
            @result:    dns-client nodeX updated and search property empty.
            @step:      Create LITP plan.
            @result:    LITP plan created.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check nameserver1 has been removed from the list of
                        configured nameservers.
            @result:    nameserver1 removed from list of nameservers.
            @step:      Check the search line has been removed from
                        resolv.conf.
            @result:    Search line removed from resolv.conf.
            @step:      Remove the dns-client on the MS.
            @result:    dns-client in ForRemoval.
            @step:      Remove dns-client on nodeX.
            @result:    dns-client in ForRemoval.
            @step:      Remove the items of type nameserver on nodeY.
            @result:    nameserver items in ForRemoval.
            @step:      Remove dns-client on nodeY
            @result:    dns-client in ForRemoval.
            @step:      Create LITP plan.
            @result:    LITP plan created.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check resolv.conf on MS
            @result:    All configured items are deconfigured and not
                        mentioned in resolv.conf
            @step:      Check resolv.conf on NodeX
            @result:    All configured items are deconfigured and not
                        mentioned in resolv.conf
            @step:      Check resolv.conf on NodeY
            @result:    All configured items are deconfigured and not
                        mentioned in resolv.conf
        @tms_test_precondition: N/A
        @tms_execution_type: Automated
        """
        # Remove dns configuration if one exists
        self.remove_itemtype_from_model(self.test_ms, "dns-client")

        # Get Managed Nodes
        self._get_managed_nodes()

        # Find the desired collection on the MS
        collection_type = "collection-of-node-config"
        config_path = self.find(
            self.test_ms, "/ms", collection_type)
        ms_config_path = config_path[0]

        # Find the desired collection on the nodes
        config_path = self.find(
            self.test_ms, "/deployments", collection_type)
        n1_config_path = config_path[0]
        n2_config_path = config_path[1]

        # Backup resolv.conf file
        self.backup_file(
            self.test_ms, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node1, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node2, test_constants.RESOLV_CFG_FILE)

        # Test Attributes
        ms_search1 = "foo.com"
        ms_search2 = "bar.com"
        ms_n1_ip1 = "10.10.10.101"
        ms_n1_ip2 = "10.10.10.110"

        n1_search1 = "d1.com,d2.com,d3.com,d4.com,d5.com,d6.com"
        n1_search_1 = "d1.com d2.com d3.com d4.com d5.com d6.com"
        n1_search2 = "d6.com,d5.com,d4.com,d3.com,d2.com,d1.com"
        n1_search_2 = "d6.com d5.com d4.com d3.com d2.com d1.com"
        n1_n1_ip1 = "10.10.10.101"
        n1_n2_ip1 = "0:0:0:0:0:ffff:a0a:a6"
        n1_n2_ip1_prefix = "64"
        n1_n3_ip1 = "10.10.10.103"
        n1_n3_ip2 = "0:0:0:0:0:ffff:a0a:a78"
        n1_n3_ip2_prefix = "128"

        n2_search1 = "amm.com"
        n2_n1_ip1 = "0:0:0:0:0:ffff:a0a:a66"
        n2_n2_ip1 = "10.10.10.202"
        n2_n3_ip1 = "0:0:0:0:0:ffff:a0a:a67"

        # Fix to avoid extreme SSH latency under RHEL7.7 by adding gateway
        # ip as a nameserver, see TORF-462156
        gateway_ip = "192.168.0.1"

        # 1. Create dns-client on MS with search property if not found
        ms_config_path = self.find(
            self.test_ms, "/ms", collection_type)[0]
        ms_dns_client = self._create_dns_client(
            ms_config_path, "mstest01a", search="{0}".format(ms_search1))

        # 2. Create nameserver on the MS with the ip property set to the
        #    gateway address and the position property set to 2
        props = "ipaddress={0} position=2".format(gateway_ip)
        self._create_nameserver(
                      ms_dns_client, "gw_name_server", props)

        # 3. Create nameserver2 on the MS with the ip property set to an
        #    IPv4 address and the position property set to 3
        props = "ipaddress={0} position=3".format(ms_n1_ip1)
        ms_namesrv2 = self._create_nameserver(
                      ms_dns_client, "nameserver_01a", props)

        # 4. Create dns-client on nodeX with the search property
        #    defined with 6 domains
        n1_dns_client = self._create_dns_client(
            n1_config_path, "n1test01a",
            search="{0}".format(n1_search1))

        # 5. Create nameserver1 on nodeX with the ip property set to the
        #    gateway address and the position property set to 1
        props = "ipaddress={0} position=1".format(gateway_ip)
        n1_namesrv1 = self._create_nameserver(
                            n1_dns_client, "gw_name_server", props)

        # 6. Create nameserver2 on nodeX with the ip property set to an
        # IPv6 address with prefix and the position property set to 3
        props = "ipaddress={0}/{1} position=3".format(n1_n2_ip1,
                                                      n1_n2_ip1_prefix)
        self._create_nameserver(
            n1_dns_client, "nameserver_01b", props)

        # 7. Create nameserver3 on nodeX with the ip property set to an
        # IPv4 address and the position property set to 2
        props = "ipaddress={0} position=2".format(n1_n1_ip1)
        n1_namesrv3 = self._create_nameserver(
            n1_dns_client, "nameserver_01a", props)

        # 8. Create dns-client on nodeY without the search property defined
        n2_dns_client = self._create_dns_client(
            n2_config_path, "n2test01a")

        # 9. Create nameserver1 on nodeY with the ip property set to an
        #    IPv6 address and the position property set to 3
        props = "ipaddress={0} position=3".format(n2_n1_ip1)
        n2_namesrv1 = self._create_nameserver(
            n2_dns_client, "nameserver_01a", props)

        # 10. Create nameserver2 on nodeY with the ip property set to
        #     gateway address and the position property set to 1
        props = "ipaddress={0} position=1".format(gateway_ip)
        n2_namesrv2 = self._create_nameserver(
                      n2_dns_client, "gw_name_server", props)

        # 11.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 12. Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 13.Check the resolv.conf on the MS:
        # Check that the domain was added to the resolv.conf on the MS
        # Check that the nameserver was added to the resolv.conf on the MS
        rfile = self.get_file_contents(
                    self.test_ms,
                    test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile), 3)
        self.assertEqual("search {0}".format(ms_search1), rfile[0])
        self.assertEqual("nameserver {0}".format(gateway_ip), rfile[1])
        self.assertEqual("nameserver {0}".format(ms_n1_ip1), rfile[2])

        # 14.Check the resolv.conf on nodeX:
        #  Check that the domains added to the resolv.conf on NodeX
        #  in the order they were specified
        #  Check that the nameservers are added to the resolv.conf on NodeX
        # in the order they were specified via the position property
        # Check Ipv6 address is present without CIDR prefix
        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 4)
        self.assertEqual(
            "search {0}".format(n1_search_1), rfile_n1[0])
        self.assertEqual("nameserver {0}".format(gateway_ip), rfile_n1[1])
        self.assertEqual("nameserver {0}".format(n1_n1_ip1), rfile_n1[2])
        self.assertEqual("nameserver {0}".format(n1_n2_ip1), rfile_n1[3])
        self.assertNotEqual("nameserver {0}/{1}".format(n1_n2_ip1,
                                            n1_n2_ip1_prefix), rfile_n1[3],
            "resolv.conf contain IPv6 address with CIDR prefix, not expected")

        # 15.Check the resolv.conf on nodeY:
        # Check that search is not specified in the resolv.conf on NodeY
        # Check that the nameservers are added to the resolv.conf on NodeY
        # in the order they were specified via the position property
        rfile_n2 = self.get_file_contents(
                self.test_node2,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n2), 2)
        self.assertEqual("nameserver {0}".format(gateway_ip), rfile_n2[0])
        self.assertEqual("nameserver {0}".format(n2_n1_ip1), rfile_n2[1])

        # 16.Add nameserver3 on nodeY with the ip property set to an
        # IPv6 address and the position property set to 3
        props = "ipaddress={0} position=3".format(n2_n3_ip1)
        n2_namesrv3 = self._create_nameserver(
            n2_dns_client, "nameserver_01b", props)

        # 17.Update the the position property on nameserver1 on nodeY to 2
        props = 'position="2"'
        self._update_nameserver_props(
            n2_namesrv1, props)

        # 18.Update the search property on the MS to "bar.com"
        self._update_dns_client(ms_dns_client, "search={0}".format(ms_search2))

        # 19.Update ip property to an ipv4 address nameserver2 on MS
        self._update_nameserver_props(
            ms_namesrv2, "ipaddress={0}".format(ms_n1_ip2))

        # 20.Update ip property to an ipv6 address nameserver3 on nodeX
        self._update_nameserver_props(
            n1_namesrv3, "ipaddress={0}/{1}".format(n1_n3_ip2,
                                                    n1_n3_ip2_prefix))

        # 21.Add a search property on nodeY, amm.com
        self._update_dns_client(n2_dns_client, "search={0}".format(n2_search1))

        # 22.Shuffle the 6 domains on nodeX
        self._update_dns_client(
            n1_dns_client, "search={0}".format(n1_search2))

        # 23.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 24. Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 25.Check the resolv.conf on the MS:
        # Check that the search line is replaced with "search bar.com"
        rfile = self.get_file_contents(
            self.test_ms,
            test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile), 3)
        self.assertEqual("search {0}".format(ms_search2), rfile[0])
        self.assertEqual("nameserver {0}".format(gateway_ip), rfile[1])
        self.assertEqual("nameserver {0}".format(ms_n1_ip2), rfile[2])

        # 26.Check the resolv.conf on nodeX:
        # Check that the domains added to the resolv.conf on NodeX are in
        # the order they were specified
        # Check IPv6 address is present without CIDR prefix
        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 4)
        self.assertEqual(
            "search {0}".format(n1_search_2), rfile_n1[0])
        self.assertEqual("nameserver {0}".format(gateway_ip), rfile_n1[1])
        self.assertEqual("nameserver {0}".format(n1_n3_ip2), rfile_n1[2])
        self.assertEqual("nameserver {0}".format(n1_n2_ip1), rfile_n1[3])
        self.assertNotEqual("nameserver {0}/{1}".format(n1_n3_ip2,
                                        n1_n3_ip2_prefix), rfile_n1[3],
             "resolv.conf contain IPv6 address with CIDR prefix, not expected")

        # 27.Check the resolv.conf on nodeY:
        # Check that the nameservers are added to the resolv.conf on NodeY
        # in the order they were specified via the position property
        # Check that the search line, "search amm.com" is added
        rfile_n2 = self.get_file_contents(
                self.test_node2,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n2), 4)
        self.assertEqual("search {0}".format(n2_search1), rfile_n2[0])
        self.assertEqual("nameserver {0}".format(gateway_ip), rfile_n2[1])
        self.assertEqual("nameserver {0}".format(n2_n1_ip1), rfile_n2[2])
        self.assertEqual("nameserver {0}".format(n2_n3_ip1), rfile_n2[3])

        # 28.Remove nameserver1 from nodeX
        self.execute_cli_remove_cmd(self.test_ms, n1_namesrv1)

        # 29.Remove the search property from the dns-client on nodeX
        self._update_dns_client_remove_search_prop(n1_dns_client)

        # 30.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 31. Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 32.Check nameserver1 has been removed from the
        #  list of configured nameservers
        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 2)
        self.assertEqual("nameserver {0}".format(n1_n3_ip2), rfile_n1[0])
        self.assertEqual("nameserver {0}".format(n1_n2_ip1), rfile_n1[1])

        # 33.Check the search line has been removed from resolv.conf
        self._find_line_in_resolv_conf(
            self.test_node1, n1_search_2, positive=False)

        # 34.Remove the dns-client on the MS
        self.execute_cli_remove_cmd(self.test_ms, ms_dns_client)

        # 35.Remove dns-client on nodeX
        self.execute_cli_remove_cmd(self.test_ms, n1_dns_client)

        # 36.Remove the items of type nameserver on nodeY
        self.execute_cli_remove_cmd(self.test_ms, n2_namesrv1)
        self.execute_cli_remove_cmd(self.test_ms, n2_namesrv2)
        self.execute_cli_remove_cmd(self.test_ms, n2_namesrv3)

        # 37.Remove dns-client on nodeY
        self.execute_cli_remove_cmd(self.test_ms, n2_dns_client)

        # 38.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 39.Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 40.Check resolv.conf on MS
        self._find_line_in_resolv_conf(
            self.test_ms, ms_search2, positive=False)

        self._find_line_in_resolv_conf(
            self.test_ms, ms_n1_ip2, positive=False)

        # 41.Check resolv.conf on NodeX
        self._find_line_in_resolv_conf(
            self.test_node1, n1_n2_ip1, positive=False)

        self._find_line_in_resolv_conf(
            self.test_node1, n1_n3_ip1, positive=False)

        # 42.Check resolv.conf on NodeY
        self._find_line_in_resolv_conf(
            self.test_node2, n2_search1, positive=False)

        self._find_line_in_resolv_conf(
            self.test_node2, n2_n1_ip1, positive=False)

        self._find_line_in_resolv_conf(
            self.test_node2, n2_n2_ip1, positive=False)

        self._find_line_in_resolv_conf(
            self.test_node2, n2_n3_ip1, positive=False)

    @attr('all', 'non-revert', 'story72', 'story72_tc02')
    def test_02_n_nameserver_validation_negative(self):
        """
        @tms_id: litpcds_72_tc02
        @tms_requirements_id: LITPCDS-72
        @tms_title: test_02_n_nameserver_validation_negative
        @tms_description: Attempts to create an invalid DNS client and/or
                          nameservers must produce clear validation errors and
                          messages.
        @tms_test_steps:
            @step:      Execute create dns-client command on nodeX.
            @result:    dns-client created for nodeX.
            @step:      Create LITP plan.
            @result:    LITP plan creation fails.
            @step:      Check for expected validation error as dns-client has
                        an empty collection of nameservers.
            @result:    Validation error for empty collection of nameservers.
            @step:      Create a nameserver on nodeX without the mandatory
                        position property.
            @result:    Validation error for mandatory position property.
            @step:      Create a nameserver on nodeX with the mandatory
                        position property with a string value.
            @result:    Validation error for invalid value type.
            @step:      Create a nameserver on nodeX with the mandatory
                        position property with a numeric value other than 1,
                        2 or 3.
            @result:    Validation error for invalid value range.
            @step:      Create a nameserver on nodeX with the mandatory
                        position property with a value of 1.
            @result:    nameserver item created with position 1.
            @step:      Execute create dns-client command on nodeX to create a
                        2nd dns-client.
            @result:    dns-client item created for nodeX.
            @step:      Create LITP plan.
            @result:    LITP plan creation fails.
            @step:      Check for expected validation error as not allowed to
                        have more than one config.
            @result:    Validation error not allowed to have more than one
                        dns-client configuration.
            @step:      Remove 2nd dns-client.
            @result:    2nd dns-client item removed.
            @step:      Attempt to create a nameserver with no IP.
            @result:    Validation error, nameserver without an IP address.
            @step:      Attempt to create a nameserver with an IPv4 address
                        not in dot notation.
            @result:    Validation error, invalid value for IP.
            @step:      Create a nameserver on nodeX with the mandatory
                        position property with a value of 1.
            @result:    nameserver item for nodeX created with position 1.
            @step:      Create LITP plan.
            @result:    LITP plan creation fails.
            @step:      Check for expected validaton error as position 1
                        already used.
            @result:    Validation error position 1 already used.
            @step:      Create a nameserver on nodeX with the mandatory
                        position property with a value of 2 with an IPv4
                        address.
            @result:    nameserver item for nodeX created with position 2 and
                        IPv4 address.
            @step:      Create a nameserver on nodeX with the mandatory
                        position property with a value of 3 with an IPv6
                        address.
            @result:    nameserver item for nodeX created with position 3 and
                        IPv6 address.
            @step:      Attempt to create a 4th nameserver on nodeX.
            @result:    Validation error too many nameservers nodeX (max 3).
            @step:      Update the dns-client with "search" property
                        containing more than 6 domains.
            @result:    Validation error (max 6 domains for dns-client search).
            @step:      Update the dns-client with "search" property containing
                        more than 256 characters.
            @result:    Validation error more than 256 char for domain search.
            @step:      Remove nameservers.
            @result:    nameserver items in ForRemoval
            @step:      Create LITP plan
            @result:    LITP plan creation fails.
            @step:      Check cardinaltiy error
            @result:    Cardinality error on LITP create_plan
            @step:      Remove dns-client
            @result:    dns-client in ForRemoval
            @step:      Create LITP plan.
            @result:    LITP plan creation fails.
            @step:      Check LITP plan does not exist.
            @result:    No plan tasks created message.
        @tms_test_precondition: N/A
        @tms_execution_type: Automated
        """
        # Find the managed node
        self._get_managed_nodes()

        # Find the desired collection on the nodes
        config_path = self.find(
            self.test_ms, "/deployments", "collection-of-node-config")
        n1_config_path = config_path[0]

        # Backup resolv.conf file
        self.backup_file(
            self.test_ms, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node1, test_constants.RESOLV_CFG_FILE)

        # 1. Execute create dns-client command on nodeX
        n1_dns_client = self._create_dns_client(
            n1_config_path, "n1test02a",
            search="d1.com")

        # 2.Check for expected validation error as
        # dns-client has an empty collection of nameservers
        rule_sets = []
        rule_set = {
        'description': '1. Check for expected validation error as '
                       'dns-client has an empty collection of nameservers',
        'param': None,
        'results':
        [
         {
          'path': n1_dns_client + '/nameservers',
          'msg': 'CardinalityError    Create plan failed: This collection '
                 'requires a minimum of 1 items not marked for removal'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

        # 3. Create plan
        self._execute_createplan_cmd_and_verify_msg(rule_sets)

        # 4. Create a nameserver on nodeX without
        # the mandatory position property
        props = 'ipaddress="10.10.10.101"'
        rule_sets = []
        rule_set = {
        'description': '2. Create a nameserver on nodeX without'
                       'the mandatory position property',
        'param': props,
        'results':
        [
         {
          'msg': 'MissingRequiredPropertyError in property: "position"    '
                 'ItemType "nameserver" is required to have a property with '
                 'name "position"'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

        # 5. Create a nameserver on nodeX with the mandatory position property
        #   with a string value
        props = 'ipaddress="10.10.10.101" position="a"'
        rule_set = {
        'description': '3. Create a nameserver on nodeX with the mandatory '
                       'position property the mandatory position property',
        'param': props,
        'results':
        [
         {
          'msg': 'ValidationError in property: "position"    '
                 'Invalid value \'a\'.'
          },
         ]
        }
        rule_sets.append(rule_set.copy())

        # 6. Create a nameserver on nodeX with the mandatory position property
        # with a numeric value other than 1, 2 or 3
        props = 'ipaddress="10.10.10.101" position="10"'
        rule_set = {
        'description': '4. Create a nameserver on nodeX with the mandatory '
                       'position property with a numeric value other than '
                       '1, 2 or 3',
        'param': props,
        'results':
        [
         {
          'msg': 'ValidationError in property: "position"    '
                 'Invalid value \'10\'.'
          },
         ]
        }
        rule_sets.append(rule_set.copy())

        # 7. Check for expected validation error
        self._execute_create_cmd_and_verify_msg(
                                rule_sets,
                                n1_dns_client + "/nameservers/nameserver_02a",
                                "nameserver")

        # 8.Create a nameserver on nodeX with the mandatory position property
        # with a value of 1
        props = 'ipaddress="10.10.10.101" position="1"'
        n1_namesrv1 = self._create_nameserver(
            n1_dns_client, "nameserver_test02a", props)

        # 9.Execute create dns-client command on nodeX
        # to create a 2nd dns-client
        n1_dns_client2 = self._create_dns_client(
                n1_config_path, "dns2", search="d2.com")

        rule_sets = []
        rule_set = {
        'description': '5. Create a nameserver on nodeX with the mandatory '
                        'position property with a value of 1',
        'param': props,
        'results':
        [
         {
          'path': n1_dns_client2 + '/nameservers',
          'msg': 'CardinalityError    Create plan failed: This collection '
                 'requires a minimum of 1 items not marked for removal'
          },
         {
          'path': n1_dns_client2,
          'msg': 'ValidationError    Create plan failed: Only one '
                 '"dns-client" may be configured per node'
          },
         {
          'path': n1_dns_client,
          'msg': 'ValidationError    Create plan failed: Only one '
                 '"dns-client" may be configured per node'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

         # 10. Execute create_plan command to see expected validation error
        self._execute_createplan_cmd_and_verify_msg(rule_sets)

        props = 'ipaddress="10.10.10.201" position="1"'
        self._create_nameserver(
                            n1_dns_client2, "nameserver_test02a", props)
        rule_sets = []
        rule_set = {
        'description': '6. Run create plan',
        'param': props,
        'results':
        [
         {
          'path': n1_dns_client2,
          'msg': 'ValidationError    Create plan failed: Only one '
                 '"dns-client" may be configured per node'
          },
         {
          'path': n1_dns_client,
          'msg': 'ValidationError    Create plan failed: Only one '
                 '"dns-client" may be configured per node'
          }
         ]
        }
        rule_sets.append(rule_set.copy())
        self._execute_createplan_cmd_and_verify_msg(rule_sets)

        # 11.Remove 2nd dns-client
        self.execute_cli_remove_cmd(self.test_ms, n1_dns_client2)

        # 12.Attempt to create a nameserver with no IP
        props = 'position="2"'

        rule_sets = []
        rule_set = {
        'description': '7. Attempt to create a nameserver with no IP',
        'param': props,
        'results':
        [
         {
          'msg': 'MissingRequiredPropertyError in property: "ipaddress"    '
                 'ItemType "nameserver" is required to have a property with '
                 'name "ipaddress"'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

        # 13.Attempt to create a nameserver with an IPv4 address
        # not in dot notation
        props = 'ipaddress="10:10:10:101" position="10"'
        rule_set = {
        'description': '8. Attempt to create a nameserver with an IPv4 address'
                       'not in dot notation',
        'param': props,
        'results':
        [
         {
          'msg': 'ValidationError in property: "position"    '
                 'Invalid value \'10\'.'
          },
         {
          'msg': 'ValidationError in property: "ipaddress"    '
                 'Invalid IP address value \'10:10:10:101\''
          }
         ]
        }
        rule_sets.append(rule_set.copy())

         # 14.Check for expected validation error
        self._execute_create_cmd_and_verify_msg(
                                rule_sets,
                                n1_dns_client + "/nameservers/nameserver_02b",
                                "nameserver")

        # 15.Create a nameserver on nodeX with the mandatory position property
        # with a value of 1
        props = 'ipaddress="10.10.10.102" position="1"'
        n1_namesrv2 = self._create_nameserver(
            n1_dns_client, "nameserver_test02b", props)

        rule_sets = []
        rule_set = {
        'description': '9. Attempt to create a nameserver with position 1 and '
                       ' IPv4 address in dot notation',
        'param': props,
        'results':
        [
          {
          'path': n1_namesrv2,
          'msg': 'ValidationError    Create plan failed: Duplicate nameserver '
                 'position "1"'
          },
         {
          'path': n1_namesrv1,
          'msg': 'ValidationError    Create plan failed: Duplicate nameserver '
                 'position "1"'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

        # 16.Create plan and check for expected validation error as position 1
        # already used
        self._execute_createplan_cmd_and_verify_msg(rule_sets)

        # 17.Update nameserver on nodeX with the mandatory position property
        # with a value of 2 with an IPv4 address
        self._update_nameserver_props(
            n1_namesrv2, "ipaddress=10.10.10.102 position=2")

        # 18.Create a nameserver on nodeX with the mandatory position property
        # with a value of 3 with an IPv6 address
        props = 'ipaddress="0:0:0:0:0:ffff:a0a:a77" position="3"'
        n1_namesrv3 = self._create_nameserver(
            n1_dns_client, "nameserver_test02c", props)

        # 19.Attempt to create a 4th nameserver on nodeX
        props = 'ipaddress="10.10.10.104" position="3"'
        n1_namesrv4 = self._create_nameserver(
                    n1_dns_client, "nameserver_test02d", props)

        rule_sets = []
        rule_set = {
        'description': '10. Attempt to create a 4th nameserver on nodeX ',
        'param': props,
        'results':
        [
         {
          'path': n1_namesrv3,
          'msg': 'ValidationError    Create plan failed: Duplicate nameserver '
                 'position "3"'
          },
         {
          'path': n1_namesrv4,
          'msg': 'ValidationError    Create plan failed: Duplicate nameserver '
                 'position "3"'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

        # 20. Check expected validation error as a collection can have a max
        # of 3 nameservers
        self._execute_createplan_cmd_and_verify_msg(rule_sets)

        # 21.Update the dns-client with "search" property containing
        # more than 6 domains
        props = '"search=d1.com,d2.com,d3.com,d4.com,d5.com,d6.com,d7.com"'

        rule_sets = []
        rule_set = {
        'description': '11. Update the dns-client with "search" property '
                       'containing more than 6 domains',
        'param': props,
        'results':
        [
         {
          'msg': 'ValidationError in property: "search"    '
                 'A maximum of 6 domains per search may be specified'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

        # 22.Check for expected validation error
        self._execute_update_cmd_and_verify_msg(rule_sets, n1_dns_client)

        # 23.Update the dns-client with "search" property containing
        # more than 256 characters
        props = ('search="nagrehgajkjgaehgaheajgagjaljhsjhsjhsjhsjhlkskjhsjgo'
               'rkwhw3486h42ig9q4ukjsjhsnyu0m42mgjaojgagjajaljgaljgoagjakg'
               'ajohgakhgjahkahjazhahajhoahahalkeoiqut4ajgangangoahangmoma'
               'ontobmyonnq5vnyn5mvqynqiigahgoajnuccoiuwtvvwotutqmqtnuntvy'
               'mimuntvntvtvqpmtqmtqimtqrrreefjuthroewhfaHFIUAFHHFUA.com"')

        rule_sets = []
        rule_set = {
        'description': '12. Update the dns-client with "search" property '
                       'containing more than 256 characters',
        'param': props,
        'results':
        [
         {
          'msg': 'ValidationError in property: "search"    '
                 'Length of property cannot be more than 256 characters'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

        # 24.Check for expected validation error
        self._execute_update_cmd_and_verify_msg(rule_sets, n1_dns_client)

        # 25.Remove nameservers
        self._remove_nameserver(n1_namesrv1)
        self._remove_nameserver(n1_namesrv2)
        self._remove_nameserver(n1_namesrv3)
        self._remove_nameserver(n1_namesrv4)

        rule_sets = []
        rule_set = {
        'description': '13. Create Plan',
        'param': None,
        'results':
        [
         {
           'path': n1_dns_client + '/nameservers',
           'msg': 'CardinalityError    Create plan failed: This collection '
                 'requires a minimum of 1 items not marked for removal'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

        # 26.Create plan and check cardinaltiy error
        self._execute_createplan_cmd_and_verify_msg(rule_sets)

        # 27.remove dns-client
        self.execute_cli_remove_cmd(self.test_ms, n1_dns_client)

        rule_sets = []
        rule_set = {
        'description': '14. Create Plan after removing dns-client',
        'param': None,
        'results':
         [
         {
          'msg': 'DoNothingPlanError    Create plan failed: no tasks were '
                 'generated'
          }
         ]
        }
        rule_sets.append(rule_set.copy())

        # 28.Create plan and check that plan is not created
        self._execute_createplan_cmd_and_verify_msg(rule_sets)

    @attr('all', 'non-revert', 'story72', 'story72_tc03')
    def test_03_p_dns_client_export_load_xml(self):
        """
        @tms_id: litpcds_72_tc03
        @tms_requirements_id: LITPCDS-72
        @tms_title: test_03_p_dns_client_export_load_xml
        @tms_description: Verify the dns-client and nameserver model items can
                          be loaded and exported via XML.
        @tms_test_steps:
            @step:      Create a dns-client on nodeX.
            @result:    dns-client for nodeX created.
            @step:      Create a dns-client on nodeY.
            @result:    dns-client for nodeY created.
            @step:      Define namesevers on nodeX.
            @result:    nameserver item for nodeX created.
            @step:      Define namesevers on nodeY.
            @result:    nameserver item for nodeY created.
            @step:      export the dns-client.
            @result:    dns-client item exported to XML file.
            @step:      export the nameserver item-type.
            @result:    nameserver item export to XML file.
            @step:      remove the nameserver item-type.
            @result:    nameserver item in ForRemoval.
            @step:      load the dns-client into the model using --merge.
            @result:    dns-client XML loaded into model.
            @step:      Check the dns-client is in state initial.
            @result:    dns-client item in Initial state.
            @step:      load the nameserver item-type into the model
                        using --replace.
            @result:    nameserver XML loaded into model.
            @step:      Check the nameserver is in state initial.
            @result:    nameserver item in Initial state.
            @step:      Copy xml files onto the MS. XML files for dns-client
                        with optional search for nodeX and nodeY, update to
                        nameserver item IP and position properties, removed
                        nameserver and create nameserver.
            @result:    Files copied to MS.
            @step:      Load xml file using the --merge.
            @result:    dns-client created/loaded in model
            @step:      Check the created dns-client is in state "initial".
            @result:    dns-client in state Initial.
            @step:      Load xml file using the --replace.
            @result:    XML file loaded into model.
            @step:      Create LITP plan.
            @result:    LITP plan created.
            @step:      Run LITP plan.
            @result:    LITP plan runs successfully.
            @step:      Check state of items in tree.
            @result:    All items in Applied state or removed from tree.
            @step:      Check resolv.conf on nodeX
            @result:    resolv.conf successfully configured.
            @step:      Check resolv.conf on nodeY
            @result:    resolv.conf successfully configured.
            @step:      Remove all items that were loaded.
            @result:    All items in ForRemoval.
            @step:      Create LITP plan.
            @result:    LITP plan created.
            @step:      Run LITP plan.
            @result:    LITP plan runs successfully.
            @step:      Check all items removed from model.
            @result:    All test items removed from model.
        @tms_test_precondition: N/A
        @tms_execution_type: Automated
        """
        # Find the managed nodes
        self._get_managed_nodes()

        # Find the desired collection on the nodes
        config_path = self.find(
            self.test_ms, "/deployments", "collection-of-node-config")
        n1_config_path = config_path[0]
        n2_config_path = config_path[1]

        # Backup resolv.conf file
        self.backup_file(
            self.test_ms, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node1, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node2, test_constants.RESOLV_CFG_FILE)

        # 1. Create a dns-client on nodeX
        n1_dns_client = self._create_dns_client(
            n1_config_path, "n1dns_client03a", search="foo.com")

        # 2. Create a dns-client on nodeY
        n2_dns_client = self._create_dns_client(
            n2_config_path, "n2dns_client03a")

        # 3. Define namesevers om nodeX
        props = 'ipaddress="10.10.10.101" position="1"'
        self._create_nameserver(
            n1_dns_client, "nameserver_03a", props)

        props = 'ipaddress="0:0:0:0:0:ffff:a0a:a66" position="2"'
        self._create_nameserver(
            n1_dns_client, "nameserver_03b", props)

        # 4. Define a namesever om nodeY
        props = 'ipaddress="10.10.10.201" position="3"'
        n2_namesrv1 = self._create_nameserver(
            n2_dns_client, "nameserver_03a", props)

        try:
            # 5. export the dns-client
            self.execute_cli_export_cmd(
                self.test_ms, n2_dns_client, "xml_03a_story72.xml")

            # 6. export the nameserver item-type
            self.execute_cli_export_cmd(
                self.test_ms, n2_namesrv1, "xml_03b_story72.xml")

            # 7. remove the nameserver item-type
            self._remove_nameserver(n2_namesrv1)

            # 8. load the dns-client into the model using --merge
            self.execute_cli_load_cmd(
                self.test_ms, n2_config_path, "xml_03a_story72.xml", "--merge")

            # 9. Check the dns-client is in state initial
            self.assertEqual(
                self.get_item_state(self.test_ms, n2_dns_client), "Initial")

            # 10. load the nameserver item-type into the model using --merge
            self.execute_cli_load_cmd(
                self.test_ms, n2_dns_client + "/nameservers",
                "xml_03b_story72.xml", "--merge")

            # 11. Check the nameserver is in state initial
            self.assertEqual(
                self.get_item_state(self.test_ms, n2_namesrv1), "Initial")

            # 12. load the nameserver item-type into the model using --replace
            self.execute_cli_load_cmd(
                self.test_ms, n2_dns_client + "/nameservers",
                "xml_03b_story72.xml", "--replace")

            # 13. Check the nameserver is in state initial
            self.assertEqual(
                self.get_item_state(self.test_ms, n2_namesrv1), "Initial")

            # 14. Copy xml files onto the MS
            #   XML files contain
            #   ==> dns-client with optional search property on nodeX
            #   ==> dns-client with optional search property removed on nodeY
            #   ==> an updated nameserver ip and position property
            #   ==> removed nameserver
            #   ==> Created nameserver
            xml_filenames = \
                    ['xml_dns_client_1_story72.xml',
                     'xml_dns_client_2_story72.xml']
            local_filepath = os.path.dirname(__file__)
            for xml_filename in xml_filenames:
                local_xml_filepath = local_filepath + "/xml_files/" + \
                    xml_filename
                xml_filepath = "/tmp/" + xml_filename
                self.assertTrue(self.copy_file_to(
                    self.test_ms, local_xml_filepath, xml_filepath,
                    root_copy=True))

            # 15. Load xml file using the --merge
            self.execute_cli_load_cmd(
                self.test_ms, n1_config_path,
                "/tmp/xml_dns_client_1_story72.xml", "--replace")

            # 16. Check the created dns-client is in state "initial"
            self.assertEqual(
                self.get_item_state(self.test_ms, n1_dns_client), "Initial")

            # 17. Load xml file using the --replace
            self.execute_cli_load_cmd(
                self.test_ms, n2_config_path,
                "/tmp/xml_dns_client_2_story72.xml", "--merge")

            # 18. Create plan
            self.execute_cli_createplan_cmd(self.test_ms)

            # 19. Run plan
            self.execute_cli_runplan_cmd(self.test_ms)

            # Wait for plan to complete
            self.assertTrue(self.wait_for_plan_state(
                self.test_ms, test_constants.PLAN_COMPLETE))

            self.execute_cli_removeplan_cmd(self.test_ms)

            # 20. Check state of items in tree
            self.assertTrue(self.is_all_applied(self.test_ms))

            # 21. Check resolv.conf on node1
            rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
            self.assertEqual(len(rfile_n1), 2)
            self.assertEqual(
                "nameserver 0:0:0:0:0:ffff:a0a:a66", rfile_n1[0])
            self.assertEqual(
                "nameserver 10.10.10.101", rfile_n1[1])

            # 22. Check resolv.conf on node2
            rfile_n2 = self.get_file_contents(
                self.test_node2,
                test_constants.RESOLV_CFG_FILE, su_root=True)
            self.assertEqual(len(rfile_n2), 4)
            self.assertEqual(
                "search bar.com", rfile_n2[0])
            self.assertEqual(
                "nameserver 10.10.10.10", rfile_n2[1])
            self.assertEqual(
                "nameserver 0:0:0:0:0:ffff:a0a:a67", rfile_n2[2])
            self.assertEqual(
            "nameserver 10.10.10.201", rfile_n2[3])

        finally:
            # 23. Remove all items that were loaded
            self.execute_cli_remove_cmd(self.test_ms, n1_dns_client)
            self.execute_cli_remove_cmd(self.test_ms, n2_dns_client)

    @attr('all', 'non-revert', 'story72', 'story72_tc04')
    def test_04_p_nameserver_manually_update_resolv_conf(self):
        """
        @tms_id: litpcds_72_tc04
        @tms_requirements_id: LITPCDS-72
        @tms_title: test_04_p_nameserver_manually_update_resolv_conf
        @tms_description: The resolv.conf file must be under puppet control
                          and any manual updated performed, should be
                          overidden/removed by puppet.
        @tms_test_steps:
            @step:      Create a dns-config on nodeX.
            @result:    nodeX dns-config item created.
            @step:      Create a nameserver.
            @result:    nameserver item created.
            @step:      Create LITP plan.
            @result:    LITP plan created.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check nameserver has been added.
            @result:    Nameserver added to resolv.conf on nodeX.
            @step:      Manually update resolv.conf
            @result:    resolv.conf file updated outside LITP.
            @step:      Check nameserver has been added
            @result:    Nameserver added to resolv.conf file by user.
            @step:      Wait for a puppet run and check that manual update has
                        been removed.
            @result:    Manual updated removed after puppet run replaces
                        resolv.conf file.
        @tms_test_precondition: N/A
        @tms_execution_type: Automated
        Description:
        test that the /etc/resolv.conf in nodeX is under puppet control
        """
        # Find the managed nodes
        self._get_managed_nodes()

        # Find the desired collection on the nodes
        config_path = self.find(
            self.test_ms, "/deployments", "collection-of-node-config")
        n1_config_path = config_path[0]

        # Backup resolv.conf file
        self.backup_file(
            self.test_ms, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node1, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node2, test_constants.RESOLV_CFG_FILE)

        # 1. Create a dns-config on nodeX
        n1_dns_client = self._create_dns_client(
            n1_config_path, "n1test04a",
            search="d1.com")

        # 2. Create a nameserver
        props = 'ipaddress="10.10.10.101" position="1"'
        self._create_nameserver(
            n1_dns_client, "nameserver_04a", props)

        # 3. Create a plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 4. Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 5. Check nameserver has been added
        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 2)
        self.assertEqual("search d1.com", rfile_n1[0])
        self.assertEqual("nameserver 10.10.10.101", rfile_n1[1])

        # 6. Manually update /etc/resolv.conf
        std_out, std_err, rc = self.run_command(
            self.test_node1,
            "/bin/echo 'nameserver 172.11.10.12' >> {0}".format(
            test_constants.RESOLV_CFG_FILE),
            su_root=True)
        self.assertEquals(0, rc)
        self.assertEquals([], std_out)
        self.assertEquals([], std_err)

        # 7. Check nameserver has been added
        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 3)
        self.assertEqual("search d1.com", rfile_n1[0])
        self.assertEqual("nameserver 10.10.10.101", rfile_n1[1])
        self.assertEqual("nameserver 172.11.10.12", rfile_n1[2])

        # 8. Wait for a puppet run and check that manual
        # update has been removed
        cmd_to_run = \
            self.redhatutils.get_grep_file_cmd(
            test_constants.RESOLV_CFG_FILE, "172.11.10.12")

        self.assertTrue(
            self.wait_for_puppet_action(
            self.test_ms, self.test_node1, cmd_to_run, 1))

    @attr('all', 'non-revert', 'story72', 'story72_tc06',
               'cdb-only', 'cdb_priority1')
    def test_05_p_create_remove_nameserver(self):
        """
        @tms_id: litpcds_72_tc05
        @tms_requirements_id: LITPCDS-72
        @tms_title: test_05_p_create_remove_nameserver
        @tms_description:
        @tms_test_steps:
            @step:      Create dns-client on the MS with a search property set
                        to "foo.com".
            @result:    dns-client model item created for MS.
            @step:      Create nameserver1 on the MS with the ip property set
                        to am IPv4 address and the position property set to 3.
            @result:    nameserver model item created for MS with IPv4 address
                        and position 3.
            @step:      Create dns-client on nodeX with the search property
                        defined with 6 domains.
            @result:    dns-client model item for nodeX created with 6 domains
                        in search field.
            @step:      Create nameserver1 on nodeX with the ip property set to
                        an IPv4 address and the position property set to 1.
            @result:    nameserver1 model item created for nodeX with IPv4
                        address and position 1.
            @step:      Create nameserver2 on nodeX with the ip property set to
                        an IPv6 address and the position property set to 3.
            @result:    nameserver2 model item created for nodeX with IPv4
                        address and position 3.
            @step:      Create nameserver3 on nodeX with the ip property set
                        to an IPv4 address and the position property set to 2.
            @result:    nameserver3 model item created for nodeX with IPv4
                        address and position 2.
            @step:      Create LITP plan.
            @result:    LITP plan created successfully.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check resolv.conf on MS has added domain and
                        nameserver.
            @result:    resolv.conf file on MS has domain and nameserver
                        listed.
            @step:      Check resolv.conf on nodeX has added domain and
                        nameservers according to position specified.
            @result:    resolv.conf file on nodeX has domain and nameserver
                        listed in correct position.
            @step:      Remove nameserver1 from nodeX.
            @result:    nameserver1 item in ForRemoval.
            @step:      Remove the search property from the dns-client on the
                        MS.
            @result:    dns-client search property empty and dns-client model
                        item in Updated state.
            @step:      Create LITP plan.
            @result:    LITP plan created successfully.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check nameserver1 has been removed from the list of
                        configured nameservers.
            @result:    nameserver1 no longer listed in resolv.conf
            @step:      Check the search line has been removed from
                        resolv.conf.
            @result:    search line in resolv.conf removed.
            @step:      Remove the dns-client on the MS.
            @result:    dns-client model item in ForRemoval for MS.
            @step:      Remove dns-client on nodeX.
            @result:    dns-client model item in ForRemoval for nodeX.
            @step:      Create LITP plan.
            @result:    LITP plan created successfully.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check resolv.conf on MS.
            @result:    Test items are deconfigured and no longer listed in
                        resolve.conf on MS.
            @step:      Check resolv.conf on NodeX.
            @result:    Test items are deconfigured and no longer listed in
                        resolve.conf on NodeX.
        @tms_test_precondition: N/A
        @tms_execution_type: Automated
        """
        # Remove dns configuration if one exists
        self.remove_itemtype_from_model(self.test_ms, "dns-client")

        # Get Managed Nodes
        self._get_managed_nodes()

        # Find the desired collection on the MS
        collection_type = "collection-of-node-config"
        config_path = self.find(
            self.test_ms, "/ms", collection_type)
        ms_config_path = config_path[0]

        # Find the desired collection on the nodes
        config_path = self.find(
            self.test_ms, "/deployments", collection_type)
        n1_config_path = config_path[0]

        # Backup resolv.conf file
        self.backup_file(
            self.test_ms, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node1, test_constants.RESOLV_CFG_FILE)

        # Test Attributes
        ms_search1 = "foo.com"
        ms_n1_ip1 = "10.10.10.101"

        n1_search1 = "d1.com,d2.com,d3.com,d4.com,d5.com,d6.com"
        n1_search_1 = "d1.com d2.com d3.com d4.com d5.com d6.com"
        n1_n1_ip1 = "10.10.10.101"
        n1_n2_ip1 = "0:0:0:0:0:ffff:a0a:a6"
        n1_n3_ip1 = "10.10.10.103"

        # Update the online_timeout of the httpd service
        vcs_service_paths = self.find(self.test_ms,
                                        '/deployments',
                                        'vcs-clustered-service',
                                        assert_not_empty=False)
        for path in vcs_service_paths:
            if 'httpd' in path:
                self.execute_cli_update_cmd(self.test_ms,
                                        path,
                                        'online_timeout=45')

        # 1. Create dns-client on MS with search property
        ms_dns_client = self._create_dns_client(
            ms_config_path, "mstest01a", search="{0}".format(ms_search1))

        # 2. Create nameserver1 on the MS with the ip property set to an
        #    IPv4 address and the position property set to 3
        props = "ipaddress={0} position=3".format(ms_n1_ip1)
        self._create_nameserver(
            ms_dns_client, "nameserver_01a", props)

        # 3. Create dns-client on nodeX with the search property
        #    defined with 6 domains
        n1_dns_client = self._create_dns_client(
            n1_config_path, "n1test01a",
            search="{0}".format(n1_search1))

        # 4. Create nameserver1 on nodeX with the ip property set to an
        #    IPv4 address and the position property set to 1
        props = "ipaddress={0} position=1".format(n1_n1_ip1)
        n1_namesrv1 = self._create_nameserver(
            n1_dns_client, "nameserver_01a", props)

        # 5. Create nameserver2 on nodeX with the ip property set to an
        # IPv6 address and the position property set to 3
        props = "ipaddress={0} position=3".format(n1_n2_ip1)
        self._create_nameserver(
            n1_dns_client, "nameserver_01b", props)

        # 6. Create nameserver3 on nodeX with the ip property set to an
        # IPv4 address and the position property set to 2
        props = "ipaddress={0} position=2".format(n1_n3_ip1)
        self._create_nameserver(
            n1_dns_client, "nameserver_01c", props)

        # 7.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 8. Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 9.Check the resolv.conf on the MS:
        # Check that the domain was added to the resolv.conf on the MS
        # Check that the nameserver was added to the resolv.conf on the MS
        rfile = self.get_file_contents(
                    self.test_ms,
                    test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile), 2)
        self.assertEqual("search {0}".format(ms_search1), rfile[0])
        self.assertEqual("nameserver {0}".format(ms_n1_ip1), rfile[1])

        # 10.Check the resolv.conf on nodeX:
        #  Check that the domains added to the resolv.conf on NodeX
        #  in the order they were specified
        #  Check that the nameservers are added to the resolv.conf on NodeX
        # in the order they were specified via the position property
        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 4)
        self.assertEqual(
            "search {0}".format(n1_search_1), rfile_n1[0])
        self.assertEqual("nameserver {0}".format(n1_n1_ip1), rfile_n1[1])
        self.assertEqual("nameserver {0}".format(n1_n3_ip1), rfile_n1[2])
        self.assertEqual("nameserver {0}".format(n1_n2_ip1), rfile_n1[3])

        # 11.Remove nameserver1 from nodeX
        self.execute_cli_remove_cmd(self.test_ms, n1_namesrv1)

        # 12.Remove the search property from the dns-client on the MS
        self._update_dns_client_remove_search_prop(ms_dns_client)

        # 13.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 14. Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 15.Check nameserver1 has been removed from the
        #  list of configured nameservers
        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 3)
        self.assertEqual(
            "search {0}".format(n1_search_1), rfile_n1[0])
        self.assertEqual("nameserver {0}".format(n1_n3_ip1), rfile_n1[1])
        self.assertEqual("nameserver {0}".format(n1_n2_ip1), rfile_n1[2])

        # 16.Check the search line has been removed from resolv.conf
        self._find_line_in_resolv_conf(
            self.test_node1, ms_search1, positive=False)

        # 17.Remove the dns-client on the MS
        self.execute_cli_remove_cmd(self.test_ms, ms_dns_client)

        # 18.Remove dns-client on nodeX
        self.execute_cli_remove_cmd(self.test_ms, n1_dns_client)

        # 19.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 20.Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 21.Check resolv.conf on MS
        self._find_line_in_resolv_conf(
            self.test_ms, ms_search1, positive=False)

        self._find_line_in_resolv_conf(
            self.test_ms, ms_n1_ip1, positive=False)

        # 22.Check resolv.conf on NodeX
        self._find_line_in_resolv_conf(
                    self.test_ms, n1_search_1, positive=False)

        self._find_line_in_resolv_conf(
            self.test_node1, n1_n2_ip1, positive=False)

        self._find_line_in_resolv_conf(
            self.test_node1, n1_n3_ip1, positive=False)

    @attr('all', 'non-revert', 'story72', 'story72_tc05')
    def test_06_p_create_remove_nameserver_ForRemoval(self):
        """
        @tms_id: litpcds_72_tc06
        @tms_requirements_id: LITPCDS-72
        @tms_title: test_06_p_create_remove_nameserver_ForRemoval
        @tms_description: A user is allowed to remove and create a nameserver,
                          in the same plan, even when the maximum number of
                          nameservers has been reached.
        @tms_test_steps:
            @step:      Create dns-client on nodeX with the search property
                        defined with 6 domains.
            @result:    dns-client model item created for nodeX with 6 domains
                        search.
            @step:      Create nameserver1 on nodeX with the ip property set
                        to an IPv4 address and the position property set to 1.
            @result:    nameserver1 model item for nodeX created with IPv4 and
                        position 1.
            @step:      Create nameserver2 on nodeX with the ip property set
                        to an IPv6 address and the position property set to 3.
            @result:    nameserver2 model item for nodeX created with IPv6 and
                        position 3.
            @step:      Create nameserver3 on nodeX with the ip property set
                        to an IPv4 address and the position property set to 2.
            @result:    nameserver3 model item for nodeX created with IPv4 and
                        position 2.
            @step:      Create LITP plan.
            @result:    LITP plan created successfuly.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check the resolv.conf on nodeX domains and nameservers
                        added in position/order specified.
            @result:    resolv.conf on nodeX has domains and nameservers
                        listed in order specified.
            @step:      Remove nameserver1 from nodeX.
            @result:    nameserver1 model item in ForRemoval.
            @step:      Create nameserver4 on nodeX with the ip property set
                        to an IPv4 address and the position property set to 1.
            @result:    nameserver4 model item created successfully with IPv4
                        address and position 1.
            @step:      Create LITP plan.
            @result:    LITP plan created successfully.
            @step:      Run LITP plan.
            @result:    LITP plan completed successfully.
            @step:      Check nameserver1 has been removed from the
                        list of configured nameservers.
            @result:    nameserver1 removed from resolv.conf.
            @step:      Check nameserver4 has been added.
            @result:    nameserver4 added to resolv.conf.
        @tms_test_precondition: N/A
        @tms_execution_type: Automated
        """
        # Get Managed Nodes
        self._get_managed_nodes()

        collection_type = "collection-of-node-config"
        # Find the desired collection on the nodes
        config_path = self.find(
            self.test_ms, "/deployments", collection_type)
        n1_config_path = config_path[0]

        # Backup resolv.conf file
        self.backup_file(
            self.test_ms, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node1, test_constants.RESOLV_CFG_FILE)

        # Test Attributes
        n1_search1 = "d1.com,d2.com,d3.com,d4.com,d5.com,d6.com"
        n1_search_1 = "d1.com d2.com d3.com d4.com d5.com d6.com"
        n1_n1_ip1 = "10.10.10.101"
        n1_n2_ip1 = "0:0:0:0:0:ffff:a0a:a6"
        n1_n3_ip1 = "10.10.10.103"
        n1_n4_ip1 = "10.10.10.104"

        # 1. Create dns-client on nodeX with the search property
        #    defined with 6 domains
        n1_dns_client = self._create_dns_client(
            n1_config_path, "n1test01a",
            search="{0}".format(n1_search1))

        # 2. Create nameserver1 on nodeX with the ip property set to an
        #    IPv4 address and the position property set to 1
        props = "ipaddress={0} position=1".format(n1_n1_ip1)
        n1_namesrv1 = self._create_nameserver(
            n1_dns_client, "nameserver_01a", props)

        # 3. Create nameserver2 on nodeX with the ip property set to an
        # IPv6 address and the position property set to 3
        props = "ipaddress={0} position=3".format(n1_n2_ip1)
        self._create_nameserver(
            n1_dns_client, "nameserver_01b", props)

        # 4. Create nameserver3 on nodeX with the ip property set to an
        # IPv4 address and the position property set to 2
        props = "ipaddress={0} position=2".format(n1_n3_ip1)
        self._create_nameserver(
            n1_dns_client, "nameserver_01c", props)

        # 5. Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 6. Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 7. Check the resolv.conf on nodeX:
        #    Check that the domains added to the resolv.conf on NodeX
        #    in the order they were specified
        #    Check that the nameservers are added to the resolv.conf on NodeX
        #    in the order they were specified via the position property
        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 4)
        self.assertEqual(
            "search {0}".format(n1_search_1), rfile_n1[0])
        self.assertEqual("nameserver {0}".format(n1_n1_ip1), rfile_n1[1])
        self.assertEqual("nameserver {0}".format(n1_n3_ip1), rfile_n1[2])
        self.assertEqual("nameserver {0}".format(n1_n2_ip1), rfile_n1[3])

        # 8. Remove nameserver1 from nodeX
        self.execute_cli_remove_cmd(self.test_ms, n1_namesrv1)

        # 9. Create nameserver1 on nodeX with the ip property set to an
        #    IPv4 address and the position property set to 1
        props = "ipaddress={0} position=1".format(n1_n4_ip1)
        self._create_nameserver(
            n1_dns_client, "nameserver_01d", props)

        # 10. Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 11. Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 12. Check nameserver1 has been removed from the
        #  list of configured nameservers
        #  and that nameserver4 has been added
        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 4)
        self.assertEqual(
            "search {0}".format(n1_search_1), rfile_n1[0])
        self.assertEqual("nameserver {0}".format(n1_n4_ip1), rfile_n1[1])
        self.assertEqual("nameserver {0}".format(n1_n3_ip1), rfile_n1[2])
        self.assertEqual("nameserver {0}".format(n1_n2_ip1), rfile_n1[3])

    # @attr('all', 'non-revert', 'story72', 'story72_t07')
    def obsolete_07_p_create_update_remove_nameserver_stop_plan(self):
        """
        Description:
        Obosoleting.
        This test case is more extensevely and appropriately verified by tests:
        - core.testset_story46.
               test_09_p_create_plan_after_plan_stop_and_updates
        - core.testset_story46.
               test_10_p_create_plan_after_plan_stop_remaining_tasks

        Test that all items under dns-client get set to "Applied" when
        the task is completed i.e. the tasks need to be hanging off
        the relevant model items

        Actions:
        1. Create dns-client on nodeX with the search property
           defined with 6 domains
        2. Create nameserver1 on nodeX with the ip property set to an
           IPv4 address and the position property set to 1
        3. Create nameserver3 on nodeX with the ip property set to an
           IPv4 address and the position property set to 2
        4. Create dns-client on nodeY without the search property
        5. Create nameserver1 on nodeY with the ip property set to an
           IPv4 address and the position property set to 1
        6. Create plan
        7. Run plan
        8. Stop plan
        9. Check the state of items under dns-client get set to "Applied"
           when the task is completed
        10.Run plan
        11.Check the resolv.conf on nodeX:
           Check that the domains added to the resolv.conf on NodeX
           in the order they were specified
           Check that the nameservers are added to the resolv.conf on NodeX
           in the order they were specified via the position property
        12.Create nameserver2 on nodeX with the ip property set to an
           IPv6 address and the position property set to 3
        13.Update nameserver1 on nodeX
        14.Add a nameserver to nodeY
        15.Create plan
        16.Run plan
        17.Stop plan
        18.Check the state of items under dns-client get set to "Applied"
           when the task is completed
        19.Run plan
        20.Remove nameserver1 from nodeX
        21.Remove nameserver1 from nodeY
        22.Create plan
        23.Run plan
        24.Stop plan
        25.Check the state of items under dns-client get set to "Applied"
           when the task is completed
        26.Run plan

        Result:
        All items are in the correct state
        """
        # Get Managed Nodes
        self._get_managed_nodes()

        collection_type = "collection-of-node-config"
        # Find the desired collection on the nodes
        config_path = self.find(
            self.test_ms, "/deployments", collection_type)
        n1_config_path = config_path[0]
        n2_config_path = config_path[1]

        # Backup resolv.conf file
        self.backup_file(
            self.test_ms, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node1, test_constants.RESOLV_CFG_FILE)
        self.backup_file(
            self.test_node2, test_constants.RESOLV_CFG_FILE)

        # Test Attributes
        ms_n1_ip1 = "10.10.10.105"
        ms_n1_ip2 = "10.10.10.106"
        n1_search1 = "d1.com,d2.com,d3.com,d4.com,d5.com,d6.com"
        n1_search_1 = "d1.com d2.com d3.com d4.com d5.com d6.com"
        n1_n1_ip1 = "10.10.10.101"
        n1_n2_ip1 = "0:0:0:0:0:ffff:a0a:a6"
        n1_n3_ip1 = "10.10.10.103"
        n1_n3_ip2 = "10.10.10.104"
        n2_n1_ip1 = "10.10.10.110"
        n2_n2_ip1 = "10.10.10.111"

        # 1. Create dns-client on the ms
        ms_config_path = self.find(self.test_ms, "/ms", collection_type)[0]
        ms_dns_client = self._create_dns_client(
            ms_config_path, "mstest01a")

        # 2. Create nameserver1 on the MS with the ip property set to an
        #    IPv4 address and the position property set to 3
        props = "ipaddress={0} position=1".format(ms_n1_ip1)
        ms_namesrv1 = self._create_nameserver(
            ms_dns_client, "nameserver_01a", props)

        # 3. Create dns-client on nodeX with the search property
        #    defined with 6 domains
        n1_dns_client = self._create_dns_client(
            n1_config_path, "n1test01a",
            search="{0}".format(n1_search1))

        # 4. Create nameserver1 on nodeX with the ip property set to an
        #    IPv4 address and the position property set to 1
        props = "ipaddress={0} position=1".format(n1_n1_ip1)
        n1_namesrv1 = self._create_nameserver(
            n1_dns_client, "nameserver_01a", props)

        # 5. Create nameserver3 on nodeX with the ip property set to an
        # IPv4 address and the position property set to 2
        props = "ipaddress={0} position=3".format(n1_n3_ip1)
        n1_namesrv3 = self._create_nameserver(
            n1_dns_client, "nameserver_01c", props)

        # 6. Create dns-client on nodeY without the search property
        n2_dns_client = self._create_dns_client(
            n2_config_path, "n2test01a")

        # 7. Create nameserver1 on nodeY with the ip property set to an
        #    IPv4 address and the position property set to 1
        props = "ipaddress={0} position=1".format(n2_n1_ip1)
        n2_namesrv1 = self._create_nameserver(
            n2_dns_client, "nameserver_01a", props)

        # 8. Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 9. Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait until phase 2 task is running to stop the plan
        self.assertTrue(self.wait_for_task_state(
            self.test_ms, 'Create DNS client configuration on node "ms1"',
            test_constants.PLAN_TASKS_RUNNING, ignore_variables=False))

        # 10.Stop plan
        self.execute_cli_stopplan_cmd(self.test_ms)

        # Wait for plan to stop
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_STOPPED))

        # 11.Check the state of items under dns-client on ms
        #    get set to "Applied"
        #    when the ms task is completed and check other items are still
        #    in state, "Initial"
        state = self.get_item_state(self.test_ms, ms_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, ms_namesrv1)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_dns_client)
        self.assertEqual(state, "Initial")

        state = self.get_item_state(self.test_ms, n1_namesrv1)
        self.assertEqual(state, "Initial")

        state = self.get_item_state(self.test_ms, n1_namesrv3)
        self.assertEqual(state, "Initial")

        state = self.get_item_state(self.test_ms, n2_dns_client)
        self.assertEqual(state, "Initial")

        state = self.get_item_state(self.test_ms, n2_namesrv1)
        self.assertEqual(state, "Initial")

        # 12.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 13.Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait until node2 task is running before stoppimng the plan
        self.assertTrue(self.wait_for_task_state(
            self.test_ms, "Create DNS client configuration on node \"node2\"",
            test_constants.PLAN_TASKS_RUNNING, ignore_variables=False))

        # 14.Stop plan
        self.execute_cli_stopplan_cmd(self.test_ms)

        # Wait for plan to stop
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_STOPPED))

        # 15.Check the state of items under node2 dns-client
        #    are set to "Applied"
        #    when the node2 task has completed
        state = self.get_item_state(self.test_ms, ms_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, ms_namesrv1)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_dns_client)
        self.assertEqual(state, "Initial")

        state = self.get_item_state(self.test_ms, n1_namesrv1)
        self.assertEqual(state, "Initial")

        state = self.get_item_state(self.test_ms, n1_namesrv3)
        self.assertEqual(state, "Initial")

        state = self.get_item_state(self.test_ms, n2_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_namesrv1)
        self.assertEqual(state, "Applied")

        # 16.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 17.Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 18.Check the state of items under dns-client get set to "Applied"
        #    when the task is completed
        state = self.get_item_state(self.test_ms, ms_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, ms_namesrv1)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_namesrv1)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_namesrv3)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_namesrv1)
        self.assertEqual(state, "Applied")

        # 19.Check the resolv.conf on the nodes:
        #    Check that the domains added to the resolv.conf on NodeX
        #    in the order they were specified
        #    Check that the nameservers are added to the resolv.conf on NodeX
        #    in the order they were specified via the position property
        rfile_ms = self.get_file_contents(
                self.test_ms,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_ms), 1)
        self.assertEqual("nameserver {0}".format(ms_n1_ip1), rfile_ms[0])

        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 3)
        self.assertEqual(
            "search {0}".format(n1_search_1), rfile_n1[0])
        self.assertEqual("nameserver {0}".format(n1_n1_ip1), rfile_n1[1])
        self.assertEqual("nameserver {0}".format(n1_n3_ip1), rfile_n1[2])

        rfile_n2 = self.get_file_contents(
                self.test_node2,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n2), 1)
        self.assertEqual("nameserver {0}".format(n2_n1_ip1), rfile_n2[0])

        # 20.Update the ip address of the nameserver on the ms
        self._update_nameserver_props(
            ms_namesrv1, "ipaddress={0}".format(ms_n1_ip2))

        # 21.Add nameserver2 on nodeX with the ip property set to an
        # IPv4 address and the position property set to 2
        props = "ipaddress={0} position=2".format(n1_n2_ip1)
        n1_namesrv2 = self._create_nameserver(
            n1_dns_client, "nameserver_01b", props)

        # 22.Update nameserver3 on nodeX
        self._update_nameserver_props(
            n1_namesrv3, "ipaddress={0}".format(n1_n3_ip2))

        # 23.Add a nameserver to nodeY
        props = "ipaddress={0} position=2".format(n2_n2_ip1)
        n2_namesrv2 = self._create_nameserver(
            n2_dns_client, "nameserver_01b", props)

        # 24.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 25.Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait until node2 task is running before stoppimng the plan
        self.assertTrue(self.wait_for_task_state(
            self.test_ms, "Update DNS client configuration on node \"node2\"",
            test_constants.PLAN_TASKS_RUNNING, ignore_variables=False))

        # 26.Stop plan
        self.execute_cli_stopplan_cmd(self.test_ms)

        # Wait for plan to stop
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_STOPPED))

        # 27.Check the state of items under node2 dns-client
        #    are set to "Applied"
        #    when the node2 task has completed
        state = self.get_item_state(self.test_ms, ms_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, ms_namesrv1)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_namesrv1)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_namesrv2)
        self.assertEqual(state, "Initial")

        state = self.get_item_state(self.test_ms, n1_namesrv3)
        self.assertEqual(state, "Updated")

        state = self.get_item_state(self.test_ms, n2_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_namesrv1)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_namesrv2)
        self.assertEqual(state, "Applied")

        # 28.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 29.Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        # 30.Check the state of items under dns-client get set to "Applied"
        #    when the task is completed
        state = self.get_item_state(self.test_ms, n1_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_namesrv1)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_namesrv2)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n1_namesrv3)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_namesrv1)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_namesrv2)
        self.assertEqual(state, "Applied")

        # 31.Check the resolv.conf on nodeX:
        #    Check that the domains added to the resolv.conf on NodeX
        #    in the order they were specified
        #    Check that the nameservers are added to the resolv.conf on NodeX
        #    in the order they were specified via the position property
        rfile_ms = self.get_file_contents(
                self.test_ms,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_ms), 1)
        self.assertEqual("nameserver {0}".format(ms_n1_ip2), rfile_ms[0])

        rfile_n1 = self.get_file_contents(
                self.test_node1,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n1), 4)
        self.assertEqual(
            "search {0}".format(n1_search_1), rfile_n1[0])
        self.assertEqual("nameserver {0}".format(n1_n1_ip1), rfile_n1[1])
        self.assertEqual("nameserver {0}".format(n1_n2_ip1), rfile_n1[2])
        self.assertEqual("nameserver {0}".format(n1_n3_ip2), rfile_n1[3])

        rfile_n2 = self.get_file_contents(
                self.test_node2,
                test_constants.RESOLV_CFG_FILE, su_root=True)
        self.assertEqual(len(rfile_n2), 2)
        self.assertEqual("nameserver {0}".format(n2_n1_ip1), rfile_n2[0])
        self.assertEqual("nameserver {0}".format(n2_n2_ip1), rfile_n2[1])

        # 32.Remove dns-client from nodeX
        self.execute_cli_remove_cmd(self.test_ms, n1_dns_client)

        # 33.Remove nameserver1 from nodeY
        self.execute_cli_remove_cmd(self.test_ms, n2_namesrv1)

        # 34.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        self.execute_cli_showplan_cmd(self.test_ms)

        # 35.Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait until node2 task is running before stopping the plan
        self.assertTrue(self.wait_for_task_state(
            self.test_ms, "Update DNS client configuration on node \"node2\"",
            test_constants.PLAN_TASKS_RUNNING, ignore_variables=False))

        # 36.Stop plan
        self.execute_cli_stopplan_cmd(self.test_ms)

        # Wait for plan to stop
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_STOPPED))

        # 37.Check the state of items under dns-client have been removed"
        #    when the task is completed
        state = self.get_item_state(self.test_ms, n1_dns_client)
        self.assertEqual(state, "ForRemoval")

        state = self.get_item_state(self.test_ms, n1_namesrv1)
        self.assertEqual(state, "ForRemoval")

        state = self.get_item_state(self.test_ms, n1_namesrv2)
        self.assertEqual(state, "ForRemoval")

        state = self.get_item_state(self.test_ms, n1_namesrv3)
        self.assertEqual(state, "ForRemoval")

        state = self.get_item_state(self.test_ms, n2_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_namesrv1)
        self.assertEqual(state, "ForRemoval (deployment of properties "
                                "indeterminable)")

        state = self.get_item_state(self.test_ms, n2_namesrv2)
        self.assertEqual(state, "Applied")

        # 38.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 39.Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        self.assertTrue(self.wait_for_task_state(
            self.test_ms, "Remove DNS client configuration on node \"node1\"",
            test_constants.PLAN_TASKS_RUNNING, ignore_variables=False))

        # 40.Stop plan
        self.execute_cli_stopplan_cmd(self.test_ms)

        # Wait for plan to stop
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_STOPPED))

        state = self.get_item_state(self.test_ms, n1_dns_client)
        self.assertEqual(state, "ForRemoval (deployment of properties "
                                "indeterminable)")

        state = self.get_item_state(self.test_ms, n1_namesrv1)
        self.assertEqual(state, "ForRemoval (deployment of properties "
                                "indeterminable)")

        state = self.get_item_state(self.test_ms, n1_namesrv2)
        self.assertEqual(state, "ForRemoval (deployment of properties "
                                "indeterminable)")

        state = self.get_item_state(self.test_ms, n1_namesrv3)
        self.assertEqual(state, "ForRemoval (deployment of properties "
                                "indeterminable)")

        state = self.get_item_state(self.test_ms, n2_dns_client)
        self.assertEqual(state, "Applied")

        state = self.get_item_state(self.test_ms, n2_namesrv1)
        self.assertEqual(state, "ForRemoval")

        state = self.get_item_state(self.test_ms, n2_namesrv2)
        self.assertEqual(state, "Applied")

        # 41.Create plan
        self.execute_cli_createplan_cmd(self.test_ms)

        # 42.Run plan
        self.execute_cli_runplan_cmd(self.test_ms)

        # Wait for plan to complete
        self.assertTrue(self.wait_for_plan_state(
            self.test_ms, test_constants.PLAN_COMPLETE))

        self.execute_cli_show_cmd(
            self.test_ms, n2_namesrv1, expect_positive=False)
