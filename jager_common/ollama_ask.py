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
    prompt_eng = ' '.join(sys.argv[1:])
    print(f'first text {prompt_eng}')
    dataText = ' '.join(sys.argv[2:])
    print(f'second text {dataText}')
    question = ' '.join(sys.argv[3:])
    print(f'third text {question}')
    text = prompt_eng + dataText + question
    main(text)
