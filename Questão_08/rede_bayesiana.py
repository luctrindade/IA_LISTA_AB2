"""Inferência exata com pgmpy em uma rede bayesiana binária de uso acadêmico."""

import argparse
import json
import math
from itertools import product
from pathlib import Path

from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from pgmpy.models import DiscreteBayesianNetwork

MODELO = Path(__file__).with_name("modelo_influenza.json")
ESTADOS = ("nao", "sim")
ALVO = "influenza"


def carregar_modelo(caminho):
    modelo = json.loads(caminho.read_text(encoding="utf-8"))
    if tuple(modelo["estados"]) != ESTADOS:
        raise ValueError("O modelo deve usar os estados nao e sim, nessa ordem.")

    rede = DiscreteBayesianNetwork()
    vistos = set()
    for no in modelo["nos"]:
        nome, pais, tabela = no["id"], no["pais"], no["p_sim"]
        if nome in vistos or len(set(pais)) != len(pais) or not set(pais) <= vistos:
            raise ValueError(f"Nó repetido ou pais fora da ordem topológica: {nome}.")
        chaves = [",".join(valores) for valores in product(ESTADOS, repeat=len(pais))]
        if set(tabela) != set(chaves) or not all(0 <= valor <= 1 for valor in tabela.values()):
            raise ValueError(f"Tabela de probabilidades inválida: {nome}.")
        p_sim = [tabela[chave] for chave in chaves]
        rede.add_node(nome)
        rede.add_edges_from((pai, nome) for pai in pais)
        rede.add_cpds(TabularCPD(
            variable=nome,
            variable_card=len(ESTADOS),
            values=[[1 - p for p in p_sim], p_sim],
            evidence=pais or None,
            evidence_card=[len(ESTADOS)] * len(pais) if pais else None,
            state_names={variavel: list(ESTADOS) for variavel in (nome, *pais)},
        ))
        vistos.add(nome)
    if ALVO not in vistos:
        raise ValueError(f"O modelo precisa conter o nó {ALVO}.")
    rede.check_model()
    return rede


def posterior(rede, evidencias):
    """Consulta P(influenza=sim) por eliminação de variáveis."""
    observadas = {}
    virtuais = []
    for nome, pesos in evidencias.items():
        maior_peso = max(pesos)
        if 0 in pesos:
            observadas[nome] = ESTADOS[pesos.index(maior_peso)]
        else:
            virtuais.append(TabularCPD(
                nome, len(ESTADOS), [[peso / maior_peso] for peso in pesos],
                state_names={nome: list(ESTADOS)},
            ))

    inferencia = VariableElimination(rede)
    # Em modelos com zeros nas CPTs, verifique a massa das observações antes da
    # consulta. O pgmpy pode podar uma evidência impossível separada do alvo.
    if observadas and any((cpd.values == 0).any() for cpd in rede.get_cpds()):
        marginal = inferencia.query(list(observadas), show_progress=False)
        if marginal.get_value(**observadas) == 0:
            raise ValueError("As evidências têm probabilidade zero no modelo.")

    distribuicao = inferencia.query(
        [ALVO], evidence=observadas, virtual_evidence=virtuais or None, show_progress=False,
    )
    probabilidade = float(distribuicao.get_value(influenza="sim"))
    if not math.isfinite(probabilidade):
        raise ValueError("As evidências têm probabilidade zero no modelo.")
    return probabilidade


def interpretar_evidencia(texto, rede):
    nome, separador, valor = texto.strip().lower().partition("=")
    permitidos = set(rede.nodes) - {ALVO}
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


def executar_cenario(rede, titulo, observacoes):
    print(f"\n{titulo}")
    evidencias = {}
    print(f"  A priori (sem evidências): {posterior(rede, evidencias):.2%}")
    for texto in observacoes:
        nome, pesos = interpretar_evidencia(texto, rede)
        # Uma nova observação da mesma variável substitui a anterior.
        evidencias[nome] = pesos
        print(f"  {texto:<25} -> {posterior(rede, evidencias):.2%}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", type=Path, default=MODELO)
    parser.add_argument("evidencias", nargs="*", help="Ex.: febre=sim tosse=nao dor_muscular=0.2:0.8")
    args = parser.parse_args()
    try:
        rede = carregar_modelo(args.modelo)
        print("Probabilidade de influenza em um modelo fictício de uso acadêmico.")
        if args.evidencias:
            executar_cenario(rede, "Consulta personalizada", args.evidencias)
        else:
            executar_cenario(rede, "1. Evidência incompleta", ["febre=sim"])
            executar_cenario(rede, "2. Sintomas acrescentados em sequência",
                              ["febre=sim", "tosse=sim", "dor_muscular=sim"])
            executar_cenario(rede, "3. Exposição com febre ausente",
                              ["exposicao=sim", "febre=nao", "tosse=sim"])
            executar_cenario(rede, "4. Relato incerto de dor muscular",
                              ["febre=sim", "dor_muscular=0.2:0.8"])
    except (OSError, ValueError, KeyError, TypeError) as erro:
        parser.error(str(erro))


if __name__ == "__main__":
    main()
