"""Replace xfail_impl(...) with pytest.param(..., marks=xfail_impl) in test_fiat.py.

Handles both single-line and multi-line implicit string concatenation calls
by tracking parenthesis depth.
"""
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text()
result = []
i = 0
tag = 'xfail_impl('

while i < len(text):
    pos = text.find(tag, i)
    if pos == -1:
        result.append(text[i:])
        break
    result.append(text[i:pos])
    # Find matching closing paren by tracking depth
    depth = 0
    j = pos + len(tag) - 1  # points at '('
    while j < len(text):
        if text[j] == '(':
            depth += 1
        elif text[j] == ')':
            depth -= 1
            if depth == 0:
                break
        j += 1
    inner = text[pos + len(tag):j]
    result.append('pytest.param(' + inner + ', marks=xfail_impl)')
    i = j + 1

path.write_text(''.join(result))
