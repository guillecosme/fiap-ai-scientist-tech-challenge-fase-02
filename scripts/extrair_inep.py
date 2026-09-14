"""Extrai as metas e os dados de alunos do Indicador Crianca Alfabetizada direto do Inep.

O Inep passou a publicar as planilhas de resultados e metas por municipio e por UF
(2023 a 2025) e, em agosto de 2025, os microdados da avaliacao no grao de aluno
(2024 e 2025). Com isso as quatro entidades que na primeira versao da pipeline eram
simuladas (meta_brasil, meta_uf, meta_municipio e alunos) passam a ser extratos
reais, no mesmo esquema. O territorio continua vindo da API do IBGE.

Os arquivos brutos vao para data/fontes_inep (fora do git). O download e feito por
HTTP porque o servidor do Inep publica uma cadeia de certificado incompleta.
"""

from __future__ import annotations

import io
import os
import re
import urllib.request
import zipfile

import pandas as pd

INEP = "http://download.inep.gov.br"
PLANILHAS_MUNICIPIO = {
    2023: f"{INEP}/avaliacao_da_alfabetizacao/resultados_e_metas_municipios.xlsx",
    2024: f"{INEP}/alfabetiza_brasil/resultados_e_metas_municipios_2024.xlsx",
    2025: f"{INEP}/avaliacao_da_alfabetizacao/resultados/resultados_e_metas_municipios_2025_3.xlsx",
}
PLANILHAS_UF = {
    2023: f"{INEP}/avaliacao_da_alfabetizacao/resultados_e_metas_ufs.xlsx",
    2024: f"{INEP}/alfabetiza_brasil/resultados_e_metas_ufs_2024_2.xlsx",
    2025: f"{INEP}/avaliacao_da_alfabetizacao/resultados/resultados_e_metas_ufs_2025_v1.xlsx",
}
MICRODADOS = {
    2024: f"{INEP}/dados_abertos/microdados_avaliacao_da_alfabetizacao_2024.zip",
    2025: f"{INEP}/dados_abertos/microdados_AEEB_2025.zip",
}
NA = ["-", "--", "...", ""]
REDES = {1: "federal", 2: "estadual", 3: "municipal", 4: "privada"}


def baixar(url: str, destino: str) -> str:
    if os.path.exists(destino):
        return destino
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "tech-challenge-fase2"})
    with urllib.request.urlopen(req, timeout=900) as resp, open(destino, "wb") as f:
        while True:
            bloco = resp.read(1 << 20)
            if not bloco:
                break
            f.write(bloco)
    print(f"[inep] baixado {os.path.basename(destino)}")
    return destino


def _metas_longo(df: pd.DataFrame, chave: str) -> pd.DataFrame:
    partes = []
    for col in df.columns:
        m = re.fullmatch(r"META_FINAL_(\d{4})", str(col))
        if not m:
            continue
        valores = pd.to_numeric(
            df[col].astype(str).str.replace(">", "").str.strip(), errors="coerce"
        )
        partes.append(
            pd.DataFrame({chave: df[chave], "ano": int(m.group(1)), "meta_indicador": valores})
        )
    metas = pd.concat(partes, ignore_index=True)
    # meta igual a zero e erro de preenchimento na planilha de 2025
    return metas[metas["meta_indicador"] > 0]


def metas_municipio(pasta: str) -> pd.DataFrame:
    """Trajetoria 2024-2030 de cada municipio, da planilha mais recente em que esta
    completa; a planilha de 2025 arredonda para inteiros, entao as anteriores tem
    prioridade quando coincidem apos o arredondamento."""
    versoes = {}
    for ano, url in sorted(PLANILHAS_MUNICIPIO.items()):
        df = pd.read_excel(
            baixar(url, os.path.join(pasta, f"municipios_{ano}.xlsx")), header=1, na_values=NA
        )
        df["CO_MUNICIPIO"] = pd.to_numeric(df["CO_MUNICIPIO"], errors="coerce")
        df = df.dropna(subset=["CO_MUNICIPIO"])
        df["id_municipio"] = df["CO_MUNICIPIO"].astype("int64")
        versoes[ano] = _metas_longo(df, "id_municipio")
    return _consolidar(versoes, "id_municipio")


def metas_uf(pasta: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    versoes = {}
    for ano, url in sorted(PLANILHAS_UF.items()):
        df = pd.read_excel(
            baixar(url, os.path.join(pasta, f"ufs_{ano}.xlsx")), header=1, na_values=NA
        )
        df = df.dropna(subset=["NOME_UF"])
        df["sigla_uf"] = (
            df["SIGLA_UF"].fillna("BR").astype(str).str.replace("*", "", regex=False).str.strip()
        )
        versoes[ano] = _metas_longo(df, "sigla_uf")
    metas = _consolidar(versoes, "sigla_uf")
    brasil = metas[metas["sigla_uf"] == "BR"][["ano", "meta_indicador"]]
    return brasil, metas[metas["sigla_uf"] != "BR"]


def _consolidar(versoes: dict[int, pd.DataFrame], chave: str) -> pd.DataFrame:
    anos_meta = sorted({a for v in versoes.values() for a in v["ano"].unique()})
    escolha = {}
    for ano_planilha in sorted(versoes):
        v = versoes[ano_planilha]
        completos = v.groupby(chave)["ano"].nunique()
        for unidade in completos[completos == len(anos_meta)].index:
            escolha[unidade] = ano_planilha  # a mais recente completa vence
    saida = []
    for unidade, ano_base in escolha.items():
        base = versoes[ano_base][versoes[ano_base][chave] == unidade].set_index("ano")[
            "meta_indicador"
        ]
        melhor = base
        for ano_planilha in sorted(versoes):
            if ano_planilha >= ano_base:
                break
            cand = versoes[ano_planilha]
            cand = cand[cand[chave] == unidade].set_index("ano")["meta_indicador"]
            if len(cand) == len(anos_meta) and (cand.round(0) == base.round(0)).all():
                melhor = cand
                break
        saida.append(
            pd.DataFrame(
                {chave: unidade, "ano": melhor.index, "meta_indicador": melhor.values.round(4)}
            )
        )
    return pd.concat(saida, ignore_index=True).sort_values([chave, "ano"]).reset_index(drop=True)


def alunos(pasta: str) -> pd.DataFrame:
    """Agregado dos microdados no grao ano x municipio x rede, reproduzindo o calculo
    oficial (media ponderada pelo peso amostral entre presentes com prova preenchida)."""
    partes = []
    for ano, url in sorted(MICRODADOS.items()):
        zip_path = baixar(url, os.path.join(pasta, f"microdados_{ano}.zip"))
        with zipfile.ZipFile(zip_path) as z:
            nome = next(n for n in z.namelist() if n.endswith("TS_ALUNO.csv"))
            with z.open(nome) as f:
                df = pd.read_csv(
                    io.TextIOWrapper(f, encoding="latin-1"),
                    sep=";",
                    usecols=[
                        "TP_DEPENDENCIA",
                        "CO_MUNICIPIO",
                        "IN_PRESENCA_LP",
                        "IN_PREENCHIMENTO_LP",
                        "VL_PESO_ALUNO_LP",
                        "VL_PROFICIENCIA_LP",
                        "IN_ALFABETIZADO",
                    ],
                    dtype={"TP_DEPENDENCIA": "Int8", "CO_MUNICIPIO": "Int64"},
                )
        p = (
            df[(df["IN_PRESENCA_LP"] == 1) & (df["IN_PREENCHIMENTO_LP"] == 1)]
            .dropna(subset=["CO_MUNICIPIO", "TP_DEPENDENCIA"])
            .copy()
        )
        p["w"] = pd.to_numeric(p["VL_PESO_ALUNO_LP"], errors="coerce").astype(float)
        p["prof"] = pd.to_numeric(p["VL_PROFICIENCIA_LP"], errors="coerce").astype(float)
        p["w_alf"] = p["w"] * p["IN_ALFABETIZADO"]
        p["w_prof"] = p["w"] * p["prof"]
        g = (
            p.groupby(["CO_MUNICIPIO", "TP_DEPENDENCIA"])
            .agg(
                qtd_avaliados=("IN_ALFABETIZADO", "size"),
                qtd_alfabetizados=("IN_ALFABETIZADO", "sum"),
                soma_w=("w", "sum"),
                soma_w_alf=("w_alf", "sum"),
                soma_w_prof=("w_prof", "sum"),
            )
            .reset_index()
        )
        g["ano"] = ano
        g["id_municipio"] = g["CO_MUNICIPIO"].astype("int64")
        g["rede"] = g["TP_DEPENDENCIA"].astype(int).map(REDES)
        g["media_proficiencia"] = (g["soma_w_prof"] / g["soma_w"]).round(1)
        # qtd_alfabetizados ponderada, para que a razao com qtd_avaliados reproduza o
        # percentual oficial
        g["qtd_alfabetizados"] = (
            (g["qtd_avaliados"] * g["soma_w_alf"] / g["soma_w"]).round().astype("int64")
        )
        partes.append(
            g[
                [
                    "ano",
                    "id_municipio",
                    "rede",
                    "qtd_avaliados",
                    "qtd_alfabetizados",
                    "media_proficiencia",
                ]
            ]
        )
        n_mun = g["id_municipio"].nunique()
        print(f"[inep] alunos {ano}: {len(p):,} avaliados em {n_mun:,} municipios")
    return (
        pd.concat(partes, ignore_index=True)
        .sort_values(["ano", "id_municipio", "rede"])
        .reset_index(drop=True)
    )
