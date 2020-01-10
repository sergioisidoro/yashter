import re
import os
import glob
import json
import json
import click
import pprint
import operator
import ruamel.yaml
import collections
from pathlib import Path
from functools import reduce
# DEBUG
import pdb
    
# default_style ∈ None, '', '"', "'", '|', '>'
DEFAULT_STYLE = None
PRESERVE_QUOTES = None
DEFAULT_FLOW_STYLE = False


def _parse_yaml_comments(sub_doc, parent=None, parent_comments=None):
    state = collections.defaultdict(dict)
    state["_comments"] = []

    try:
        sub_doc.keys()
    except AttributeError:
        # This means it's a leaf node (string / integer / other)
        state["_is_leaf"] = True
        return state

    # Root node case first
    current_level_ordered_keys = list(sub_doc.keys())
    current_level_comments = sub_doc.ca.comment[1] if sub_doc.ca.comment else []

    for index, key in enumerate(sub_doc):
        state[key] = _parse_yaml_comments(
            sub_doc[key],
            parent=sub_doc,
            parent_comments=current_level_comments
        )

        if index == 0:
            # First nodes of a level have the comments on the parent node
            # print("%s is a index 0" % key)
            # print("Parent comments are %s" % current_level_comments)
            comments = [
                str(i.value) for i in current_level_comments or [] if i
                ]
            state[key]['_comments'] += comments

        elif state[key]["_is_leaf"]:
            # Leaf nodes will have the comment on the previous node.
            previous_key = current_level_ordered_keys[index-1]
            comment_token = sub_doc.ca.items.get(
                previous_key, [None, None, None, None]
                )[2]
            state[key]["_comments"] += [comment_token.value] if comment_token else []

    return state


def getFromDict(dataDict, mapList):
    try: 
        return reduce(operator.getitem, mapList, dataDict)
    except KeyError:
        print("KEY %s not found" % ".".join(mapList))
        return None


def _restorer(sub_doc, comments_repo, current_path=[], current_indentation=0):
    try:
        sub_doc.keys()
    except AttributeError:
        # We're a leaf node... continue
        return

    for index, key in enumerate(sub_doc):
        # pdb.set_trace()
        next_path = current_path + [key]
        print("Handling %s" % ".".join(next_path))

        current_keys_dict = getFromDict(
            comments_repo,
            next_path)

        if current_keys_dict: 
            current_keys_comments = current_keys_dict["_comments"]
        else:
            continue

        if current_keys_comments:
            print("Setting comment")
            # Remove first # at the beginning of the lines
            # because yaml_set_comment_before_after_key does not
            # expect the hash at the beginning of the string.
            # It will also handle indentation, so all the white
            # spaces at the start of the string need to be cut.
            comments = [
                re.sub('^\s*#\s*', '', line) for line in 
                current_keys_comments
                ]

            comment = "".join(comments).strip()
            print("Key: %s" % key)
            print(comment)
            # pdb.set_trace()
            if index == 0:
                sub_doc.yaml_set_start_comment(
                    comment, 
                    indent=current_indentation
                )
            else:
                sub_doc.yaml_set_comment_before_after_key(
                    key,
                    comment,
                    indent=current_indentation
                )
            print("done...")
        next_path = current_path + [key]
        _restorer(sub_doc[key], comments_repo, current_path=next_path, current_indentation=current_indentation+2)


def restore_comments(doc_data, comments_repo):
    _restorer(doc_data, comments_repo)
    return doc_data


@click.group()
@click.pass_context
def main(ctx):
    click.echo("Command running...")


@main.command()
@click.argument('files')
@click.option(
    '--output', '-o',
    default='./yaml_comment_repo.json',
    help='The output for yaml comments repo',
)
@click.option(
    '--base-path', '-b',
    default='.',
    help='The base path for globbing',
)
@click.option(
    '--replace',
    default=False,
    is_flag=True,
    help='Replace existing file with comments?',
)
@click.option(
    '--exclude', '-e',
    help='CURRENTLY NOT SUPPORTED',
)
def stash(files, base_path, output, replace, exclude):
    click.echo(
        "LOADING glob %s (base path %s) and generating in %s" % (files, base_path, output)
    )
    base_glob = files
    yaml = ruamel.yaml.YAML()
    yaml.default_style = DEFAULT_STYLE
    yaml.explicit_start = True
    yaml.preserve_quotes = PRESERVE_QUOTES
    yaml.default_flow_style = DEFAULT_FLOW_STYLE
    yaml.compact(seq_seq=False, seq_map=False)

    non_comment_parser = ruamel.yaml.YAML(typ='safe')
    non_comment_parser.default_style = DEFAULT_STYLE
    non_comment_parser.explicit_start = True
    non_comment_parser.preserve_quotes = PRESERVE_QUOTES
    non_comment_parser.default_flow_style = DEFAULT_FLOW_STYLE
    non_comment_parser.compact(seq_seq=False, seq_map=False)

    comment_directory = collections.defaultdict(dict)
    for file in Path(base_path).rglob(base_glob):
        click.echo("Processing file %s " % file)
        # For each file, parse the YAML
        doc = Path(file)
        data = yaml.load(doc)
        relative_path = file.relative_to(base_path)
        comment_directory[str(relative_path)] = _parse_yaml_comments(data)

    with open(output, 'w+') as fp:
        json.dump(comment_directory, fp, indent=2)

    if replace:
        for file in Path(base_path).rglob(base_glob):
            click.echo("Removing all comments from file %s " % file)
            # For each file, parse the YAML
            doc_path = Path(file)
            data = non_comment_parser.load(doc_path)
            with open(doc_path, "w+") as output_stream:
                yaml.dump(data, output_stream)


@main.command()
@click.option(
    '--input', '-i',
    default='./yaml_comment_repo.json',
    help='Thin input for yaml comments repo',
)
@click.option(
    '--base-path', '-b',
    default='.',
    help='The base path used when loading',
)
@click.option(
    '--replace',
    default=False,
    is_flag=True,
    help='Replace existing file with comments?',
)
@click.option(
    '--exclude', '-e',
    help='CURRENTLY NOT SUPPORTED',
)
def pop(input, base_path, replace, exclude):
    if replace:
        click.echo("REPLACING FILES")
    else:
        click.echo("Dry run. Generating _dryrun files")

    yaml = ruamel.yaml.YAML()
    yaml.explicit_start = True
    yaml.default_style = DEFAULT_STYLE
    yaml.preserve_quotes = PRESERVE_QUOTES
    yaml.default_flow_style = DEFAULT_FLOW_STYLE
    yaml.compact(seq_seq=False, seq_map=False)

    with open(input) as json_file:
        comment_directory = json.load(json_file)
        for file, comments_repo in comment_directory.items():
            click.echo("Processing file %s " % file)
            doc_path = Path(base_path, file)
            doc_data = yaml.load(doc_path)
            new_data = restore_comments(doc_data, comments_repo)

            if replace:
                with open(doc_path, "w+") as output_stream:
                    yaml.dump(new_data, output_stream)
            else:
                alt_path = Path(base_path, file + "dryrun")
                with open(alt_path, "w+") as output_stream:
                    yaml.dump(new_data, output_stream)


if __name__ == '__main__':
    main()
