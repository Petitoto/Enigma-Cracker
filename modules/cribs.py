# Find possible cribs in a text
def find_cribs(words, text, filter_text):
    cribs = {}
    for c in words:
        for i in range(len(text) - len(c) + 1):
            j = 0
            while j < len(c) and (\
                ('' != filter_text(c[j]) != filter_text(text[i+j]) != '') \
                or ('' == filter_text(c[j]) == filter_text(text[i+j]) and c[j] == text[i+j])):
                j += 1
            if j == len(c):
                if c in cribs:
                    cribs[c].append(i)
                else:
                    cribs[c] = [i]
    return cribs