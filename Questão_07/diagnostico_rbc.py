"""Protótipo acadêmico de raciocínio baseado em casos fictícios."""

import argparse
import json
import sqlite3
import unicodedata
from contextlib import closing
from fractions import Fraction
from pathlib import Path

PASTA = Path(__file__).resolve().parent


def normalizar(texto):
    """Unifica caixa, acentos e espaços sem alterar o texto exibido."""
    decomposicao = unicodedata.normalize("NFKD", texto.casefold())
    sem_acentos = "".join(c for c in decomposicao if not unicodedata.combining(c))
    return " ".join(sem_acentos.split())


def conjunto(sintomas):
    return {normalizar(sintoma) for sintoma in sintomas if sintoma.strip()}


def iniciar_base(conexao):
    origem = json.loads((PASTA / "casos.json").read_text(encoding="utf-8"))
    with conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS casos (
                numero INTEGER PRIMARY KEY,
                sintomas TEXT NOT NULL,
                diagnostico TEXT NOT NULL,
                tratamento TEXT NOT NULL
            )
        """)
        conexao.executemany(
            "INSERT OR IGNORE INTO casos VALUES (?, ?, ?, ?)",
            [(int(c["id"][1:]), json.dumps(c["sintomas"], ensure_ascii=False),
              c["diagnostico"], c["tratamento"]) for c in origem],
        )


def recuperar(conexao, sintomas):
    consulta = conjunto(sintomas)
    candidatos = []
    for numero, dados, diagnostico, tratamento in conexao.execute("SELECT * FROM casos"):
        registrados = json.loads(dados)
        sintomas_caso = conjunto(registrados)
        comuns = consulta & sintomas_caso
        if comuns:
            similaridade = Fraction(len(comuns), len(consulta | sintomas_caso))
            candidatos.append((similaridade, numero, registrados, diagnostico, tratamento))
    candidatos.sort(key=lambda item: (-item[0], item[1]))
    return candidatos


def revisar(sugestao):
    opcoes = "[v] validar, [c] corrigir, [n] descartar" if sugestao else "[c] informar caso, [n] descartar"
    validas = ("v", "c", "n") if sugestao else ("c", "n")
    acao = input(f"Revisão ({opcoes}): ").strip().lower()
    while acao not in validas:
        acao = input(f"Opção inválida ({opcoes}): ").strip().lower()
    if acao == "n":
        return None
    if acao == "v":
        return sugestao
    diagnostico = input("Diagnóstico revisado do caso fictício: ").strip()
    tratamento = input("Tratamento revisado do caso fictício: ").strip()
    if not diagnostico or not tratamento:
        print("Revisão descartada: informe diagnóstico e tratamento.")
        return None
    return diagnostico, tratamento


def reter(conexao, sintomas, solucao):
    diagnostico, tratamento = solucao
    with conexao:
        cursor = conexao.execute(
            "INSERT INTO casos (sintomas, diagnostico, tratamento) VALUES (?, ?, ?)",
            (json.dumps(sintomas, ensure_ascii=False), diagnostico, tratamento),
        )
    return cursor.lastrowid


def consultar(conexao, sintomas):
    vizinhos = recuperar(conexao, sintomas)
    sugestao = None
    if vizinhos:
        print("Casos recuperados (similaridade de Jaccard):")
        melhor_grau = vizinhos[0][0]
        exibidos = [item for indice, item in enumerate(vizinhos)
                    if indice < 3 or item[0] == melhor_grau]
        for grau, numero, registrados, diagnostico, _ in exibidos:
            print(f"  C{numero:02d} | {grau} ({float(grau):.1%}) | {diagnostico}")
            print("    Sintomas: " + ", ".join(registrados))

        grau, numero, _, diagnostico, tratamento = vizinhos[0]
        # Quando casos de classes diferentes empatam no topo, a escolha fica com a revisão.
        empate = any(item[0] == grau and item[3] != diagnostico for item in vizinhos[1:])
        if empate:
            print("Empate entre diagnósticos no topo. Informe a solução na revisão.")
        else:
            sugestao = (diagnostico, tratamento)
            print(f"Hipótese do protótipo (C{numero:02d}): {diagnostico}")
            print(f"Tratamento registrado no caso: {tratamento}")
    else:
        print("Nenhum caso tem sintomas em comum. Não há hipótese automática.")

    solucao = revisar(sugestao)
    if solucao and input("Guardar o caso revisado? [s/N]: ").strip().lower() == "s":
        numero = reter(conexao, sintomas, solucao)
        print(f"Caso C{numero:02d} gravado.")
    else:
        print("Nenhum caso foi gravado.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=PASTA / "base_local.sqlite3")
    args = parser.parse_args()
    print("Protótipo didático. Use somente sintomas e casos fictícios.")
    try:
        with closing(sqlite3.connect(args.base)) as conexao:
            iniciar_base(conexao)
            total = conexao.execute("SELECT COUNT(*) FROM casos").fetchone()[0]
            print(f"Base carregada: {total} casos.")
            while True:
                entrada = input("\nSintomas separados por vírgula (Enter para sair): ")
                sintomas = list({normalizar(s): s.strip() for s in entrada.split(",") if s.strip()}.values())
                if not sintomas:
                    break
                consultar(conexao, sintomas)
    except (EOFError, KeyboardInterrupt):
        print("\nSessão encerrada.")
    except (OSError, sqlite3.Error) as erro:
        parser.exit(1, f"Falha ao acessar a base: {erro}\n")


if __name__ == "__main__":
    main()
