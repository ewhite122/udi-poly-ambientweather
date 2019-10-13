#!/usr/bin/env python3

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import sys
import asyncio
from aiohttp import ClientSession
from aioambient import Client

LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'Ambient Weather'
        self.app_key = 'b740e1341b4443eca15dccbb612f1d70374902a30a59465787f8c550038efa44'
        self.api_key = ''

    def start(self):
        LOGGER.info('Started AmbientWeather')
        self.removeNoticesAll()
        if self.check_params():
            LOGGER.info('API Key is set')
            self.removeNoticesAll()
            _loop = asyncio.new_event_loop()
            _loop.create_task(self.AmbientWeather(self.app_key, self.api_key))
            _loop.run_forever()
        else:
            LOGGER.info('API Key is not set')

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    @staticmethod
    def lux_convert(wm2):
        lux = round(wm2 / 0.0079, 0)
        return lux
    
    @staticmethod
    def cardinal_direction(winddir):
        # Returns the Cardinal Direction Name
        if 0 <= winddir <= 11.24:
            return 1
        elif 11.25 <= winddir <= 33.74:
            return 2
        elif 33.75 <= winddir <= 56.24:
            return 3
        elif 56.25 <= winddir <= 78.74:
            return 4
        elif 78.75 <= winddir <= 101.24:
            return 5
        elif 101.25 <= winddir <= 123.74:
            return 6
        elif 123.75 <= winddir <= 146.24:
            return 7
        elif 146.25 <= winddir <= 168.74:
            return 8
        elif 168.75 <= winddir <= 191.24:
            return 9
        elif 191.25 <= winddir <= 213.74:
            return 10
        elif 213.75 <= winddir <= 236.24:
            return 11
        elif 236.25 <= winddir <= 258.74:
            return 12
        elif 258.75 <= winddir <= 281.24:
            return 13
        elif 281.25 <= winddir <= 303.74:
            return 14
        elif 303.75 <= winddir <= 326.24:
            return 15
        elif 326.25 <= winddir <= 348.74:
            return 16
        elif 348.75 <= winddir <= 360:
            return 1
        else:
            return 0

    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        pass

    def delete(self):
        LOGGER.info('Ambient Weather NodeServer:  Deleted')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def check_params(self):
        default_api_key = 'Your_API_Key'

        if 'api_key' in self.polyConfig['customParams']:
            if self.polyConfig['customParams']['api_key'] != default_api_key:
                self.api_key = self.polyConfig['customParams']['api_key']
                return True
            else:
                self.addNotice({'myNotice': 'Please set proper API Key in the configuration page, and restart this NodeServer'})
                return False
            # if self.api_key is not '':
            #     api_set = True
            # else:
            #     api_set = False
        else:
            # self.api_key = ''
            self.addNotice({'myNotice': 'Please set proper API Key in the configuration page, and restart this NodeServer'})
            LOGGER.error('check_params: Ambient Weather user API key missing.  Using {}'.format(self.api_key))
            # api_set = False
            self.addCustomParam({'api_key': default_api_key})
            return False

        # if api_set:
        #     return True
        # else:
        #     return False

    def remove_notices_all(self, command):
        LOGGER.info('remove_notices_all:')
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self, command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    async def AmbientWeather(self, *args, **kwargs):
        """Create the aiohttp session and run."""
        async with ClientSession() as websession:
            client = Client(self.api_key, self.app_key, websession)

        def connect_method():
            """Print a simple "hello" message."""
            LOGGER.info('Client has connected to the websocket')

        def subscribed_method(data):
            """Process the data received upon subscribing."""
            # LOGGER.info('Subscription data received: {0}'.format(data))
            for k, v in data.items():
                if k == 'devices':
                    for pws in v:
                        raw_mac = pws['macAddress'].split(':')
                        mac_type = raw_mac[0] + raw_mac[1] + raw_mac[2]
                        pws_address = pws['macAddress'].replace(':', '').lower()
                        pws_name = str(pws['info']['name'])
                        add_on_address = pws_address + '_1'

                        if mac_type == '000EC6':  # Observer IP Module used by most Ambient PWS systems
                            self.addNode(PwsNode(self, self.address, pws_address, pws_name))
                            self.addNode(AddonNode(self, self.address, add_on_address, pws_name + '-Addon'))
                        elif mac_type == 'ECFABC':  # WS-2902 Display
                            self.addNode(PwsNode(self, self.address, pws_address, pws_name))
                        else:  # All other Ambient systems
                            self.addNode(PwsNode(self, self.address, pws_address, pws_name))

        def data_method(data):
            """Print the data received."""
            # print('Data received: {0}'.format(data))
            for node in self.nodes:
                raw_mac = data['macAddress'].split(':')
                mac_type = raw_mac[0] + raw_mac[1] + raw_mac[2]
                pws_address = data['macAddress'].replace(':','').lower()
                add_on_address = pws_address + '_1'

                if pws_address == self.nodes[node].address:
                    # Convert solarradiation into lux
                    lux = self.lux_convert(data['solarradiation'])
                    
                    # Convert Wind Direction Degrees to cardinal direction
                    cardinal = self.cardinal_direction(data['winddir'])

                    self.nodes[node].setDriver('CLITEMP', data['tempf'])
                    self.nodes[node].setDriver('GV1', data['tempinf'])
                    self.nodes[node].setDriver('CLIHUM', data['humidity'])
                    self.nodes[node].setDriver('GV3', data['humidityin'])
                    self.nodes[node].setDriver('BARPRES', data['baromrelin'])
                    self.nodes[node].setDriver('ATMPRES', data['baromabsin'])
                    self.nodes[node].setDriver('LUMIN', lux) # Use mw/2 converted data for lux
                    self.nodes[node].setDriver('UV', data['uv'])
                    self.nodes[node].setDriver('SOLRAD', data['solarradiation'])
                    self.nodes[node].setDriver('GV9', data['hourlyrainin']) 
                    self.nodes[node].setDriver('GV10', data['dailyrainin'])
                    self.nodes[node].setDriver('GV11', data['weeklyrainin'])
                    self.nodes[node].setDriver('GV12', data['monthlyrainin'])
                    
                    if mac_type == '000EC6':  # Observer IP Module used by most Ambient PWS systems
                        self.nodes[node].setDriver('GV13', data['yearlyrainin'])
                    elif mac_type == 'C0210D':  # WS-1002-WIFI does not support totalrainin
                        self.nodes[node].setDriver('GV13', data['yearlyrainin'])

                    if mac_type != 'C0210D':  # WS-1002-WIFI does not support totalrainin
                        self.nodes[node].setDriver('GV14', data['totalrainin'])

                    self.nodes[node].setDriver('WINDDIR', data['winddir'])
                    self.nodes[node].setDriver('GV16', cardinal)
                    self.nodes[node].setDriver('SPEED', data['windspeedmph'])
                    self.nodes[node].setDriver('GV17', data['windgustmph'])
                    self.nodes[node].setDriver('GV18', data['maxdailygust'])
                    self.nodes[node].setDriver('GV19', data['feelsLike'])
                    self.nodes[node].setDriver('GV20', data['dewPoint'])

                if add_on_address == self.nodes[node].address:
                    if 'temp1f' in data:
                        self.nodes[node].setDriver('GV0', data['temp1f'])
                    if 'temp2f' in data:
                        self.nodes[node].setDriver('GV1', data['temp2f'])
                    if 'temp3f' in data:
                        self.nodes[node].setDriver('GV2', data['temp3f'])
                    if 'temp4f' in data:
                        self.nodes[node].setDriver('GV3', data['temp4f'])
                    if 'temp5f' in data:
                        self.nodes[node].setDriver('GV4', data['temp5f'])
                    if 'temp6f' in data:
                        self.nodes[node].setDriver('GV5', data['temp6f'])
                    if 'temp7f' in data:
                        self.nodes[node].setDriver('GV6', data['temp7f'])
                    if 'temp8f' in data:
                        self.nodes[node].setDriver('GV7', data['temp8f'])
                    if 'humidity1' in data:
                        self.nodes[node].setDriver('GV8', data['humidity1'])
                    if 'humidity2' in data:
                        self.nodes[node].setDriver('GV9', data['humidity2'])
                    if 'humidity3' in data:
                        self.nodes[node].setDriver('GV10', data['humidity3'])
                    if 'humidity4' in data:
                        self.nodes[node].setDriver('GV11', data['humidity4'])
                    if 'humidity5' in data:
                        self.nodes[node].setDriver('GV12', data['humidity5'])
                    if 'humidity6' in data:
                        self.nodes[node].setDriver('GV13', data['humidity6'])
                    if 'humidity7' in data:
                        self.nodes[node].setDriver('GV14', data['humidity7'])
                    if 'humidity8' in data:
                        self.nodes[node].setDriver('GV15', data['humidity8'])

        def disconnect_method():
            """Print a simple "goodbye" message."""
            LOGGER.info('Client has disconnected from the websocket')

        # Connect to the websocket:
        client.websocket.on_connect(connect_method)
        client.websocket.on_subscribed(subscribed_method)
        client.websocket.on_data(data_method)
        client.websocket.on_disconnect(disconnect_method)

        await client.websocket.connect()

        # At any point, disconnect from the websocket:
        # await client.websocket.disconnect()

    id = 'controller'
    commands = {
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class PwsNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(PwsNode, self).__init__(controller, primary, address, name)

    def start(self):
        self.setDriver('ST', 1)

    def setOn(self, command):
        self.setDriver('ST', 1)

    def setOff(self, command):
        self.setDriver('ST', 0)

    def query(self):
        self.reportDrivers()

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17},  # Outside Temperature F
        {'driver': 'GV1', 'value': 0, 'uom': 17},  # Inside Temperature F
        {'driver': 'CLIHUM', 'value': 0, 'uom': 22},  # Outside Humidity
        {'driver': 'GV3', 'value': 0, 'uom': 22},  # Inside Humidity
        {'driver': 'BARPRES', 'value': 0, 'uom': 23},  # Rel Pressure
        {'driver': 'ATMPRES', 'value': 0, 'uom': 23},  # Abs Pressure
        {'driver': 'LUMIN', 'value': 0, 'uom': 36},  # Lux
        {'driver': 'UV', 'value': 0, 'uom': 71},  # UV
        {'driver': 'SOLRAD', 'value': 0, 'uom': 74},  # Solar Radiation
        {'driver': 'GV9', 'value': 0, 'uom': 105},  # Hourly Rain
        {'driver': 'GV10', 'value': 0, 'uom': 105},  # Daily Rain
        {'driver': 'GV11', 'value': 0, 'uom': 105},  # Weekly Rain
        {'driver': 'GV12', 'value': 0, 'uom': 105},  # Monthly Rain
        {'driver': 'GV13', 'value': 0, 'uom': 105},  # Yearly Rain
        {'driver': 'GV14', 'value': 0, 'uom': 105},  # Total Rain
        {'driver': 'WINDDIR', 'value': 0, 'uom': 76},  # Wind Direction (degree)
        {'driver': 'GV16', 'value': 0, 'uom': 25},  # Wind Direction (cardinal)
        {'driver': 'SPEED', 'value': 0, 'uom': 48},  # Wind Speed
        {'driver': 'GV17', 'value': 0, 'uom': 48},  # Wind Gust
        {'driver': 'GV18', 'value': 0, 'uom': 48},  # Max Wind Gust Daily
        {'driver': 'GV19', 'value': 0, 'uom': 17},  # Feels Like Temperature
        {'driver': 'GV20', 'value': 0, 'uom': 17},  # Dew Point Temperature
        ]

    id = 'pwsnodetype'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class AddonNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(AddonNode, self).__init__(controller, primary, address, name)

    def start(self):
        self.setDriver('ST', 1)

    def setOn(self, command):
        self.setDriver('ST', 1)

    def setOff(self, command):
        self.setDriver('ST', 0)

    def query(self):
        self.reportDrivers()

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Sensor 1 Temperature
        {'driver': 'GV1', 'value': 0, 'uom': 17},  # Sensor 2 Temperature
        {'driver': 'GV2', 'value': 0, 'uom': 17},  # Sensor 3 Temperature
        {'driver': 'GV3', 'value': 0, 'uom': 17},  # Sensor 4 Temperature
        {'driver': 'GV4', 'value': 0, 'uom': 17},  # Sensor 5 Temperature
        {'driver': 'GV5', 'value': 0, 'uom': 17},  # Sensor 6 Temperature
        {'driver': 'GV6', 'value': 0, 'uom': 17},  # Sensor 7 Temperature
        {'driver': 'GV7', 'value': 0, 'uom': 17},  # Sensor 8 Temperature
        {'driver': 'GV8', 'value': 0, 'uom': 22},  # Sensor 1 Humidity
        {'driver': 'GV9', 'value': 0, 'uom': 22},  # Sensor 2 Humidity
        {'driver': 'GV10', 'value': 0, 'uom': 22},  # Sensor 3 Humidity
        {'driver': 'GV11', 'value': 0, 'uom': 22},  # Sensor 4 Humidity
        {'driver': 'GV12', 'value': 0, 'uom': 22},  # Sensor 5 Humidity
        {'driver': 'GV13', 'value': 0, 'uom': 22},  # Sensor 6 Humidity
        {'driver': 'GV14', 'value': 0, 'uom': 22},  # Sensor 7 Humidity
        {'driver': 'GV15', 'value': 0, 'uom': 22},  # Sensor 8 Humidity
        ]

    id = 'addontype'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('AmbientWeather')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
