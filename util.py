import json
import subprocess

def exec(cmd: list, input: str = ''):
	pipe = subprocess.PIPE
	p = subprocess.run(cmd, input = input.encode('utf8'), stdout = pipe, stderr = pipe)
	result = (p.stdout.decode('utf8'), p.stderr.decode('utf8'))
	if p.returncode != 0 and result[1] == '':
		result = (result[0], 'Process returned %d' % p.returncode)
	return result

def dictmap(fn, d: dict):
	for k, v in d.items():
		if isinstance(v, dict): dictmap(fn, v)
		else: d[k] = fn(v)

def merge(d1: dict, d2: dict) -> dict:
	for k, v in d2.items():
		if isinstance(d2[k], dict) and isinstance(d1.setdefault(k, {}), dict): merge(d1[k], d2[k])
		else: d1[k] = d2[k]
	return d1

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

def saveFile(fn, s):
	with open(fn, 'w') as f:
		f.write(s)
