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
				'test': 'Ok:Good',
				'test;type=str': 'Val',
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
				'test': 'Ok:Good',
				'test;type=str': 'Val',
				'sub': [ { 'x': 'X' } ],
			} ]
		}
		expected = (
			'BEGIN:OBJECT\n'
			'FOO:BAR\n'
			'LONG:start:\\nlongline longline longline longline longline longli\n'
			' ne longline longline longline longline\n'
			'TEST:Ok:Good\n'
			'TEST;TYPE=STR:Val\n'
			'BEGIN:SUB\n'
			'X:X\n'
			'END:SUB\n'
			'END:OBJECT\n'
		)

		result = icsinviter.dictToImc(input)

		self.assertEqual(result, expected)

	def test_main(self):
		self.maxDiff = None

		tmpfiles = [ tempfile.mkstemp()[1] for n in range(5) ]

		config = {
			'dtstartfilter': '%Y%m%d',
			'cmd': {
				'sendmail': ['tee', '-a', tmpfiles[0]],
				'download': ['cat'],
			},
			'var': {
				'mail-from': 'mailer@example.com'
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
					'dtstart': '20301010',
					'uid': 'id.new',
				},
			]
		} ] }

		self.saveFile(tmpfiles[2], icsinviter.dictToImc(data))

		data = '{mail-from} {mail-to} {uid} {summary}\n{ics}\n'
		self.saveFile(tmpfiles[3], 'REQUEST:' + data)
		self.saveFile(tmpfiles[4], 'CANCEL:' + data)

		expected = (
			'REQUEST:mailer@example.com user@example.com id.new event will be sent\n'
			'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:Test\nMETHOD:REQUEST\n'
			'BEGIN:VEVENT\nSUMMARY:event will be sent\nDTSTART:20301010\nUID:id.new\n'
			'ORGANIZER:mailto:mailer@example.com\nATTENDEE:mailto:user@example.com\nEND:VEVENT\nEND:VCALENDAR\n'
			'\n'
			'CANCEL:mailer@example.com user@example.com id.cancel event will be cancelled\n'
			'BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:Test\nMETHOD:CANCEL\n'
			'BEGIN:VEVENT\nSUMMARY:event will be cancelled\nDTSTART:20301010\nUID:id.cancel\n'
			'ORGANIZER:mailto:mailer@example.com\nATTENDEE:mailto:user@example.com\nSTATUS:CANCELLED\nSEQUENCE:1\nEND:VEVENT\nEND:VCALENDAR\n'
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
