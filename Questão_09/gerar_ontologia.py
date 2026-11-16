"""Gera o arquivo OWL 2 do catálogo fictício em RDF/XML."""

from pathlib import Path
from types import new_class

from owlready2 import AllDisjoint, AllDifferent, FunctionalProperty, PropertyChain, Thing, World

ARQUIVO = Path(__file__).with_name("biblioteca.owl")
IRI = "https://example.org/biblioteca#"


def gerar():
    mundo = World()
    onto = mundo.get_ontology(IRI)
    with onto:
        class Livro(Thing): pass
        class Romance(Livro): pass
        class Coletanea(Livro): pass
        class LivroFiccaoCientifica(Livro): pass
        class LeituraIntrodutoria(Livro): pass
        class Leitor(Thing): pass
        class Autor(Thing): pass
        class Genero(Thing): pass
        class Tema(Thing): pass
        class Idioma(Thing): pass
        class Nivel(Thing): pass
        class Editora(Thing): pass

        class temGenero(Livro >> Genero): pass
        class temGeneroPrincipal(temGenero, FunctionalProperty): pass
        class temAutor(Livro >> Autor): pass
        class escreveu(Autor >> Livro): pass
        escreveu.inverse_property = temAutor
        class temTema(Livro >> Tema): pass
        class generoAbordaTema(Genero >> Tema): pass
        temTema.property_chain = [PropertyChain([temGeneroPrincipal, generoAbordaTema])]
        class temIdioma(Livro >> Idioma, FunctionalProperty): pass
        class temNivel(Livro >> Nivel, FunctionalProperty): pass
        class publicadoPor(Livro >> Editora): pass
        class prefereGenero(Leitor >> Genero): pass
        class prefereIdioma(Leitor >> Idioma): pass

        for nome, tipo in (("titulo", str), ("codigoCatalogo", str), ("sinopse", str),
                           ("paginas", int), ("anoPublicacao", int)):
            new_class(nome, (Livro >> tipo, FunctionalProperty))
        class nomeAutor(Autor >> str, FunctionalProperty): pass

        AllDisjoint([Livro, Leitor, Autor, Genero, Tema, Idioma, Nivel, Editora])
        AllDisjoint([Romance, Coletanea])
        ficcao = Genero("FiccaoCientifica", label=["Ficção científica"])
        fantasia = Genero("Fantasia", label=["Fantasia"])
        misterio = Genero("Misterio", label=["Mistério"])
        pt = Idioma("Portugues", label=["Português"])
        en = Idioma("Ingles", label=["Inglês"])
        inicial = Nivel("Iniciante", label=["Iniciante"])
        intermediario = Nivel("Intermediario", label=["Intermediário"])
        AllDifferent([ficcao, fantasia, misterio])
        AllDifferent([pt, en])
        AllDifferent([inicial, intermediario])

        LivroFiccaoCientifica.equivalent_to = [Livro & temGenero.value(ficcao)]
        LeituraIntrodutoria.equivalent_to = [Livro & temNivel.value(inicial)]
        Livro.is_a.extend([temGeneroPrincipal.some(Genero), temIdioma.some(Idioma),
                           temNivel.some(Nivel)])

        ficcao.generoAbordaTema = [Tema("Tecnologia", label=["Tecnologia"])]
        fantasia.generoAbordaTema = [Tema("Magia", label=["Magia"])]
        misterio.generoAbordaTema = [Tema("Investigacao", label=["Investigação"])]
        horizonte = Editora("Horizonte", label=["Horizonte"])
        autores = [
            Autor("LiaCosta", nomeAutor="Lia Costa"),
            Autor("RuiAlves", nomeAutor="Rui Alves"),
            Autor("IaraDias", nomeAutor="Iara Dias"),
        ]
        registros = [
            ("Orbita", Romance, "Órbita", ficcao, pt, inicial, autores[0], 164, 2021,
             "Uma tripulação recebe sinais de uma estação abandonada."),
            ("CidadeDeSilicio", Romance, "Cidade de Silício", ficcao, pt, intermediario, autores[0], 242, 2023,
             "Uma pesquisadora investiga a origem de uma cidade automatizada."),
            ("StarArchive", Coletanea, "Star Archive", ficcao, en, inicial, autores[1], 128, 2022,
             "Contos sobre arquivos perdidos em viagens espaciais."),
            ("BosqueDeVidro", Romance, "Bosque de Vidro", fantasia, pt, inicial, autores[2], 176, 2020,
             "Uma aprendiz descobre um bosque que muda de forma."),
            ("MapaDasBrumas", Coletanea, "Mapa das Brumas", fantasia, pt, intermediario, autores[2], 201, 2024,
             "Contos sobre mapas encantados e territórios desconhecidos."),
            ("CartaSemSelo", Romance, "Carta sem Selo", misterio, pt, inicial, autores[1], 132, 2024,
             "Uma carta anônima leva a uma investigação em uma pequena cidade."),
        ]
        for numero, registro in enumerate(registros, 1):
            chave, classe, titulo, genero, idioma, nivel, autor, paginas, ano, sinopse = registro
            classe(chave, titulo=titulo, codigoCatalogo=f"L{numero:02d}", sinopse=sinopse,
                   paginas=paginas, anoPublicacao=ano, temGeneroPrincipal=genero,
                   temIdioma=idioma, temNivel=nivel, temAutor=[autor], publicadoPor=[horizonte])
        Leitor("Ana", prefereGenero=[ficcao], prefereIdioma=[pt], label=["Ana"])

    onto.save(file=str(ARQUIVO), format="rdfxml")
    return ARQUIVO


if __name__ == "__main__":
    print(gerar())
