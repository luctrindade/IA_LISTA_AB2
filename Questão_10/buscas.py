"""Demonstra as buscas da questão 10 com desempate alfabético."""

from collections import deque
from heapq import heappop, heappush

TRECHOS = (
    ("A", "B", 4), ("A", "D", 3), ("B", "C", 5), ("B", "E", 2),
    ("C", "F", 2), ("D", "E", 4), ("D", "G", 6), ("E", "F", 3),
    ("E", "H", 5), ("F", "I", 4), ("G", "H", 3), ("H", "I", 2),
)
H = dict(zip("ABCDEFGHI", (10, 8, 6, 9, 6, 4, 5, 2, 0)))
GRAFO = {no: {} for no in H}
for origem, destino, custo in TRECHOS:
    GRAFO[origem][destino] = GRAFO[destino][origem] = custo


def largura():
    fila = deque([("A",)])
    descobertos = {"A"}
    retirados = []
    while fila:
        rota = fila.popleft()
        no = rota[-1]
        retirados.append(no)
        if no == "I":
            return rota, custo_rota(rota), retirados
        for vizinho in sorted(GRAFO[no]):
            if vizinho not in descobertos:
                descobertos.add(vizinho)
                fila.append((*rota, vizinho))


def profundidade():
    visitados = set()
    retirados = []

    def visitar(no, rota):
        visitados.add(no)
        retirados.append(no)
        if no == "I":
            return rota
        for vizinho in sorted(GRAFO[no]):
            if vizinho not in visitados:
                solucao = visitar(vizinho, (*rota, vizinho))
                if solucao is not None:
                    return solucao
        return None

    rota = visitar("A", ("A",))
    return rota, custo_rota(rota), retirados


def custo_rota(rota):
    return sum(GRAFO[a][b] for a, b in zip(rota, rota[1:]))


def busca_prioritaria(heuristica, obrigatorios=()):
    bits = {no: 1 << posicao for posicao, no in enumerate(obrigatorios)}
    completo = (1 << len(bits)) - 1
    inicial = ("A", 0)
    fronteira = [(heuristica("A"), inicial, 0, ("A",))]
    melhor = {inicial: 0}
    retirados = []
    while fronteira:
        f, estado, g, rota = heappop(fronteira)
        if g != melhor[estado]:
            continue
        no, mascara = estado
        retirados.append((no, mascara, g, heuristica(no), f))
        if no == "I" and mascara == completo:
            return rota, g, retirados
        for vizinho, custo in sorted(GRAFO[no].items()):
            nova_mascara = mascara | bits.get(vizinho, 0)
            if vizinho == "I" and nova_mascara != completo:
                continue
            proximo = (vizinho, nova_mascara)
            novo_g = g + custo
            if novo_g < melhor.get(proximo, float("inf")):
                melhor[proximo] = novo_g
                heappush(fronteira, (novo_g + heuristica(vizinho), proximo,
                                     novo_g, (*rota, vizinho)))


if __name__ == "__main__":
    resultados = {
        "DFS": profundidade(),
        "BFS": largura(),
        "UCS": busca_prioritaria(lambda _: 0),
        "A*": busca_prioritaria(H.__getitem__),
        "UCS com D e F": busca_prioritaria(lambda _: 0, ("D", "F")),
    }
    for nome, (rota, custo, retirados) in resultados.items():
        print(f"{nome}: {' -> '.join(rota)} ({custo} min)")
        print(f"  Retiradas até o objetivo: {retirados}")
