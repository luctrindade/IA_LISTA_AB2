"""Inferência exata em uma rede bayesiana binária para uso acadêmico."""

import argparse
import json
import math
from itertools import product
from pathlib import Path

MODELO = Path(__file__).with_name("modelo_influenza.json")
ESTADOS = ("nao", "sim")
ALVO = "influenza"


def carregar_modelo(caminho):
    modelo = json.loads(caminho.read_text(encoding="utf-8"))
    if tuple(modelo["estados"]) != ESTADOS:
        raise ValueError("O modelo deve usar os estados nao e sim, nessa ordem.")

    nos = modelo["nos"]
    vistos = set()
    for no in nos:
        nome, pais, tabela = no["id"], no["pais"], no["p_sim"]
        if nome in vistos or len(set(pais)) != len(pais) or not set(pais) <= vistos:
            raise ValueError(f"Nó repetido ou pais fora da ordem topológica: {nome}.")
        chaves = {",".join(valores) for valores in product(ESTADOS, repeat=len(pais))}
        if set(tabela) != chaves or not all(0 <= valor <= 1 for valor in tabela.values()):
            raise ValueError(f"Tabela de probabilidades inválida: {nome}.")
        vistos.add(nome)
    if ALVO not in vistos:
        raise ValueError(f"O modelo precisa conter o nó {ALVO}.")
    return nos


def probabilidade_conjunta(nos, estados):
    conjunta = 1.0
    for no in nos:
        chave = ",".join(estados[pai] for pai in no["pais"])
        p_sim = no["p_sim"][chave]
        conjunta *= p_sim if estados[no["id"]] == "sim" else 1 - p_sim
    return conjunta


def posterior(nos, evidencias):
    """Soma os pesos das configurações completas e normaliza pelo total."""
    nomes = [no["id"] for no in nos]
    pesos = {estado: [] for estado in ESTADOS}
    for valores in product(ESTADOS, repeat=len(nomes)):
        estados = dict(zip(nomes, valores))
        verossimilhanca = math.prod(
            pesos_no[ESTADOS.index(estados[nome])]
            for nome, pesos_no in evidencias.items()
        )
        if verossimilhanca:
            peso = probabilidade_conjunta(nos, estados) * verossimilhanca
            pesos[estados[ALVO]].append(peso)
    massas = {estado: math.fsum(valores) for estado, valores in pesos.items()}
    total = math.fsum(massas.values())
    if total == 0:
        raise ValueError("As evidências têm probabilidade zero no modelo.")
    return massas["sim"] / total


def interpretar_evidencia(texto, nos):
    nome, separador, valor = texto.strip().lower().partition("=")
    permitidos = {no["id"] for no in nos} - {ALVO}
    if not separador or nome not in permitidos:
        raise ValueError(f"Evidência inválida: {texto}. Use uma das variáveis {', '.join(sorted(permitidos))}.")
    if valor in ESTADOS:
        return nome, (1.0, 0.0) if valor == "nao" else (0.0, 1.0)

    partes = valor.split(":")
    if len(partes) != 2:
        raise ValueError("Use sim, nao ou pesos no formato peso_nao:peso_sim.")
    pesos = tuple(float(parte) for parte in partes)
    if not all(math.isfinite(peso) and 0 <= peso <= 1 for peso in pesos) or max(pesos) == 0:
        raise ValueError("Os pesos devem estar em [0, 1], com pelo menos um positivo.")
    return nome, pesos


def executar_cenario(nos, titulo, observacoes):
    print(f"\n{titulo}")
    evidencias = {}
    print(f"  A priori (sem evidências): {posterior(nos, evidencias):.2%}")
    for texto in observacoes:
        nome, pesos = interpretar_evidencia(texto, nos)
        # Uma nova observação da mesma variável substitui a anterior.
        evidencias[nome] = pesos
        print(f"  {texto:<25} -> {posterior(nos, evidencias):.2%}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", type=Path, default=MODELO)
    parser.add_argument("evidencias", nargs="*", help="Ex.: febre=sim tosse=nao dor_muscular=0.2:0.8")
    args = parser.parse_args()
    try:
        nos = carregar_modelo(args.modelo)
        print("Probabilidade de influenza em um modelo fictício de uso acadêmico.")
        if args.evidencias:
            executar_cenario(nos, "Consulta personalizada", args.evidencias)
        else:
            executar_cenario(nos, "1. Evidência incompleta", ["febre=sim"])
            executar_cenario(nos, "2. Sintomas acrescentados em sequência",
                              ["febre=sim", "tosse=sim", "dor_muscular=sim"])
            executar_cenario(nos, "3. Exposição com febre ausente",
                              ["exposicao=sim", "febre=nao", "tosse=sim"])
            executar_cenario(nos, "4. Relato incerto de dor muscular",
                              ["febre=sim", "dor_muscular=0.2:0.8"])
    except (OSError, ValueError, KeyError, TypeError) as erro:
        parser.error(str(erro))


if __name__ == "__main__":
    main()
