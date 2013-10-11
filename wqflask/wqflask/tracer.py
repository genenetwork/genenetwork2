from __future__ import absolute_import, division, print_function

print("At top of tracer")

import sys

####################################################################################

# Originally based on http://stackoverflow.com/a/8315566
def tracefunc(frame, event, arg, indent=[0]):
    
    func = dict(funcname = frame.f_code.co_name,
                     filename = frame.f_code.co_filename,
                     lineno = frame.f_lineno)
    
    #These are too common to bother printing...
    too_common = (
        '/home/sam/ve27/local/lib/python2.7/site-packages/werkzeug/',
        '/home/sam/ve27/local/lib/python2.7/site-packages/jinja2/',
    )
    
    
    if func['filename'].startswith(too_common):
        return tracefunc
    
    info = "{funcname} [{filename}: {lineno}]".format(**func)

    if event == "call":
        indent[0] += 2
        #print("-" * indent[0] + "> call function", frame.f_code.co_name)
        print("-" * indent[0] + "> call function:", info)
    elif event == "return":
        print("<" + "-" * indent[0], "exit function:", info)
        indent[0] -= 2
    return tracefunc

def turn_on():
    sys.settrace(tracefunc)
    print("Tracing turned on!!!!")  
####################################################################################

