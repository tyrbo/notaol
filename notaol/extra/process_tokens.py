'''Process the token HTML and TXT files.'''
import re
import string

import lxml.html
import collections
import pprint
import textwrap


HTML_DB_FILENAMES = tuple(
    ['token_!.html', 'token_0-9.html'] +
    ['token_{}.html'.format(char) for char in string.ascii_lowercase]
    )


TokenMetadata = collections.namedtuple(
    'TokenMetadataType',
    ['token', 'description', 'category', 'flags', 'arg', 'form']
)


def new_token_metadata(token, description=None, category=None, flags=None,
                       arg=None, form=None):
    return TokenMetadata(token, description, category, flags, arg, form)


def main():
    print(textwrap.dedent('''\
    import collections


    TokenMetadata = collections.namedtuple(
        'TokenMetadataType',
        ['token', 'description', 'category', 'flags', 'arg', 'form']
    )
    '''))

    rows = [
        new_token_metadata('AA', 'Normal chat message'),
        new_token_metadata('AB', 'Chat message with name'),
        new_token_metadata('AC', 'Chat message with count'),
        new_token_metadata('AD', 'Auditorium count msg.'),
        new_token_metadata('CA', 'User entry'),
        new_token_metadata('CB', 'User exit'),
        new_token_metadata('D3', 'Causes a message to Codeman which sends a D6 token'),
        new_token_metadata('OT', 'Display Alert Message'),
        new_token_metadata('XS', 'Force Off and Hang up'),
        new_token_metadata('hO', 'Luanch a PC Game'),  # sic
        new_token_metadata('D*', 'Disconnect'),
        new_token_metadata('**', 'P3 Release - Not used any longer'),
        new_token_metadata('tj', 'The packet contains info about file we\'re getting ready to download'),
        new_token_metadata('ta', 'file flags, count, size, and filename to be D/Led'),
        new_token_metadata('tf', 'receive D/L file; host requests immediate xG ack (?????)'),
        new_token_metadata('F8', 'receive D/L file; host requests immediate xG ack'),
        new_token_metadata('FF', 'receive D/L file; no immediate ack required'),
        new_token_metadata('F7', 'receive D/L file; no immediate ack required'),
        new_token_metadata('F9', 'receive D/L file; this is the last packet of the file'),
        new_token_metadata('fX', 'Upload Token'),
        new_token_metadata('tN', 'Upload Token'),
        new_token_metadata('tt', 'Upload Token'),
        new_token_metadata('td', 'Upload Token'),
        new_token_metadata('th', 'Upload Token'),
        new_token_metadata('ti', 'Upload Token'),
        new_token_metadata('tc', 'Upload Token'),
        new_token_metadata('tx', 'Upload Token'),
        new_token_metadata('f2', 'DOD request'),
        new_token_metadata('ff', 'DOD request - art control'),
        new_token_metadata('ft', 'DOD request'),
        new_token_metadata('fh', 'DOD request - new styled art'),
        new_token_metadata('AN', 'Client requests a list of area code / time-stamps from Host'),
        new_token_metadata('ET', 'Phone Home report'),
        new_token_metadata('Wh', 'Client received ACK for INIT and is secure'),
        new_token_metadata('Wk', 'Acknowledgement for Wh'),
        new_token_metadata('Wd', 'Encrypted version of Dd token'),
        new_token_metadata('Tu', 'Notify DRUL that a particular tool has been upated'),  # sic
        new_token_metadata('SD', 'Go ahead after INIT'),
        new_token_metadata('ya', 'After log in, show mail and buddy list'),
        new_token_metadata('at', 'Begin log in'),
        new_token_metadata('At', 'Log in confirmed'),
        new_token_metadata('AT', 'Log in ???'),
    ]

    for row in read_1998_txt():
        rows.append(row)
    for row in read_list_tokens_html():
        rows.append(row)

    for filename in HTML_DB_FILENAMES:
        for row in read_token_html(filename):
            rows.append(row)

    print('TOKEN_METADATA = \\')
    pprint.pprint(rows)


def read_1998_txt():
    with open('1998.txt', 'r') as in_file:
        start = False
        for line in in_file:
            if line.startswith('(This'):
                start = True
                continue
            elif line.startswith('Transmitted:'):
                break
            elif not line.strip():
                continue

            if not start:
                continue

            line = line.strip()
            flags = []
            token = line[0:2]
            words = line[2:].split()

            while True:
                if len(words[-1]) == 2 and words[-1].isupper():
                    flags.append(words.pop())
                else:
                    break

            if words[0] == 'S]':
                token = words.pop(0)

            category = words.pop()
            description = ' '.join(words)

            yield new_token_metadata(token, description=description,
                                     category=category, flags=flags)


def read_list_tokens_html():
    with open('list_tokens.html', 'r') as in_file:
        start = False
        for line in in_file:
            if not start and line.startswith('edit_token'):
                start = True
                continue
            elif start and line.startswith('edit_token'):
                break
            elif not line.strip():
                continue
            elif not start:
                continue

            token = line.strip().split(' ', 1)[0]

            if len(line.strip()) == 2:
                description = None
                category = None
            else:
                rest_of_line = line.split(' ', 1)[1].strip()
                match = re.match('(.*)(   .+)$', rest_of_line)

                if match:
                    description = ' '.join(match.group(1).split())
                    category = match.group(2).strip()
                else:
                    description = ' '.join(rest_of_line.split())
                    category = None

            yield new_token_metadata(token, description=description,
                                     category=category)


def read_token_html(filename):
    tree = lxml.html.parse(filename)

    for table_row in tree.findall('//tr'):
        if table_row.get('bgcolor') == '#FFFFFF':
            table_cells = tuple(table_row.findall('td'))

            if not len(table_cells) == 4:
                continue

            token = table_cells[0].text_content().strip()
            arg = table_cells[1].text_content().strip()
            form = table_cells[2].text_content().strip()
            description = table_cells[3].text_content().strip()
            if description:
                description = ' '.join(description.split())

            if not token:
                token = prev_token
            prev_token = token

            for token in expand_token(token):
                try:
                    arg = int(arg) if arg else None
                except ValueError:
                    arg = arg or None

                yield new_token_metadata(token, arg=arg, form=form or None,
                                         description=description or None)


def expand_token(token_string):
    ranges = token_string.split(',')

    for range_ in ranges:
        if '-' in range_:
            start, end = range_.split('-')
            start = start.strip()
            end = end.strip()

            for i in range(ord(start[1]), ord(end[1]) + 1):
                yield '{}{}'.format(start[0], chr(i))
        else:
            yield range_.strip()


if __name__ == '__main__':
    main()
