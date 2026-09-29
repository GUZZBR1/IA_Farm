# Conceito e visão — AgriBrain

O AgriBrain é um assistente agrícola offline-first para apoiar o produtor com
informação técnica local, rastreável e revisada. Na execução do aplicativo não
há LLM generativo: regras determinísticas conduzem a conversa e a busca local
recupera referências; a interface exibe o trecho original, sem inventar uma
recomendação.

## Filosofia de projeto

### Determinismo e segurança

- Região, clima e demais campos são extraídos por regras explícitas; o sistema
  pede esclarecimentos quando falta contexto.
- Dados só são exibidos quando possuem texto, fonte, estado de aprovação e data
  de revisão válida.
- A calculadora faz aritmética sobre uma dose que já foi validada. Ela não
  escolhe produtos nem determina uma dose agronômica.

### Conhecimento estruturado

Manuais e tabelas devem ser convertidos para dados estruturados durante a
curadoria, com proveniência e revisão por profissional qualificado antes de
serem disponibilizados. A busca pode usar embeddings locais, que servem apenas
para localizar documentos e não geram respostas.

### Execução em celular

O objetivo é funcionar offline em aparelhos modestos, mas Android ainda não foi
validado. Quantização, `mmap`, cache e consumo de bateria só podem ser afirmados
depois de implementados e medidos no aparelho-alvo. Veja
`docs/mobile_optimization.md`.

## Pilares técnicos

- Fontes agronômicas estruturadas e versionadas.
- Extração explícita de contexto e perguntas de esclarecimento.
- Resposta por trechos locais revisados, sem geração de texto.
- Testes red-team determinísticos com agricultor incrédulo, profissional e
  usuário casual.
