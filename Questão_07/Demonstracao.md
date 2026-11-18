# Demonstração do protótipo RBC

Execute na pasta da questão. A primeira execução usa um arquivo de demonstração novo e separado da base padrão.

```powershell
python diagnostico_rbc.py --base demo.sqlite3
```

## Primeira execução

Use o mesmo comando. Envie uma linha por vez. A última linha vazia encerra a sessão.

```text
febre, tosse, dor muscular
v
n
coriza, espirros
c
Rinite alérgica
Redução da exposição ao alérgeno no caso fictício.
s

```

Saída capturada do programa:

```text
Protótipo didático. Use somente sintomas e casos fictícios.
Base carregada: 15 casos.

Sintomas separados por vírgula (Enter para sair): Casos recuperados (similaridade de Jaccard):
  C04 | 3/4 (75.0%) | Influenza
    Sintomas: febre, tosse, dor muscular, fadiga
  C05 | 2/5 (40.0%) | Influenza
    Sintomas: febre, calafrios, dor muscular, dor de cabeça
  C06 | 2/5 (40.0%) | Influenza
    Sintomas: febre, tosse, fadiga, dor de garganta
Hipótese do protótipo (C04): Influenza
Tratamento registrado no caso: Repouso, hidratação e avaliação clínica no caso fictício.
Revisão ([v] validar, [c] corrigir, [n] descartar): Guardar o caso revisado? [s/N]: Nenhum caso foi gravado.

Sintomas separados por vírgula (Enter para sair): Casos recuperados (similaridade de Jaccard):
  C01 | 1/2 (50.0%) | Resfriado comum
    Sintomas: coriza, espirros, dor de garganta, tosse
  C07 | 1/2 (50.0%) | Rinite alérgica
    Sintomas: espirros, coriza, coceira no nariz, olhos lacrimejantes
  C02 | 1/4 (25.0%) | Resfriado comum
    Sintomas: coriza, congestão nasal, dor de garganta
Empate entre diagnósticos no topo. Informe a solução na revisão.
Revisão ([c] informar caso, [n] descartar): Diagnóstico revisado do caso fictício: Tratamento revisado do caso fictício: Guardar o caso revisado? [s/N]: Caso C16 gravado.

Sintomas separados por vírgula (Enter para sair):
```

## Segunda execução

Use o mesmo comando. Envie uma linha por vez. A última linha vazia encerra a sessão.

```text
CORÍZA, espirros, espirros
n
sintoma fictício sem correspondência
n

```

Saída capturada do programa:

```text
Protótipo didático. Use somente sintomas e casos fictícios.
Base carregada: 16 casos.

Sintomas separados por vírgula (Enter para sair): Casos recuperados (similaridade de Jaccard):
  C16 | 1 (100.0%) | Rinite alérgica
    Sintomas: coriza, espirros
  C01 | 1/2 (50.0%) | Resfriado comum
    Sintomas: coriza, espirros, dor de garganta, tosse
  C07 | 1/2 (50.0%) | Rinite alérgica
    Sintomas: espirros, coriza, coceira no nariz, olhos lacrimejantes
Hipótese do protótipo (C16): Rinite alérgica
Tratamento registrado no caso: Redução da exposição ao alérgeno no caso fictício.
Revisão ([v] validar, [c] corrigir, [n] descartar): Nenhum caso foi gravado.

Sintomas separados por vírgula (Enter para sair): Nenhum caso tem sintomas em comum. Não há hipótese automática.
Revisão ([c] informar caso, [n] descartar): Nenhum caso foi gravado.

Sintomas separados por vírgula (Enter para sair):
```
