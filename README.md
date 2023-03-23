# Arbety crawler


## dependências

- [asdf](https://asdf-vm.com/)
- Firefox


## setup

De dentro da pasta do projeto:

    asdf plugin add python
    asdf install
    python -m venv .venv
    pip install poetry
    asdf reshim python
    poetry env use .venv/bin/python
    poetry install


## executando

1 - Execute o mitmdump:

    mitmdump -k -s mitmproxy.py

2 - [Configure o Firefox](https://docs.mitmproxy.org/stable/overview-getting-started/#configure-your-browser-or-device)

3 - Abra a url https://www.arbety.com/games/double no Firefox para iniciar a captura dos dados
