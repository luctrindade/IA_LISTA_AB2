"""Agente de agenda acadêmica com Ollama e planejamento exato."""

import argparse
import json
import re
from functools import lru_cache
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PESOS = {"alta": 10, "media": 5, "baixa": 1}
HORARIO = {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"}
HORARIO_OPCIONAL = {"anyOf": [HORARIO, {"type": "null"}]}


def objeto(campos):
    return {"type": "object", "properties": campos, "required": list(campos),
            "additionalProperties": False}


ESQUEMA = objeto({
    "pergunta": {"type": "string"},
    "inicio": HORARIO_OPCIONAL,
    "fim": HORARIO_OPCIONAL,
    "tarefas": {
        "type": "array", "maxItems": 8,
        "items": objeto({
            "nome": {"type": "string"},
            "duracao": {"type": "integer", "minimum": 1, "maximum": 1440},
            "prioridade": {"enum": list(PESOS)},
            "prazo": {"enum": ["hoje", "amanha", "depois", "sem prazo"]},
            "fixo": HORARIO_OPCIONAL,
            "concluir_ate": HORARIO_OPCIONAL,
        }),
    },
})

INSTRUCAO = """Extraia dados de um pedido de agenda de um único dia.
Retorne apenas JSON. Use minutos inteiros para duração e HH:MM para horários.
Tarefas são indivisíveis e compromissos com início fixo são obrigatórios.
Inclua todas as atividades solicitadas, inclusive as que pareçam inviáveis.
Preencha "fixo" somente com um início obrigatório, como "a reunião começa às 10h".
O início obrigatório deve ter sido informado para aquela mesma tarefa. Para
tarefas flexíveis ou com apenas prazo de entrega, use "fixo": null.
No campo prazo, use "hoje" para hoje, "amanha" para amanhã, "depois" para
datas posteriores a amanhã e "sem prazo" apenas quando o prazo estiver ausente.
Use prioridade media quando omitida e 'sem prazo' quando não houver prazo.
Mapeie urgente para alta. Use 'depois' para prazo após amanhã.
Em "concluir_ate", use o horário limite somente se a tarefa precisar terminar
até uma hora explícita no dia planejado, por exemplo "entregar hoje até 15h".
Nesse caso, use também prazo "hoje". Use null nos demais casos. Para um compromisso
das 10h às 11h, extraia início fixo 10:00 e duração 60 minutos.
Use pergunta vazia quando puder extrair os dados. Durações em minutos e
intervalos com início e fim são suficientes. Peça esclarecimento em português
se faltar a janela, duração ou início obrigatório, ou se o pedido envolver
mais de um dia, dependências ou tarefas divisíveis.

Exemplo de extração:
Pedido: Tenho das 9h às 12h. Quero ler por 30 minutos até amanhã.
Preciso enviar um formulário hoje até 10h. O formulário leva 20 minutos e é
urgente. Tenho também uma reunião das 9h às 10h, com prioridade alta.
JSON: {"pergunta":"","inicio":"09:00","fim":"12:00","tarefas":[
{"nome":"Ler","duracao":30,"prioridade":"media","prazo":"amanha","fixo":null,"concluir_ate":null},
{"nome":"Enviar formulário","duracao":20,"prioridade":"alta","prazo":"hoje","fixo":null,"concluir_ate":"10:00"},
{"nome":"Reunião","duracao":60,"prioridade":"alta","prazo":"sem prazo","fixo":"09:00","concluir_ate":null}]}"""

DEMO = {
    "pergunta": "", "inicio": "14:00", "fim": "18:00",
    "tarefas": [
        {"nome": "Preparar aula de IA", "duracao": 90, "prioridade": "alta",
         "prazo": "hoje", "fixo": None},
        {"nome": "Corrigir trabalhos", "duracao": 120, "prioridade": "media",
         "prazo": "amanha", "fixo": None},
        {"nome": "Reunião de pesquisa", "duracao": 60, "prioridade": "alta",
         "prazo": "hoje", "fixo": "16:00"},
        {"nome": "Revisar artigo", "duracao": 60, "prioridade": "baixa",
         "prazo": "depois", "fixo": None},
    ],
}


def interpretar(modelo, pedido):
    payload = {
        "model": modelo, "format": ESQUEMA, "stream": False,
        "options": {"temperature": 0},
        "messages": [{"role": "system", "content": INSTRUCAO},
                     {"role": "user", "content": pedido}],
    }
    request = Request("http://127.0.0.1:11434/api/chat",
                      data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(json.load(response)["message"]["content"])
    except HTTPError as erro:
        detalhe = erro.read(4096).decode("utf-8", errors="replace")
        raise ValueError(f"Ollama retornou HTTP {erro.code}. {detalhe}") from erro


def minutos(valor):
    if valor == "24:00":
        return 1440
    if not isinstance(valor, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", valor, re.ASCII):
        raise ValueError("Informe os horários no formato HH:MM.")
    horas, minutos_restantes = map(int, valor.split(":"))
    return horas * 60 + minutos_restantes


def hora(valor):
    return f"{valor // 60:02d}:{valor % 60:02d}"


def hora_limite(tarefa):
    limite = tarefa.get("concluir_ate")
    return minutos(limite) if limite is not None else 1440


def validar(dados):
    inicio, fim = minutos(dados["inicio"]), minutos(dados["fim"])
    tarefas = dados["tarefas"]
    if inicio >= fim or not isinstance(tarefas, list) or not 1 <= len(tarefas) <= 8:
        raise ValueError("Informe uma janela válida e de uma a oito tarefas.")
    ocupados, livres = [], []
    nomes = set()
    for indice, tarefa in enumerate(tarefas):
        nome = tarefa["nome"].strip()
        duracao = tarefa["duracao"]
        if not nome or nome.casefold() in nomes or type(duracao) is not int or not 1 <= duracao <= 1440:
            raise ValueError("Cada tarefa precisa de um nome distinto e de uma duração em minutos.")
        nomes.add(nome.casefold())
        if tarefa["prioridade"] not in PESOS or tarefa["prazo"] not in ("hoje", "amanha", "depois", "sem prazo"):
            raise ValueError("Prioridade ou prazo inválido na interpretação.")
        limite = hora_limite(tarefa)
        if tarefa.get("concluir_ate") is not None and tarefa["prazo"] != "hoje":
            raise ValueError(f"O horário limite de {nome} precisa pertencer ao dia planejado.")
        if tarefa["fixo"] is None:
            livres.append(indice)
        else:
            comeco = minutos(tarefa["fixo"])
            if comeco + duracao > limite and tarefa.get("concluir_ate") is not None:
                raise ValueError(f"O compromisso fixo {nome} termina depois do seu horário limite.")
            ocupados.append((comeco, comeco + duracao, indice))
    blocos = []
    cursor = inicio
    for comeco, termino, _ in sorted(ocupados):
        if comeco < cursor or termino > fim:
            raise ValueError("Os compromissos fixos se sobrepõem ou ficam fora da janela.")
        if cursor < comeco:
            blocos.append((cursor, comeco))
        cursor = termino
    if cursor < fim:
        blocos.append((cursor, fim))
    return blocos, ocupados, livres


def planejar(tarefas, blocos, ocupados, livres):
    limites = [hora_limite(tarefa) for tarefa in tarefas]

    @lru_cache(maxsize=None)
    def melhor(bloco, cursor, restantes):
        if bloco == len(blocos) or not restantes:
            return (0, 0), ()
        proximo_inicio = blocos[bloco + 1][0] if bloco + 1 < len(blocos) else 0
        resultado = melhor(bloco + 1, proximo_inicio, restantes)
        for indice in restantes:
            tarefa = tarefas[indice]
            fim = cursor + tarefa["duracao"]
            if fim <= min(blocos[bloco][1], limites[indice]):
                (pontos, urgentes), itens = melhor(
                    bloco, fim, tuple(i for i in restantes if i != indice))
                nota = (pontos + PESOS[tarefa["prioridade"]],
                        urgentes + (tarefa["prazo"] == "hoje"))
                if nota > resultado[0]:
                    resultado = nota, ((cursor, fim, indice), *itens)
        return resultado

    inicio = blocos[0][0] if blocos else 0
    _, flexiveis = melhor(0, inicio, tuple(livres))
    return sorted([*ocupados, *flexiveis])


def explicar(tarefas, plano, blocos):
    selecionadas = {indice for _, _, indice in plano}
    maior_bloco = max((fim - inicio for inicio, fim in blocos), default=0)
    pontos = sum(PESOS[tarefas[i]["prioridade"]] for i in selecionadas)
    print(f"\nAgenda proposta. Utilidade total de {pontos} pontos.")
    for inicio, fim, indice in plano:
        tarefa = tarefas[indice]
        motivo = "compromisso fixo" if tarefa["fixo"] else "selecionada por utilidade"
        print(f"  {hora(inicio)}–{hora(fim)}  {tarefa['nome']} | {motivo}, prioridade {tarefa['prioridade']}")
    for indice, tarefa in enumerate(tarefas):
        if indice in selecionadas:
            continue
        limite = hora_limite(tarefa)
        if tarefa["duracao"] > maior_bloco:
            motivo = "duração maior que qualquer bloco contínuo livre"
        elif all(inicio + tarefa["duracao"] > min(fim, limite) for inicio, fim in blocos):
            motivo = f"nenhum bloco comporta a tarefa até {hora(limite)}"
        else:
            motivo = "o plano selecionado tem maior ou igual utilidade com as demais tarefas"
        aviso = " | prazo de hoje em risco" if tarefa["prazo"] == "hoje" else ""
        prazo = f"hoje até {hora(limite)}" if tarefa.get("concluir_ate") is not None else tarefa["prazo"]
        print(f"  Pendente: {tarefa['nome']} ({tarefa['duracao']} min, prazo {prazo}) | {motivo}{aviso}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pedido", nargs="?", help="Pedido completo em português")
    parser.add_argument("--modelo", default="qwen2.5:3b")
    parser.add_argument("--demo", action="store_true", help="Usa interpretação de exemplo, sem LLM")
    args = parser.parse_args()
    try:
        if args.demo:
            print("Demonstração com entrada estruturada de exemplo.")
            dados = DEMO
            blocos, ocupados, livres = validar(dados)
        else:
            pedido = args.pedido or input("Descreva a agenda que você quer montar: ")
            while True:
                dados = interpretar(args.modelo, pedido)
                pergunta = dados["pergunta"].strip()
                if pergunta:
                    complemento = input(f"{pergunta}\nResposta (Enter para sair): ").strip()
                else:
                    print("Interpretação para revisão:")
                    print(f"Janela {dados['inicio']}–{dados['fim']}.")
                    for tarefa in dados["tarefas"]:
                        limite = tarefa.get("concluir_ate")
                        prazo = f"hoje até {limite}" if limite is not None else tarefa["prazo"]
                        print(f"  {tarefa['nome']} | {tarefa['duracao']} min | {tarefa['prioridade']} | "
                              f"prazo {prazo} | início fixo {tarefa['fixo'] or 'livre'}")
                    try:
                        blocos, ocupados, livres = validar(dados)
                    except ValueError as erro:
                        print(f"Confira a interpretação. {erro}")
                    else:
                        if input("Calcular com esses dados? [s/N]: ").strip().lower() == "s":
                            break
                    complemento = input("Informe a correção (Enter para sair): ").strip()
                if not complemento:
                    return
                pedido += "\nComplemento: " + complemento

        plano = planejar(dados["tarefas"], blocos, ocupados, livres)
        explicar(dados["tarefas"], plano, blocos)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as erro:
        parser.exit(1, f"Falha ao montar a agenda: {erro}\nConfira os dados e, no modo normal, se o Ollama e o modelo estão disponíveis.\n")
    except (EOFError, KeyboardInterrupt):
        print("\nSessão encerrada.")


if __name__ == "__main__":
    main()
