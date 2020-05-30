from re import match

def maybe(re):
    return f'(?:{re})?'

def one(regexs, s, throw=True):
    matches = [ (match(regex, s), regex) for regex in regexs ]
    matches = [ (m.groupdict(), regex) for m, regex in matches if m ]
    if not matches:
        if throw:
            raise Exception('No regexs matched %s:\n\t%s' % (s, '\n\t'.join(regexs)))
        else:
            return None
    num_matches = len(matches)
    if num_matches > 1:
        if throw:
            raise Exception(
                'Multiple regexs matched %s:\n\t%s' % (
                    s,
                    '\n\t'.join([
                        str(m)
                        for m, _ in matches
                    ])
                )
            )
        else:
            return None

    [ (m, _) ] = matches
    return m
