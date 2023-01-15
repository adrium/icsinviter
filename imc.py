def toDict(imc: str, suffix: str = '_p') -> dict:
	mkkey = lambda s: s.lower().replace('-', '_')
	result = { 'LAST:END': True }
	lines = []

	for fileline in imc.split('\n'):
		if fileline[0:1] in [' ', '\t']:
			fileline = lines.pop() + fileline[1:]
		if fileline != '':
			lines.append(fileline)

	for line in lines:
		k, v = line.split(':', maxsplit = 1)
		k, *p = k.split(';')
		v = v.replace('\\n', '\n').replace('\r', '')
		x = f'END:{v}'

		if k == 'BEGIN':
			new = { x: result }
			result.setdefault(mkkey(v), []).append(new)
			result = new
			continue

		if k == 'END':
			result = result.pop(x)
			continue

		k = mkkey(k)
		x = k + suffix
		p = { mkkey(pk): pv for ps in p for pk, pv in [ ps.split('=', maxsplit = 1) ] }
		result[k] = v
		result[x] = p

		if result[x] == {}:
			del result[x]

	del result['LAST:END']
	return result

def fromDict(imcdict: dict, suffix: str = '_p') -> str:
	mkkey = lambda s: s.upper().replace('_', '-')
	result = ''

	for k, v in imcdict.items():
		if k.endswith(suffix):
			continue

		x = k + suffix
		k = mkkey(k)

		if isinstance(v, list):
			for item in v:
				result += f'BEGIN:{k}\n'
				result += fromDict(item, suffix)
				result += f'END:{k}\n'
			continue

		v = v.replace('\n', '\\n')
		p = imcdict.get(x, {})
		p = [ '='.join([ mkkey(pk), pv ]) for pk, pv in p.items() ]
		line = ';'.join([ k ] + p)
		line = ':'.join([ line, v ])

		while len(line) > 64:
			result += line[0:64] + '\n'
			line = ' ' + line[64:]

		result += line + '\n'

	return result
