set shell := ["bash", "-lc"]

default:
    just --list

init:
    quarto check

q-doctor:
    quarto check
    quarto --version

q-preview:
    quarto preview

q-preview-render:
    quarto preview --render all

q-render:
    quarto render

q-clean:
    rm -rf build .quarto

q-rebuild:
    just q-clean
    just q-render

q-serve:
    python3 -m http.server 8000 --directory build
