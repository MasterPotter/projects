import nltk
from nltk.corpus import words


#
# string = input("Enter the letters left to right, top to bottom, all caps, without spaces: ")
# string = string.lower()
# lst = [[string[0], string[1], string[2], string[3]], [string[4], string[5], string[6], string[7]],
#        [string[8], string[9], string[10], string[11]], [string[12], string[13], string[14], string[15]]]


def print_matrix(matrix):
    for row in matrix:
        print(' '.join(map(str, row)))


def is_english_word(word):
    return word.lower() in word_list


def recur():
    for i in range(16):
        lst = [i]
        recurrence(lst)


def recurrence(indices):
    r = indices[-1]
    if r == 0:
        recurrence(check(indices.append(1)))
        recurrence(check(indices.append(4)))
        recurrence(check(indices.append(5)))
    if r == 1:
        recurrence(check(indices.append(0)))
        recurrence(check(indices.append(2)))
        recurrence(check(indices.append(4)))
        recurrence(check(indices.append(5)))
        recurrence(check(indices.append(6)))
    if r == 2:
        recurrence(check(indices.append(1)))
        recurrence(check(indices.append(3)))
        recurrence(check(indices.append(5)))
        recurrence(check(indices.append(6)))
        recurrence(check(indices.append(7)))
    if r == 3:
        recurrence(check(indices.append(2)))
        recurrence(check(indices.append(6)))
        recurrence(check(indices.append(7)))
    if r == 4:
        recurrence(check(indices.append(0)))
        recurrence(check(indices.append(1)))
        recurrence(check(indices.append(5)))
        recurrence(check(indices.append(8)))
        recurrence(check(indices.append(9)))
    if r == 5:
        recurrence(check(indices.append(0)))
        recurrence(check(indices.append(1)))
        recurrence(check(indices.append(2)))
        recurrence(check(indices.append(4)))
        recurrence(check(indices.append(6)))
        recurrence(check(indices.append(7)))
        recurrence(check(indices.append(8)))
        recurrence(check(indices.append(9)))
    if r == 6:
        recurrence(check(indices.append(1)))
        recurrence(check(indices.append(2)))
        recurrence(check(indices.append(3)))
        recurrence(check(indices.append(5)))
        recurrence(check(indices.append(6)))
        recurrence(check(indices.append(2)))
        recurrence(check(indices.append(2)))
        recurrence(check(indices.append(2)))


def check(data):
    if len(data) == len(set(data)):
        return data
    else:
        return data.append("a")


word_list = set(words.words())

print(is_english_word("apple"))
print(is_english_word("blorf"))

print(check([1, 1, 2, 3, 4]))
