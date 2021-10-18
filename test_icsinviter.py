import icsinviter
import json
import os
import unittest
import tempfile

class Testing(unittest.TestCase):

	def test_imcToDict(self):

		input = (
			'BEGIN:OBJECT\n'
			'FOO:BAR\n'
			'LONG:start:\\nlongline longline longline longline longline longli\n'
			' ne longline longline longline longline\n'
			'TEST:Ok:Good\n'
			'TEST;TYPE=Str:Val\n'
			'BEGIN:SUB\n'
			'X:X\n'
			'END:SUB\n'
			'END:OBJECT\n'
		)
		expected = {
			'object': [ {
				'foo': 'BAR',
				'long': 'start:\nlongline longline longline longline longline longline longline longline longline longline',
				'test': 'Val',
				'test_p': { 'type': 'Str' },
				'sub': [ { 'x': 'X' } ],
			} ]
		}

		result = icsinviter.imcToDict(input)

		self.assertEqual(result, expected)

	def test_dictToImc(self):

		input = {
			'object': [ {
				'foo': 'BAR',
				'long': 'start:\nlongline longline longline longline longline longline longline longline longline longline',
				'test': 'Val',
				'test_p': { 'type': 'Str' },
				'sub': [ { 'x': 'X' } ],
			} ]
		}
		expected = (
			'BEGIN:OBJECT\n'
			'FOO:BAR\n'
			'LONG:start:\\nlongline longline longline longline longline longli\n'
			' ne longline longline longline longline\n'
			'TEST;TYPE=Str:Val\n'
			'BEGIN:SUB\n'
			'X:X\n'
			'END:SUB\n'
			'END:OBJECT\n'
		)

		result = icsinviter.dictToImc(input)

		self.assertEqual(result, expected)

	def test_exec(self):
		out, err = icsinviter.exec(['sh', '-c', 'echo hello'])
		self.assertEqual(out, 'hello\n')
		self.assertEqual(err, '')

		out, err = icsinviter.exec(['sh', '-c', 'exit 2'])
		self.assertEqual(out, '')
		self.assertEqual(err, 'Process returned 2')

		out, err = icsinviter.exec(['sh', '-c', 'echo hello; echo error 1>&2; exit 2'])
		self.assertEqual(out, 'hello\n')
		self.assertEqual(err, 'error\n')

	def test_main(self):
		self.maxDiff = None

		tmpfiles = [ tempfile.mkstemp()[1] for n in range(5) ]

		config = {
			'dtstartfilter': '%Y%m%d',
			'uid': 'uid',
			'cmd': {
				'sendmail': ['tee', '-a', tmpfiles[0]],
				'download': ['cat'],
			},
			'var': {
				'mail_from': 'mailer@example.com'
			},
			'compare': [ 'dtstart' ],
			'update': {
				'summary': { 'render': '{description}', 'pattern': r'([\w-]+).+', 'repl': r'Shift \1' },
				'organizer': { 'render': 'mailto:{mail_from}' },
				'attendee': { 'render': 'mailto:{mail_to}' },
				'attendee_p': { 'set': { 'rsvp': 'FALSE' } },
			},
			'events': tmpfiles[1],
			'feeds': {
				'user@example.com': tmpfiles[2],
			},
			'template': {
				'request': tmpfiles[3],
				'cancel': tmpfiles[4],
			},
		}

		data = { 'user@example.com': {
			'id.existing': {
				'summary': 'event will not be sent again',
				'dtstart': '20301010',
				'uid': 'id.existing',
			},
			'id.update': {
				'summary': 'event needs update',
				'dtstart': '20301010',
				'uid': 'id.update',
				'sequence': '2',
			},
			'id.nocancel': {
				'summary': 'event is in the past',
				'dtstart': '20201010',
				'uid': 'id.nocancel',
			},
			'id.cancel': {
				'summary': 'event will be cancelled',
				'dtstart': '20301010',
				'uid': 'id.cancel',
				'organizer': 'mailto:mailer@example.com',
				'attendee': 'mailto:user@example.com',
			},
		} }
		self.saveJson(tmpfiles[1], data)

		data = { 'vcalendar': [ {
			'version': '2.0',
			'prodid': 'Test',
			'vevent': [
				{
					'summary': 'event will not be sent again',
					'dtstart': '20301010',
					'uid': 'id.existing',
				},
				{
					'summary': 'event will not be sent',
					'dtstart': '20201010',
					'uid': 'id.old',
				},
				{
					'summary': 'event will be sent',
					'description': 'E-SOC-8 --\nLocation: Zurich --\n',
					'dtstart': '20301010',
					'uid': 'id.new',
				},
				{
					'summary': 'event needs update',
					'description': 'Updated!',
					'dtstart': '20301020',
					'uid': 'id.update',
				},
			]
		} ] }

		self.saveFile(tmpfiles[2], icsinviter.dictToImc(data))

		data = '{mail_from} {mail_to} {uid} {summary}\n{ics}\n'
		self.saveFile(tmpfiles[3], 'REQUEST:' + data)
		self.saveFile(tmpfiles[4], 'CANCEL:' + data)

		expected = (
			'REQUEST:mailer@example.com user@example.com id.new Shift E-SOC-8\n'
			'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:Test\nMETHOD:REQUEST\n'
			'BEGIN:VEVENT\nSUMMARY:Shift E-SOC-8\n'
			'DESCRIPTION:E-SOC-8 --\\nLocation: Zurich --\\n\nDTSTART:20301010\nUID:id.new\n'
			'ORGANIZER:mailto:mailer@example.com\n'
			'ATTENDEE;RSVP=FALSE:mailto:user@example.com\nEND:VEVENT\nEND:VCALENDAR\n'
			'\n'
			'REQUEST:mailer@example.com user@example.com id.update Shift Updated\n'
			'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:Test\nMETHOD:REQUEST\n'
			'BEGIN:VEVENT\nSUMMARY:Shift Updated\n'
			'DESCRIPTION:Updated!\nDTSTART:20301020\nUID:id.update\nSEQUENCE:3\n'
			'ORGANIZER:mailto:mailer@example.com\n'
			'ATTENDEE;RSVP=FALSE:mailto:user@example.com\nEND:VEVENT\nEND:VCALENDAR\n'
			'\n'
			'CANCEL:mailer@example.com user@example.com id.cancel event will be cancelled\n'
			'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:Test\nMETHOD:CANCEL\n'
			'BEGIN:VEVENT\nSUMMARY:event will be cancelled\nDTSTART:20301010\nUID:id.cancel\n'
			'ORGANIZER:mailto:mailer@example.com\n'
			'ATTENDEE:mailto:user@example.com\nSTATUS:CANCELLED\nSEQUENCE:1\nEND:VEVENT\nEND:VCALENDAR\n'
			'\n'
		)

		icsinviter.main(config)
		result = self.loadFile(tmpfiles[0])
		self.assertEqual(result, expected)

		self.saveFile(tmpfiles[0], '')
		icsinviter.main(config)
		result = self.loadFile(tmpfiles[0])
		self.assertEqual(result, '')

		_ = [ os.unlink(fn) for fn in tmpfiles ]

	def loadFile(self, fn):
		with open(fn) as f:
			return f.read()

	def saveFile(self, fn, s):
		with open(fn, 'w') as f:
			f.write(s)

	def loadJson(self, fn):
		with open(fn) as f:
			return json.load(f)

	def saveJson(self, fn, x):
		with open(fn, 'w') as f:
			json.dump(x, f, indent = 2)
