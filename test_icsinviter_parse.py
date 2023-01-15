import imc
import unittest
import util

class Testing(unittest.TestCase):

	def testImcToDict(self):

		input = util.loadFile('testdata/arbitrary.ics')
		expected = util.loadJson('testdata/arbitrary.json')

		result = imc.toDict(input)
		self.assertEqual(result, expected)

	def testDictToImc(self):

		input = util.loadJson('testdata/arbitrary.json')
		expected = util.loadFile('testdata/arbitrary.ics')

		expected = expected.replace('TEST-OVERWRITE;TYPE=Str:Missing\n', '')

		result = imc.fromDict(input)
		self.assertEqual(result, expected)

	def testParseVcf1(self):

		input = util.loadFile('testdata/rfc2426.vcf')

		result = imc.toDict(input)
		self.assertEqual('3.0', result['vcard'][0]['version'])
		self.assertEqual('Frank Dawson', result['vcard'][0]['fn'])
		self.assertEqual('fdawson@earthlink.net', result['vcard'][0]['email'])
		self.assertEqual('howes@netscape.com', result['vcard'][1]['email'])

	def testParseVcf2(self):

		input = util.loadFile('testdata/rfc6350.vcf')

		result = imc.toDict(input)
		self.assertEqual('4.0', result['vcard'][0]['version'])
		self.assertEqual('Simon Perreault', result['vcard'][0]['fn'])
		self.assertEqual('http://nomis80.org', result['vcard'][0]['url'])

	def testParseIcs1(self):

		input = util.loadFile('testdata/rfc5545-event1.ics')

		result = imc.toDict(input)
		self.assertEqual('2.0', result['vcalendar'][0]['version'])
		self.assertEqual('Networld+Interop Conference', result['vcalendar'][0]['vevent'][0]['summary'])

	def testParseIcs2(self):

		input = util.loadFile('testdata/rfc5545-event2.ics')

		result = imc.toDict(input)
		self.assertEqual('2.0', result['vcalendar'][0]['version'])
		self.assertEqual('America/New_York', result['vcalendar'][0]['vtimezone'][0]['tzid'])
		self.assertEqual('XYZ Project Review', result['vcalendar'][0]['vevent'][0]['summary'])

	def testParseIcs3(self):

		input = util.loadFile('testdata/rfc5545-other.ics')

		result = imc.toDict(input)
		self.assertEqual('AUDIO', result['vcalendar'][0]['vtodo'][0]['valarm'][0]['action'])
		self.assertEqual('Project Report,XYZ,Weekly Meeting', result['vcalendar'][1]['vjournal'][0]['categories'])
		self.assertEqual('mailto:jsmith@example.com', result['vcalendar'][2]['vfreebusy'][0]['organizer'])
