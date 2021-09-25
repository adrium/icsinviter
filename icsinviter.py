import json
import subprocess
import time

def main():

	config = loadJson('config.json')

	events = loadJson(config['events'])
	emlRequest = loadFile(config['template']['request'])
	emlCancel = loadFile(config['template']['cancel'])
	newevents = {}

	templatevars = {}
	templatevars['now-rfc2822'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
	templatevars['now-iso'] = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
	templatevars['dtstartfilter'] = time.strftime(config['dtstartfilter'], time.gmtime())
	templatevars.update(config['var'])

	for mail, url in config['feeds'].items():

		p = subprocess.run(config['cmd']['download'] + [url], stdout = subprocess.PIPE)
		icsfeed = p.stdout.decode('utf8')
		icsfeed = imcToDict(icsfeed)
		icsfeed = icsfeed['vcalendar'][0]

		templatevars['mail-to'] = mail

		icsfile = {'vevent': []}
		icsfile.update(icsfeed)
		del icsfile['vevent']

		tocancel = {}
		newevents[mail] = {}

		if mail in events:
			for uid in events[mail].keys():
				tocancel[uid] = True

		for event in icsfeed['vevent']:

			uid = event['uid']

			if event['dtstart'] < templatevars['dtstartfilter']:
				continue

			newevents[mail][uid] = event

			event['organizer'] = 'mailto:' + templatevars["mail-from"]
			event['attendee'] = 'mailto:' + templatevars["mail-to"]

			icsfile['method'] = 'REQUEST'
			icsfile['vevent'] = [ event ]

			if mail in events and uid in events[mail]:
				del tocancel[uid]
				continue

			mailtext = render(emlRequest, templatevars, icsfile)
			if mailtext != '':
				p = subprocess.run(config['cmd']['sendmail'], input = mailtext.encode('utf8'))

		for uid in tocancel.keys():

			icsfile['method'] = 'CANCEL'
			icsfile['vevent'] = [ events[mail][uid] ]
			icsfile['vevent'][0]['status'] = 'CANCELLED'
			icsfile['vevent'][0]['sequence'] = '1'

			mailtext = render(emlCancel, templatevars, icsfile)
			if mailtext != '':
				p = subprocess.run(config['cmd']['sendmail'], input = mailtext.encode('utf8'))

	saveJson(config['events'], newevents)

def render(template: str, vars: dict, icsfile: dict) -> str:
	if (icsfile['vevent'][0]['dtstart'] < vars['dtstartfilter']):
		return ''

	vars.update(icsfile)
	vars.update(icsfile['vevent'][0])

	vars['ics'] = dictToImc({ 'vcalendar': [ icsfile ] })

	result = template.format(**vars)

	return result

def loadJson(file: str) -> dict:
	result = {}
	with open(file) as f:
		result.update(json.load(f))
	return result

def saveJson(file: str, x: dict):
	with open(file, 'w') as f:
		json.dump(x, f, indent = 2)

def loadFile(filename: str) -> str:
	result = ''
	with open(filename) as f:
		result = f.read()

	return result

def imcToDict(imc: str) -> dict:
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

		[k, v] = line.split(':', maxsplit = 1)

		k = k.lower()
		v = v.replace('\\n', '\n')

		lines += [(k, v)]
		line = ''

	lines.reverse()

	result = imcToDictTreeImpl(None, iter(lines))
	return result

def imcToDictTreeImpl(scope: str, it) -> dict:
	result = {}

	while (x := next(it, None)) != None:

		k, v = x

		if k == 'begin':
			k = v.lower()
			v = imcToDictTreeImpl(k, it)

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

	if scope != None:
		raise TypeError('Missing END tag')

	return result

def dictToImc(imcdict: dict) -> str:

	result = ''

	for k, v in imcdict.items():
		if isinstance(v, list):
			for d in v:
				result += f'BEGIN:{k.upper()}\n'
				result += dictToImc(d)
				result += f'END:{k.upper()}\n'
			continue

		k = k.upper()
		v = v.replace('\n', '\\n')

		line = f'{k}:{v}'

		while len(line) > 64:
			result += line[0:64] + '\n'
			line = ' ' + line[64:]

		result += line + '\n'

	return result

main()
