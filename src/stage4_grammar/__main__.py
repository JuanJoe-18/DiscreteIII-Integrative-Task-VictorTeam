"""Validate a DSL file: python -m src.stage4_grammar path/to/candidate.resume."""

import argparse
from dataclasses import asdict
import json
import sys
from pathlib import Path

from src.stage4_grammar import validate_document


def main(argv=None):
    parser = argparse.ArgumentParser(description='Validate a ResumeLens candidate DSL file.')
    parser.add_argument('path', help='UTF-8 .resume document')
    parser.add_argument('--html', metavar='OUTPUT', help='Write HTML only if the entire DSL is valid')
    args = parser.parse_args(argv)
    try:
        if args.html and Path(args.path).resolve() == Path(args.html).resolve():
            raise ValueError('The HTML output must not overwrite the DSL input.')
        document = validate_document(Path(args.path).read_text(encoding='utf-8'), filename=args.path)
        profile = document.profile
        if args.html:
            Path(args.html).write_text(document.html, encoding='utf-8')
    except (ValueError, OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    # ASCII escapes also make redirected output safe on Windows legacy consoles.
    print(json.dumps(asdict(profile), indent=2, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
