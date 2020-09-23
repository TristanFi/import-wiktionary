from loguru import logger
import json
import pprint
import wiktextract
import re


def main():
    words = {}
    wordlike = re.compile(r"[a-zA-Z']+")

    def word_cb(data):
        word = data['word']
        ipas = []

        if word.upper() in words:
            if word != word.upper():
                # We can use the capitalization from Wiktionary
                words[word] = words.pop(word.upper())
        elif word == word.upper():
            return  # We don't need to add a bunch of new acronyms
        else:
            match = wordlike.match(word)
            if not match:
                logger.error(f'what even is this: {word}')
                return  # What even is this
            elif match.span()[1] != len(word):
                logger.warning(f'skipping "{word}"')
                return  # We don't care about extended wiktionary entries

        if not 'pronunciations' in data:
            return  # We only care about entries with a pronunciation
        pronunciations = data['pronunciations']
        for pronunciation in pronunciations:
            if 'ipa' in pronunciation:
                ipa = re.sub('[.ˌˈ()]', '', pronunciation['ipa'][0][1][1:-1])
                append = False
                if 'accent' in pronunciation:
                    accent = pronunciation['accent']
                    if 'US' in accent or 'GenAm' in accent or 'GA' in accent:
                        append = True
                else:
                    append = True
                if append and ipa not in ipas:
                    ipas.append(ipa)

        if ipas:
            if word in words:
                for existing in words[word]:
                    try:
                        ipas.remove(existing)
                    except ValueError:
                        pass
                if ipas:
                    words[word].extend(ipas)
                    logger.debug(f'{word}: {words[word]}')

            else:
                words.update({word: ipas})
                logger.info(f'NEW {word}: {words[word]}')

    cmudict = 'cmudict-0.7b-ipa.txt'
    with open(cmudict, 'r') as infile:
        # There are 69 lines of symbols before the words
        for _ in range(69):
            next(infile)
        for line in infile:
            word, pronunciations = line.rstrip().split('\t')
            if '-' not in word:
                word = word.replace('.', '').rstrip()
                pronunciations = pronunciations.split(', ')
                pronunciations = [re.sub('[.ˌˈ()]', '', x) for x in pronunciations]
                words.update({word: pronunciations})

    path = 'enwiktionary-latest-pages-articles.xml'
    logger.debug(f'Processing {path}')
    ctx = wiktextract.parse_wiktionary(path=path, word_cb=word_cb, pronunciations=True)
    with open('dict.json', 'w') as outfile:
        json.dump(words, fp=outfile, indent=2)


if __name__ == '__main__':
    main()
