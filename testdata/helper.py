import json

def loadFile(fn):
	with open(fn) as f:
		return f.read()

def saveFile(fn, s):
	with open(fn, 'w') as f:
		f.write(s)

def loadJson(fn):
	with open(fn) as f:
		return json.load(f)

def saveJson(fn, x):
	with open(fn, 'w') as f:
		json.dump(x, f, indent = 1)
