"""UniFi Network client for UniFi Traffic Rules."""
import aiohttp
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class UnifiClient:
    """Client to interact with UniFi Network API."""

    def __init__(self, host, username, password):
        """Initialize the client."""
        self._host = host
        self._username = username
        self._password = password
        self._session = None
        self._cookies = None
        self._csrf_token = None
        self._site_id = None
        self._is_udm = False

    def _get_api_url(self, endpoint):
        """Construct the correct API URL based on device type."""
        base_url = f"https://{self._host}"
        if self._is_udm:
            return f"{base_url}/proxy/network/{endpoint.lstrip('/')}"
        return f"{base_url}/{endpoint.lstrip('/')}"

    async def _authenticate(self):
        """Authenticate with the UniFi Network device."""
        auth_urls = [
            f"https://{self._host}/api/login",
            f"https://{self._host}/api/auth/login"
        ]
        
        for auth_url in auth_urls:
            auth_data = {"username": self._username, "password": self._password}
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(auth_url, json=auth_data, ssl=False) as resp:
                        if resp.status == 200:
                            self._cookies = resp.cookies
                            self._csrf_token = resp.headers.get('X-CSRF-Token')
                            self._is_udm = auth_url.endswith('/api/auth/login')
                            _LOGGER.info(f"Successfully authenticated with UniFi Network device (UDM: {self._is_udm})")
                            return
                except aiohttp.ClientError:
                    continue
        
        raise Exception("Authentication failed for all endpoints")
                
    async def get_console_name(self):
        """Fetch the UniFi Console name for the component name."""
        if not self._cookies or not self._csrf_token:
            await self._authenticate()
        if not self._site_id:
            await self._get_site_info()

        #url = f"https://{self._host}/proxy/network/api/s/{self._site_id}/stat/sysinfo"
        url = self._get_api_url(f"api/s/{self._site_id}/stat/sysinfo")
        
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            headers = {"X-Csrf-Token": self._csrf_token}
            async with session.get(url, headers=headers, ssl=False) as resp:
                if resp.status == 200:
                    sysinfo = await resp.json()
                    return sysinfo.get('data', [{}])[0].get('name', 'UniFi Console')
                else:
                    _LOGGER.error(f"Failed to fetch console name. Status: {resp.status}")
                    return 'UniFi Console'

    async def _get_site_info(self):
        """Get the site information."""
        #url = f"https://{self._host}/proxy/network/api/self/sites"
        url = self._get_api_url("api/self/sites")

        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            headers = {"X-Csrf-Token": self._csrf_token}
            async with session.get(url, headers=headers, ssl=False) as resp:
                if resp.status == 200:
                    sites = await resp.json()
                    if sites and 'data' in sites and sites['data']:
                        self._site_id = sites['data'][0]['name']
                        _LOGGER.info(f"Found site ID: {self._site_id}")
                    else:
                        raise Exception("No site information found")
                else:
                    raise Exception(f"Failed to fetch site information. Status: {resp.status}")

    async def get_traffic_rules(self):
        """Fetch all traffic rules."""
        if not self._cookies or not self._csrf_token:
            await self._authenticate()
        if not self._site_id:
            await self._get_site_info()

        #url = f"https://{self._host}/proxy/network/v2/api/site/{self._site_id}/trafficrules"
        url = self._get_api_url(f"v2/api/site/{self._site_id}/trafficrules")
        
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            headers = {"X-Csrf-Token": self._csrf_token}
            async with session.get(url, headers=headers, ssl=False) as resp:
                if resp.status == 200:
                    rules = await resp.json()
                    return {"traffic_rules": {rule['description']: rule for rule in rules if 'description' in rule}}
                else:
                    raise Exception(f"Failed to fetch traffic rules. Status: {resp.status}")

    async def set_traffic_rule(self, rule_name, allow):
        """Set a traffic rule to allow or block."""
        rules_data = await self.get_traffic_rules()
        rules = rules_data.get("traffic_rules", {})
        if rule_name not in rules:
            raise Exception(f"Rule '{rule_name}' not found")

        rule = rules[rule_name]
        rule_id = rule['_id']
        #url = f"https://{self._host}/proxy/network/v2/api/site/{self._site_id}/trafficrules/{rule_id}"
        url = self._get_api_url(f"v2/api/site/{self._site_id}/trafficrules/{rule_id}")

        updated_rule = rule.copy()
        updated_rule['action'] = "ALLOW" if allow else "BLOCK"

        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            headers = {
                "X-Csrf-Token": self._csrf_token,
                "Content-Type": "application/json"
            }
            async with session.put(url, json=updated_rule, headers=headers, ssl=False) as resp:
                if resp.status in [200, 201]:
                    _LOGGER.info(f"Successfully {'allowed' if allow else 'blocked'} {rule_name}")
                else:
                    raise Exception(f"Failed to set traffic rule. Status: {resp.status}")
                
    async def get_firewall_rules(self):
        """Fetch all firewall rules."""
        #url = f"https://{self._host}/proxy/network/api/s/{self._site_id}/rest/firewallrule"
        url = self._get_api_url(f"api/s/{self._site_id}/rest/firewallrule")
        
        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            headers = {"X-Csrf-Token": self._csrf_token}
            async with session.get(url, headers=headers, ssl=False) as resp:
                if resp.status == 200:
                    rules = await resp.json()
                    return {"firewall_rules": {rule['name']: rule for rule in rules.get('data', []) if 'name' in rule}}
                else:
                    raise Exception(f"Failed to fetch firewall rules. Status: {resp.status}")

    async def set_firewall_rule(self, rule_name, allow):
        """Set a firewall rule to allow or drop."""
        rules_data = await self.get_firewall_rules()
        rules = rules_data.get("firewall_rules", {})
        if rule_name not in rules:
            raise Exception(f"Firewall rule '{rule_name}' not found")

        rule = rules[rule_name]
        rule_id = rule['_id']
        #url = f"https://{self._host}/proxy/network/api/s/{self._site_id}/rest/firewallrule/{rule_id}"
        url = self._get_api_url(f"api/s/{self._site_id}/rest/firewallrule/{rule_id}")

        updated_rule = rule.copy()
        updated_rule['action'] = "accept" if allow else "drop"

        async with aiohttp.ClientSession(cookies=self._cookies) as session:
            headers = {
                "X-Csrf-Token": self._csrf_token,
                "Content-Type": "application/json"
            }
            async with session.put(url, json=updated_rule, headers=headers, ssl=False) as resp:
                if resp.status in [200, 201]:
                    _LOGGER.info(f"Successfully {'allowed' if allow else 'blocked'} firewall rule {rule_name}")
                else:
                    raise Exception(f"Failed to set firewall rule. Status: {resp.status}")