#!/usr/bin/env python3
"""Calcula indicadores descritivos da carteira sintética do e-book.

Requer somente Python 3.10+ e sua biblioteca padrão.
Executar: python scripts/analisar_carteira.py
"""

from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def numero(value, field):
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f'{field}: valor numérico inválido.') from exc
    if not parsed.is_finite():
        raise ValueError(f'{field}: valor deve ser finito.')
    return parsed


def validar(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('A base deve ser uma lista não vazia.')
    clean, seen = [], set()
    required = {'segmento', 'exposicao_contratos_ano', 'sinistros', 'custo_total'}
    for row in rows:
        if not isinstance(row, dict) or not required.issubset(row):
            raise ValueError('Registro sem todos os campos obrigatórios.')
        if not isinstance(row['segmento'], str):
            raise ValueError('Segmento deve ser um texto.')
        label = row['segmento'].strip().upper()
        if not label or label in seen:
            raise ValueError('Segmento vazio ou duplicado.')
        seen.add(label)
        exposure = numero(row['exposicao_contratos_ano'], 'Exposição')
        cost = numero(row['custo_total'], 'Custo')
        claims = row['sinistros']
        if exposure <= 0 or cost < 0:
            raise ValueError('Exposição deve ser positiva e custo não negativo.')
        if type(claims) is not int or claims < 0:
            raise ValueError('Sinistros devem ser um inteiro não negativo.')
        if claims == 0 and cost != 0:
            raise ValueError('Neste exemplo, custo positivo requer sinistros.')
        clean.append({'segmento': label, 'exposicao': exposure,
                      'sinistros': claims, 'custo': cost})
    return clean


def indicadores(exposure, claims, cost):
    return {
        'exposicao_contratos_ano': f'{exposure:f}',
        'sinistros': claims,
        'custo_total': f'{cost:.2f}',
        'frequencia': f'{Decimal(claims) / exposure:.8f}',
        'severidade': f'{cost / Decimal(claims):.2f}' if claims else None,
        'custo_por_exposicao': f'{cost / exposure:.2f}'
    }


def analisar(rows):
    rows = validar(rows)
    per_segment = [dict(segmento=row['segmento'], **indicadores(
        row['exposicao'], row['sinistros'], row['custo'])) for row in rows]
    total_exposure = sum((r['exposicao'] for r in rows), Decimal(0))
    total_claims = sum(r['sinistros'] for r in rows)
    total_cost = sum((r['custo'] for r in rows), Decimal(0))
    simple_mean = sum((r['custo'] / r['exposicao'] for r in rows),
                      Decimal(0)) / Decimal(len(rows))
    return {
        'natureza_dados': 'Sintéticos, com período comum e custos em reais.',
        'por_segmento': per_segment,
        'carteira': indicadores(total_exposure, total_claims, total_cost),
        'media_simples_segmentos': f'{simple_mean:.2f}'
    }


def main():
    data_path = ROOT / 'dados/carteira_sintetica.json'
    results = analisar(json.loads(data_path.read_text(encoding='utf-8')))
    output = ROOT / 'output'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'analise_resultados.json').write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
