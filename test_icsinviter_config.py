import icsinviter
import unittest
import testdata.helper

class Testing(unittest.TestCase):

	def testLoadConfig(self):

		expected = testdata.helper.loadJson('testdata/config-merged.json')
		result = icsinviter.loadConfig(['testdata/config1.json', 'testdata/config2.json'])
		self.assertEqual(result, expected)
