"""Recomenda livros com OWL 2, HermiT e uma consulta SPARQL."""

import argparse
from pathlib import Path

import owlready2
from owlready2 import OwlReadyInconsistentOntologyError, OwlReadyJavaError, World, sync_reasoner

ARQUIVO = Path(__file__).with_name("biblioteca.owl")
CONSULTA = """
PREFIX b: <https://example.org/biblioteca#>
SELECT DISTINCT ?livro ?genero ?idioma WHERE {
    ?? b:prefereGenero ?genero .
    ?? b:prefereIdioma ?idioma .
    ?genero b:generoAbordaTema ?tema .
    ?livro b:temGeneroPrincipal ?genero ; b:temIdioma ?idioma ; b:temTema ?tema .
}
"""


def nome(entidade):
    return entidade.label[0] if entidade.label else entidade.name


def entidade(onto, chave, classe):
    item = onto[chave]
    if item is None or not isinstance(item, classe):
        opcoes = ", ".join(sorted(individuo.name for individuo in classe.instances()))
        raise ValueError(f"Opção inválida: {chave}. Escolha entre: {opcoes}.")
    return item


def buscar(mundo, perfil):
    return list(mundo.sparql(CONSULTA, [perfil, perfil]))


def recomendar(onto, perfil, nivel, max_paginas):
    resultados = []
    for livro, genero, idioma in buscar(onto.world, perfil):
        if nivel is not None and livro.temNivel != nivel:
            continue
        if max_paginas is not None and (livro.paginas is None or livro.paginas > max_paginas):
            continue
        resultados.append((livro, genero, idioma))
    return sorted(resultados, key=lambda linha: (linha[0].paginas or 0, linha[0].titulo))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--genero", help="FiccaoCientifica, Fantasia ou Misterio")
    parser.add_argument("--idioma", help="Portugues ou Ingles")
    parser.add_argument("--nivel", help="Iniciante ou Intermediario")
    parser.add_argument("--max-paginas", type=int)
    parser.add_argument("--java", help="Caminho para java.exe, caso não esteja no PATH")
    parser.add_argument("--testar-inconsistencia", action="store_true",
                        help="Classifica Órbita também como Autor e verifica a disjunção")
    args = parser.parse_args()
    if args.max_paginas is not None and args.max_paginas <= 0:
        parser.error("--max-paginas deve ser positivo.")
    if args.java:
        owlready2.JAVA_EXE = args.java

    mundo = World()
    try:
        with ARQUIVO.open("rb") as arquivo:
            onto = mundo.get_ontology("https://example.org/biblioteca#").load(fileobj=arquivo)
        genero = entidade(onto, args.genero or "FiccaoCientifica", onto.Genero)
        idioma = entidade(onto, args.idioma or "Portugues", onto.Idioma)
        nivel = entidade(onto, args.nivel, onto.Nivel) if args.nivel else None
        perfil = onto.Leitor("PerfilConsulta", prefereGenero=[genero], prefereIdioma=[idioma])
        if args.testar_inconsistencia:
            onto.Orbita.is_a.append(onto.Autor)
        classes_antes = set(onto.Orbita.is_a)
        temas_antes = set(onto.Orbita.temTema)
        antes = len(buscar(mundo, perfil))
        sync_reasoner([onto], infer_property_values=True, debug=0)
        if args.testar_inconsistencia:
            parser.exit(1, "Falha: o teste esperava uma ontologia inconsistente.\n")
        resultados = recomendar(onto, perfil, nivel, args.max_paginas)
        classes_novas = set(onto.Orbita.is_a) - classes_antes
        temas_novos = set(onto.Orbita.temTema) - temas_antes
        if onto.LivroFiccaoCientifica not in classes_novas or not temas_novos:
            raise ValueError("O HermiT não produziu as inferências esperadas. "
                             "Confira o Java e use uma pasta TEMP sem chaves ou caracteres especiais.")

        print("HermiT: ontologia consistente.")
        print("Classes inferidas para Órbita: " + ", ".join(sorted(c.name for c in classes_novas)))
        print("Temas inferidos para Órbita: " + ", ".join(sorted(nome(t) for t in temas_novos)))
        print(f"Resultados SPARQL antes da inferência: {antes}.")
        print(f"Preferências: gênero={nome(genero)}, idioma={nome(idioma)}, "
              f"nível={nome(nivel) if nivel else 'qualquer'}, "
              f"máximo de páginas={args.max_paginas or 'sem limite'}.")
        print(f"Recomendações: {len(resultados)}")
        for livro, genero_encontrado, idioma_encontrado in resultados:
            temas = ", ".join(sorted(nome(t) for t in livro.temTema))
            autores = ", ".join(sorted(a.nomeAutor for a in livro.temAutor))
            print(f"- {livro.titulo} ({livro.paginas} páginas) — {autores}")
            print(f"  Motivo: gênero {nome(genero_encontrado)}, idioma {nome(idioma_encontrado)}, "
                  f"nível {nome(livro.temNivel)}. Temas inferidos: {temas}.")
            print(f"  {livro.sinopse}")
    except OwlReadyInconsistentOntologyError:
        if args.testar_inconsistencia:
            print("HermiT detectou a inconsistência esperada: Órbita pertence a Livro e Autor, classes disjuntas.")
        else:
            parser.exit(1, "HermiT detectou uma ontologia inconsistente.\n")
    except (OwlReadyJavaError, OSError, ValueError) as erro:
        parser.exit(1, f"Falha na consulta: {erro}\n")
    finally:
        mundo.close()


if __name__ == "__main__":
    main()
