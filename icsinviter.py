from datetime import datetime
from uuid import uuid1
import imc
import json
import re
import util

def main(config: dict):

	events = util.loadJson(config['events'])
	emlRequest = util.loadFile(config['template']['request'])
	emlCancel = util.loadFile(config['template']['cancel'])
	newevents = {}

	config['uuid()'] = lambda: uuid1(0x61647269756d)
	filters = config.get('filter', {})
	templatevars = config.get('var', {})
	dry = config.get('dry', False)
	logok = 'dry' if dry else 'ok'

	now = datetime.utcnow()
	mystrftime = lambda x: now.strftime(x) if isinstance(x, str) else x
	util.dictmap(mystrftime, filters)
	util.dictmap(mystrftime, templatevars)

	for mail, url in config['feeds'].items():
		newevents[mail] = events.setdefault(mail, {})

		icsfeed, err = util.exec(config['cmd']['download'] + [url])
		if err != '':
			logFeed('download', mail, url, err.strip())
			continue
		try:
			err = icsfeed.replace('\n', ' ')
			icsfeed = imc.toDict(icsfeed)
			icsfeed = icsfeed['vcalendar'][0]
		except Exception as e:
			logFeed('parse', mail, url, err[0:48])
			continue

		logFeed(logok, mail, url)
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
			set = util.merge({}, config.get('set', {}))
			util.dictmap(lambda x: render(x, var), set)

			util.merge(event, set)
			for k, update in config.get('replace', {}).items():
				event[k] = re.sub(update['pattern'], update['repl'], event[k], flags = re.S)

			mailtext = render(emlRequest, getVars(config['uuid()'], templatevars, mail, icsfile, True))

			if not dry:
				_, err = util.exec(config['cmd']['sendmail'], mailtext)
				if err != '':
					logEvent('sendmail', mail, icsfile, err.strip())
					continue

			logEvent(logok, mail, icsfile)
			newevents[mail][uid] = event

		for uid in tocancel.keys():

			event = util.merge({}, events[mail][uid])

			icsfile['method'] = 'CANCEL'
			icsfile['vevent'] = [ event ]

			event['status'] = 'CANCELLED'
			event['sequence'] = str(1 + int(event.get('sequence', '0')))

			if not includeEvent(event, filters, icsfile['method']):
				logEvent('ignore', mail, icsfile)
				continue

			mailtext = render(emlCancel, getVars(config['uuid()'], templatevars, mail, icsfile, True))

			if not dry:
				_, err = util.exec(config['cmd']['sendmail'], mailtext)
				if err != '':
					logEvent('sendmail', mail, icsfile, err.strip())
					newevents[mail][uid] = events[mail][uid]
					continue

			logEvent(logok, mail, icsfile)

	if not dry:
		util.saveJson(config['events'], newevents)

def render(template: str, vars: dict) -> str:
	return template.format(**vars)

def getVars(uuidfn, vars: dict, mail: str, icsfile: dict, withics: bool = False) -> dict:
	ics = imc.fromDict({ 'vcalendar': [ icsfile ] }) if withics else ''
	builtin = { 'mail_to': mail, 'uuid': uuidfn(), 'ics': ics }
	return util.merge(util.merge(util.merge(util.merge({}, vars), icsfile), icsfile['vevent'][0]), builtin)

def includeEvent(event: dict, filters: dict, method: str) -> bool:
	for k, p in filters.items():
		if not method.lower() in p.get('methods', [method.lower()]): continue
		if p['op'] == '<' and not event[k] < p['value']: return False
		if p['op'] == '>' and not event[k] > p['value']: return False
		if p['op'] == '=' and not event[k] == p['value']: return False
		if p['op'] == '~' and re.search(p['value'], event[k]) == None: return False
	return True

def logFeed(error, mail, url, detail = None):
	print(json.dumps({ 'error': error, 'url': url, 'mail': mail, 'detail': detail }))

def logEvent(error, mail, icsfile, detail = None):
	e = icsfile['vevent'][0]
	print(json.dumps({ 'error': error, 'method': icsfile['method'],
		'uid': e['uid'], 'dtstart': e['dtstart'], 'summary': e['summary'], 'mail': mail, 'detail': detail }))

if __name__ == '__main__':
	import sys
	main(util.loadConfig(sys.argv[1:]))
