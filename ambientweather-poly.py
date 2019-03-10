#!/usr/bin/env python3

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import sys
import time
import requests
import json
import asyncio
from aiohttp import ClientSession
from aioambient import Client

LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'Ambient Weather'
        self.APP_Key = '072059fe7f804c468689496e8249124f2e5457906cf44938a097bc07ea6efdc5'

    def start(self):
        LOGGER.info('Started AmbientWeather')
        self.removeNoticesAll()
        if self.check_params():
            LOGGER.info('Configuration is set')
            LOOP = asyncio.new_event_loop()
            LOOP.create_task(self.AmbientWeather(self.APP_Key, self.API_Key))
            LOOP.run_forever()
        else:
            LOGGER.info('API Key is not set')

    def shortPoll(self):
        pass

    def longPoll(self):
        pass
        #self.ambientPoll()

    def awConnect(self):
        try:
            ApiUrl = 'https://api.ambientweather.net/v1/devices?applicationKey=' + self.APP_Key + '&apiKey=' + self.API_Key
            r = requests.get(ApiUrl)
            Data = r.json()
            return Data
        except Exception as ex:
            LOGGER.error('Ambient Weather Connection Error' + ' ' + str(ex))

    def luxConv(self, wm2):
        lux = round(wm2 / 0.0079, 0)
        return lux
    
    def cardinalDirection(self, winddir):
        # Returns the Cardinal Direction Name
        if winddir >=0 and winddir <=11.24:
            return 1
        elif winddir >=11.25 and winddir <=33.74:
            return 2
        elif winddir >=33.75 and winddir <=56.24:
            return 3
        elif winddir >=56.25 and winddir <=78.74:
            return 4
        elif winddir >=78.75 and winddir <=101.24:
            return 5
        elif winddir >=101.25 and winddir <=123.74:
            return 6
        elif winddir >=123.75 and winddir <=146.24:
            return 7
        elif winddir >=146.25 and winddir <=168.74:
            return 8
        elif winddir >=168.75 and winddir <=191.24:
            return 9
        elif winddir >=191.25 and winddir <=213.74:
            return 10
        elif winddir >=213.75 and winddir <=236.24:
            return 11
        elif winddir >=236.25 and winddir <=258.74:
            return 12
        elif winddir >=258.75 and winddir <=281.24:
            return 13
        elif winddir >=281.25 and winddir <=303.74:
            return 14
        elif winddir >=303.75 and winddir <=326.24:
            return 15
        elif winddir >=326.25 and winddir <=348.74:
            return 16
        elif winddir >=348.75 and winddir <=360:
            return 1
        else:
            return 0

    def ambientPoll(self):
        try:
            Data = self.awConnect()
            for node in self.nodes:
                for pws in Data:
                    rawMAC = pws['macAddress'].split(':')
                    macType = rawMAC[0] + rawMAC[1] + rawMAC[2]
                    pwsAddress = pws['macAddress'].replace(':','').lower()
                    addOnAddress = pwsAddress + '_1'

                    if pwsAddress == self.nodes[node].address:
                        # Convert solarradiation into lux
                        lux = self.luxConv(pws['lastData']['solarradiation'])
                        
                        # Convert Wind Direction Degrees to cardinal direction
                        cardinal = self.cardinalDirection(pws['lastData']['winddir'])

                        self.nodes[node].setDriver('CLITEMP', pws['lastData']['tempf'])
                        self.nodes[node].setDriver('GV1', pws['lastData']['tempinf'])
                        self.nodes[node].setDriver('CLIHUM', pws['lastData']['humidity'])
                        self.nodes[node].setDriver('GV3', pws['lastData']['humidityin'])
                        self.nodes[node].setDriver('BARPRES', pws['lastData']['baromrelin'])
                        self.nodes[node].setDriver('ATMPRES', pws['lastData']['baromabsin'])
                        self.nodes[node].setDriver('LUMIN', lux) # Use mw/2 converted data for lux
                        self.nodes[node].setDriver('UV', pws['lastData']['uv'])
                        self.nodes[node].setDriver('SOLRAD', pws['lastData']['solarradiation'])
                        self.nodes[node].setDriver('GV9', pws['lastData']['hourlyrainin']) 
                        self.nodes[node].setDriver('GV10', pws['lastData']['dailyrainin'])
                        self.nodes[node].setDriver('GV11', pws['lastData']['weeklyrainin'])
                        self.nodes[node].setDriver('GV12', pws['lastData']['monthlyrainin'])
                        
                        if macType == '000EC6': #Observer IP Module used by most Ambient PWS systems
                            self.nodes[node].setDriver('GV13', pws['lastData']['yearlyrainin'])

                        self.nodes[node].setDriver('GV14', pws['lastData']['totalrainin'])
                        self.nodes[node].setDriver('WINDDIR', pws['lastData']['winddir'])
                        self.nodes[node].setDriver('GV16', cardinal)
                        self.nodes[node].setDriver('SPEED', pws['lastData']['windspeedmph'])
                        self.nodes[node].setDriver('GV17', pws['lastData']['windgustmph'])
                        self.nodes[node].setDriver('GV18', pws['lastData']['maxdailygust'])
                        self.nodes[node].setDriver('GV19', pws['lastData']['feelsLike'])
                        self.nodes[node].setDriver('GV20', pws['lastData']['dewPoint'])

                    if addOnAddress == self.nodes[node].address:
                        if 'temp1f' in pws['lastData']:
                            self.nodes[node].setDriver('GV0', pws['lastData']['temp1f'])
                        if 'temp2f' in pws['lastData']:
                            self.nodes[node].setDriver('GV1', pws['lastData']['temp2f'])
                        if 'temp3f' in pws['lastData']:
                            self.nodes[node].setDriver('GV2', pws['lastData']['temp3f'])
                        if 'temp4f' in pws['lastData']:
                            self.nodes[node].setDriver('GV3', pws['lastData']['temp4f'])
                        if 'temp5f' in pws['lastData']:
                            self.nodes[node].setDriver('GV4', pws['lastData']['temp5f'])
                        if 'temp6f' in pws['lastData']:
                            self.nodes[node].setDriver('GV5', pws['lastData']['temp6f'])
                        if 'temp7f' in pws['lastData']:
                            self.nodes[node].setDriver('GV6', pws['lastData']['temp7f'])
                        if 'temp8f' in pws['lastData']:
                            self.nodes[node].setDriver('GV7', pws['lastData']['temp8f'])
                        if 'humidity1' in pws['lastData']:
                            self.nodes[node].setDriver('GV8', pws['lastData']['humidity1'])
                        if 'humidity2' in pws['lastData']:
                            self.nodes[node].setDriver('GV9', pws['lastData']['humidity2'])
                        if 'humidity3' in pws['lastData']:
                            self.nodes[node].setDriver('GV10', pws['lastData']['humidity3'])
                        if 'humidity4' in pws['lastData']:
                            self.nodes[node].setDriver('GV11', pws['lastData']['humidity4'])
                        if 'humidity5' in pws['lastData']:
                            self.nodes[node].setDriver('GV12', pws['lastData']['humidity5'])
                        if 'humidity6' in pws['lastData']:
                            self.nodes[node].setDriver('GV13', pws['lastData']['humidity6'])
                        if 'humidity7' in pws['lastData']:
                            self.nodes[node].setDriver('GV14', pws['lastData']['humidity7'])
                        if 'humidity8' in pws['lastData']:
                            self.nodes[node].setDriver('GV15', pws['lastData']['humidity8'])
        except Exception as ex:
            LOGGER.error('Exception occured: ' + str(ex))

    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        try:
            Data = self.awConnect()
            for pws in Data:
                rawMAC = pws['macAddress'].split(':')
                macType = rawMAC[0] + rawMAC[1] + rawMAC[2]
                pwsAddress = pws['macAddress'].replace(':','').lower()
                pwsName = str(pws['info']['name'])
                addOnAddress = pwsAddress + '_1'

                if macType == '000EC6': #Observer IP Module used by most Ambient PWS systems
                    self.addNode(pwsnode(self, self.address, pwsAddress, pwsName))
                    self.addNode(addonnode(self, self.address, addOnAddress, pwsName + '-Addon'))
                elif macType == 'ECFABC': #WS-2902 Display
                    self.addNode(pwsnode(self, self.address, pwsAddress, pwsName))
                else: #All other Ambient systems
                    self.addNode(pwsnode(self, self.address, pwsAddress, pwsName))
        except Exception as ex:
            LOGGER.error('Exception occured: ' + ' ' + str(ex))

    def delete(self):
        LOGGER.info('Ambient Weather NodeServer:  Deleted')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def check_params(self):
        if 'API_Key' in self.polyConfig['customParams']:
            self.API_Key = self.polyConfig['customParams']['API_Key']
            if self.API_Key is not "":
                API_Set = True
            else:
                API_Set = False
        else:
            self.API_Key = ""
            self.addNotice('Please set proper API Key in the configuration page, and restart this nodeserver','mynotice')
            LOGGER.error('check_params: Ambient Weather user API key missing.  Using {}'.format(self.API_Key))
            API_Set = False

        self.addCustomParam({'API_Key': self.API_Key})

        if API_Set:
            return True
        else:
            return False

    def remove_notices_all(self,command):
        LOGGER.info('remove_notices_all:')
        # Remove all existing notices
        self.removeNoticesAll()

    def update_profile(self,command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    async def AmbientWeather(self, *args, **kwargs):
        """Create the aiohttp session and run."""
        async with ClientSession() as websession:
            client = Client(self.API_Key, self.APP_Key, websession)

        def connect_method():
            """Print a simple "hello" message."""
            LOGGER.info('Client has connected to the websocket')

        def subscribed_method(data):
            """Process the data received upon subscribing."""
            #LOGGER.info('Subscription data received: {0}'.format(data))
            pwsCount = 0
            for k,v in data.items():
                if k == 'devices':
                    pwsCount = len(v)
                    for pws in v:
                        rawMAC = pws['macAddress'].split(':')
                        macType = rawMAC[0] + rawMAC[1] + rawMAC[2]
                        pwsAddress = pws['macAddress'].replace(':','').lower()
                        pwsName = str(pws['info']['name'])
                        addOnAddress = pwsAddress + '_1'

                        if macType == '000EC6': #Observer IP Module used by most Ambient PWS systems
                            self.addNode(pwsnode(self, self.address, pwsAddress, pwsName))
                            self.addNode(addonnode(self, self.address, addOnAddress, pwsName + '-Addon'))
                        elif macType == 'ECFABC': #WS-2902 Display
                            self.addNode(pwsnode(self, self.address, pwsAddress, pwsName))
                        else: #All other Ambient systems
                            self.addNode(pwsnode(self, self.address, pwsAddress, pwsName))

                        #LOGGER.info(pws['info']['name'] + ' ' + pws['macAddress'])
            LOGGER.info('PWS Count: ' + str(pwsCount))

        def data_method(data):
            """Print the data received."""
            #print('Data received: {0}'.format(data))
            for node in self.nodes:
                rawMAC = data['macAddress'].split(':')
                macType = rawMAC[0] + rawMAC[1] + rawMAC[2]
                pwsAddress = data['macAddress'].replace(':','').lower()
                addOnAddress = pwsAddress + '_1'

                if pwsAddress == self.nodes[node].address:
                    # Convert solarradiation into lux
                    lux = self.luxConv(data['solarradiation'])
                    
                    # Convert Wind Direction Degrees to cardinal direction
                    cardinal = self.cardinalDirection(data['winddir'])

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
                    
                    if macType == '000EC6': #Observer IP Module used by most Ambient PWS systems
                        self.nodes[node].setDriver('GV13', data['yearlyrainin'])

                    self.nodes[node].setDriver('GV14', data['totalrainin'])
                    self.nodes[node].setDriver('WINDDIR', data['winddir'])
                    self.nodes[node].setDriver('GV16', cardinal)
                    self.nodes[node].setDriver('SPEED', data['windspeedmph'])
                    self.nodes[node].setDriver('GV17', data['windgustmph'])
                    self.nodes[node].setDriver('GV18', data['maxdailygust'])
                    self.nodes[node].setDriver('GV19', data['feelsLike'])
                    self.nodes[node].setDriver('GV20', data['dewPoint'])

                if addOnAddress == self.nodes[node].address:
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

        def disconnect_method(data):
            """Print a simple "goodbye" message."""
            LOGGER.info('Client has disconnected from the websocket')

        # Connect to the websocket:
        client.websocket.on_connect(connect_method)
        client.websocket.on_subscribed(subscribed_method)
        client.websocket.on_data(data_method)
        client.websocket.on_disconnect(disconnect_method)

        await client.websocket.connect()

        # At any point, disconnect from the websocket:
        #await client.websocket.disconnect()

    id = 'controller'
    commands = {
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]

class pwsnode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(pwsnode, self).__init__(controller, primary, address, name)

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
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17}, # Outside Temperature F
        {'driver': 'GV1', 'value': 0, 'uom': 17}, # Inside Temperature F
        {'driver': 'CLIHUM', 'value': 0, 'uom': 22}, # Outside Humidity
        {'driver': 'GV3', 'value': 0, 'uom': 22}, # Inside Humidity
        {'driver': 'BARPRES', 'value': 0, 'uom': 23}, # Rel Pressure
        {'driver': 'ATMPRES', 'value': 0, 'uom': 23}, # Abs Pressure
        {'driver': 'LUMIN', 'value': 0, 'uom': 36}, # Lux
        {'driver': 'UV', 'value': 0, 'uom': 71}, # UV
        {'driver': 'SOLRAD', 'value': 0, 'uom': 74}, # Solar Radiation
        {'driver': 'GV9', 'value': 0, 'uom': 105}, # Hourly Rain
        {'driver': 'GV10', 'value': 0, 'uom': 105}, # Daily Rain
        {'driver': 'GV11', 'value': 0, 'uom': 105}, # Weekly Rain
        {'driver': 'GV12', 'value': 0, 'uom': 105}, # Monthly Rain
        {'driver': 'GV13', 'value': 0, 'uom': 105}, # Yearly Rain
        {'driver': 'GV14', 'value': 0, 'uom': 105}, # Total Rain
        {'driver': 'WINDDIR', 'value': 0, 'uom': 76}, # Wind Direction (degree)
        {'driver': 'GV16', 'value': 0, 'uom': 25}, # Wind Direction (cardinal)
        {'driver': 'SPEED', 'value': 0, 'uom': 48}, # Wind Speed
        {'driver': 'GV17', 'value': 0, 'uom': 48}, # Wind Gust
        {'driver': 'GV18', 'value': 0, 'uom': 48}, # Max Wind Gust Daily
        {'driver': 'GV19', 'value': 0, 'uom': 17}, # Feels Like Temperature
        {'driver': 'GV20', 'value': 0, 'uom': 17}, # Dew Point Temperature
        ]

    id = 'pwsnodetype'
    commands = {
                    #'DON': setOn, 'DOF': setOff
                }

class addonnode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(addonnode, self).__init__(controller, primary, address, name)

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
        {'driver': 'GV0', 'value': 0, 'uom': 17}, # Sensor 1 Temperature
        {'driver': 'GV1', 'value': 0, 'uom': 17}, # Sensor 2 Temperature
        {'driver': 'GV2', 'value': 0, 'uom': 17}, # Sensor 3 Temperature
        {'driver': 'GV3', 'value': 0, 'uom': 17}, # Sensor 4 Temperature
        {'driver': 'GV4', 'value': 0, 'uom': 17}, # Sensor 5 Temperature
        {'driver': 'GV5', 'value': 0, 'uom': 17}, # Sensor 6 Temperature
        {'driver': 'GV6', 'value': 0, 'uom': 17}, # Sensor 7 Temperature
        {'driver': 'GV7', 'value': 0, 'uom': 17}, # Sensor 8 Temperature
        {'driver': 'GV8', 'value': 0, 'uom': 22}, # Sensor 1 Humidity
        {'driver': 'GV9', 'value': 0, 'uom': 22}, # Sensor 2 Humidity
        {'driver': 'GV10', 'value': 0, 'uom': 22}, # Sensor 3 Humidity
        {'driver': 'GV11', 'value': 0, 'uom': 22}, # Sensor 4 Humidity
        {'driver': 'GV12', 'value': 0, 'uom': 22}, # Sensor 5 Humidity
        {'driver': 'GV13', 'value': 0, 'uom': 22}, # Sensor 6 Humidity
        {'driver': 'GV14', 'value': 0, 'uom': 22}, # Sensor 7 Humidity
        {'driver': 'GV15', 'value': 0, 'uom': 22}, # Sensor 8 Humidity
        ]

    id = 'addontype'
    commands = {
                    #'DON': setOn, 'DOF': setOff
                }

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('AmbientWeather')
        polyglot.start()
        control = Controller(polyglot)
        #LOOP = asyncio.get_event_loop()
        #LOOP.create_task(control.AmbientWeatherWS())
        #LOOP.run_forever()
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)