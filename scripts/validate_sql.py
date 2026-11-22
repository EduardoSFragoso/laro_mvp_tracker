"""Validação estática do SQL do yellowtracker usando sqlglot (dialeto PostgreSQL).

Verifica:
- Sintaxe de todo o SQL (schema + seed);
- Contagens do seed (64 MVPs, aliases);
- Ordem dos currval (todo mvp_alias deve vir imediatamente após um INSERT em mvp);
- t1 <= t2, id_mob presente ou NULL.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import sqlglot
from sqlglot import expressions as exp


ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f'  OK {msg}')
    else:
        failures.append(msg)
        print(f'  FALHA {msg}')


def lit(e) -> str | None:
    if isinstance(e, exp.Null):
        return None
    if isinstance(e, (exp.Literal, exp.Neg)):
        return e.this if hasattr(e, 'this') else e.sql(dialect='postgres')
    return e.sql(dialect='postgres')


def main() -> int:
    for sql_file in ('sql/yellowtracker.sql', 'sql/seed_mvp_latam.sql'):
        text = (ROOT / sql_file).read_text(encoding='utf-8')
        try:
            stmts = [s for s in sqlglot.parse(text, read='postgres') if s is not None]
        except sqlglot.errors.ParseError as exc:
            print(f'FALHA: erro de sintaxe em {sql_file}: {exc}')
            return 1
        print(f'OK sintaxe: {sql_file} ({len(stmts)} statements)')

    seed = (ROOT / 'sql/seed_mvp_latam.sql').read_text(encoding='utf-8')
    stmts = [s for s in sqlglot.parse(seed, read='postgres') if s is not None]

    counts: Counter[str] = Counter()
    inserted_tables: list[str | None] = []
    mvps = 0
    for ins in [s for s in stmts if isinstance(s, exp.Insert)]:
        table = ins.this.this.name  # type: ignore[index]
        vals = ins.args.get('values_') or ins.args.get('expression')
        n_rows = len(list(vals.find_all(exp.Tuple)))
        counts[table] += n_rows
        inserted_tables.append(table)
        if table == 'mvp':
            mvps += 1
            row = list(vals.find_all(exp.Tuple))[0].expressions
            name, map_, t1, t2, id_mob = [lit(e) for e in row]
            if t1 is None or t2 is None:
                failures.append(f'mvp sem respawn: {name}')
            elif int(t1) > int(t2):
                failures.append(f't1>t2: {name}')
            if id_mob is not None and not id_mob.isdigit():
                failures.append(f'id_mob inválido: {name} -> {id_mob}')

    print(f'seed: {dict(counts)}')
    check(counts.get('mvp') == 64, f'64 MVPs (obtido {counts.get("mvp")})')
    # o seed de upgrade não recria a lista de mineração (só schema completo tinha)
    check(counts.get('mining') in (0, None), f'seed sem mining (obtido {counts.get("mining")})')
    aliases = counts.get('mvp_alias', 0)
    check(aliases <= 66, f'aliases <= 66 (obtido {aliases})')

    # mvp_alias deve seguir (direta ou indiretamente) um bloco que começou com INSERT em mvp
    in_block = False
    bad = 0
    for t in inserted_tables:
        if t == 'mvp':
            in_block = True
        elif t == 'mvp_alias':
            if not in_block:
                bad += 1
        else:
            in_block = False
    check(bad == 0, f'mvp_alias sempre em bloco após INSERT em mvp (erros: {bad})')

    full = (ROOT / 'sql/yellowtracker.sql').read_text(encoding='utf-8')
    stmts_full = [s for s in sqlglot.parse(full, read='postgres') if s is not None]
    tables_full = Counter(s.this.this.name for s in stmts_full if isinstance(s, exp.Insert))  # type: ignore[index,union-attr]
    print(f'yellowtracker.sql inserts: {dict(tables_full)}')
    check(tables_full.get('mvp') == 64, f'schema+seed: 64 MVPs (obtido {tables_full.get("mvp")})')
    check(tables_full.get('mining') in (0, None), f'schema sem mining (obtido {tables_full.get("mining")})')

    if failures:
        print(f'\n{len(failures)} problema(s): ' + '; '.join(failures))
        return 1
    print('\nSQL validado com sucesso.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
