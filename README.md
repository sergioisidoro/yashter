# Yashter 📦 
## Stash your comments before manipulating YAML
⚠️ THIS IS AN **EXPERIMENTAL** BUNCH OF CODE THAT HAS NO GUARANTEE OF WORKING.

## Rational
Using comments in yaml locale files is a great way to provide context to translators and copy editors. However, tools like Rails i18n-tasks do not parse comments, and any action (like removing unused keys) is destructive for the comments.

Most YAML parsers and manipulators work quite the same way

I've made this so that I can stash YAML comments in a intermediary structure, and once all transformations are done, pop all the comments back again to the file.

The comments are stored in association to the keys
```
# Portuguese locales
pt: 
    # models localizations
    models:
        # Block of metal with wheels
        car: Carro
```

```

{
  "config/locales/en.yml": {
    "pt": {
      "_comments": [# Portuguese locales],
      "models": {
        "_comments": [# models localizations],
        "car": {
          "_comments": ["# Block of metal with wheels"],
        }
      }
      ...
    }
    ...
  }
  "config/locales/.../en.yml": {
      ....
  }
}

```

### Works
* Simple yerarchical yaml files (eg Ruby localization files)
* Keys have the comments **BEFORE** the keys


### Doesn't work
* Poping comments if the output YAML already contains comments

### Probably doesn't work
* Likely will break with lists or other structures


# Usage
```.sh
pipenv install

# STASH
# Does not touch the originals
pipenv run python yashter.py stash "config/locales/**/en.yml"

# Stashes things so that the original no longer has the comments
pipenv run python yashter.py stash "config/locales/**/en.yml" --replace

# POP
# This is a dry-run, and will create files alongside the originals
pipenv run python yashter.py pop

# This will replace the original locale files
pipenv run python yashter.py pop --replace
```

