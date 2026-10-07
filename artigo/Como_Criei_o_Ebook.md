# Como criei um e-book de dados e atuária com apoio de inteligência artificial

Transformar conceitos técnicos em um material que outras pessoas consigam
acompanhar é um exercício de comunicação e de análise. Para o desafio de
criação de e-books da DIO, escolhi unir ciência de dados, atuária e Python
em um projeto educacional: **Do dado à decisão**.

O objetivo foi construir um guia para iniciantes, com uma pergunta clara,
exemplos numéricos e arquivos que permitissem reproduzir os resultados.
A inteligência artificial apoiou a elaboração do conteúdo e do código,
e o processo ficou documentado nos prompts do repositório.

## Um caso pequeno para aprender os conceitos

O e-book utiliza uma carteira inteiramente fictícia, composta por quatro
segmentos. Cada grupo possui uma exposição em contratos-ano, uma quantidade
de sinistros e um custo total associado às ocorrências.

A partir dessa base, o guia apresenta três indicadores: frequência,
severidade e custo por exposição. As fórmulas aparecem acompanhadas de
suas unidades e de exemplos resolvidos. Uma distinção importante é que
a frequência de sinistros por exposição não corresponde automaticamente
à probabilidade de uma pessoa ter um sinistro.

Um dos exemplos mostra por que a ponderação precisa acompanhar a pergunta
da análise. A média simples dos custos por exposição dos quatro segmentos
é de R$ 196,25. Já o indicador da carteira, calculado pela divisão do custo
total de R$ 512.000 por 3.400 contratos-ano, é de aproximadamente R$ 150,59.
O segundo cálculo considera o tamanho de cada segmento na exposição total.

## Prompts com tarefas específicas

Organizei o processo em cinco etapas: definição do título e da estrutura,
produção do conteúdo, revisão matemática, diagramação e preparação do
artigo e do README.

Em vez de um pedido amplo para gerar um livro, as instruções especificam
o público, a base fictícia, as fórmulas, o formato e os limites das conclusões.
O prompt de revisão, por exemplo, pede a conferência dos totais, das unidades
e da diferença entre análise histórica, previsão e preço comercial de seguro.

Essa documentação ajuda a entender as escolhas do projeto e oferece um
ponto de partida para criar novas versões do material.

## Código e revisão para tornar o projeto reproduzível

O script de análise utiliza somente a biblioteca padrão do Python. Ele
valida os campos da base e calcula os indicadores com aritmética decimal.
Os resultados ficam disponíveis em um arquivo JSON.

A edição em PDF foi produzida com ReportLab. O gráfico usa Matplotlib
e representa os valores calculados a partir da carteira sintética.
A capa utiliza elementos vetoriais originais. Também incluí uma versão
editável do conteúdo em Markdown e os arquivos necessários para gerar
novamente o PDF.

A conferência do projeto abrangeu os cálculos, a execução do código,
a consistência entre arquivos e a inspeção das páginas renderizadas.
Como a base possui apenas quatro registros agregados, o projeto trabalha
com análise descritiva. Não apresenta um modelo preditivo treinado nem
conclusões sobre uma carteira real.

## O que este projeto demonstra

O resultado reúne conteúdo, dados, código e documentação em uma mesma
entrega. Além de explorar prompts, o projeto permite exercitar a explicação
de conceitos quantitativos, a organização de uma análise e a comunicação
de seus limites.

Meu próximo passo de evolução seria ampliar o caso com dados sintéticos
por contrato e por período, mantendo as definições documentadas. Isso
permitiria estudar novas perguntas e estratégias de avaliação, sem
confundir uma primeira análise com uma solução pronta de precificação.

O projeto foi inspirado no
[repositório de referência de Felipe Aguiar](https://github.com/felipeAguiarCode/prompts-recipe-to-create-a-ebook),
fornecido no desafio da DIO.

[Leia o e-book em PDF](../output/Do_Dado_a_Decisao.pdf) e
[consulte os prompts completos](../prompts/).

**Projeto de Paulo Bernardo, desenvolvido com apoio de inteligência artificial.**
