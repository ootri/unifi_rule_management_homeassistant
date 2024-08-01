# UniFi firewall/traffic rules for Home Assistant

## About this repo

This custom integration for Home Assistant allows you to manage your UniFi firewall and traffic rules directly from your Home Assistant dashboard. It automatically creates switches for all user-created firewall and traffic rules, enabling you to easily toggle them on and off.

My wife wanted a physical switch to block an app on our TV. The current UniFi integration with Home Assistant doesn't (yet?) import firewall and traffic rules.

With this integration, you can:
- View the status of all your UniFi firewall and traffic rules
- Enable or disable rules with a simple toggle
- Automate rule changes based on other Home Assistant entities or conditions (leave home -> throttle app/devices)

## Requirements

- Home Assistant with HACS (Home Assistant Community Store) installed
- UniFi Network Controller (including UDM, UDM Pro, UDM-SE, and CloudKey devices)

### Creating a Local User

If you don't already have a local user on your UniFi Controller:

1. Log in to your UniFi Controller web interface.
2. Go to Settings > Administrators.
3. Click "Add Admin" and create a new local user with admin privileges.
4. Use these credentials when setting up the integration in Home Assistant.

## Installation

1. Open HACS in your Home Assistant instance.
2. Click three dots in the top right and select "Custom repository".
3. Enter the following URL: https://github.com/ootri/unifi_rule_management_homeassistant
4. Select "Integration" as the category.
5. Click "Add" to install the integration.
6. Restart Home Assistant to complete the installation.

## Configuration

1. In your Home Assistant UI, go to Settings > Devices & services.
2. Click the "+ Add Integration" button and search for "UniFi Rule Management".
3. Follow the configuration steps, providing the following information:
   - Host: The local IP address of your UniFi Controller
   - Username: A local user with network privileges
   - Password: The password for the local user
   - Scan Interval: How often to poll for rule updates (default is 300 seconds)

### Scan Interval

The scan interval determines how often the integration checks for updates to your rules. The default of 300 seconds (5 minutes) should be suitable for most users. You can increase this value to reduce network traffic, but be aware that it will also increase the time it takes for rule changes to reflect in Home Assistant when updating within UniFi Network.

## Usage

Once configured, the integration will automatically create switches for all your user-created firewall and traffic rules. These will appear as entities in Home Assistant, which you can add to your dashboard or use in automations.

### Firewall Rules vs Traffic Rules

- Traffic Rules: These are "simple" rules that specify a destination as an app, app group, website, region, etc.
- Firewall Rules: These are "advanced" rules that specify traditional firewall options, like protocol, source, destination, etc.

Both types of rules will appear as switches in Home Assistant, allowing you to enable or disable them as needed. They are named as switch.[name]_firewall_rule and switch.[name]_traffic_rule.

Enjoy managing your UniFi network rules directly from Home Assistant!

## Special Thanks

A special thanks to the contributors of the unofficial UniFi Controller API documentation at https://ubntwiki.com/products/software/unifi-controller/api