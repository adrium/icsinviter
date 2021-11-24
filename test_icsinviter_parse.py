import icsinviter
import unittest
import testdata.helper

class Testing(unittest.TestCase):

	def testImcToDict(self):

		input = testdata.helper.loadFile('testdata/arbitrary.ics')
		expected = testdata.helper.loadJson('testdata/arbitrary.json')

		result = icsinviter.imcToDict(input)
		self.assertEqual(result, expected)

	def testDictToImc(self):

		input = testdata.helper.loadJson('testdata/arbitrary.json')
		expected = testdata.helper.loadFile('testdata/arbitrary.ics')

		expected = expected.replace('TEST:Missing\n', '')

		result = icsinviter.dictToImc(input)
		self.assertEqual(result, expected)

	def testParseVcf1(self):

		input = testdata.helper.loadFile('testdata/rfc2426.vcf')

		result = icsinviter.imcToDict(input)
		self.assertEqual('3.0', result['vcard'][0]['version'])
		self.assertEqual('Frank Dawson', result['vcard'][0]['fn'])
		self.assertEqual('fdawson@earthlink.net', result['vcard'][0]['email'])
		self.assertEqual('howes@netscape.com', result['vcard'][1]['email'])

	def testParseVcf2(self):

		input = testdata.helper.loadFile('testdata/rfc6350.vcf')

		result = icsinviter.imcToDict(input)
		self.assertEqual('4.0', result['vcard'][0]['version'])
		self.assertEqual('Simon Perreault', result['vcard'][0]['fn'])
		self.assertEqual('http://nomis80.org', result['vcard'][0]['url'])

	def testParseIcs1(self):

		input = testdata.helper.loadFile('testdata/rfc5545-event1.ics')

		result = icsinviter.imcToDict(input)
		self.assertEqual('2.0', result['vcalendar'][0]['version'])
		self.assertEqual('Networld+Interop Conference', result['vcalendar'][0]['vevent'][0]['summary'])

	def testParseIcs2(self):

		input = testdata.helper.loadFile('testdata/rfc5545-event2.ics')

		result = icsinviter.imcToDict(input)
		self.assertEqual('2.0', result['vcalendar'][0]['version'])
		self.assertEqual('America/New_York', result['vcalendar'][0]['vtimezone'][0]['tzid'])
		self.assertEqual('XYZ Project Review', result['vcalendar'][0]['vevent'][0]['summary'])

	def testParseIcs3(self):

		input = testdata.helper.loadFile('testdata/rfc5545-other.ics')

		result = icsinviter.imcToDict(input)
		self.assertEqual('AUDIO', result['vcalendar'][0]['vtodo'][0]['valarm'][0]['action'])
		self.assertEqual('Project Report,XYZ,Weekly Meeting', result['vcalendar'][1]['vjournal'][0]['categories'])
		self.assertEqual('mailto:jsmith@example.com', result['vcalendar'][2]['vfreebusy'][0]['organizer'])
