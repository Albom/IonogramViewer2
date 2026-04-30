import argparse
import markdown

def main():
    parser = argparse.ArgumentParser(description="make_html input=in_file.md output=out_file.html")
    parser.add_argument("input", help="Input file name")
    parser.add_argument("output", help="Output file name")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as in_file:
        input_text = in_file.read()
    output_text = markdown.markdown(input_text)

    css = """
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            background-color: #f4f4f4;
            color: #333;
        }

        .container {
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        h1, h2, h3 {
            color: #2c3e50;
        }

        h1 {
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }

        p {
            margin: 15px 0;
        }

        a {
            color: #3498db;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        code {
            background: #eee;
            padding: 2px 5px;
            border-radius: 4px;
            font-family: Consolas, monospace;
        }

        pre {
            background: #272822;
            color: #f8f8f2;
            padding: 15px;
            overflow-x: auto;
            border-radius: 6px;
        }

        pre code {
            background: none;
            color: inherit;
        }
    </style>
    """
    with open (args.output, "w", encoding="utf-8") as out_file:
        out_file.write("<!DOCTYPE HTML>\n\n<html>\n")
        out_file.write(f"<head>\n{css}</head>\n\n<body>\n")
        out_file.write(output_text)
        out_file.write("\n</body>\n</html>\n")


if __name__ == "__main__":
    main()
