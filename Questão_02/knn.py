"""Demonstração de KNN categórico para a questão 2."""

import argparse
import csv
from collections import Counter
from pathlib import Path

ATRIBUTOS = ("Historia", "Divida", "Garantia", "Renda", "Emprego", "Idade")
NOMES = {"Historia": "Histórico", "Divida": "Dívida"}
CLASSES = ("Alto", "Moderado", "Baixo")


def ler_base(caminho):
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        campos = ("Exemplo", *ATRIBUTOS, "Risco")
        if not set(campos).issubset(leitor.fieldnames or []):
            raise ValueError("O CSV precisa conter: " + ", ".join(campos))
        base = list(leitor)

    ids = set()
    for linha in base:
        if any(not linha[campo] for campo in campos):
            raise ValueError("Há campos obrigatórios vazios no CSV.")
        identificador = linha["Exemplo"]
        if not identificador.startswith("E") or not identificador[1:].isdecimal():
            raise ValueError(f"Identificador inválido: {identificador}")
        numero = int(identificador[1:])
        if numero in ids or linha["Risco"] not in CLASSES:
            raise ValueError(f"Identificador repetido ou risco inválido: {identificador}")
        ids.add(numero)
    return base


def atributos_diferentes(consulta, referencia):
    return tuple(campo for campo in ATRIBUTOS if consulta[campo] != referencia[campo])


def ordenar_vizinhos(consulta, base):
    vizinhos = []
    for exemplo in base:
        diferencas = atributos_diferentes(consulta, exemplo)
        vizinhos.append((len(diferencas), exemplo, diferencas))
    return sorted(vizinhos, key=lambda item: (item[0], int(item[1]["Exemplo"][1:])))


def classificar(vizinhos_ordenados, k):
    if not 1 <= k <= len(vizinhos_ordenados):
        raise ValueError("k deve estar entre 1 e o número de vizinhos disponíveis.")

    vizinhos = vizinhos_ordenados[:k]
    rotulos = [exemplo["Risco"] for _, exemplo, _ in vizinhos]
    votos = Counter(rotulos)
    # max devolve a primeira classe com a maior contagem na ordem dos vizinhos.
    return max(rotulos, key=votos.get), votos, vizinhos


def avaliar(base, valores_k):
    matrizes = {k: Counter() for k in valores_k}
    for posicao, consulta in enumerate(base):
        referencias = base[:posicao] + base[posicao + 1:]
        ordenados = ordenar_vizinhos(consulta, referencias)
        for k, matriz in matrizes.items():
            previsto, _, _ = classificar(ordenados, k)
            matriz[consulta["Risco"], previsto] += 1
    return matrizes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path(__file__).with_name("arquivo.csv"))
    parser.add_argument("--exemplo", default="E1", help="Instância que será demonstrada")
    parser.add_argument("--k", type=int, default=5, help="Número de vizinhos na demonstração")
    args = parser.parse_args()

    try:
        base = ler_base(args.csv)
        consulta = next((linha for linha in base if linha["Exemplo"] == args.exemplo), None)
        if consulta is None:
            raise ValueError(f"Exemplo {args.exemplo} não encontrado.")
        referencias = [linha for linha in base if linha["Exemplo"] != args.exemplo]
        previsto, votos, vizinhos = classificar(ordenar_vizinhos(consulta, referencias), args.k)
        valores_k = sorted({args.k, *(k for k in (1, 3, 5, 7) if k < len(base))})
        matrizes = avaliar(base, valores_k)
    except (OSError, ValueError, csv.Error) as erro:
        parser.error(str(erro))

    print(f"Base: {len(base)} instâncias")
    print(f"\nClassificação de {args.exemplo} com k={args.k}")
    for distancia, exemplo, diferencas in vizinhos:
        campos = ", ".join(NOMES.get(campo, campo) for campo in diferencas)
        print(f'  {exemplo["Exemplo"]}: d={distancia}, risco={exemplo["Risco"]}, diferenças={campos or "nenhuma"}')
    print("Votos: " + ", ".join(f"{classe}={votos[classe]}" for classe in CLASSES))
    print(f'Risco previsto: {previsto}. Risco real: {consulta["Risco"]}.')

    print("\nValidação leave-one-out")
    for k, matriz in matrizes.items():
        acertos = sum(matriz[classe, classe] for classe in CLASSES)
        print(f"  k={k}: {acertos}/{len(base)} ({acertos / len(base):.1%})")
    print(f"\nMatriz de confusão (k={args.k}, linhas reais e colunas previstas)")
    print(f'{"":>9}' + "".join(f"{classe:>10}" for classe in CLASSES))
    for real in CLASSES:
        print(f"{real:>9}" + "".join(f"{matrizes[args.k][real, classe]:>10}" for classe in CLASSES))


if __name__ == "__main__":
    main()
