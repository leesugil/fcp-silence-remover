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

def fcpsec2float(text: str, fps: str='100/6000s') -> float:
    """
    text: xxxx/yyys

    output: float
    """
    if text == '0s':
        num, denom = unfrac(fps)
        text = f'0/{denom}s'
    return float(Fraction(text[:-1]))

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
    a = fcpsec2float(a)
    b = fcpsec2float(b)
    output = float2fcpsec(a+b, fps)
    #print(f"a + b = {a} + {b} = {output}")
#   a_num, a_denom = unfrac(a)
#   b_num, b_denom = unfrac(b)
#   #print(f"a: {a}, b: {b}")
#   output_num = a_num * b_denom + b_num * a_denom
#   #print(f"a_num: {a_num}, b_num: {b_num}, output_num: {output_num}")
#   output_denom = a_denom * b_denom
#   #print(f"a_denom: {a_denom}, b_denom: {b_denom}, output_denom: {output_denom}")
#   num, denom = unfrac(fps)
#   #print(f"num: {num}, denom: {denom}, output_num: {output_num}")
#   output_num = math.floor(output_num * denom / num) * num
#   output = f"{output_num}/{output_denom}s"
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
    a = fcpsec2float(a)
    b = fcpsec2float(b)
    output = float2fcpsec(a-b, fps)
    #print(f"a - b = {a} - {b} = {output}")
#   a_num, a_denom = unfrac(a)
#   b_num, b_denom = unfrac(b)
#   output_num = a_num * b_denom - b_num * a_denom
#   output_denom = a_denom * b_denom
#   num, denom = unfrac(fps)
#   output_num = math.floor(output_num * denom / num) * num
#   output = f"{output_num}/{output_denom}s"
    return output

def fcpsec_geq(a, b):
    """
    a >= b
    """
    a = fcpsec2float(a)
    b = fcpsec2float(b)
    return a >= b

def fcpsec_gt(a, b):
    """
    a > b
    """
    a = fcpsec2float(a)
    b = fcpsec2float(b)
    return a > b

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
