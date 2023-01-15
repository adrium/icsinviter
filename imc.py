def toDict(imc: str, suffix: str = '_p') -> dict:
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

def fromDict(imcdict: dict, suffix: str = '_p') -> str:

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
