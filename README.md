# Transport for Ireland (TFI) Journey Planner

Support polling of the [Transport for Ireland Journey Planner](https://journeyplanner.transportforireland.ie/) RTPI information source to display departure information at transit stops.

## Installation

This integration can be installed via HACS by adding this repository as a custom repository. See the [HACS documentation](https://hacs.xyz/docs/faq/custom_repositories/) for the procedure.

## Configuration

Once installed, add an instance of this integration via the UI (**Configuration > Integrations > +**), enter all of the stop IDs that you wish to poll data for in the **Stops** field. Click **Submit** to start the instance and generate entities for each stop entered.

To identify the stop ID for a transit stop, go to https://journeyplanner.transportforireland.ie/, search for the stop and go to the live departures for that stop. The URL of the page shows the stop ID that you need to enter into the integration.

You can see the details of all departures in the attributes of the stop entities. This can also be used by front-end integrations such as [Flex Table Card](https://github.com/custom-cards/flex-table-card) to generate a departure board.

**NOTE:** It is strongly recommended that all sensors created by this integration be excluded from your recorder database. See the[Recorder documentation](https://www.home-assistant.io/integrations/recorder/#configure-filter) for the process. Otherwise, every sensor update will be stored in the Home Assistant database and take up a lot of unnecessary disk space.

## Stop IDs

You can override departure filters on a per stop basis using the following advanced format for a stop ID:

  *stop_id*`=`*service_id*`/`*direction*`#`*limit_departures*`@`*departure_horizon*

Where multiple filters are specified, a departure must satisfy *all* filters to be included in the departures list.

If configured globally, it is not currently possible to remove service ID and direction filters on a per stop basis. Remove the global filters and configure per stop filters on every applicable stop instead.

| Parameter | Description
| --------- | -----------
| *stop_id* | The stop identifier used at https://journeyplanner.transportforireland.ie/. Multiple stop IDs can be specified for the same stop by separating them with a comma.
| *service_id* | Filter departures by service IDs. This is useful if you are not interested in all services that stop at the transit stop. Multiple service IDs can be specified for the same stop by separating them with a comma.
| *direction* | Filter departures by direction. This is usually `OUTBOUND` and `INBOUND` and can be found by reviewing the detailed departure information in the entity attributes. Multiple directions can be specified for the same stop by separating them with a comma.
| *limit_departures* | Limit the number of departures returned by this integration.
| *departure_horizon* | Limit the departures by their due time.

### Example stop ID definitions

Enable debug logging on the integration to see the departures polled by the integration.

| Stop | Description
| ---- | -----------
| `8220DB000273` | Include all departures at this transit stop.
| `8220DB000273=4` | Include only service 4 stopping at this transit stop.
| `8220DB000273/OUTBOUND` | Include only outbound services stopping at this transit stop.
| `8220DB000273#10` | Limit to the first 10 departures only.
| `8220DB000273@06:00:00` | Limit to departures due in the next 6 hours only.
| `8220DB000273=4#10` | Include the first 10 departures of service 4 at this transit stop.
| `8220DB000273,8220DB000325#10` | Include the first 10 departures stop at either transit stop.

## Polling parameters

**TODO:** describe polling parameters.

To reduce the number of poll requests, all transit stops added to the same instance of the integration are polled together.

## Reconfiguring the integration

Global departure filters and polling intervals can be modfied after the integration is added by clicking **Configure** on the integration card.

To change the stop IDs that are polled, delete the integration and add it again.

## Enabling debugging

The integration logs messages to the `custom_components.tfi_journeyplanner` namespace. See the [Logger integration documentation](https://www.home-assistant.io/integrations/logger/) for the procedure for enabling logging for this namespace.
