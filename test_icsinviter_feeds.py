import icsinviter
import os
import unittest
import tempfile
import testdata.helper

class Testing(unittest.TestCase):

	def setUp(self):

		self.maxDiff = None
		self.tmpfiles = [ tempfile.mkstemp()[1] for n in range(2) ]
		self.config = {
			'filter': {
				'dtstart': { 'op': '>', 'value': '2021' },
			},
			'cmd': {
				'sendmail': ['tee', '-a', self.tmpfiles[0]],
				'download': ['cat'],
			},
			'events': self.tmpfiles[1],
			'template': {
				'request': 'testdata/template.txt',
				'cancel': 'testdata/template.txt',
			},
		}
		testdata.helper.saveFile(self.config['events'], '{}')

	def tearDown(self):

		_ = [ os.unlink(fn) for fn in self.tmpfiles ]

	def testFeedHumanityEmpty(self):

		mail = 'humanity_empty@example.com'
		self.config['feeds'] = { mail: 'testdata/humanity-empty.ics' }
		icsinviter.main(self.config)

		self.assertOutput('/dev/null')

	def testFeedHumanityLive(self):

		mail = 'humanity_live@example.com'
		self.config['compare'] = [ 'dtstart', 'dtend' ]
		self.config['update'] = {
			'summary': { 'render': '{description}', 'pattern': r'([\w.-]+).+', 'repl': r'Shift \1' },
			'attendee': { 'render': 'mailto:{mail_to}' },
			'attendee_p': { 'set': { 'rsvp': 'FALSE' } },
		}

		self.config['filter']['dtstart']['value'] = '20211101'
		self.config['feeds'] = { mail: 'testdata/humanity-live-1.ics' }
		icsinviter.main(self.config)

		self.config['filter']['dtstart']['value'] = '20211110'
		self.config['feeds'] = { mail: 'testdata/humanity-live-2.ics' }
		icsinviter.main(self.config)

		self.config['filter']['dtstart']['value'] = '20211120'
		self.config['feeds'] = { mail: 'testdata/humanity-live-3.ics' }
		icsinviter.main(self.config)

		self.assertOutput('testdata/humanity-live-result.txt')

		events = testdata.helper.loadJson(self.config['events'])

		self.assertEqual(len(events[mail]), 1)
		self.assertIn('773212438.humanity.com', events[mail])

	def testFeedDoodle(self):

		mail = 'doodle@example.com'
		self.config['compare'] = [ 'x-microsoft-cdo-busystatus' ]

		self.config['feeds'] = { mail: 'testdata/doodle-tentative.ics' }
		icsinviter.main(self.config)

		self.config['feeds'] = { mail: 'testdata/doodle-set.ics' }
		icsinviter.main(self.config)

		self.assertOutput('testdata/doodle-result.txt')

	def testFeedFerienwiki(self):

		self.config['uid'] = 'summary'
		self.config['compare'] = [ 'description' ]

		self.config['feeds'] = { 'ferienwiki@example.com': 'testdata/ferienwiki-zurich-1.ics' }
		icsinviter.main(self.config)

		self.config['feeds'] = { 'ferienwiki@example.com': 'testdata/ferienwiki-zurich-2.ics' }
		icsinviter.main(self.config)

		self.assertOutput('testdata/ferienwiki-zurich-result.txt')

	def testFeedProcessingErrors(self):

		mail = 'processing_errors@example.com'
		testcmds = [ self.config['cmd'] ]
		testcmds.insert(0, { 'download': self.config['cmd']['download'], 'sendmail': ['false'] })
		testcmds.insert(0, { 'download': ['sh', '-c', 'echo GARBAGE'] })
		testcmds.insert(0, { 'download': ['sh', '-c', 'echo DLERROR 1>&2'] })

		self.config['compare'] = [ 'x-microsoft-cdo-busystatus' ]

		self.config['feeds'] = { mail: 'testdata/doodle-tentative.ics' }

		for testcmd in testcmds:
			self.config['cmd'] = testcmd
			icsinviter.main(self.config)

		self.config['feeds'] = { mail: 'testdata/doodle-set.ics' }

		for testcmd in testcmds:
			self.config['cmd'] = testcmd
			icsinviter.main(self.config)

		self.assertOutput('testdata/doodle-result.txt')

	def assertOutput(self, fn):

		expected = testdata.helper.loadFile(fn)
		result = testdata.helper.loadFile(self.tmpfiles[0])
		self.assertEqual(result, expected)
