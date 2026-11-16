"""Controlador de ventilação Mamdani, sem dependências externas."""

import argparse

TEMPERATURA = {
    "fria": (16, 16, 20, 25),
    "amena": (21, 26, 26, 31),
    "quente": (27, 32, 40, 40),
}
UMIDADE = {
    "baixa": (0, 0, 30, 50),
    "média": (35, 55, 55, 75),
    "alta": (60, 80, 100, 100),
}
VENTILACAO = {
    "baixa": (0, 20, 20, 40),
    "média": (25, 50, 50, 75),
    "alta": (60, 80, 80, 100),
}

# Linhas: temperatura fria, amena e quente. Colunas: umidade baixa, média e alta.
REGRAS = (
    ("baixa", "baixa", "média"),
    ("baixa", "média", "alta"),
    ("média", "alta", "alta"),
)
PASSO = 0.1  # Pontos percentuais de ventilação.


def pertinencia(valor, pontos):
    """Função trapezoidal que também representa triângulos e ombros."""
    a, b, c, d = pontos
    if valor < a or valor > d:
        return 0.0
    if valor < b:
        return (valor - a) / (b - a)
    if valor > c:
        return (d - valor) / (d - c)
    return 1.0


def fuzzificar(valor, termos):
    return {termo: pertinencia(valor, pontos) for termo, pontos in termos.items()}


def agregar_saidas(ativacoes):
    """Retorna os pontos da curva agregada pelo máximo dos consequentes cortados."""
    curva = []
    for indice in range(round(100 / PASSO) + 1):
        velocidade = indice * PASSO
        grau = max(
            min(ativacoes[termo], pertinencia(velocidade, pontos))
            for termo, pontos in VENTILACAO.items()
        )
        curva.append((velocidade, grau))
    return curva


def centroide(curva):
    """Aproxima as integrais de área e momento pela regra dos trapézios."""
    area = momento = 0.0
    for (x1, grau1), (x2, grau2) in zip(curva, curva[1:]):
        meia_largura = (x2 - x1) / 2
        area += meia_largura * (grau1 + grau2)
        momento += meia_largura * (x1 * grau1 + x2 * grau2)
    if area == 0:
        raise ValueError("A curva agregada tem área zero.")
    return momento / area, area, momento


def inferir(temperatura, umidade):
    if not 16 <= temperatura <= 40 or not 0 <= umidade <= 100:
        raise ValueError("Informe temperatura de 16 a 40 °C e umidade de 0 a 100%.")

    graus_t = fuzzificar(temperatura, TEMPERATURA)
    graus_u = fuzzificar(umidade, UMIDADE)
    ativacoes = dict.fromkeys(VENTILACAO, 0.0)
    regras_ativas = []
    for (termo_t, grau_t), linha in zip(graus_t.items(), REGRAS):
        for (termo_u, grau_u), saida in zip(graus_u.items(), linha):
            grau = min(grau_t, grau_u)
            if grau > 0:
                regras_ativas.append((termo_t, termo_u, saida, grau))
                ativacoes[saida] = max(ativacoes[saida], grau)

    velocidade, area, momento = centroide(agregar_saidas(ativacoes))
    return velocidade, graus_t, graus_u, regras_ativas, ativacoes, area, momento


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("temperatura", type=float, nargs="?", default=30.0)
    parser.add_argument("umidade", type=float, nargs="?", default=65.0)
    args = parser.parse_args()
    try:
        resultado = inferir(args.temperatura, args.umidade)
    except ValueError as erro:
        parser.error(str(erro))

    velocidade, graus_t, graus_u, regras, ativacoes, area, momento = resultado
    print(f"Entradas: {args.temperatura:g} °C e {args.umidade:g}% de umidade")
    for nome, graus in (("Temperatura", graus_t), ("Umidade", graus_u)):
        print(f"{nome}: " + ", ".join(f"{termo}={grau:.3f}" for termo, grau in graus.items()))
    print("Regras ativas:")
    for temperatura, umidade, saida, grau in regras:
        print(f"  {temperatura} E {umidade} -> {saida}: {grau:.3f}")
    print("Cortes: " + ", ".join(f"{termo}={grau:.3f}" for termo, grau in ativacoes.items()))
    print(f"Área: {area:.4f} | Momento: {momento:.4f}")
    print(f"Comando de ventilação: {velocidade:.2f}%")


if __name__ == "__main__":
    main()
