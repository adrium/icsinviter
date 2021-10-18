import glob
import json
import re
import subprocess
import time

def main(config: dict):

	events = loadJson(config['events'])
	emlRequest = loadFile(config['template']['request'])
	emlCancel = loadFile(config['template']['cancel'])
	newevents = {}

	templatevars = {}
	templatevars['now_rfc2822'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
	templatevars['now_iso'] = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
	templatevars['dtstartfilter'] = time.strftime(config['dtstartfilter'], time.gmtime())
	templatevars.update(config['var'])

	for mail, url in config['feeds'].items():
		icsfeed, err = exec(config['cmd']['download'] + [url])
		try:
			icsfeed = imcToDict(icsfeed)
			icsfeed = icsfeed['vcalendar'][0]
		except Exception as e:
			# feed could not be loaded and previous events will be remembered
			if mail in events:
				newevents[mail] = events[mail]
			continue

		templatevars['mail_to'] = mail

		icsfile = {'vevent': []}
		icsfile.update(icsfeed)
		del icsfile['vevent']

		tocancel = { uid: True for uid in events[mail].keys() } if mail in events else {}
		newevents[mail] = {}

		for event in icsfeed['vevent']:

			uid = event[config['uid']]

			if event['dtstart'] < templatevars['dtstartfilter']:
				continue # event in the past

			if mail in events and uid in events[mail]:
				del tocancel[uid]
				issame = True
				for k in config['compare']:
					issame = issame and events[mail][uid][k] == event[k]
				if issame:
					newevents[mail][uid] = events[mail][uid]
					continue # event already synchronized
				else:
					event['sequence'] = str(1 + int(events[mail][uid].get('sequence', '0')))

			icsfile['method'] = 'REQUEST'
			icsfile['vevent'] = [ event ]

			for k, update in config['update'].items():
				if 'set' in update:
					event[k] = update['set']
				if 'render' in update:
					event[k] = render(update['render'], templatevars, icsfile)
				if 'pattern' in update:
					event[k] = re.sub(update['pattern'], update['repl'], event[k], flags = re.S)

			mailtext = render(emlRequest, templatevars, icsfile)
			if mailtext == '':
				continue # event not relevant

			_, err = exec(config['cmd']['sendmail'], mailtext)
			if err != '':
				continue # event could not be sent

			# event sent successfully and added to synchronized list
			newevents[mail][uid] = event

		for uid in tocancel.keys():

			event = {}
			event.update(events[mail][uid])

			icsfile['method'] = 'CANCEL'
			icsfile['vevent'] = [ event ]

			event['status'] = 'CANCELLED'
			event['sequence'] = str(1 + int(event.get('sequence', '0')))

			mailtext = render(emlCancel, templatevars, icsfile)
			if mailtext == '':
				continue # event not relevant

			_, err = exec(config['cmd']['sendmail'], mailtext)
			if err != '':
				# event could not be cancelled and kept in synchronized list
				newevents[mail][uid] = events[mail][uid]
				continue

	saveJson(config['events'], newevents)

def render(template: str, vars: dict, icsfile: dict) -> str:
	if (icsfile['vevent'][0]['dtstart'] < vars['dtstartfilter']):
		return ''

	v = {}
	v.update(vars)
	v.update(icsfile)
	v.update(icsfile['vevent'][0])

	v['ics'] = dictToImc({ 'vcalendar': [ icsfile ] })

	result = template.format(**v)

	return result

def exec(cmd: list, input: str = ''):
	pipe = subprocess.PIPE
	p = subprocess.run(cmd, input = input.encode('utf8'), stdout = pipe, stderr = pipe)
	result = (p.stdout.decode('utf8'), p.stderr.decode('utf8'))
	if p.returncode != 0 and result[1] == '':
		result = (result[0], 'Process returned %d' % p.returncode)
	return result

def loadConfig(files: str):
	result = {}
	for file in glob.glob(files):
		result.update(loadJson(file))
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
	main(loadConfig('config/*.json'))
