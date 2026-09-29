# Avaliação de SLM local para IA_Farm

**Status: proposta de avaliação; não é uma decisão de integração.** O runtime
atual continua determinístico e não usa um modelo generativo. Esta nota registra
a análise de viabilidade para uma possível etapa futura, após validação do
produto e definição do aparelho Android-alvo.

## Conclusão

Para o escopo atual — assistência em cultivo de milho em celulares com recursos
limitados — vale avaliar um modelo de linguagem pequeno (SLM) pré-treinado,
executado localmente, combinado com uma base de conhecimento curada e busca
local. Não há justificativa atual para treinar um modelo do zero. Também não se
recomenda começar por fine-tuning: primeiro devem ser medidos os resultados com
recuperação de fontes e regras determinísticas.

O modelo pode ajudar a compreender perguntas em português, identificar intenção
e redigir explicações apoiadas nos trechos recuperados. Ele não deve inventar
fatos agronômicos, calcular doses nem substituir rótulos, registros oficiais ou
revisão profissional. Quando a fonte ou o contexto forem insuficientes, o
aplicativo deve pedir dados ou não emitir recomendação.

## O que o histórico do repositório comprova

- Phi-3 Mini aparece em planos antigos de integração local/Android, incluindo
  uma proposta de quantização. Isso comprova que foi considerado, mas não que
  seus pesos tenham sido baixados nesta máquina, integrados ao aplicativo ou
  validados em um telefone.
- O histórico contém evidência de `sentence-transformers/all-MiniLM-L6-v2`
  para embeddings e recuperação semântica. Esse modelo auxilia a busca; não é o
  gerador de respostas.
- O caminho de resposta atual é determinístico. A política vigente e os testes
  existentes não validam qualidade de geração por um SLM nem desempenho móvel.

Pesos de modelos podem ser distribuídos fora do Git, por exemplo por um
repositório de modelos ou artefatos de release, com versão e hash fixados. Não
se deve presumir que ignorar pesos no Git ou baixá-los localmente demonstre uma
integração funcional.

## Candidatos para comparação

1. **Phi-3 Mini quantizado** — candidato histórico que deve ser reproduzido se
   o formato/runtime Android ainda forem compatíveis. O relatório técnico
   descreve o Phi-3 Mini como um modelo de 3,8 bilhões de parâmetros e discute
   execução em telefone. Isso não garante desempenho ou memória suficientes em
   todo aparelho de 4 GB. [Relatório técnico do Phi-3](https://arxiv.org/abs/2404.14219)
2. **Gemma 4 E2B Mobile, texto** — candidato atual para benchmark. O Google
   estima aproximadamente 0,84 GB de memória de inferência para essa variante.
   A própria documentação ressalva que o consumo depende do ambiente; a cifra
   não deve ser interpretada como orçamento total do app e do Android.
   [Visão geral e estimativas do Gemma 4](https://ai.google.dev/gemma/docs/core)
3. **Um SLM de aproximadamente 1B parâmetro** — controle menor para comparar
   memória, latência e qualidade em português. O modelo e runtime concretos
   devem ser fixados antes da bateria para tornar o resultado reproduzível.

Esta lista é uma shortlist, não uma declaração de que qualquer candidato já
foi selecionado ou funciona no aparelho-alvo. Devem ser confirmados formato dos
pesos, runtime Android compatível, licença/termos de distribuição, suporte a
português e requisitos de memória do contexto.

## Separação de responsabilidades

- **SLM local (opcional/futuro):** compreensão da pergunta e explicação em
  português, sempre condicionado ao conteúdo recuperado.
- **Base local de conhecimento:** afirmações e trechos sobre milho com fonte,
  data, região, safra, contexto, unidade, licença e estado de revisão.
- **Código determinístico:** validação de contexto, filtros, cálculos
  explicitamente aprovados, regras de segurança, estrutura da resposta e
  recusa quando não houver suporte suficiente.
- **Revisão agronômica:** aprovação de conteúdo e casos de referência de risco;
  nenhuma resposta gerada é validação técnica por si só.

RAG mantém os documentos separados dos pesos do modelo e facilita atualizar e
auditar o conhecimento. Ainda assim, RAG não garante que a busca recupere a
fonte correta ou que o modelo a interprete corretamente; isso precisa ser
testado. [Paper original de RAG](https://arxiv.org/abs/2005.11401)

## Plano de avaliação antes de integrar

1. Definir telefone Android de referência, versão do sistema, chipset e
   orçamento máximo de memória para o processo; se o aparelho não estiver
   definido, declarar o perfil de 4 GB como hipótese, não como compatibilidade
   comprovada.
2. Fixar artefato, quantização, tokenizer, runtime, parâmetros de geração e
   hash de cada candidato. Não versionar pesos grandes no repositório de código.
3. Comparar os mesmos casos para as três personas já usadas no simulador —
   incrédulo, profissional e casual — e acrescentar casos agronômicos reais
   apenas quando suas respostas de referência tiverem fonte e revisão técnica.
4. Medir compreensão de português, extração de contexto, qualidade e
   fidelidade às citações, recuperação, abstenção correta, resistência a
   prompt injection, latência, pico de RAM, estabilidade térmica e funcionamento
   sem rede.
5. Para cada falha, classificar a causa: dado ausente/desatualizado, contexto
   insuficiente, extração ou recuperação incorreta, regra de segurança,
   interpretação/linguagem do modelo, incompatibilidade de runtime ou limite do
   aparelho. Corrigir a camada responsável e manter o caso como regressão.
6. Só considerar integração após os critérios de qualidade, segurança e
   desempenho serem acordados e aprovados. Manter doses e decisões de uso
   fitossanitário fora da geração livre.

As 130 baterias sintéticas existentes verificam contratos de comportamento do
runtime determinístico; elas não demonstram precisão agronômica, qualidade de
um SLM ou compatibilidade Android. Devem continuar sendo executadas como
regressão, separadas da avaliação de modelo e do conjunto agronômico revisado.
