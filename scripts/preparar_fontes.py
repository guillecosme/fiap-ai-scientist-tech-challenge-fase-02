"""Prepara as fontes da pipeline em escala nacional.

Territorio (UF e municipio) vem da API publica do IBGE, sem login e sem custo.
Metas e dados de alunos sao simulados de forma deterministica no mesmo grao e
esquema das fontes reais, ja que o microdado do Indicador Crianca Alfabetizada so
sai pela Base dos Dados (BigQuery, que exige projeto de billing). O resultado
substitui as amostras pequenas por um extrato do Brasil inteiro, que e o que a
ingestao batch leria da fonte.

Uso:
    python scripts/preparar_fontes.py --out data/seeds

Reprodutivel: mesma seed, mesmo resultado. So o territorio depende da rede.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import random
import urllib.request

IBGE_ESTADOS = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
IBGE_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

ANOS = (2024, 2025)
META_BRASIL = {2023: 54.0, 2024: 60.0, 2025: 64.0}

# Base de alfabetizacao por regiao (%), o que gera a desigualdade territorial real
# do indicador. Valores plausiveis, nao oficiais.
BASE_REGIAO = {
    "Norte": 57.0,
    "Nordeste": 59.0,
    "Centro-Oeste": 70.0,
    "Sudeste": 74.0,
    "Sul": 78.0,
}


def _get_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "tech-challenge-fase2", "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        bruto = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip" or bruto[:2] == b"\x1f\x8b":
            bruto = gzip.decompress(bruto)
    return json.loads(bruto.decode("utf-8"))


def carregar_ufs() -> list[dict]:
    dados = _get_json(IBGE_ESTADOS)
    ufs = []
    for e in dados:
        ufs.append(
            {
                "id_uf": e["id"],
                "sigla_uf": e["sigla"],
                "nome_uf": e["nome"],
                "id_regiao": e["regiao"]["id"],
                "nome_regiao": e["regiao"]["nome"],
            }
        )
    return sorted(ufs, key=lambda u: u["id_uf"])


def carregar_municipios(ufs: list[dict]) -> list[dict]:
    por_id = {u["id_uf"]: u for u in ufs}
    dados = _get_json(IBGE_MUNICIPIOS)
    municipios = []
    for m in dados:
        id_municipio = m["id"]
        # Os dois primeiros digitos do codigo do municipio sao o codigo da UF.
        id_uf = int(str(id_municipio)[:2])
        uf = por_id[id_uf]
        municipios.append(
            {
                "id_municipio": id_municipio,
                "nome_municipio": m["nome"],
                "sigla_uf": uf["sigla_uf"],
                "id_uf": id_uf,
                "nome_regiao": uf["nome_regiao"],
            }
        )
    return sorted(municipios, key=lambda x: x["id_municipio"])


def _escrever(path: str, campos: list[str], linhas: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for linha in linhas:
            w.writerow({c: linha[c] for c in campos})
    print(f"[fontes] {os.path.basename(path)}: {len(linhas)} linhas")


def gerar(out: str, seed: int = 42) -> None:
    os.makedirs(out, exist_ok=True)
    rng = random.Random(seed)

    ufs = carregar_ufs()
    municipios = carregar_municipios(ufs)
    print(f"[fontes] IBGE: {len(ufs)} UFs, {len(municipios)} municipios")

    # uf
    _escrever(
        os.path.join(out, "uf.csv"),
        ["id_uf", "sigla_uf", "nome_uf", "id_regiao", "nome_regiao"],
        ufs,
    )
    # municipio
    _escrever(
        os.path.join(out, "municipio.csv"),
        ["id_municipio", "nome_municipio", "sigla_uf", "id_uf"],
        municipios,
    )

    # meta_brasil
    _escrever(
        os.path.join(out, "meta_brasil.csv"),
        ["ano", "meta_indicador"],
        [{"ano": ano, "meta_indicador": META_BRASIL[ano]} for ano in sorted(META_BRASIL)],
    )

    # meta_uf: meta nacional do ano com um leve gradiente regional
    metas_uf = []
    for ano in ANOS:
        for uf in ufs:
            base = BASE_REGIAO[uf["nome_regiao"]]
            meta = round(min(95.0, base + (META_BRASIL[ano] - 60.0) + rng.uniform(-2, 4)), 1)
            metas_uf.append({"ano": ano, "sigla_uf": uf["sigla_uf"], "meta_indicador": meta})
    _escrever(os.path.join(out, "meta_uf.csv"), ["ano", "sigla_uf", "meta_indicador"], metas_uf)

    # meta_municipio: meta da UF com ruido por municipio
    meta_uf_idx = {(m["ano"], m["sigla_uf"]): m["meta_indicador"] for m in metas_uf}
    metas_mun = []
    for ano in ANOS:
        for mun in municipios:
            base = meta_uf_idx[(ano, mun["sigla_uf"])]
            meta = round(min(97.0, max(45.0, base + rng.uniform(-4, 4))), 1)
            metas_mun.append(
                {"ano": ano, "id_municipio": mun["id_municipio"], "meta_indicador": meta}
            )
    _escrever(
        os.path.join(out, "meta_municipio.csv"),
        ["ano", "id_municipio", "meta_indicador"],
        metas_mun,
    )

    # alunos: publica em todo municipio, privada em parte deles, com desigualdade regional
    alunos = []
    for ano in ANOS:
        for mun in municipios:
            base = BASE_REGIAO[mun["nome_regiao"]]
            redes = ["publica"] + (["privada"] if rng.random() < 0.35 else [])
            for rede in redes:
                avaliados = rng.randint(40, 200) if rede == "privada" else rng.randint(80, 14000)
                alvo = base + (10 if rede == "privada" else 0) + (ano - 2024) * 2 + rng.uniform(-8, 8)
                indicador = min(97.0, max(38.0, alvo))
                alfabetizados = round(avaliados * indicador / 100)
                prof = round(700 + (indicador - 55) * 1.1 + rng.uniform(-6, 6), 1)
                alunos.append(
                    {
                        "ano": ano,
                        "id_municipio": mun["id_municipio"],
                        "rede": rede,
                        "qtd_avaliados": avaliados,
                        "qtd_alfabetizados": alfabetizados,
                        "media_proficiencia": prof,
                    }
                )
    _escrever(
        os.path.join(out, "alunos.csv"),
        ["ano", "id_municipio", "rede", "qtd_avaliados", "qtd_alfabetizados", "media_proficiencia"],
        alunos,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara as fontes em escala nacional")
    parser.add_argument("--out", default="data/seeds", help="Diretorio de saida dos CSVs")
    parser.add_argument("--seed", type=int, default=42, help="Semente para reprodutibilidade")
    args = parser.parse_args()
    gerar(args.out, args.seed)


if __name__ == "__main__":
    main()
