import sys, os, re, json, yaml

def getvarnames(pattern, method):
    ''' Collect Variable Names (matched with pattern) from method prototype '''
    matchedcheck = re.search(pattern, method)
    if not matchedcheck:
        return -1, None

    varnames = [item.strip() for item in matchedcheck.group(1).split(',')]
    return len(varnames), varnames

def compose(template, varnames, varvalues):
    ''' Replace the template's variable names with values '''
    for s,t in dict(zip(varnames, varvalues)).items():
        template = template.replace(f'({s})', t)

    return template

def evaluate(content, thekey):
    ''' Evaluate a node string first class pattern nodes '''
    if thekey in content:
        return content[thekey]

    # With method names, such as, test(x,y) => {"test": "(x) (y)"}
    matched = re.search('\(([^\)]+)\)', thekey)
    if matched:
        methodname = thekey[:matched.start()].strip()
        varvalues = [item.strip() for item in matched.group(1).split(',')]
        lenval = len(varvalues)

        for method in content.keys():
            if not method.startswith(methodname):
                continue

            lenvar, varnames = getvarnames('\(([^\)]+)\)', method.strip())
            if lenval == lenvar:
                return compose(content[method], varnames, varvalues)

    # Without method names, such as, (x,y) => {"(x)": "(y)"}
    varvalues = [item.strip() for item in thekey.split(',')]
    lenval = len(varvalues)
    for method in content.keys():
        lenvar, varnames = getvarnames('^\(([^\)]+)\)$', method.strip())
        if lenval == lenvar:
            return compose(content[method], varnames, varvalues)

def traverse(content, itemptr):
    ''' Traverse all children node under itemptr (eg. goal node) '''
    if type(itemptr) is dict:
        result = []
        for thekey, thevalue in itemptr.items():
            o = json.loads('{' + evaluate(content, thekey) + '}')
            proceeds = traverse(content, thevalue)

            # hardcode here; which uses "Proceeds" to include all children node as a list
            o["Proceeds"] = proceeds if type(proceeds) is list else [proceeds]
            result.append(o)

        if len(result) == 1:
            return result[0]

        return result

    elif type(itemptr) is list:
        result = []
        for thevalue in itemptr:
            result.append(traverse(content, thevalue))

        if len(result) == 1:
            return result[0]

        return result

    elif type(itemptr) is str:
        # string will be expanded as an object
        return json.loads('{' + evaluate(content, itemptr) + '}')

if __name__ == '__main__':
    filespec = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), argv[1])
    fh = open(filespec, encoding='utf-8')
    content = yaml.load(fh, yaml.FullLoader)
    fh.close()
    # print(json.dumps(content, indent=4))

    result = traverse(content, content['Goal'])

    filespec = argv[2]
    fh = open(filespec, 'w+', encoding='utf-8')
    json.dump(result, fh, indent=4)
    print(json.dumps(result, indent=4))
    fh.close()
