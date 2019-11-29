#!/usr/bin/env python3

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import sys
import asyncio
import requests
from aiohttp import ClientSession
from aioambient import Client

LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'Ambient Weather'
        self.app_key = ''
        self.api_key = ''
        self.disco = 0

    def start(self):
        LOGGER.info('Started AmbientWeather')
        self.removeNoticesAll()
        if self.check_params():
            LOGGER.info('API Key is set')
            self.removeNoticesAll()
            self.discover()
            if self.disco == 1:
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
    def ppm_convert(mg3):
        ppm = round(float(mg3) / 1000, 3)
        return ppm

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
        api_url = 'https://api.ambientweather.net/v1/devices?applicationKey=' + self.app_key + '&apiKey=' + self.api_key
        r = requests.get(api_url)
        data = r.json()

        for pws in data:
            LOGGER.info(pws['macAddress'])
            LOGGER.info(pws['info']['name'])
            pws_address = pws['macAddress'].replace(':', '').replace('0', '').lower()
            pws_name = str(pws['info']['name'])

            self.addNode(PwsNode(self, pws_address, pws_address, pws_name))

            if 'battin' in pws['lastData']:
                LOGGER.info(pws_name + "Has a Indoor Battery: battin: " + str(pws['lastData']['battin']))
                self.addNode((BatteryInsideNode(self, pws_address, pws_address + "bi", "Battery - Inside")))
            if 'battout' in pws['lastData']:
                self.addNode((BatteryOutsideNode(self, pws_address, pws_address + "bo", "Battery - Outside")))
            if 'tempf' in pws['lastData']:
                self.addNode((TempOutsideNode(self, pws_address, pws_address + "to", "Temperature - Outside")))
            if 'tempinf' in pws['lastData']:
                self.addNode((TempInsideNode(self, pws_address, pws_address + "ti", "Temperature - Inside")))
            if 'feelsLike' in pws['lastData']:
                self.addNode((FeelsLikeOutsideNode(self, pws_address, pws_address + "fl", "Feels Like - Outside")))
            if 'feelsLikein' in pws['lastData']:
                self.addNode((FeelsLikeInsideNode(self, pws_address, pws_address + "fli", "Feels Like - Inside")))
            if 'dewPoint' in pws['lastData']:
                self.addNode((DewPointOutsideNode(self, pws_address, pws_address + "dp", "Dew Point - Outside")))
            if 'dewPointin' in pws['lastData']:
                self.addNode((DewPointInsideNode(self, pws_address, pws_address + "dpi", "Dew Point - Inside")))
            if 'humidity' in pws['lastData']:
                self.addNode((HumidityOutsideNode(self, pws_address, pws_address + "ho", "Humidity - Outside")))
            if 'humidityin' in pws['lastData']:
                self.addNode((HumidityInsideNode(self, pws_address, pws_address + "hi", "Humidity - Inside")))
            if 'baromabsin' in pws['lastData'] and 'baromrelin' in pws['lastData']:
                self.addNode((PressureNode(self, pws_address, pws_address + "hg", "Barometric Pressure")))
            if 'dailyrainin' in pws['lastData']:
                self.addNode((RainDayNode(self, pws_address, pws_address + "rd", "Rain - Day")))
            if 'monthlyrainin' in pws['lastData']:
                self.addNode((RainMonthNode(self, pws_address, pws_address + "rm", "Rain - Month")))
            if 'weeklyrainin' in pws['lastData']:
                self.addNode((RainWeekNode(self, pws_address, pws_address + "rw", "Rain - Week")))
            if 'totalrainin' in pws['lastData']:
                self.addNode((RainTotalNode(self, pws_address, pws_address + "rt", "Rain - Total")))
            if 'yearlyrainin' in pws['lastData']:
                self.addNode((RainYearNode(self, pws_address, pws_address + "ry", "Rain - Year")))
            if 'eventrainin' in pws['lastData']:
                self.addNode((RainEventNode(self, pws_address, pws_address + "re", "Rain - Event")))
            if 'hourlyrainin' in pws['lastData']:
                self.addNode((RainHourNode(self, pws_address, pws_address + "rh", "Rain - Hour")))
            if 'uv' in pws['lastData'] and 'solarradiation' in pws['lastData']:
                self.addNode((SolarNode(self, pws_address, pws_address + "sol", "Solar")))
            if 'winddir' in pws['lastData']:
                self.addNode((WindNode(self, pws_address, pws_address + "wnd", "Wind")))
            if 'temp1f' in pws['lastData']:
                self.addNode((WH31Node(self, pws_address, pws_address + "as1", "Sensor 1")))
            if 'temp2f' in pws['lastData']:
                self.addNode((WH31Node(self, pws_address, pws_address + "as2", "Sensor 2")))
            if 'temp3f' in pws['lastData']:
                self.addNode((WH31Node(self, pws_address, pws_address + "as3", "Sensor 3")))
            if 'temp4f' in pws['lastData']:
                self.addNode((WH31Node(self, pws_address, pws_address + "as4", "Sensor 4")))
            if 'temp5f' in pws['lastData']:
                self.addNode((WH31Node(self, pws_address, pws_address + "as5", "Sensor 5")))
            if 'temp6f' in pws['lastData']:
                self.addNode((WH31Node(self, pws_address, pws_address + "as6", "Sensor 6")))
            if 'temp7f' in pws['lastData']:
                self.addNode((WH31Node(self, pws_address, pws_address + "as7", "Sensor 7")))
            if 'temp8f' in pws['lastData']:
                self.addNode((WH31Node(self, pws_address, pws_address + "as8", "Sensor 8")))

        self.disco = 1

    def delete(self):
        LOGGER.info('Ambient Weather NodeServer:  Deleted')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def check_params(self):
        default_api_key = 'YOUR API KEY'
        default_app_key = 'YOUR APP KEY'

        if 'api_key' not in self.polyConfig['customParams']:
            self.addCustomParam({'api_key': default_api_key})

        if 'app_key' not in self.polyConfig['customParams']:
            self.addCustomParam({'app_key': default_app_key})

        if self.polyConfig['customParams']['app_key'] != default_app_key:
            self.app_key = self.polyConfig['customParams']['app_key']
            if self.polyConfig['customParams']['api_key'] != default_api_key:
                self.api_key = self.polyConfig['customParams']['api_key']
            else:
                self.addNotice(
                    {'api_key': 'Please set proper API Key in the configuration page, and restart this NodeServer'})
                return False
        else:
            self.addNotice(
                {'app_key': 'Please set proper APP and API Key in the configuration page, and restart this NodeServer'})
            return False

    def remove_notices_all(self, command):
        LOGGER.info('remove_notices_all:')
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
            LOGGER.info('Client has connected to the websocket')

        def subscribed_method(data):
            """Process the data received upon subscribing."""
            LOGGER.info('Subscription data received')
            # LOGGER.info('Subscription data received: {0}'.format(data))

        def data_method(data):
            # print('Data received: {0}'.format(data))
            pws_address = data['macAddress'].replace(':', '').replace('0', '').lower()
            if pws_address in self.nodes:
                if 'battin' in data:
                    naddr = pws_address + "bi"
                    self.nodes[naddr].setDriver('BATLVL', data['battin'])
                if 'battout' in data:
                    naddr = pws_address + "bo"
                    self.nodes[naddr].setDriver('BATLVL', data['battout'])
                if 'tempf' in data:
                    naddr = pws_address + "to"
                    self.nodes[naddr].setDriver('CLITEMP', data['tempf'])
                if 'tempinf' in data:
                    naddr = pws_address + "ti"
                    self.nodes[naddr].setDriver('CLITEMP', data['tempinf'])
                if 'feelsLike' in data:
                    naddr = pws_address + "fl"
                    self.nodes[naddr].setDriver('CLITEMP', data['feelsLike'])
                if 'feelsLikein' in data:
                    naddr = pws_address + "fli"
                    self.nodes[naddr].setDriver('CLITEMP', data['feelsLikein'])
                if 'dewPoint' in data:
                    naddr = pws_address + "dp"
                    self.nodes[naddr].setDriver('CLITEMP', data['dewPoint'])
                if 'dewPointin' in data:
                    naddr = pws_address + "dpi"
                    self.nodes[naddr].setDriver('CLITEMP', data['dewPointin'])
                if 'humidity' in data:
                    naddr = pws_address + "ho"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidity'])
                if 'humidityin' in data:
                    naddr = pws_address + "hi"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidityin'])
                if 'baromabsin' in data:
                    naddr = pws_address + "hg"
                    self.nodes[naddr].setDriver('ATMPRES', data['baromabsin'])
                if 'baromrelin' in data:
                    naddr = pws_address + "hg"
                    self.nodes[naddr].setDriver('BARPRES', data['baromrelin'])
                if 'dailyrainin' in data:
                    naddr = pws_address + "rd"
                    self.nodes[naddr].setDriver('WVOL', data['dailyrainin'])
                if 'monthlyrainin' in data:
                    naddr = pws_address + "rm"
                    self.nodes[naddr].setDriver('WVOL', data['monthlyrainin'])
                if 'weeklyrainin' in data:
                    naddr = pws_address + "rw"
                    self.nodes[naddr].setDriver('WVOL', data['weeklyrainin'])
                if 'totalrainin' in data:
                    naddr = pws_address + "rt"
                    self.nodes[naddr].setDriver('WVOL', data['totalrainin'])
                if 'yearlyrainin' in data:
                    naddr = pws_address + "ry"
                    self.nodes[naddr].setDriver('WVOL', data['yearlyrainin'])
                if 'eventrainin' in data:
                    naddr = pws_address + "re"
                    self.nodes[naddr].setDriver('WVOL', data['eventrainin'])
                if 'hourlyrainin' in data:
                    naddr = pws_address + "rh"
                    self.nodes[naddr].setDriver('WVOL', data['hourlyrainin'])
                if 'solarradiation' in data:
                    naddr = pws_address + "sol"
                    lux = self.lux_convert(data['solarradiation'])
                    self.nodes[naddr].setDriver('SOLRAD', data['solarradiation'])
                    self.nodes[naddr].setDriver('LUMIN', lux)
                if 'uv' in data:
                    naddr = pws_address + "sol"
                    self.nodes[naddr].setDriver('UV', data['uv'])
                if 'winddir' in data:
                    naddr = pws_address + "wnd"
                    cardinal = self.cardinal_direction(data['winddir'])
                    self.nodes[naddr].setDriver('WINDDIR', data['winddir'])
                    self.nodes[naddr].setDriver('GV0', cardinal)
                if 'windspeedmph' in data:
                    naddr = pws_address + "wnd"
                    self.nodes[naddr].setDriver('SPEED', data['windspeedmph'])
                if 'windgustmph' in data:
                    naddr = pws_address + "wnd"
                    self.nodes[naddr].setDriver('GV1', data['windgustmph'])
                if 'maxdailygust' in data:
                    naddr = pws_address + "fl"
                    self.nodes[naddr].setDriver('GV2', data['maxdailygust'])

                if 'temp1f' in data:
                    naddr = pws_address + "as1"
                    self.nodes[naddr].setDriver('CLITEMP', data['temp1f'])
                if 'humidity1' in data:
                    naddr = pws_address + "as1"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidity1'])
                if 'batt1' in data:
                    naddr = pws_address + "as1"
                    self.nodes[naddr].setDriver('BATLVL', data['batt1'])
                if 'feelsLike1' in data:
                    naddr = pws_address + "as1"
                    self.nodes[naddr].setDriver('GV0', data['feelsLike1'])
                if 'dewPoint1' in data:
                    naddr = pws_address + "as1"
                    self.nodes[naddr].setDriver('GV1', data['dewPoint1'])

                if 'temp2f' in data:
                    naddr = pws_address + "as2"
                    self.nodes[naddr].setDriver('CLITEMP', data['temp2f'])
                if 'humidity2' in data:
                    naddr = pws_address + "as2"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidity2'])
                if 'batt2' in data:
                    naddr = pws_address + "as2"
                    self.nodes[naddr].setDriver('BATLVL', data['batt2'])
                if 'feelsLike2' in data:
                    naddr = pws_address + "as2"
                    self.nodes[naddr].setDriver('GV0', data['feelsLike2'])
                if 'dewPoint2' in data:
                    naddr = pws_address + "as2"
                    self.nodes[naddr].setDriver('GV1', data['dewPoint2'])

                if 'temp3f' in data:
                    naddr = pws_address + "as3"
                    self.nodes[naddr].setDriver('CLITEMP', data['temp3f'])
                if 'humidity3' in data:
                    naddr = pws_address + "as3"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidity3'])
                if 'batt3' in data:
                    naddr = pws_address + "as3"
                    self.nodes[naddr].setDriver('BATLVL', data['batt3'])
                if 'feelsLike3' in data:
                    naddr = pws_address + "as3"
                    self.nodes[naddr].setDriver('GV0', data['feelsLike3'])
                if 'dewPoint3' in data:
                    naddr = pws_address + "as3"
                    self.nodes[naddr].setDriver('GV1', data['dewPoint3'])

                if 'temp4f' in data:
                    naddr = pws_address + "as4"
                    self.nodes[naddr].setDriver('CLITEMP', data['temp4f'])
                if 'humidity4' in data:
                    naddr = pws_address + "as4"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidity4'])
                if 'batt4' in data:
                    naddr = pws_address + "as4"
                    self.nodes[naddr].setDriver('BATLVL', data['batt4'])
                if 'feelsLike4' in data:
                    naddr = pws_address + "as4"
                    self.nodes[naddr].setDriver('GV0', data['feelsLike4'])
                if 'dewPoint4' in data:
                    naddr = pws_address + "as4"
                    self.nodes[naddr].setDriver('GV1', data['dewPoint4'])

                if 'temp5f' in data:
                    naddr = pws_address + "as5"
                    self.nodes[naddr].setDriver('CLITEMP', data['temp5f'])
                if 'humidity5' in data:
                    naddr = pws_address + "as5"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidity5'])
                if 'batt5' in data:
                    naddr = pws_address + "as5"
                    self.nodes[naddr].setDriver('BATLVL', data['batt5'])
                if 'feelsLike5' in data:
                    naddr = pws_address + "as5"
                    self.nodes[naddr].setDriver('GV0', data['feelsLike5'])
                if 'dewPoint5' in data:
                    naddr = pws_address + "as5"
                    self.nodes[naddr].setDriver('GV1', data['dewPoint5'])

                if 'temp6f' in data:
                    naddr = pws_address + "as6"
                    self.nodes[naddr].setDriver('CLITEMP', data['temp6f'])
                if 'humidity6' in data:
                    naddr = pws_address + "as6"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidity6'])
                if 'batt6' in data:
                    naddr = pws_address + "as6"
                    self.nodes[naddr].setDriver('BATLVL', data['batt6'])
                if 'feelsLike6' in data:
                    naddr = pws_address + "as6"
                    self.nodes[naddr].setDriver('GV0', data['feelsLike6'])
                if 'dewPoint6' in data:
                    naddr = pws_address + "as6"
                    self.nodes[naddr].setDriver('GV1', data['dewPoint6'])

                if 'temp7f' in data:
                    naddr = pws_address + "as7"
                    self.nodes[naddr].setDriver('CLITEMP', data['temp7f'])
                if 'humidity7' in data:
                    naddr = pws_address + "as7"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidity7'])
                if 'batt7' in data:
                    naddr = pws_address + "as7"
                    self.nodes[naddr].setDriver('BATLVL', data['batt7'])
                if 'feelsLike7' in data:
                    naddr = pws_address + "as7"
                    self.nodes[naddr].setDriver('GV0', data['feelsLike7'])
                if 'dewPoint7' in data:
                    naddr = pws_address + "as7"
                    self.nodes[naddr].setDriver('GV1', data['dewPoint7'])

                if 'temp8f' in data:
                    naddr = pws_address + "as8"
                    self.nodes[naddr].setDriver('CLITEMP', data['temp8f'])
                if 'humidity8' in data:
                    naddr = pws_address + "as8"
                    self.nodes[naddr].setDriver('CLIHUM', data['humidity8'])
                if 'batt8' in data:
                    naddr = pws_address + "as8"
                    self.nodes[naddr].setDriver('BATLVL', data['batt8'])
                if 'feelsLike8' in data:
                    naddr = pws_address + "as8"
                    self.nodes[naddr].setDriver('GV0', data['feelsLike8'])
                if 'dewPoint8' in data:
                    naddr = pws_address + "as8"
                    self.nodes[naddr].setDriver('GV1', data['dewPoint8'])

        def disconnect_method():
            """Print a simple "goodbye" message."""
            LOGGER.info('Client has disconnected from the websocket')
            LOGGER.info('Attempting to reconnect')
            client.websocket.connect()

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
        {'driver': 'ST', 'value': 0, 'uom': 2}
        ]

    id = 'PWS_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class BatteryInsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(BatteryInsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'BATLVL', 'value': 0, 'uom': 2},
        ]

    id = 'BATTIN_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class BatteryOutsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(BatteryOutsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'BATLVL', 'value': 0, 'uom': 2},
        ]

    id = 'BATT_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class TempOutsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(TempOutsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17},
        ]

    id = 'TEMPF_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class TempInsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(TempInsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17},
        ]

    id = 'TEMPINF_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class FeelsLikeOutsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(FeelsLikeOutsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17},
        ]

    id = 'FEELSLIKE_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class FeelsLikeInsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(FeelsLikeInsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17},
        ]

    id = 'FEELSLIKEIN_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class DewPointOutsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(DewPointOutsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17},
        ]

    id = 'DEWPOINT_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class DewPointInsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(DewPointInsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17},
        ]

    id = 'DEWPOINTIN_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class HumidityOutsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(HumidityOutsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLIHUM', 'value': 0, 'uom': 22},
        ]

    id = 'HUMIDITY_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class HumidityInsideNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(HumidityInsideNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLIHUM', 'value': 0, 'uom': 22},
        ]

    id = 'HUMIDITYIN_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class PressureNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(PressureNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'BARPRES', 'value': 0, 'uom': 23},
        {'driver': 'ATMPRES', 'value': 0, 'uom': 23}
        ]

    id = 'PRESSURE_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class RainHourNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(RainHourNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'WVOL', 'value': 0, 'uom': 105},
        ]

    id = 'RAINHOUR_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class RainDayNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(RainDayNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'WVOL', 'value': 0, 'uom': 105},
        ]

    id = 'RAINDAY_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class RainWeekNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(RainWeekNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'WVOL', 'value': 0, 'uom': 105},
        ]

    id = 'RAINWEEK_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class RainMonthNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(RainMonthNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'WVOL', 'value': 0, 'uom': 105},
        ]

    id = 'RAINMONTH_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class RainYearNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(RainYearNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'WVOL', 'value': 0, 'uom': 105},
        ]

    id = 'RAINYEAR_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class RainTotalNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(RainTotalNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'WVOL', 'value': 0, 'uom': 105},
        ]

    id = 'RAINTOTAL_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class RainEventNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(RainEventNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'WVOL', 'value': 0, 'uom': 105},
        ]

    id = 'RAINEVENT_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class SolarNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(SolarNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'SOLRAD', 'value': 0, 'uom': 74},
        {'driver': 'UV', 'value': 0, 'uom': 71},
        {'driver': 'LUMIN', 'value': 0, 'uom': 36}
        ]

    id = 'SOLAR_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class WindNode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(WindNode, self).__init__(controller, primary, address, name)

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
        {'driver': 'WINDDIR', 'value': 0, 'uom': 76},  # Wind Direction (degree)
        {'driver': 'GV0', 'value': 0, 'uom': 25},  # Wind Direction (cardinal)
        {'driver': 'SPEED', 'value': 0, 'uom': 48},  # Wind Speed
        {'driver': 'GV1', 'value': 0, 'uom': 48},  # Wind Gust
        {'driver': 'GV2', 'value': 0, 'uom': 48},  # Max Wind Gust Daily
        ]

    id = 'WIND_NODE'
    commands = {
                    # 'DON': setOn, 'DOF': setOff
                }


class WH31Node(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(WH31Node, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17},  # Temperature
        {'driver': 'CLIHUM', 'value': 0, 'uom': 22},  # Humidity
        {'driver': 'BATLVL', 'value': 0, 'uom': 2},  # Battery
        {'driver': 'GV0', 'value': 0, 'uom': 17},  # Feels Like
        {'driver': 'GV1', 'value': 0, 'uom': 17},  # Dew Point
        ]

    id = 'WH31_NODE'
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
