# Momentos de uso da IA

Cinco momentos em que a direção humana mudou o resultado. Dois são erros da IA (1 e 4).

---

### Momento 1: a IA leu os valores da planilha e ignorou o comentário e o tachado (erro da IA)
- **O que pedimos:** o perfil da planilha de taxas, para montar o cadastro de lojistas.
- **O que a IA devolveu:** só os valores das células. Ficaram de fora o comentário da Bia na Casa do Estudante ("conversar com Diego (comercial) sobre condição especial") e a linha tachada da Globo Trotter, e a Casa foi tratada como lojista comum.
- **O que fizemos com isso:** voltamos ao arquivo lendo comentários, formatação e linhas ocultas, e a Helena confirmou a isenção de set a dez (R-08). Isso virou a pendência de devolução de R$ 15.396,77 ao lojista, que é o que a Orbe cobrou durante a isenção.

### Momento 2: o mapeamento dos ECs pela "impressão digital" das taxas ficou como hipótese até a resposta
- **O que pedimos:** descobrir de quem são os 3 ECs da Orbe que não estão na planilha.
- **O que a IA devolveu:** um mapeamento pelo conjunto de taxas cobradas em cada EC: Kiwi, Novo Horizonte e Horizonte Viagens.
- **O que fizemos com isso:** não usamos como fato. Perguntamos no canal, a Helena confirmou os três (R-05), e o alias ficou como dado com fonte e aprovador. Assim, um EC novo em outubro vira pendência de cadastro em vez de ser adivinhado.

### Momento 3: não confiar no que já estava escrito (direção humana)
- **O que pedimos:** reler os dados e o canal inteiro sem confiar a priori no repositório, separando o que o financeiro disse do que um time propôs.
- **O que a IA devolveu:** erros no nosso plano (o Aurora tem 84 lançamentos, não 80; a divergência da Rota começa em 12/09) e regras registradas que, pelo texto, eram propostas de outro time. Duas leituras paralelas do mesmo canal divergiram entre si.
- **O que fizemos com isso:** conferimos no Slack cada thread em que as leituras divergiam, em vez de escolher uma versão. Reescrevemos o `HIPOTESES.md` em três níveis: fato medido, regra do financeiro (com link) e premissa nossa.

### Momento 4: conferência dos números e um diagnóstico errado da IA (erro da IA)
- **O que pedimos:** uma régua independente antes de confiar em qualquer saída: uma prévia própria das regras e, no fim, uma segunda implementação das 3 trilhas para comparar com a da `main`.
- **O que a IA devolveu:** os mesmos valores nas duas implementações e na prévia, em todas as saídas. Antes disso, a IA arredondou só a soma da remessa (R$ 39.542,88 em vez de R$ 39.543,45) e escreveu no plano que a Rota era cobrada pela "tabela 2025".
- **O que fizemos com isso:** o arredondamento por linha veio da Helena (R-02) e virou regra de contrato do rastro. O diagnóstico da Rota foi conferido na planilha e corrigido: na verdade, é +0,50 p.p. no crédito desde 12/09. A suíte caixa-preta, que falha em um valor nas duas implementações, ficou para triagem humana, e não a IA ajustando o código até passar.

### Momento 5: o gabarito caixa-preta estava desatualizado, não o código (direção humana)
- **O que pedimos:** entender por que `npm test` falhava, com liberação explícita para ler o teste e as fixtures (a diretiva 0 do `CLAUDE.md` proíbe isso por padrão).
- **O que a IA devolveu:** o gabarito foi escrito às 09h16 de 17/10, antes das respostas do financeiro (13h25), e trazia premissas da manhã. Comparando todas as saídas, e não só a primeira asserção, apareceram cinco diferenças. Comissão do Beta pela taxa aplicada (53,80), quando a R-01 manda pela contratada (43,80); o próprio gabarito listava os R$ 10,00 de excesso como divergência a contestar, ou seja, cobrava e contestava o mesmo dinheiro. Divergência de spread da remessa PC-BB-001 ausente (1,50% contratado contra 2,00% realizado, R$ 49,00, R-23). Tarifa bancária na conta `4.1.02.001`, que não existe no plano de contas da fixture (`4.2.01` é "Tarifas bancárias"). Pix do lojista para remessa lançado contra a própria conta Meridiano (`1.1.01.002`), quando é recurso de lojista a remeter (`2.1.02.001`). E uma só pendência com decisor "Financeiro Tarvo", quando as regras R-14, R-22/R-25 e R-23 geram quatro, decididas pela Helena.
- **O que fizemos com isso:** a mudança de regra foi real, então o gabarito foi regravado a partir das regras, com o mínimo de mudança: mesmos IDs e mesmo formato, só os valores afetados. A IA não ajustou o código até passar: o código já seguia as regras. Duas mudanças no teste e no código. O teste agora casa a pendência por `ref_origem` e `tipo`, porque uma operação pode ter contestação e acompanhamento de repasse ao mesmo tempo. E o `Spread R$` passou a ser arredondado ao centavo na leitura, porque saía `-50` em vez de `-50.00`; setembro real não mudou. A mesma investigação achou um bug nosso na prévia independente: ela escolhia o extrato Aurora pelo primeiro CSV com "aurora" no começo, e o plano de contas também tem "Banco Aurora". Dependia da ordem do sistema de arquivos e quebrava nesta máquina.
- **A percepção que fica:** um teste "imutável" protege contra a IA afrouxar asserção para passar, mas congela também as premissas de quando foi escrito. Quando o cliente muda a regra, o gabarito precisa mudar junto, por decisão humana registrada e não pela IA sozinha. Teste vermelho contra regra nova é sinal para triagem, não para adaptar o código.
