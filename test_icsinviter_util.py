import unittest
import util

class Testing(unittest.TestCase):

	def testDictmap(self):

		fn = lambda x: x + '-OK'
		result = { "var": { "mail_from_name": "Mailer" }, "Test": "OK" }
		expected = { "var": { "mail_from_name": "Mailer-OK" }, "Test": "OK-OK" }
		util.dictmap(fn, result)
		self.assertEqual(result, expected)

	def testExec(self):

		out, err = util.exec(['cat'], 'input')
		self.assertEqual(out, 'input')
		self.assertEqual(err, '')

		out, err = util.exec(['sh', '-c', 'echo ok'])
		self.assertEqual(out.strip(), 'ok')
		self.assertEqual(err.strip(), '')

		out, err = util.exec(['sh', '-c', 'echo error >&2'])
		self.assertEqual(out.strip(), '')
		self.assertEqual(err.strip(), 'error')

		out, err = util.exec(['false'])
		self.assertEqual(out.strip(), '')
		self.assertEqual(err.strip(), 'Process returned 1')

	def testLoadConfig(self):

		expected = util.loadJson('testdata/config-merged.json')
		result = util.loadConfig(['testdata/config1.json', 'testdata/config2.json'])
		self.assertEqual(result, expected)

	def testMerge(self):

		test1 = util.loadJson('testdata/config1.json')
		test2 = util.loadJson('testdata/config2.json')
		expected = util.loadJson('testdata/config-merged.json')
		result = util.merge(test1, test2)
		self.assertEqual(result, expected)
