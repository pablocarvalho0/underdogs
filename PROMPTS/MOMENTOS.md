# Momentos de uso da IA

Quatro momentos em que a direção humana mudou o resultado. Dois são erros da IA (1 e 4).

---

### Momento 1: a IA leu os valores da planilha e ignorou o comentário e o tachado (erro da IA)
- **O que pedimos:** o perfil da planilha de taxas, para montar o cadastro de lojistas.
- **O que a IA devolveu:** só os valores das células. Ficaram de fora o comentário da Bia na Casa do Estudante ("conversar com Diego (comercial) sobre condição especial") e a linha tachada da Globo Trotter, e a Casa foi tratada como lojista comum.
- **O que fizemos com isso:** voltamos ao arquivo lendo comentários, formatação e linhas ocultas, e a Helena confirmou a isenção de set a dez (R-08). Isso virou a pendência de devolução de R$ 15.396,77 ao lojista, que é o que a Orbe cobrou durante a isenção.

### Momento 2: o mapeamento dos ECs pela "impressão digital" das taxas ficou como hipótese até a resposta
- **O que pedimos:** descobrir de quem são os 3 ECs da Orbe que não estão na planilha.
- **O que a IA devolveu:** um mapeamento pelo conjunto de taxas cobradas em cada EC: Kiwi, Novo Horizonte e Horizonte Viagens.
- **O que fizemos com isso:** não usamos como fato. A pergunta já estava no canal compartilhado, feita por outro time (Fox AI, [T4] no `HIPOTESES.md`); esperamos a resposta, a Helena confirmou os três (R-05), e o alias ficou como dado com fonte e aprovador. Assim, um EC novo em outubro vira pendência de cadastro em vez de ser adivinhado.

### Momento 3: não confiar no que já estava escrito (direção humana)
- **O que pedimos:** reler os dados e o canal inteiro sem confiar a priori no repositório, separando o que o financeiro disse do que um time propôs.
- **O que a IA devolveu:** erros no nosso plano (o Aurora tem 84 lançamentos, não 80; a divergência da Rota começa em 12/09) e regras registradas que, pelo texto, eram propostas de outro time. Duas leituras paralelas do mesmo canal divergiram entre si.
- **O que fizemos com isso:** conferimos no Slack cada thread em que as leituras divergiam, em vez de escolher uma versão. Reescrevemos o `HIPOTESES.md` em três níveis: fato medido, regra do financeiro (com link) e premissa nossa.

### Momento 4: conferência dos números e um diagnóstico errado da IA (erro da IA)
- **O que pedimos:** uma régua independente antes de confiar em qualquer saída: uma prévia própria das regras e, no fim, uma segunda implementação das 3 trilhas para comparar com a da `main`.
- **O que a IA devolveu:** os mesmos valores nas duas implementações e na prévia, em todas as saídas. Antes disso, a IA arredondou só a soma da remessa (R$ 39.542,88 em vez de R$ 39.543,45) e escreveu no plano que a Rota era cobrada pela "tabela 2025".
- **O que fizemos com isso:** o arredondamento por linha veio da Helena (R-02) e virou regra de contrato do rastro. O diagnóstico da Rota foi conferido na planilha e corrigido: na verdade, é +0,50 p.p. no crédito desde 12/09. A suíte caixa-preta, que falha em um valor nas duas implementações, ficou para triagem humana, e não a IA ajustando o código até passar.
