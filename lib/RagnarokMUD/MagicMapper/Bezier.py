########################################################################################
#  _______  _______  _______ _________ _______  _______  _______  _______              #
# (       )(  ___  )(  ____ \\__   __/(  ____ \(       )(  ___  )(  ____ ) Ragnarok    #
# | () () || (   ) || (    \/   ) (   | (    \/| () () || (   ) || (    )| MUD         #
# | || || || (___) || |         | |   | |      | || || || (___) || (____)| Magic       #
# | |(_)| ||  ___  || | ____    | |   | |      | |(_)| ||  ___  ||  _____) Mapper      #
# | |   | || (   ) || | \_  )   | |   | |      | |   | || (   ) || (       Client      #
# | )   ( || )   ( || (___) |___) (___| (____/\| )   ( || )   ( || )       (rag.com)   #
# |/     \||/     \|(_______)\_______/(_______/|/     \||/     \||/                    #
#   ______    __       _______         _______  _        _______           _______     #
#  / ____ \  /  \     (  __   )       (  ___  )( \      (  ____ )|\     /|(  ___  )    #
# ( (    \/  \/) )    | (  )  |       | (   ) || (      | (    )|| )   ( || (   ) |    #
# | (____      | |    | | /   | _____ | (___) || |      | (____)|| (___) || (___) |    #
# |  ___ \     | |    | (/ /) |(_____)|  ___  || |      |  _____)|  ___  ||  ___  |    #
# | (   ) )    | |    |   / | |       | (   ) || |      | (      | (   ) || (   ) |    #
# ( (___) )_ __) (_ _ |  (__) |       | )   ( || (____/\| )      | )   ( || )   ( | _  #
#  \_____/(_)\____/(_)(_______)       |/     \|(_______/|/       |/     \||/     \|(_) #
#                                                                                      #
########################################################################################
#
# The following code was contributed by user "unutbu" to the public forum 
# "Stack Overflow".  It calculates Bezier curve points which we draw with
# polygons.
# 
def make_bezier(xys):
    '''Given Bezier control points <xys> as sequence of 2-tuples, 
    this function constructs and returns a function to plot points 
    on the curve described.'''

    n = len(xys)
    combinations=pascal_row(n-1)

    def bezier(ts):
        '''Return list of 2-tuples describing points on curve for input 
	values for t.  t should be a list of values in the range [0,1]
	(e.g., if ts=[0,0.2,0.4,0.6,0.8,1] then you'll get 6 points
	output at equal points along the curve's path).'''

        result = []
        for t in ts:
            tpowers = (t**i for i in range(n))
            upowers = reversed([(1-t)**i for i in range(n)])
            coefs = [c*a*b for c,a,b in zip(combinations, tpowers, upowers)]
            result.append(tuple(sum([coef*p for coef,p in zip(coefs,ps)]) for ps in list(zip(*xys))))
        return result

    return bezier

def pascal_row(n):
    "Return the nth row of Pascal's Triangle."

    result = [1]
    x, numerator = 1, n
    for denominator in range(1, n//2+1):
        x *= numerator
        x /= denominator
        result.append(x)
        numerator -= 1

    if n&1 == 0:
        result.extend(reversed(result[:-1]))
    else:
        result.extend(reversed(result))

    return result

