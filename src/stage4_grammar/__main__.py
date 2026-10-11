"""Validate a DSL file: python -m src.stage4_grammar path/to/candidate.resume."""

import argparse
from dataclasses import asdict
import json
import sys

from src.stage4_grammar import ProfileValidationError, parse_profile_file


def main(argv=None):
    parser = argparse.ArgumentParser(description='Validate a ResumeLens candidate DSL file.')
    parser.add_argument('path', help='UTF-8 .resume document')
    args = parser.parse_args(argv)
    try:
        profile = parse_profile_file(args.path)
    except (ProfileValidationError, OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    # ASCII escapes also make redirected output safe on Windows legacy consoles.
    print(json.dumps(asdict(profile), indent=2, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
