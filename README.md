# yashter 📦 - Stash your YAML comments before transforming your files
⚠️ THIS IS AN **EXPERIMENTAL** BUNCH OF CODE THAT HAS NO GUARANTEE OF WORKING.

## Rational
We are using comments in our locale files to provide context to our translators. However, tools
like Ruby i18n do not parse comments, and any action is destructive. 

I've made this so that we can stash our comments, and once all transformations are done, pop
all the comments back again to the file.

### Works
* Simple yerarchical yaml files (eg Ruby localization files):
```
# Portuguese locales
pt: 
    # models localizations
    models:
        # Block of metal with wheels
        car: Carro
```

### Doesn't work
* If the YAML already contains comments, things are likely to break
* NOTHING ELSE WAS TESTED!

# Usage
```
pipenv install
# Does not touch the originals
pipenv run python yashter.py stash "config/locales/**/en.yml"
# Stashes things so that the original no longer has the comments
pipenv run python yashter.py stash "config/locales/**/en.yml" --replace


# This is a dry-run, and will create files alongside the originals
pipenv run python yashter.py pop
# This will replace the original locale files
pipenv run python yashter.py pop --replace
```

