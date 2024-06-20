import sys

import ollama


def main(prompt):
    response = ollama.generate('llama3', prompt)
    content = response['response']
    print("the Bot answer is:\n")
    print(content)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script.py <parameter>")
        sys.exit(1)
    text = ' '.join(sys.argv[1:])
    main(text)
