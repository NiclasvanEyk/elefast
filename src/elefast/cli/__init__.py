from elefast.cli.parser import build_parser


def main():
    cli = build_parser()
    args = cli.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
