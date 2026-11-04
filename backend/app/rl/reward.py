"""Synthetic proxy reward, not patient benefit or clinical outcomes."""
def reward(before,action,after,unsafe,unsupported,completed):
    if unsafe:return -20.0
    value=-0.2 + 1.5*(after[1]-before[1]) + .5*(after[2]-before[2])
    if unsupported:value-=4.0
    if action==before[5]:value-=.75
    if action in (1,2) and before[3]>0:value+=.3
    if completed:value+=6.0 if before[4]==0 else 2.0
    if action==5 and before[4]==0:value-=1.0
    return float(value)
