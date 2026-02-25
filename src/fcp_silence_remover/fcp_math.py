from fractions import Fraction
import math

def unfrac(frac):
    """
    frac: 100/6000s
    """
    if frac == '0s':
        frac = '0/6000s'
    num, denom = frac[:-1].split('/')
    num = eval(num)
    denom = eval(denom)
    # reduce fraction first
    output = Fraction(num, denom)
    return output.numerator, output.denominator

# DEPRECIATED. NEVER USE IT, RESULTS DRIFT.
def fcpsec2float(text: str, fps: str='100/6000s') -> float:
    """
    text: xxxx/yyys

    output: float

    >>> fcpsec2float('4.866666666666666s', '100/6000s')
    4.866666666666666

    >>> fcpsec2float('346/60s', '100/6000s')
    5.766666666666667
    """
    if text == '0s':
        num, denom = unfrac(fps)
        text = f'0/{denom}s'
    output = float(Fraction(text[:-1]))
    #print(f"fcpsec2float input: {text}, output: {output}")
    return output

# DEPRECIATED. NEVER USE IT, RESULTS DRIFT.
def float2fcpsec(x: float, fps: str='100/6000s') -> str:
    """
    x: xxx.yy
    fps: 100/6000s

    output: aaaaaa/bbs
    """
    num, denom = unfrac(fps)
    # round x to the nearest lower multiple of num
    # lower because otherwise it might indicate a region out of the media scope.
    numerator = math.floor(x * denom / num) * num
    output = f"{numerator}/{denom}s"
    #print(f"input: {x}, output: {output}")
    #print(f"input: {x}")
    return output

def fcpsec2frac(text: str):
    if not ('/' in text):
        text = text[:-1] + '/1s'
    return Fraction(text[:-1])

def frac2fcpsec(frac, fps='100/6000s'):
    num, denom = unfrac(fps)
    frac = frac.limit_denominator(denom)
    return f"{frac.numerator}/{frac.denominator}s"

def fcpsec_add(a: str, b: str, fps: str='100/6000s') -> str:
    """
    a: xxxx/yys
    b: aaaa/bbs
    fps: 100/6000s

    returns a plus b
    """
    # convert to common denominator fractions
    # add
    # return in a fcpsec format
    #a = fcpsec2float(a)
    #b = fcpsec2float(b)
    #output = float2fcpsec(a+b, fps)
    a = fcpsec2frac(a)
    b = fcpsec2frac(b)
    output = frac2fcpsec(a+b, fps)
    return output

def fcpsec_subtract(a: str, b: str, fps: str='100/6000s') -> str:
    """
    a: xxxx/yys
    b: aaaa/bbs
    fps: 100/6000s

    returns a minus b
    """
    # convert to common denominator fractions
    # subtract
    # return in a fcpsec format
    #a = fcpsec2float(a)
    #b = fcpsec2float(b)
    #output = float2fcpsec(a-b, fps)
    a = fcpsec2frac(a)
    b = fcpsec2frac(b)
    output = frac2fcpsec(a-b, fps)
    return output

def fcpsec_geq(a, b):
    """
    a >= b
    """
    #a = fcpsec2float(a)
    #b = fcpsec2float(b)
    a = fcpsec2frac(a)
    b = fcpsec2frac(b)
    return a >= b

def fcpsec_gt(a, b):
    """
    a > b
    """
    #a = fcpsec2float(a)
    #b = fcpsec2float(b)
    a = fcpsec2frac(a)
    b = fcpsec2frac(b)
    return a > b

# WARNING. USE THIS FOR ROUGH APPROXIMATION WORK, NEVER FOR PRECISE RESULTS.
# FCPSEC TO FLOAT CONVERSION HERE IS VERY ROUGH
def dict2list(x: list[dict]) -> list[list[float]]:
    """
    x: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    output: [[xxx.yy, aaa.bb], ...]
    """
    output = []
    for e in x:
        start = fcpsec2float(e['start'])
        end = fcpsec2float(e['end'])
        output.append([start, end])
    return output

# WARNING. USE THIS FOR ROUGH APPROXIMATION WORK, NEVER FOR PRECISE RESULTS.
# FCPSEC TO FLOAT CONVERSION HERE IS VERY ROUGH
def list2dict(x: list[list[float]]) -> list[dict]:
    """
    x: [[xxx.yy, aaa.bb], ...]
    output: [{'start': 'xxxx/yyys', 'end': 'aaaa/bbs'}, ...]
    """
    output = []
    for e in x:
        d = {}
        d['start'] = float2fcpsec(e[0])
        d['end'] = float2fcpsec(e[1])
        output.append(d)
    return output
