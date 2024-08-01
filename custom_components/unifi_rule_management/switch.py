"""Switch platform for UniFi Rules Management."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from . import DOMAIN
from .unifi_client import UnifiClient

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UniFi Rules switches."""
    config = hass.data[DOMAIN][entry.entry_id]
    host = config[CONF_HOST]
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    scan_interval = config.get("scan_interval", 300)

    client = UnifiClient(host, username, password)

    async def async_update_data():
        """Fetch data from API endpoint."""
        traffic_data = await client.get_traffic_rules()
        firewall_data = await client.get_firewall_rules()
        return {**traffic_data, **firewall_data}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="unifi_rule_management",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    entities = []
    for rule_name, rule_data in coordinator.data.get("traffic_rules", {}).items():
        entities.append(UnifiTrafficRuleSwitch(coordinator, rule_name, client))
    
    for rule_name, rule_data in coordinator.data.get("firewall_rules", {}).items():
        entities.append(UnifiFirewallRuleSwitch(coordinator, rule_name, client))

    async_add_entities(entities, True)

class UnifiTrafficRuleSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a UniFi Traffic Rule switch."""

    def __init__(self, coordinator, rule_name, client):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._rule_name = rule_name
        self._client = client
        self._attr_name = f"{rule_name.capitalize()} Traffic Rule"
        self._attr_unique_id = f"unifi_traffic_rule_{rule_name}"
        #self._attr_icon = f"/custom_components/{DOMAIN}/icons/unifi_traffic_rules.png"

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self.coordinator.data.get("traffic_rules", {}).get(self._rule_name, {}).get("action") == "ALLOW"

    async def async_turn_on(self, **kwargs):
        """Turn the switch on (allow traffic)."""
        await self._client.set_traffic_rule(self._rule_name, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off (block traffic)."""
        await self._client.set_traffic_rule(self._rule_name, False)
        await self.coordinator.async_request_refresh()

class UnifiFirewallRuleSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a UniFi Firewall Rule switch."""

    def __init__(self, coordinator, rule_name, client):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._rule_name = rule_name
        self._client = client
        self._attr_name = f"{rule_name.capitalize()} Firewall Rule"
        self._attr_unique_id = f"unifi_firewall_rule_{rule_name}"
        #self._attr_icon = f"/custom_components/{DOMAIN}/icons/unifi_traffic_rules.png"

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self.coordinator.data.get('firewall_rules', {}).get(self._rule_name, {}).get('action') == "accept"

    async def async_turn_on(self, **kwargs):
        """Turn the switch on (allow traffic)."""
        await self._client.set_firewall_rule(self._rule_name, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off (block traffic)."""
        await self._client.set_firewall_rule(self._rule_name, False)
        await self.coordinator.async_request_refresh()
