"""Planejador clássico para a agenda acadêmica da questão 11."""

from itertools import permutations

# Duração em minutos e utilidade pela conclusão no dia.
TAREFAS = {"A": (90, 10), "B": (120, 5), "C": (60, 10), "D": (60, 1)}
REUNIAO = ("C", 120, 180)
FIM = 240


def planos_validos():
    """Enumera as ordens de tarefas opcionais e as divisões em torno da reunião."""
    opcionais = [tarefa for tarefa in TAREFAS if tarefa != "C"]
    for quantidade in range(len(opcionais) + 1):
        for ordem in permutations(opcionais, quantidade):
            for corte in range(quantidade + 1):
                plano = [REUNIAO]
                for bloco, inicio, limite in (
                    (ordem[:corte], 0, REUNIAO[1]),
                    (ordem[corte:], REUNIAO[2], FIM),
                ):
                    for tarefa in bloco:
                        fim = inicio + TAREFAS[tarefa][0]
                        plano.append((tarefa, inicio, fim))
                        inicio = fim
                    if inicio > limite:
                        break
                else:
                    yield sorted(plano, key=lambda item: item[1])


def utilidade(plano):
    return sum(TAREFAS[tarefa][1] for tarefa, _, _ in plano)


def horario(minutos):
    horas, resto = divmod(14 * 60 + minutos, 60)
    return f"{horas:02d}h{resto:02d}"


if __name__ == "__main__":
    plano = max(planos_validos(), key=utilidade)
    for tarefa, inicio, fim in plano:
        print(f"{horario(inicio)} - {horario(fim)}: {tarefa}")
    print(f"Utilidade: {utilidade(plano)}")
    print("B fica pendente para agendamento até amanhã.")
