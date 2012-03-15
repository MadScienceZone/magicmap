#
# vi:set ai sm nu ts=4 sw=4 expandtab:
#
from unittest import TestSuite, findTestCases
# XXX we really need subclassed exceptions from MapFileFormatError for specific failure types

def suite():
    modules_to_test = (
        'AnsiParserTest',
        'ConfigurationManagerTest',
        'MapCacheManagerTest',
        'MapDataHandlerTest',
        'MapPageTest',
        'MapRoomTest',
        'MapSourceTest',
        'NetworkIOTest',

        'ConversionScriptTest',
    )
    suite = TestSuite()
    for module in map(__import__, modules_to_test):
        suite.addTest(findTestCases(module))
    return suite
