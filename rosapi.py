import logging
import re
import telnetlib
import time


def untag(text):
    return text.replace("\x1b[m", "").replace("\x1b[32m", "").replace("\x1b[1m", "").replace("\x1b[31;1m", "").replace("\x1b[K", "").replace("\x1b[36m", "")

class TelnetCtrl(object):
    """Telnet Control Class

    """

    def __init__(self, host, username="admin", password="", finish=">"):
        self.logger = logging.getLogger("TelnetCtrl")
        self.login(host, username, password, finish)

    def login(self, host, username="admin", password="", finish=">"):
        """Connect to the telnet server

        Arguments:
            host {str} -- the ip for the telnet server
            finish {str} -- the symbol to connnect success
            username {str} -- username to login
            password {str} -- password to login   
        """
        self.tn = telnetlib.Telnet(host, 23)
        if username:
            self.tn.read_until("Login:", timeout=100)
            self.write(str(username))
            self.tn.read_until("Password:", timeout=100)
            self.write(str(password))
        self.tn.read_until(str(finish))
        
        self.logger.debug("Telnet connected")

    def write(self, command):
        """Send command to telnet server
        
        Arguments:
            command {str} -- the command to send.
        """
        self.logger.debug("Send telnet command {}".format(command))
        self.tn.write(command + "\r")

    def read_until(self, match, timeout=10):
        """telnet read until match
        
        Arguments:
            match {str} -- match string
        
        Keyword Arguments:
            timeout {int} -- timeout (default: {10})
        """

        return self.tn.read_until(match, timeout)
    

class RosError(RuntimeError):
    """ Ros Error Class"""

    pass


class ErrorHandler(object):
    """Deal with Exception
    
    """

    def __init__(self):
        self.logger = logging.getLogger("ErrorHandler")
    
    def check_result(self, where, result):
        failure = re.findall("\r\n\r(.*)\n\r", result)
        if failure:
            error_msg = "{} Failed, {}".format(where, failure[0])
            raise RosError(error_msg)
        else:
            self.logger.info("{} Success".format(where))
            

class AddressPool(ErrorHandler):
    """IP Pool
    
    """
    def __init__(self):
        self.api = None
        self.logger = logging.getLogger("AddressPool")
    
    def get_address_pool(self):
        """get the current ip address pool 
        
        Returns:
            list -- pool list each item includes pool name and ranges, e.g: [('pppoe', '192.168.100.201-192.168.100.250')]
        """

        cmd = "/ip pool print detail"
        self.api.write(cmd)
        time.sleep(1)
        rc = untag(self.api.tn.read_very_eager()) 
        pool_list =  re.findall("name=\"(.*)\" ranges=(.*) ", rc)
        pool_dict = {}
        for pool in pool_list:
            pool_dict[pool[0]] = pool[1]
        return pool_list  
    
    def add_address_pool(self, name, ranges):
        """add address pool
        
        Arguments:
            name {str} -- the pool name
            ranges {str} -- the ranges for IP address, e.g: 192.168.2.1-192.168.2.100
        """
        cmd = "/ip pool add name={} ranges={}".format(name, ranges)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Add Pool", rc)
    
    def remove_address_pool(self, numbers):
        """remove address pool
        
        Arguments:
            numbers {str} -- the number, starting from 0
        """
        cmd = "/ip pool remove numbers={}".format(numbers)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Remove Address Pool", rc)
    
    def set_address_pool_name(self, numbers, new_name):
        """set the new name for the pool exits
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_name {str} -- the new name to set
        """

        cmd = "/ip pool set numbers={} name={}".format(numbers, new_name)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set Pool Name", rc)
    
    def set_address_pool_ranges(self, numbers, new_ranges):
        """set the new ranges for the pool exits
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_ranges {str} -- the new ranges to set
        """

        cmd = "/ip pool set numbers={} ranges={}".format(numbers, new_ranges)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set Pool Ranges", rc)


class DHCPServer(ErrorHandler):
    """DHCP Server Api
    
    """
    def __init__(self):
        self.api = None
    
    def add_dhcp_server(self, name, interface, address_pool, lease_time="00:10:00", enabled=True):
        """add dhcp server
        
        Arguments:
            name {str} -- dhcp server name
            interface {str} -- interface name
            address_pool {str} -- address pool name
        
        Keyword Arguments:
            lease_time {str} -- lease time (default: {"00:10:00"})
            enabled {bool} -- enable or disable (default: {True})
        """

        if enabled:
            enabled = "no"
        else:
            enabled = "yes"
        cmd = "/ip dhcp-server add name={} interface={} address-pool={} lease-time={} disabled={}".format(name, interface, address_pool, lease_time, enabled)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Add DHCP Server", rc)
    
    def remove_dhcp_server(self, numbers):
        """remove one dhcp server
        
        Arguments:
            numbers {str} -- the number, starting from 0
        """

        cmd = "/ip dhcp-server remove numbers={}".format(numbers)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Remove DHCP Server", rc)
    
    def set_dhcp_server_status(self, numbers, enabled=True):
        """enable the special dhcp server
        
        Arguments:
            numbers {str} -- the number, starting from 0
            enabled {bool} -- the dhcp name
        
        Keyword Arguments:
            enabled {bool} -- [description] (default: {True})
        """

        if enabled:
            status = "enable"
        else:
            status = "disable"
        cmd = "/ip dhcp-server {} numbers={}".format(status, numbers)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set DHCP Server Status", rc)
    
    def set_dhcp_server_address_pool(self, numbers, address_pool):
        """set the address pool for the special dhcp server
        
        Arguments:
            numbers {str} -- the number, starting from 0
            address_pool {str} -- the address pool name
        """
        cmd = "/ip dhcp-server set numbers={} address-pool={}".format(numbers, address_pool)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set DHCP Servel Address Pool", rc)
    
    def set_dhcp_server_lease_time(self, numbers, lease_time):
        """set the address pool for the special dhcp server
        
        Arguments:
            numbers {str} -- the number, starting from 0
            lease_time {str} -- the lease time to set, e.g: 00:10:00
        """
        cmd = "/ip dhcp-server set numbers={} lease-time={}".format(numbers, lease_time)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set DHCP Lease Time", rc)
    
    def get_dhcp_server_client(self):
        """get the client info, including ip, mac, server and hostname
        
        Returns:
            list -- client list, e.g: [{'ip': '192.168.8.191', 'mac': '48:4D:7E:B2:A7:1C', 'hostname': 'PC-FX008685', 'server': 'test'}]
        """

        cmd = "/ip dhcp-server lease print detail"
        self.api.write(cmd)
        time.sleep(0.5)
        rc = untag(self.api.tn.read_very_eager())
        client_result =  re.findall("address=(.*) mac-address=(.*) (?:[\s\S]*)server=(.*) (?:[\s\S]*)host-name=\"(.*)\" ", rc)
        client_list = []
        for client in client_result:
            client_dict = {}
            client_dict["ip"] = client[0]
            client_dict["mac"] = client[1]
            client_dict["server"] = client[2]
            client_dict["hostname"] = client[3]
            client_list.append(client_dict)
        return client_list
    
    def get_dhcp_server_network(self):
        """get DHCP server network list
        
        Returns:
            list -- network list, including num, address, gateway, netmask and dns_server
        """

        cmd = "/ip dhcp-server network print detail"
        self.api.write(cmd)
        time.sleep(0.5)
        rc = untag(self.api.tn.read_very_eager())
        network_result = re.findall("(\d) address=(.*?) gateway=(.*?) netmask=(.*?) (?:[\s\S]*)dns-server=(.*?) ", rc)
        network_list = []
        for network in network_result:
            network_dict = {}
            network_dict["num"] = network[0]
            network_dict["address"] = network[1]
            network_dict["gateway"] = network[2]
            network_dict["netmask"] = network[3]
            network_dict["dns_server"] = network[4]
            network_list.append(network_dict)
        return network_list
    
    def add_dhcp_server_network(self, address, gateway, netmask, dns_server):
        """add DHCP server network
        
        Arguments:
            address {st} -- ip address with netmask, e.g: 10.0.0.1/8
            gateway {str} -- gateway
            netmask {str} -- netmask
            dns_server {str} -- dns server
        """

        cmd = "/ip dhcp-server network add address={} gateway={} netmask={} dns-server={}".format(address, gateway, netmask, dns_server)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Add DHCP Server Network", rc)
    
    def get_dhcp_server_network_number(self, address):
        """get the number of DHCP server network
        
        Arguments:
            address {str} -- ip address with netmask, e.g: 10.0.0.1/8
        
        Raises:
            RosError -- netwrok not found
        
        Returns:
            int -- the number for the special network
        """

        network_list = self.get_dhcp_server_network()
        num = -1
        for network in network_list:
            if network["address"] == address:
                num = network["num"]
        if num == -1:
            errmsg = "No Matched DHCP Server Network Number for Address{}".format(address)
            raise RosError(errmsg)
        else:
            return num
    
    def remove_dhcp_server_network(self, numbers):
        """remove the DHCP server network
        
        Arguments:
            numbers {str} -- the number, starting from 0
        """

        cmd = "/ip dhcp-server network remove numbers={}".format(numbers)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Remove DHCP Server Network", rc)
    
    def set_dhcp_server_network(self, numbers, new_address, new_gateway, new_netmask, new_dns_server):
        """set DHCP server network
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_address {str} -- new ip address with netmask, e.g: 10.0.0.1/8
            new_gateway {str} -- new gateway
            new_netmask {str} -- new netmask
            new_dns_server {str} -- new dns server
        """

        cmd = "/ip dhcp-server network set numbers={} address={} gateway={} netmask={} dns-server={}".format(numbers, new_address, new_gateway, new_netmask, new_dns_server)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set DHCP Server Network", rc)
    
    def set_dhcp_server_network_address(self, numbers, new_address):
        """set the address for the special DHCP server network
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_address {str} -- new ip address with netmask, e.g: 10.0.0.1/8
        """

        cmd = "/ip dhcp-server network set numbers={} address={}".format(numbers, new_address)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set DHCP Server Network Address", rc)
    
    def set_dhcp_server_network_gateway(self, numbers, new_gateway):
        """set the gateway for the special DHCP server
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_gateway {str} -- new gateway
        """

        cmd = "/ip dhcp-server network set numbers={} gateway={}".format(numbers, new_gateway)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set DHCP Server Network Gateway", rc)
    
    def set_dhcp_server_network_netmask(self, numbers, new_netmask):
        """set the netmask for the special DHCP server network
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_netmask {str} -- new netmask
        """

        cmd = "/ip dhcp-server network set numbers={} netmask={}".format(numbers, new_netmask)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set DHCP Server Network Netmask", rc)
    
    def set_dhcp_server_network_dns_server(self, numbers, new_dns_server):
        """set the dns server for the special DHCP server network
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_dns_server {str} -- new dns server
        """

        cmd = "/ip dhcp-server network set numbers={} dns-server={}".format(numbers, new_dns_server)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set DHCP Server Network DNS Server", rc)


class PPPoEServer(ErrorHandler):
    """PPPoE Server Api
    
    """
    
    def __init__(self):
        self.api = None
        self.logger = logging.getLogger("PPPoEServer")
    
    def get_ppp_profile_name(self):
        """get ppp profile list
        
        Returns:
            list -- ppp profile list
        """

        cmd = "/ppp profile print detail"
        self.api.write(cmd)
        time.sleep(0.5)
        rc = untag(self.api.tn.read_very_eager())
        profile_list = re.findall("name=\"(.*)\"", rc)
        return profile_list
    
    def get_pppoe_server(self):
        """get the pppoe server list
        
        Returns:
            list -- pppoe server list
        """

        cmd = "/interface pppoe-server server print detail"
        self.api.write(cmd)
        time.sleep(0.5)
        rc = untag(self.api.tn.read_very_eager())
        pppoe_server_result = re.findall("(\d+) (.*?) (?:[\s\S]*?)service-name=\"(.*)\" interface=(.*) max-mtu=(.*) max-mru=(.*) (?:[\s\S]*?)authentication=(.*?) (?:[\s\S]*?)default-profile=(.*) ", rc)
        pppoe_server_list = []
        for item in pppoe_server_result:
            pppoe_server = {}
            pppoe_server["num"] = item[0]
            if item[1] == "X":
                pppoe_server["status"] = "disabled"
            elif item[1] == "I":
                pppoe_server["status"] = "invalid"
            elif item[1] == "XI":
                pppoe_server["status"] = "disabled and invalid"
            else:
                pppoe_server["status"] = "enabled"
            pppoe_server["service_name"] = item[2]
            pppoe_server["interface"] = item[3]
            pppoe_server["max_mtu"] = item[4]
            pppoe_server["max_mru"] = item[5]
            pppoe_server["authentication"] = item[6]
            pppoe_server["default_profile"] = item[7]
            pppoe_server_list.append(pppoe_server)
        return pppoe_server_list
    
    def get_ppp_profile(self):
        """get the ppp profile list
        
        Returns:
            list -- the ppp profile list
        """

        cmd = "/ppp profile print without-paging"
        self.api.write(cmd)
        time.sleep(0.5)
        rc = untag(self.api.tn.read_very_eager())
        profile_result = re.findall("name=\"(.*)\" local-address=(.*) remote-address=(.*?) (?:[\s\S]*?)use-encryption=(.*?) (?:[\s\S]*?)dns-server=(.*?) ", rc)
        profile_list = []
        for item in profile_result:
            profile = {}
            profile["name"] = item[0]
            profile["local_address"] = item[1]
            profile["remote_address"] = item[2]
            profile["use_encryption"] = item[3]
            profile["dns_server"] = item[4]
            profile_list.append(profile)
        return profile_list
    
    def get_pppoe_server_number(self, service_name):
        """get the number of the special pppoe service name
        
        Arguments:
            service_name {str} -- the pppoe service name
        
        Raises:
            RosError -- no matched pppoe server number
        
        Returns:
            str -- pppoe server number
        """

        pppoe_server_list = self.get_pppoe_server()
        num = -1
        for pppoe_server in pppoe_server_list:
            if pppoe_server["service_name"] == service_name:
                num = pppoe_server["num"]
        if num == -1:
            errmsg = "No Matched PPPoE Server Number for Service Name {}".format(service_name)
            raise RosError(errmsg)
        else:
            return num
    
    def add_pppoe_server(self, service_name, interface, default_profile, max_mtu="auto", max_mru="auto", enabled=True):
        """add pppoe server
        
        Arguments:
            service_name {str} -- service name
            interface {str} -- interface name
            default_profile {str} -- profile name
        
        Keyword Arguments:
            max_mtu {str} -- max MTU (default: {auto})
            max_mru {str} -- max MRU (default: {auto})
            enabled {bool} -- enable the pppoe server (default: {True})
        """ 

        if enabled:
            enabled = "yes"
        else:enabled = "no"
        cmd = "/ interface pppoe-server server add service-name={} interface={} default-profile={} max-mtu={} max-mru={} disabled={}".format(service_name, interface, default_profile, max_mtu, max_mru, enabled)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Add PPPoE Server", rc)
    
    def remove_pppoe_server(self, numbers):
        """remove one pppoe server
        
        Arguments:
            numbers {str} -- the number, starting from 0
        """

        cmd = "/interface pppoe-server server remove numbers={}".format(numbers)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Remove PPPoE Server", rc)
    
    def set_pppoe_server_status(self, numbers, enabled=True):
        """set the status of the pppoe server, including enabled or disabled
        
        Arguments:
            numbers {str} -- the number, starting from 0
        
        Keyword Arguments:
            enabled {bool} -- True for enabled and False for disabled (default: {True})
        """
        
        if enabled:
            status = "enable"
        else:
            status = "disable"
        cmd = "/interface pppoe-server server {} numbers={}".format(status, numbers)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set PPPoE Server Status", rc)
    
    def set_pppoe_server_name(self, numbers, new_service_name):
        """set the new service name for the special pppoe server
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_service_name {str} -- the new server name
        """
        
        cmd = "/interface pppoe-server server set numbers={} service-name={}".format(numbers, new_service_name)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set PPPoE Server Service Name", rc)
    
    def set_pppoe_server_auth(self, numbers, authentication="pap,chap,mschap1,mschap2"):
        """set the authentication for the special pppoe server
        
        Arguments:
            numbers {str} -- the number, starting from 0
        
        Keyword Arguments:
            authentication {str} -- authentication, split with "," e.g: pap,chap     (default: {"pap,chap,mschap1,mschap2"})
        """ 

        cmd = "/interface pppoe-server server set numbers={} authentication={}".format(numbers, authentication.lower())
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set PPPoE Server Authentication", rc)
    
    def set_pppoe_server_max_mtu(self, numbers, max_mtu="auto"):
        """set the max MTU for the special pppoe server
        
        Arguments:
            numbers {str} -- the number, starting from 0
        
        Keyword Arguments:
            max_mtu {str} -- max MTU to set (default: {"auto"})
        """

        cmd = "/interface pppoe-server server set numbers={} max-mtu={}".format(numbers, max_mtu)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set PPPoE Server Max MTU", rc)
    
    def set_pppoe_server_max_mru(self, numbers, max_mru="auto"):
        """set the max MRU for the special pppoe server
        
        Arguments:
            numbers {str} -- the number, starting from 0
        
        Keyword Arguments:
            max_mru {str} -- max MRU to set (default: {"auto"})
        """

        cmd = "/interface pppoe-server server set numbers={} max-mru={}".format(numbers, max_mru)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set PPPoE Server Max MRU", rc)
    
    def set_pppoe_server_dns(self, numbers, new_dns):
        """set the pppoe server dns
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_dns {str} -- the new dns to set
        """
 
        servers = self.get_pppoe_server()
        for server in servers:
            if server["num"] == numbers:
                service_name = server["service_name"]
        profile_name = None
        for server in servers:
            if server["service_name"] == service_name:
                profile_name = server["default_profile"]
        if profile_name:
            cmd = "/ppp profile set numbers={} dns-server={}".format(profile_name, new_dns)
            self.api.write(cmd)
            time.sleep(0.5)
            rc = self.api.tn.read_very_eager()
            self.check_result("Set PPPoE Server DNS", rc)
        else:
            errmsg = "No Matched PPPoE Server Profile for Service Name {}".format(service_name)
            raise RosError(errmsg)
    
    def get_ppp_secret(self):
        """get PPP secret
        
        Returns:
            list -- the secret list
        """

        cmd = "/ppp secret print detail"
        self.api.write(cmd)
        time.sleep(0.5)
        rc = untag(self.api.tn.read_very_eager())
        secret_result = re.findall("(\d+) (.*?) name=\"(.*?)\" service=(.*?) (?:[\s\S]*?)password=\"(.*)\"(?:[\s\S]*?)profile=(.*?) ", rc)
        secret_list = []
        for item in secret_result:
            secret = {}
            secret["num"] = item[0]
            if item[1] == "X":
                secret["status"] = "disabled"
            else:
                secret["status"] = "enabled"
            secret["name"] = item[2]
            secret["service"] = item[3]
            secret["password"] = item[4]
            secret["profile"] = item[5]
            secret_list.append(secret)
        return secret_list
    
    def add_ppp_secret(self, secret_name, service_name, profile_name, password, enabled=True):
        """add the secret for the pppoe server
        
        Arguments:
            secret_name {str} -- the username to dial
            service_name {str} -- the pppoe server name
            profile_name {str} -- the profile name
            password {str} -- the password to dial

        Keyword Arguments:
            enabled {bool} -- true for enabled and flase for disabled (default: {True})
        """
        if enabled:
            enabled = "no"
        else:
            enabled = "yes"
        cmd = "/ppp secret add name={} service={} profile={} password={} disabled={}".format(secret_name, service_name, profile_name, password, enabled)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Add PPPoE Server Secret", rc)
    
    def remove_ppp_secret(self, numbers):
        """remove the ppp secret
        
        Arguments:
            numbers {str} -- the number, starting from 0
        """

        cmd = "/ppp secret remove numbers={}".format(numbers)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Remove PPPoE Server Secret", rc)
    
    def get_ppp_secret_number(self, secret_name):
        """get the number of the special ppp secret name
        
        Arguments:
            secret_name {str} -- the ppp secret name
        
        Raises:
            RosError -- no matched pppoe server number
        
        Returns:
            str -- ppp secret number
        """

        secret_list = self.get_ppp_secret()
        num = -1
        for secret in secret_list:
            if secret["name"] == secret_name:
                num = secret["num"]
        if num == -1:
            errmsg = "No Matched PPP Secret Number for Secret Name {}".format(secret_name)
            raise RosError(errmsg)
        else:
            return num
    
    def set_ppp_secret_name(self, numbers, new_name): 
        """set PPP secret name
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_name {str} -- the new name to set
        """

        cmd = "/ppp secret set numbers={} name={}".format(numbers, new_name)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set PPP Secret Name", rc)

    def set_ppp_secret_password(self, numbers, new_password):
        """set PPP secret password
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_password {str} -- the new password
        """

        cmd = "/ppp secret set numbers={} password={}".format(numbers, new_password)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set PPP Secret Password", rc)
    
    def set_ppp_secret_status(self, numbers, enabled=True):
        """set PPP secret status
        
        Arguments:
            numbers {str} -- the number, starting from 0
        
        Keyword Arguments:
            enabled {bool} -- true for enabled and flase for disabled (default: {True})
        """

        if enabled:
            enabled = "no"
        else:
            enabled = "yes"
        cmd = "/ppp secret set numbers={} disabled={}".format(numbers, enabled)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set PPP Secret Status", rc)
    
    def set_ppp_secret_profile(self, numbers, new_profile_name):
        """set PPP secret profile
        
        Arguments:
            numbers {str} -- the number, starting from 0
            new_profile_name {str} -- the new profile name
        """

        cmd = "/ppp secret set numbers={} profile={}".format(numbers, new_profile_name)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set PPP Secret Profile", rc)


class NTPServer(ErrorHandler):
    """NTP Server Api
    
    """
    
    def __init__(self):
        self.api = None
        self.logger = logging.getLogger("NTPServer")
    
    def set_ntp_clock(self, date, time, time_zone="Asia/Shanghai"):
        """set the NTP server clock, including date, time
        
        Arguments:
            date {str} -- formatted date, month/day/year, e.g: Jan/01/2018
            time {str} -- formatted time, hour:min:second, e.g: 08:00:00
        
        Keyword Arguments:
            time_zone {str} -- the time zone (default: {"Asia/Shanghai"})
        """

        cmd = "/system clock set date={} time={} time-zone-autodetect=no time-zone-name={}".format(date, time, time_zone)
        self.api.write(cmd)
        time.sleep(0.5)
        rc = self.api.tn.read_very_eager()
        self.check_result("Set NTP Clock", rc)


class RosApi(AddressPool, DHCPServer, PPPoEServer):
    """MikroTik RouterOS Api

    """

    def __init__(self, ip, username="admin", password=""):
        self.api = TelnetCtrl(ip, username, password)
        self.logger = logging.getLogger("RosApi")
