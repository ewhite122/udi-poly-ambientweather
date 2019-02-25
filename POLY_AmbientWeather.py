#!/usr/bin/env python3
"""
This is a NodeServer template for Polyglot v2 written in Python2/3
by Einstein.42 (James Milne) milne.james@gmail.com
"""
try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import sys
import time
import requests
import json

"""
Import the polyglot interface module. This is in pypy so you can just install it
normally. Replace pip with pip3 if you are using python3.

Virtualenv:
pip install polyinterface

Not Virutalenv:
pip install polyinterface --user

*I recommend you ALWAYS develop your NodeServers in virtualenv to maintain
cleanliness, however that isn't required. I do not condone installing pip
modules globally. Use the --user flag, not sudo.
"""

LOGGER = polyinterface.LOGGER
"""
polyinterface has a LOGGER that is created by default and logs to:
logs/debug.log
You can use LOGGER.info, LOGGER.warning, LOGGER.debug, LOGGER.error levels as needed.
"""

class Controller(polyinterface.Controller):
    """
    The Controller Class is the primary node from an ISY perspective. It is a Superclass
    of polyinterface.Node so all methods from polyinterface.Node are available to this
    class as well.

    Class Variables:
    self.nodes: Dictionary of nodes. Includes the Controller node. Keys are the node addresses
    self.name: String name of the node
    self.address: String Address of Node, must be less than 14 characters (ISY limitation)
    self.polyConfig: Full JSON config dictionary received from Polyglot for the controller Node
    self.added: Boolean Confirmed added to ISY as primary node
    self.config: Dictionary, this node's Config

    Class Methods (not including the Node methods):
    start(): Once the NodeServer config is received from Polyglot this method is automatically called.
    addNode(polyinterface.Node, update = False): Adds Node to self.nodes and polyglot/ISY. This is called
        for you on the controller itself. Update = True overwrites the existing Node data.
    updateNode(polyinterface.Node): Overwrites the existing node data here and on Polyglot.
    delNode(address): Deletes a Node from the self.nodes/polyglot and ISY. Address is the Node's Address
    longPoll(): Runs every longPoll seconds (set initially in the server.json or default 10 seconds)
    shortPoll(): Runs every shortPoll seconds (set initially in the server.json or default 30 seconds)
    query(): Queries and reports ALL drivers for ALL nodes to the ISY.
    getDriver('ST'): gets the current value from Polyglot for driver 'ST' returns a STRING, cast as needed
    runForever(): Easy way to run forever without maxing your CPU or doing some silly 'time.sleep' nonsense
                  this joins the underlying queue query thread and just waits for it to terminate
                  which never happens.
    """
    def __init__(self, polyglot):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.
        """
        super(Controller, self).__init__(polyglot)
        self.name = 'Ambient Weather'
        self.APP_Key = '072059fe7f804c468689496e8249124f2e5457906cf44938a097bc07ea6efdc5'

    def start(self):
        """
        Optional.
        Polyglot v2 Interface startup done. Here is where you start your integration.
        This will run, once the NodeServer connects to Polyglot and gets it's config.
        In this example I am calling a discovery method. While this is optional,
        this is where you should start. No need to Super this method, the parent
        version does nothing.
        """
        LOGGER.info('Started MyNodeServer')
        # Remove all existing notices
        self.removeNoticesAll()
        if self.check_params():
            self.discover()
        

    def shortPoll(self):
        """
        Optional.
        This runs every 10 seconds. You would probably update your nodes either here
        or longPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        pass

    def longPoll(self):
        """
        Optional.
        This runs every 30 seconds. You would probably update your nodes either here
        or shortPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        #pass
        self.ambientPoll()

    def awConnect(self):
        try:
            ApiUrl = 'https://api.ambientweather.net/v1/devices?applicationKey=' + self.APP_Key + '&apiKey=' + self.API_Key
            r = requests.get(ApiUrl)
            Data = r.json()
            return Data
        except Exception as ex:
            LOGGER.error('Ambient Weather Connection Error' + ' ' + str(ex))

    def luxConv(self, wm2):
        lux = round(wm2 / 0.0079, 2)
        return lux

    def ambientPoll(self):
        try:
            Data = self.awConnect()
            for node in self.nodes:
                for pws in Data:
                    rawMAC = pws['macAddress'].split(':')
                    macType = rawMAC[0] + rawMAC[1] + rawMAC[2]
                    pwsAddress = pws['macAddress'].replace(':','').lower()
                    newAddress = pwsAddress + '_1'

                    if pwsAddress == self.nodes[node].address:
                        # Convert solarradiation into lux
                        lux = self.luxConv(pws['lastData']['solarradiation'])
                        
                        self.nodes[node].setDriver('GV0', pws['lastData']['tempf'])
                        self.nodes[node].setDriver('GV1', pws['lastData']['tempinf'])
                        self.nodes[node].setDriver('GV2', pws['lastData']['humidity'])
                        self.nodes[node].setDriver('GV3', pws['lastData']['humidityin'])
                        self.nodes[node].setDriver('GV4', pws['lastData']['baromrelin'])
                        self.nodes[node].setDriver('GV5', pws['lastData']['baromabsin'])
                        self.nodes[node].setDriver('GV15', lux) # Use mw/2 converted data for lux
                        self.nodes[node].setDriver('GV7', pws['lastData']['uv'])
                        self.nodes[node].setDriver('GV8', pws['lastData']['solarradiation'])
                        self.nodes[node].setDriver('GV9', pws['lastData']['hourlyrainin']) 
                        self.nodes[node].setDriver('GV10', pws['lastData']['dailyrainin'])
                        self.nodes[node].setDriver('GV11', pws['lastData']['weeklyrainin'])
                        self.nodes[node].setDriver('GV12', pws['lastData']['monthlyrainin'])
                        
                        if macType == '000EC6': #Observer IP Module used by most Ambient PWS systems
                            self.nodes[node].setDriver('GV13', pws['lastData']['yearlyrainin'])

                        self.nodes[node].setDriver('GV14', pws['lastData']['totalrainin'])
                        self.nodes[node].setDriver('WINDDIR', pws['lastData']['winddir'])
                        self.nodes[node].setDriver('GV16', pws['lastData']['windspeedmph'])
                        self.nodes[node].setDriver('GV17', pws['lastData']['windgustmph'])
                        self.nodes[node].setDriver('GV18', pws['lastData']['maxdailygust'])
                        self.nodes[node].setDriver('GV19', pws['lastData']['feelsLike'])
                        self.nodes[node].setDriver('GV20', pws['lastData']['dewPoint'])

                    if newAddress == self.nodes[node].address:
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
        """
        Optional.
        By default a query to the control node reports the FULL driver set for ALL
        nodes back to ISY. If you override this method you will need to Super or
        issue a reportDrivers() to each node manually.
        """
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        """
        Example
        Do discovery here. Does not have to be called discovery. Called from example
        controller start method and from DISCOVER command recieved from ISY as an exmaple.
        """

        try:
            Data = self.awConnect()
            for pws in Data:
                #LOGGER.info(pws['macAddress'])
                #LOGGER.info(pws['info']['name'])
                rawMAC = pws['macAddress'].split(':')
                macType = rawMAC[0] + rawMAC[1] + rawMAC[2]
                pwsAddress = pws['macAddress'].replace(':','').lower()
                pwsName = str(pws['info']['name'])
                #addOnAddress = pwsName.replace('-','').lower() + 'addon'
                newAddress = pwsAddress + '_1'

                if macType == '000EC6': #Observer IP Module used by most Ambient PWS systems
                    self.addNode(pwsnode(self, self.address, pwsAddress, pwsName))
                    self.addNode(addonnode(self, self.address, newAddress, pwsName + '-Addon'))
                elif macType == 'ECFABC': #WS-2902
                    self.addNode(pwsnode(self, self.address, pwsAddress, pwsName))
                else: #All other Ambient systems
                    self.addNode(pwsnode(self, self.address, pwsAddress, pwsName))
        except Exception as ex:
            LOGGER.error('Exception occured: ' + ' ' + str(ex))

    def delete(self):
        """
        Example
        This is sent by Polyglot upon deletion of the NodeServer. If the process is
        co-resident and controlled by Polyglot, it will be terminiated within 5 seconds
        of receiving this message.
        """
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def check_params(self):
        """
        This is an example of using custom Params for user and password and an example with a Dictionary
        """        

        if 'API_Key' in self.polyConfig['customParams']:
            self.API_Key = self.polyConfig['customParams']['API_Key']
            API_Set = True
        else:
            self.API_Key = ""
            self.addNotice('Please set proper API Key in the configuration page, and restart this nodeserver','mynotice')
            LOGGER.error('check_params: Ambient Weather user API key missing.  Using {}'.format(self.API_Key))
            API_Set = False

        self.addCustomParam({'API_Key': self.API_Key})

        # Add a notice if they need to change the user/password from the default.
        #if self.API_Key == None:
        #    self.addNotice('Please set proper API Key in the configuration page, and restart this nodeserver','mynotice')
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

    """
    Optional.
    Since the controller is the parent node in ISY, it will actual show up as a node.
    So it needs to know the drivers and what id it will use. The drivers are
    the defaults in the parent Class, so you don't need them unless you want to add to
    them. The ST and GV1 variables are for reporting status through Polyglot to ISY,
    DO NOT remove them. UOM 2 is boolean.
    """
    id = 'controller'
    commands = {
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'REMOVE_NOTICES_ALL': remove_notices_all
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class pwsnode(polyinterface.Node):
    """
    This is the class that all the Nodes will be represented by. You will add this to
    Polyglot/ISY with the controller.addNode method.

    Class Variables:
    self.primary: String address of the Controller node.
    self.parent: Easy access to the Controller Class from the node itself.
    self.address: String address of this Node 14 character limit. (ISY limitation)
    self.added: Boolean Confirmed added to ISY

    Class Methods:
    start(): This method is called once polyglot confirms the node is added to ISY.
    setDriver('ST', 1, report = True, force = False):
        This sets the driver 'ST' to 1. If report is False we do not report it to
        Polyglot/ISY. If force is True, we send a report even if the value hasn't changed.
    reportDrivers(): Forces a full update of all drivers to Polyglot/ISY.
    query(): Called when ISY sends a query request to Polyglot for this specific node
    """
    def __init__(self, controller, primary, address, name):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.

        :param controller: Reference to the Controller class
        :param primary: Controller address
        :param address: This nodes address
        :param name: This nodes name
        """
        super(pwsnode, self).__init__(controller, primary, address, name)

    def start(self):
        """
        Optional.
        This method is run once the Node is successfully added to the ISY
        and we get a return result from Polyglot. Only happens once.
        """
        self.setDriver('ST', 1)
        pass

    def setOn(self, command):
        """
        Example command received from ISY.
        Set DON on pwsnode.
        Sets the ST (status) driver to 1 or 'True'
        """
        self.setDriver('ST', 1)

    def setOff(self, command):
        """
        Example command received from ISY.
        Set DOF on pwsnode
        Sets the ST (status) driver to 0 or 'False'
        """
        self.setDriver('ST', 0)

    def query(self):
        """
        Called by ISY to report all drivers for this node. This is done in
        the parent class, so you don't need to override this method unless
        there is a need.
        """
        self.reportDrivers()

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
        {'driver': 'GV0', 'value': 0, 'uom': 17}, # Outside Temperature F
        {'driver': 'GV1', 'value': 0, 'uom': 17}, # Inside Temperature F
        {'driver': 'GV2', 'value': 0, 'uom': 22}, # Outside Humidity
        {'driver': 'GV3', 'value': 0, 'uom': 22}, # Inside Humidity
        {'driver': 'GV4', 'value': 0, 'uom': 23}, # Rel Pressure
        {'driver': 'GV5', 'value': 0, 'uom': 23}, # Abs Pressure
        {'driver': 'GV15', 'value': 0, 'uom': 36}, # Lux
        {'driver': 'GV7', 'value': 0, 'uom': 71}, # UV
        {'driver': 'GV8', 'value': 0, 'uom': 74}, # Solar Radiation
        {'driver': 'GV9', 'value': 0, 'uom': 105}, # Hourly Rain
        {'driver': 'GV10', 'value': 0, 'uom': 105}, # Daily Rain
        {'driver': 'GV11', 'value': 0, 'uom': 105}, # Weekly Rain
        {'driver': 'GV12', 'value': 0, 'uom': 105}, # Monthly Rain
        {'driver': 'GV13', 'value': 0, 'uom': 105}, # Yearly Rain
        {'driver': 'GV14', 'value': 0, 'uom': 105}, # Total Rain
        {'driver': 'WINDDIR', 'value': 0, 'uom': 76}, # Wind Direction
        {'driver': 'GV16', 'value': 0, 'uom': 48}, # Wind Speed
        {'driver': 'GV17', 'value': 0, 'uom': 48}, # Wind Gust
        {'driver': 'GV18', 'value': 0, 'uom': 48}, # Max Wind Gust Daily
        {'driver': 'GV19', 'value': 0, 'uom': 17}, # Feels Like Temperature
        {'driver': 'GV20', 'value': 0, 'uom': 17}, # Dew Point Temperature
        ]
    """
    Optional.
    This is an array of dictionary items containing the variable names(drivers)
    values and uoms(units of measure) from ISY. This is how ISY knows what kind
    of variable to display. Check the UOM's in the WSDK for a complete list.
    UOM 2 is boolean so the ISY will display 'True/False'
    """
    id = 'pwsnodetype'
    """
    id of the node from the nodedefs.xml that is in the profile.zip. This tells
    the ISY what fields and commands this node has.
    """
    commands = {
                    #'DON': setOn, 'DOF': setOff
                }
    """
    This is a dictionary of commands. If ISY sends a command to the NodeServer,
    this tells it which method to call. DON calls setOn, etc.
    """

class addonnode(polyinterface.Node):
    def __init__(self, controller, primary, address, name):
        super(addonnode, self).__init__(controller, primary, address, name)

    def start(self):
        self.setDriver('ST', 1)
        pass

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
    """
    Optional.
    This is an array of dictionary items containing the variable names(drivers)
    values and uoms(units of measure) from ISY. This is how ISY knows what kind
    of variable to display. Check the UOM's in the WSDK for a complete list.
    UOM 2 is boolean so the ISY will display 'True/False'
    """
    id = 'addontype'
    """
    id of the node from the nodedefs.xml that is in the profile.zip. This tells
    the ISY what fields and commands this node has.
    """
    commands = {
                    #'DON': setOn, 'DOF': setOff
                }
    """
    This is a dictionary of commands. If ISY sends a command to the NodeServer,
    this tells it which method to call. DON calls setOn, etc.
    """

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('MyNodeServer')
        """
        Instantiates the Interface to Polyglot.
        """
        polyglot.start()
        """
        Starts MQTT and connects to Polyglot.
        """
        control = Controller(polyglot)
        """
        Creates the Controller Node and passes in the Interface
        """
        control.runForever()
        """
        Sits around and does nothing forever, keeping your program running.
        """
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
        """
        Catch SIGTERM or Control-C and exit cleanly.
        """
