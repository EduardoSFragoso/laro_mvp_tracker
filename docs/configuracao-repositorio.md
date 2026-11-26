# Configuração do repositório: PRs, commits e segurança

Checklist para **quem administra o repositório** (EduardoSFragoso/laro_mvp_tracker, público, plano gratuito). Estas configurações ficam no GitHub e **o agente não as altera**: ele propõe e a pessoa aplica. É referenciado pelo `AGENTS.md`.

Cada seção traz o **estado atual** — verificado em 2026-11-23 via `gh api` (comandos na seção 5). Os nomes de menus mudam com o tempo; se um caminho não existir, procure o nome da opção em **Settings**.

## 1. Ruleset da branch principal

Em **Settings → Rules → Rulesets → `protege-main`** (ativas em repositórios públicos no plano gratuito).

| Regra | Estado atual | Recomendação | Por quê |
|---|---|---|---|
| Restrict deletions | ✅ ligada | manter | Impede apagar a `main` |
| Block force pushes | ✅ ligada | manter | Impede reescrever o histórico publicado |
| Require linear history | ✅ ligada | manter | Exige rebase no merge; histórico linear e fácil de reverter |
| Require a pull request before merging | ✅ ligada | manter | Nada entra sem PR |
| ↳ aprovações exigidas | 0 | manter (projeto de uma pessoa) | Quem abre o PR não aprova o próprio; exigir 1 com um só mantenedor trava o fluxo |
| ↳ métodos de merge | Rebase only (outros desligados via repo settings) | manter | O método da casa; sem risco do merge errado |
| ↳ Require status checks | ✅ `checks (3.13)/(3.14)/(3.15)`, `types`, `audit` | manter — **toda check nova da CI entra aqui antes do primeiro merge** | A CI é o portão do merge (lição da PR #13: o `types` pegou defeito na PR que o instalou) |
| Require code scanning results | desligada | avaliar se exigir os resultados do CodeQL, que já está ativo | Faz os resultados do code scanning participarem do bloqueio de merge |
| Require signed commits | desligada | avaliar; **testar em PR descartável antes** | Docs do GitHub: commits sem assinatura na branch da PR podem bloquear o merge, e o caso do Rebase and merge não é detalhado |
| Bypass list | vazio | manter vazio | Emergência não deve ter atalho |

**Limite do plano:** regras "Restrict file paths/extensions/size" são push rulesets de plano pago. No gratuito, o bloqueio de `.env`/`.pem`/dumps é feito por `.gitignore`, secret scanning com push protection e detector local de segredos (seção 2).

## 2. Segurança dos commits

### Segredos

| Recurso | Estado atual |
|---|---|
| Secret scanning | ✅ enabled |
| Push protection | ✅ enabled |

- O detector do GitHub recusa o push que carregar um segredo conhecido. Complemento local opcional: hook de pre-commit com `gitleaks`.
- Se um segredo entrar mesmo assim: **rotacione primeiro** (token do bot no Developer Portal, senha do Postgres na VM). Apagar do código não basta, porque o histórico guarda o valor. Reescrever o histórico é opcional e vem depois.

### Assinatura de commits

Recomendada, mas **a exigência tem armadilhas**. Para assinar com chave SSH:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

Depois adicione a mesma chave pública em **Settings → SSH and GPG keys** como *Signing Key*. Antes de ligar **Require signed commits** na ruleset, teste num PR descartável: a documentação do GitHub cita bloqueio de merge por commits sem assinatura na branch da PR e não detalha o caso do **Rebase and merge** — que é exatamente o fluxo da casa.

## 3. Segurança do repositório e das Actions

| Item | Estado atual | Onde |
|---|---|---|
| Dependabot alerts + security updates | ✅ enabled | Settings → Code security |
| Code scanning (CodeQL) | ✅ ativo | checks `Analyze` (Python/Actions) e `CodeQL` observados no PR #24 em 2026-11-25; configuração gerenciada pelo GitHub | manter e triar alerts; workflow não é versionado neste repo |
| Private vulnerability reporting | ✅ enabled | confirmado pelo mantenedor em 2026-11-25; Settings → Code security | manter ativo para receber relatos em canal privado |
| Workflow permissions | `contents: read` declarado no workflow | manter; cada workflow declara o que precisa |
| PRs por workflows (GITHUB_TOKEN) | n/a | autorizar manualmente se um dia um workflow abrir PR |

- Pull requests abertas por workflows (autor `github-actions[bot]`) ficam em *Action required* e só rodam a CI após **Approve workflows to run** — vale saber antes de automatizar merges do Dependabot.

## 4. Arquivos de apoio no repositório

| Arquivo | Estado |
|---|---|
| `.github/dependabot.yml` | ✅ pip (`/` e `/src`) + github-actions + docker, semanal — o exemplo deste arquivo é a própria config real do repo |
| `.github/pull_request_template.md` | ✅ existe: "O que mudou e por quê / Como foi testado / Riscos e como reverter" |
| `.gitignore` | ✅ cobre `.env`, `.env.*`, `*.pem`, `*.key`, `.venv/`, `__pycache__/` |
| `SECURITY.md` | ✅ orienta reporte privado; o estado da configuração deve ser confirmado no GitHub |
| `CODEOWNERS` | não aplicável (revisor único) |

## 5. Como mostrar a configuração a uma IA, sem prints

Estes comandos só **leem** a configuração (precisam do GitHub CLI, `gh`) e não expõem segredos:

```bash
gh api repos/EduardoSFragoso/laro_mvp_tracker/rulesets --jq '.[] | {id, name, enforcement, target}'
gh api repos/EduardoSFragoso/laro_mvp_tracker/rulesets/ID_DA_RULESET
gh api repos/EduardoSFragoso/laro_mvp_tracker --jq '{private, default_branch, allow_rebase_merge, allow_squash_merge, allow_merge_commit, delete_branch_on_merge}'
```

A IA compara o resultado com este checklist e aponta o que falta. Auditoria de infra da VM e do banco: `docs/auditoria-infra.md`.
