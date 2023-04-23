# Transport for Ireland (TFI) Journey Planner

Support polling of the [Transport for Ireland Journey Planner](https://journeyplanner.transportforireland.ie/) RTPI information source to display departure board information.

## Installation

This integration can be installed via HACS by adding this repository as a custom repository. See the [HACS documentation](https://hacs.xyz/docs/faq/custom_repositories/) for the procedure.

## Configuration

Once installed, add this integration via the UI (**Configuration > Integrations > +**), enter the stop IDs that you wish to poll data for, then click **Submit**. Polling parameters can be modfied by reconfiguring the integration.

Enable debug logging on the integration to see the departures polled by the integration.

To change the stop IDs that are polled, delete the integration and add it again.

## Enabling debugging

The integration logs messages to the `custom_components.tfi_journeyplanner` namespace. See the [Logger integration documentation](https://www.home-assistant.io/integrations/logger/) for the procedure for enabling logging for this namespace.
