# Status do IA_Farm

| Área | Estado | Evidência / próximo passo |
|---|---|---|
| Runtime | Determinístico, fail-closed | Requer hash exato do trecho no registro de curadoria. Registro atual vazio; status `approved` sozinho não basta. |
| Calculadora | Determinística | Faz aritmética sobre dose já validada; não escolhe dose. |
| RAG / vetores | Validado em WSL isolado | FAISS/Sentence-Transformers reais carregaram 9 vetores (384 dimensões); busca semântica, filtros, escrita/leitura temporária e fail-closed passaram. O índice de produto permanece 0/9 elegível. |
| Memória | Portável | Persistência SQLite existe; política de retenção/consentimento precisa estar definida antes de beta com conversas persistidas. |
| Simulação | Passou no perfil comportamental | 165 baterias × 4 personas = 660/660 execuções passaram. Fixtures sintéticas não validam fatos agronômicos nem hardware. |
| Conjunto-ouro agronômico | Bloqueado para score | 18 candidatos revisados por dois agentes IA: 13 julgamentos iguais, 5 divergências de julgamento/escopo, citações distintas nos relatórios; 0 casos aprovados no conjunto. Não há validador humano obrigatório por enquanto. |
| Segurança | Baseline passou | Scanner não encontrou credenciais ativas na árvore atual. Credenciais citadas no histórico Git ainda exigem verificação/rotação com o mantenedor e provedor. |
| Android | Última etapa, pendente | Nenhum APK ou aparelho físico validado. Não iniciar antes das demais fases de prontidão. |

## Verificações nesta revisão — 2026-09-29

- `python -m unittest discover -s tests -p 'test_*.py'`: 54 testes passaram.
- `python -m compileall -q .`: passou.
- `python -m tools.security_scan`: passou.
- `python tests/run_golden_set.py`: 165 baterias / 660 execuções passaram.
- `python tests/run_low_mid_smoke.py`: passou em Windows (sem envelope de CPU/RAM) e em WSL/Linux (1 CPU lógica e limite de 1536 MiB de espaço virtual).
- O smoke verifica inicialização, demonstração e encerramento da CLI; não valida Android ou ARM64.
- O scorer do conjunto-ouro retorna `not_evaluable` porque o conjunto está vazio. Isso não é falha de precisão nem score zero.
- Precisão agronômica: `not_measured`. Não usar as simulações sintéticas como benchmark de fatos sobre milho.

## Validação real do RAG/FAISS — 2026-09-30

- WSL Python 3.12.3 recebeu os wheels Linux num venv temporário via wheelhouse
  transferida pelo host Windows; instalação offline, sem mexer no Python global.
- Versões validadas: FAISS 1.9.0.post1, NumPy 2.5.3,
  Sentence-Transformers 6.1.0 e PyTorch 2.6.0+cpu; modelo
  `all-MiniLM-L6-v2` carregado do cache local em modo offline.
- `tests/validate_real_vector_db.py`: leu o índice existente (9 vetores × 384),
  recuperou semanticamente o trecho esperado, validou filtros positivos e
  negativos, testou gravação/leitura num índice temporário e confirmou que o
  índice original não mudou. O runtime recusou corretamente todos os trechos
  legados sem aprovação no registro de curadoria.
- DNS WSL continua com `SERVFAIL` no resolvedor Tailscale `100.100.100.100`;
  isso foi contornado pela transferência offline. Não alteramos DNS nem outras
  configurações globais. Instalações online futuras ainda dependem do
  mantenedor/admin do tailnet corrigir esse resolvedor.

## Revalidação do gate de curadoria — 2026-09-30

- 58 testes unitários passaram; compilação, scanner, smoke Windows/WSL e validador
  do registro passaram. Simulação completa: 660/660 execuções.
- `tools.curation_registry` confere integridade de arquivos, hash do conjunto
  congelado, papéis de revisão, acordo por caso e hash do excerto. Registro
  continua vazio; pareceres atuais não têm hash de excerto e cinco casos
  divergem.
- Nenhum caso foi promovido. RAG real, privacidade/retenção, licenças e
  credenciais históricas seguem pendentes. Android continua por último.

## Limites e pendências

- Obter nova revisão de IA ligada ao texto exato para cada trecho candidato; o
  registro/validador já existe, mas nenhum candidato atual atende aos requisitos.
- Avaliar os 18 casos candidatos com fontes oficiais primárias, localizadores, vigência e escopo; divergências entre agentes mantêm o caso pendente.
- Comparar recuperação lexical e embeddings em consultas anotadas, com recall,
  escopo, citações e latência; o índice atual contém apenas material legado não
  elegível e não comprova qualidade de RAG de produção.
- Definir política de retenção de conversas e revisar fontes/licenças antes de qualquer beta restrito.
- Credenciais expostas em commits históricos não são corrigidas pelo scanner da árvore atual. Rotação no provedor e eventual reescrita do histórico precisam de ação coordenada do mantenedor.
- A validação física de Android fica por último e continua não executada.
