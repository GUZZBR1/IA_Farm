# Roadmap do IA_Farm

## Fase 1 — Segurança e estabilidade do runtime

- [x] Orquestrador determinístico e calculadora limitada a aritmética de dose já validada.
- [x] Fail-closed sem fonte/contexto aprovado e filtros de região/clima.
- [x] Ingestão Markdown marca os registros como pendentes e ignora autoprovação.
- [x] CI, testes unitários, compilação e varredura de credenciais na árvore atual.
- [x] Smoke de inicialização, demonstração e encerramento em Windows e WSL; o perfil Linux limita CPU/espaço virtual e não simula Android.
- [ ] Definir retenção e consentimento para persistência de conversas antes de beta.
- [ ] Verificar com o mantenedor/provedor se credenciais dos commits antigos foram revogadas; decidir reescrita coordenada do histórico.

## Fase 2 — Evidências de milho e conjunto de avaliação

- [x] Catálogo de candidatos com fontes oficiais e perguntas em rascunho.
- [x] Especialista de Evidências Agronômicas de IA e Verificador independente definidos; não são humanos nem profissionais licenciados.
- [ ] Revisar os 18 casos candidatos contra os documentos oficiais originais, com localizadores, vigência, escopo e ressalvas.
- [ ] Manter sem promoção todo caso divergente, inseguro, desatualizado ou sem evidência suficiente.
- [ ] Confirmar licença antes de redistribuir ou indexar conteúdo protegido.
- [ ] Promover apenas casos com dois pareceres IA independentes rastreáveis; nenhum agrônomo humano é validador obrigatório por enquanto.
- [x] Implementar registro/validador que confira os dois relatórios, hash comum, fonte, escopo e hash exato do conteúdo; o registro está vazio e nenhuma aprovação manual é aceita.
- [ ] Refazer pareceres dos trechos candidatos com hash do texto exato nos dois relatórios; os artefatos atuais não permitem promoção.
- [ ] Executar benchmark de respostas apenas com conjunto aprovado e cobertura mínima acordada; não usar baterias sintéticas como precisão agronômica.

## Fase 3 — RAG e curadoria offline

- [x] Instalar dependências em venv Linux isolado via wheelhouse offline e validar execução real de FAISS/embeddings. O DNS Tailscale segue com falha; instalações online ainda dependem do admin do tailnet.
- [ ] Excluir documentos sintéticos e registros sem proveniência/status/data válidos do índice de usuário.
- [ ] Reconstruir e verificar paridade vetor/metadados para fontes elegíveis.
- [ ] Comparar recuperação lexical e embeddings em consultas anotadas, registrando recall, escopo, citações e latência.

## Fase 4 — Auditoria e decisão de beta restrito

- [ ] Revisar avisos de produto, escopo, fonte/licença, segurança, privacidade, atualização/rollback e comportamento de abstenção.
- [ ] Executar baterias completas e revisar falhas encontradas por auditoria IA; registrar cobertura, lacunas e ações pendentes.
- [ ] Decidir sobre beta restrito com limitações explícitas. Não anunciar certificação, precisão agronômica global ou prontidão de produção sem evidência compatível.

## Fase final — Android físico

Só começar após as fases anteriores. Não inferir desempenho físico de perfis simulados.

- [ ] Preparar build Android e registrar aparelho, versão do sistema e dependências empacotadas.
- [ ] Medir instalação, armazenamento, início offline, RAM, latência, bateria, temperatura e recuperação após pressão de memória.
- [ ] Registrar metodologia e limites aceitáveis; se não houver aparelho disponível, manter Android como pendente.

## Situação atual

As 165 baterias comportamentais (660 execuções) e 58 testes unitários passaram na revalidação de 2026-09-30. Smoke Windows/WSL, compilação, scanner, validador do registro e validação real de FAISS em WSL também passaram. O registro de curadoria segue vazio. Os 18 candidatos anteriores não incluem hash de trecho; 5 divergem em julgamento/escopo. O conjunto-ouro segue vazio e precisão agronômica não foi medida. A validação do RAG foi contornada via wheelhouse offline; DNS Tailscale ainda requer correção administrativa para instalações online. Android físico fica deliberadamente para a etapa final.
