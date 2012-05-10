#import mmseg
#mmseg.dict_load_defaults()
from mmseg import seg_txt

def segment(string):
#    alphas = ''
#    unicode = ''
#    last_is_alpha = False
#    for char in string:
#        if char.isalpha():
#            if not last_is_alpha:
#                alphas += ' '
#            alphas += char
#        else:
#            if last_is_alpha:
#                unicode += ' '
#            unicode += char
#    print "ALPHAS", alphas
#    print "UNICODE", unicode[:20]
#    return alphas + u' '.join([ txt.decode('utf8') for txt in seg_txt( unicode.encode('utf8')) ])
    return u' '.join([ txt.decode('utf8') for txt in seg_txt( string.encode('utf8')) ])
