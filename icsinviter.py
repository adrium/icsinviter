from datetime import datetime
from uuid import uuid1
import json
import re
import subprocess

def main(config: dict):

	events = loadJson(config['events'])
	emlRequest = loadFile(config['template']['request'])
	emlCancel = loadFile(config['template']['cancel'])
	newevents = {}

	config['uuid()'] = lambda: uuid1(0x61647269756d)
	filters = config.get('filter', {})
	templatevars = config.get('var', {})

	now = datetime.utcnow()
	mystrftime = lambda x: now.strftime(x) if isinstance(x, str) else x
	dictmap(mystrftime, filters)
	dictmap(mystrftime, templatevars)

	for mail, url in config['feeds'].items():
		newevents[mail] = events.setdefault(mail, {})

		icsfeed, err = exec(config['cmd']['download'] + [url])
		if err != '':
			logFeed('download', mail, url, err.strip())
			continue
		try:
			err = icsfeed.replace('\n', ' ')
			icsfeed = imcToDict(icsfeed)
			icsfeed = icsfeed['vcalendar'][0]
		except Exception as e:
			logFeed('parse', mail, url, err[0:48])
			continue

		logFeed('ok', mail, url)
		icsfile = icsfeed
		tocancel = { uid: True for uid in events[mail].keys() }
		newevents[mail] = {}

		for event in icsfeed.pop('vevent', []):

			uid = event[config.get('uid', 'uid')]

			if uid in events[mail]:
				del tocancel[uid]
				newevents[mail][uid] = events[mail][uid]

				issame = True
				for k in config.get('compare', []):
					issame = issame and events[mail][uid][k] == event[k]
				if issame:
					continue # event already synchronized
				else:
					event['uid'] = events[mail][uid]['uid']
					event['sequence'] = str(1 + int(events[mail][uid].get('sequence', '0')))

			icsfile['method'] = 'REQUEST'
			icsfile['vevent'] = [ event ]

			if not includeEvent(event, filters, icsfile['method']):
				logEvent('ignore', mail, icsfile)
				continue

			var = getVars(config['uuid()'], templatevars, mail, icsfile)
			set = merge({}, config.get('set', {}))
			dictmap(lambda x: render(x, var), set)

			merge(event, set)
			for k, update in config.get('replace', {}).items():
				event[k] = re.sub(update['pattern'], update['repl'], event[k], flags = re.S)

			mailtext = render(emlRequest, getVars(config['uuid()'], templatevars, mail, icsfile, True))

			_, err = exec(config['cmd']['sendmail'], mailtext)
			if err != '':
				logEvent('sendmail', mail, icsfile, err.strip())
				continue

			logEvent('ok', mail, icsfile)
			newevents[mail][uid] = event

		for uid in tocancel.keys():

			event = merge({}, events[mail][uid])

			icsfile['method'] = 'CANCEL'
			icsfile['vevent'] = [ event ]

			event['status'] = 'CANCELLED'
			event['sequence'] = str(1 + int(event.get('sequence', '0')))

			if not includeEvent(event, filters, icsfile['method']):
				logEvent('ignore', mail, icsfile)
				continue

			mailtext = render(emlCancel, getVars(config['uuid()'], templatevars, mail, icsfile, True))

			_, err = exec(config['cmd']['sendmail'], mailtext)
			if err != '':
				logEvent('sendmail', mail, icsfile, err.strip())
				newevents[mail][uid] = events[mail][uid]
				continue

			logEvent('ok', mail, icsfile)

	saveJson(config['events'], newevents)

def render(template: str, vars: dict) -> str:
	return template.format(**vars)

def getVars(uuidfn, vars: dict, mail: str, icsfile: dict, withics: bool = False) -> dict:
	ics = dictToImc({ 'vcalendar': [ icsfile ] }) if withics else ''
	builtin = { 'mail_to': mail, 'uuid': uuidfn(), 'ics': ics }
	return merge(merge(merge(merge({}, vars), icsfile), icsfile['vevent'][0]), builtin)

def includeEvent(event: dict, filters: dict, method: str) -> bool:
	for k, p in filters.items():
		if not method.lower() in p.get('methods', [method.lower()]): continue
		if p['op'] == '<' and not event[k] < p['value']: return False
		if p['op'] == '>' and not event[k] > p['value']: return False
		if p['op'] == '=' and not event[k] == p['value']: return False
		if p['op'] == '~' and re.search(p['value'], event[k]) == None: return False
	return True

def exec(cmd: list, input: str = ''):
	pipe = subprocess.PIPE
	p = subprocess.run(cmd, input = input.encode('utf8'), stdout = pipe, stderr = pipe)
	result = (p.stdout.decode('utf8'), p.stderr.decode('utf8'))
	if p.returncode != 0 and result[1] == '':
		result = (result[0], 'Process returned %d' % p.returncode)
	return result

def logFeed(error, mail, url, detail = None):
	print(json.dumps({ 'error': error, 'url': url, 'mail': mail, 'detail': detail }))

def logEvent(error, mail, icsfile, detail = None):
	e = icsfile['vevent'][0]
	print(json.dumps({ 'error': error, 'method': icsfile['method'],
		'uid': e['uid'], 'dtstart': e['dtstart'], 'summary': e['summary'], 'mail': mail, 'detail': detail }))

def loadConfig(files: list):
	result = {}
	for file in files: merge(result, loadJson(file))
	return result

def loadJson(file: str) -> dict:
	with open(file) as f:
		return json.load(f)

def saveJson(file: str, x: dict):
	with open(file, 'w') as f:
		json.dump(x, f, indent = 2)

def loadFile(filename: str) -> str:
	with open(filename) as f:
		return f.read()

def dictmap(fn, d: dict):
	for k, v in d.items():
		if isinstance(v, dict): dictmap(fn, v)
		else: d[k] = fn(v)

def merge(d1: dict, d2: dict) -> dict:
	for k, v in d2.items():
		if isinstance(d2[k], dict) and isinstance(d1.setdefault(k, {}), dict): merge(d1[k], d2[k])
		else: d1[k] = d2[k]
	return d1

def imcToDict(imc: str, suffix: str = '_p') -> dict:
	lines = []
	line = ''

	for fileline in reversed(imc.split('\n')):
		fileline = fileline.replace('\r', '')

		if fileline[0:1] in [' ', '\t']:
			line = fileline[1:] + line
			continue

		line = fileline + line

		if line == '':
			continue

		k, v = line.split(':', maxsplit = 1)
		v = v.replace('\\n', '\n')
		p = k.split(';')
		k = p[0].lower()
		p = { pk.lower(): pv for ps in p[1:] for pk, pv in [ ps.split('=', maxsplit = 1) ] }

		lines += [(k, v, p)]
		line = ''

	lines.reverse()

	result = imcToDictTreeImpl(None, suffix, iter(lines))
	return result

def imcToDictTreeImpl(scope: str, suffix: str, it) -> dict:
	result = {}

	while (x := next(it, None)) != None:

		k, v, p = x

		if k == 'begin':
			k = v.lower()
			v = imcToDictTreeImpl(k, suffix, it)

			if not k in result:
				result[k] = []

			result[k] += [v]

		elif k == 'end':
			k = v.lower()

			if scope != k:
				raise TypeError('Invalid nesting')

			return result

		else:
			result[k] = v
			if p != {}:
				result[k + suffix] = p

	if scope != None:
		raise TypeError('Missing END tag')

	return result

def dictToImc(imcdict: dict, suffix: str = '_p') -> str:

	result = ''

	for k, v in imcdict.items():
		if k.endswith(suffix):
			continue

		if isinstance(v, list):
			for d in v:
				result += f'BEGIN:{k.upper()}\n'
				result += dictToImc(d)
				result += f'END:{k.upper()}\n'
			continue

		p = imcdict[k + suffix] if k + suffix in imcdict else {}
		v = v.replace('\n', '\\n')
		k = k.upper()

		for pk, pv in p.items():
			k += f';{pk.upper()}={pv}'

		line = f'{k}:{v}'

		while len(line) > 64:
			result += line[0:64] + '\n'
			line = ' ' + line[64:]

		result += line + '\n'

	return result

if __name__ == '__main__':
	import sys
	main(loadConfig(sys.argv[1:]))
