"""
Banco de questões para o questionário político do Brado.

Cada questão possui:
- id: identificador único
- text: texto da pergunta
- tags: categorias temáticas
- dimensions: lista de (dimensão, peso) — peso positivo = resposta alta (7) empurra para
  o polo positivo da dimensão; peso negativo = resposta alta empurra para o polo negativo.

As 8 dimensões políticas:
  economico        — intervenção do Estado na economia (-1=mercado livre, +1=estatismo)
  social           — costumes/comportamento (-1=conservador, +1=progressista)
  ambiental        — pauta ambiental (-1=desenvolvimentismo, +1=ambientalismo)
  seguranca        — política criminal (-1=punitivismo, +1=reabilitação/direitos)
  federalismo      — concentração de poder (-1=descentralização, +1=centralização)
  anticorrupcao    — combate à corrupção (-1=tolerância, +1=rigor institucional)
  exterior         — política externa (-1=nacionalismo/soberania, +1=multilateralismo)
  laicidade        — relação Estado/religião (-1=conservadorismo religioso, +1=laicidade)
"""

from typing import List, Optional, Tuple

# (dimensão, peso) — peso em [-1, +1]
DimWeight = Tuple[str, float]

QUESTIONS: List[dict] = [
    {
        "id": "q01",
        "text": "O Estado deve controlar empresas estratégicas como Petrobras e o setor elétrico.",
        "tags": ["economia", "empresas_estatais"],
        "dims": [("economico", +1.0)],
    },
    {
        "id": "q02",
        "text": "Privatizações de serviços públicos melhoram a eficiência e reduzem o custo para o cidadão.",
        "tags": ["economia", "privatizacao"],
        "dims": [("economico", -1.0)],
    },
    {
        "id": "q03",
        "text": "Programas de transferência de renda como o Bolsa Família são essenciais para reduzir a desigualdade.",
        "tags": ["economia", "assistencia_social"],
        "dims": [("economico", +0.8)],
    },
    {
        "id": "q04",
        "text": "A reforma trabalhista que flexibilizou contratos foi positiva para gerar mais empregos.",
        "tags": ["economia", "trabalho"],
        "dims": [("economico", -0.8)],
    },
    {
        "id": "q05",
        "text": "O casamento civil deve ser permitido entre pessoas do mesmo sexo.",
        "tags": ["direitos", "familia"],
        "dims": [("social", +1.0), ("laicidade", +0.5)],
    },
    {
        "id": "q06",
        "text": "O aborto deve ser descriminalizado em casos além dos já previstos em lei.",
        "tags": ["direitos", "saude"],
        "dims": [("social", +1.0), ("laicidade", +0.6)],
    },
    {
        "id": "q07",
        "text": "A educação sexual nas escolas públicas deve ser abrangente e incluir discussões sobre identidade de gênero.",
        "tags": ["educacao", "genero"],
        "dims": [("social", +0.9), ("laicidade", +0.4)],
    },
    {
        "id": "q08",
        "text": "Valores tradicionais de família devem ser preservados e incentivados pelo governo.",
        "tags": ["familia", "costumes"],
        "dims": [("social", -1.0), ("laicidade", -0.7)],
    },
    {
        "id": "q09",
        "text": "O desmatamento da Amazônia deve ser combatido com políticas rígidas, mesmo que isso limite atividades econômicas.",
        "tags": ["meio_ambiente", "amazonia"],
        "dims": [("ambiental", +1.0)],
    },
    {
        "id": "q10",
        "text": "O agronegócio é fundamental para a economia brasileira e não deve ser excessivamente regulado ambientalmente.",
        "tags": ["economia", "agronegocio", "meio_ambiente"],
        "dims": [("ambiental", -1.0), ("economico", -0.4)],
    },
    {
        "id": "q11",
        "text": "O Brasil deve assumir metas ambiciosas de redução de emissões de carbono mesmo com custo econômico.",
        "tags": ["meio_ambiente", "clima"],
        "dims": [("ambiental", +1.0), ("exterior", +0.4)],
    },
    {
        "id": "q12",
        "text": "Penas mais severas para crimes violentos são a melhor forma de reduzir a criminalidade.",
        "tags": ["seguranca", "justica_criminal"],
        "dims": [("seguranca", -1.0)],
    },
    {
        "id": "q13",
        "text": "O investimento em educação e geração de empregos é mais eficaz que o encarceramento para reduzir o crime.",
        "tags": ["seguranca", "educacao"],
        "dims": [("seguranca", +1.0), ("economico", +0.3)],
    },
    {
        "id": "q14",
        "text": "A posse de armas de fogo deve ser facilitada para cidadãos comuns se defenderem.",
        "tags": ["seguranca", "armas"],
        "dims": [("seguranca", -0.8)],
    },
    {
        "id": "q15",
        "text": "Estados e municípios devem ter maior autonomia para gerir seus próprios recursos e políticas.",
        "tags": ["federalismo", "governo"],
        "dims": [("federalismo", -1.0)],
    },
    {
        "id": "q16",
        "text": "Políticas nacionais unificadas são mais eficazes do que deixar cada estado decidir.",
        "tags": ["federalismo", "governo"],
        "dims": [("federalismo", +1.0)],
    },
    {
        "id": "q17",
        "text": "Agentes públicos corruptos devem perder automaticamente seus direitos políticos e enfrentar penas mais duras.",
        "tags": ["corrupcao", "justica"],
        "dims": [("anticorrupcao", +1.0)],
    },
    {
        "id": "q18",
        "text": "Operações policiais e judiciais como a Lava Jato foram fundamentais para combater a corrupção no Brasil.",
        "tags": ["corrupcao", "justica"],
        "dims": [("anticorrupcao", +0.9)],
    },
    {
        "id": "q19",
        "text": "Delações premiadas e acordos de leniência são instrumentos legítimos no combate à corrupção.",
        "tags": ["corrupcao", "justica"],
        "dims": [("anticorrupcao", +0.8)],
    },
    {
        "id": "q20",
        "text": "O Brasil deve priorizar relações bilaterais com países vizinhos em vez de organismos multilaterais.",
        "tags": ["politica_externa"],
        "dims": [("exterior", -0.7)],
    },
    {
        "id": "q21",
        "text": "O Brasil deve buscar integração mais profunda com blocos regionais como o Mercosul e a UNASUL.",
        "tags": ["politica_externa", "integracao_regional"],
        "dims": [("exterior", +0.8)],
    },
    {
        "id": "q22",
        "text": "A influência de líderes religiosos na política e nas leis brasileiras é positiva.",
        "tags": ["religiao", "politica"],
        "dims": [("laicidade", -1.0)],
    },
    {
        "id": "q23",
        "text": "O Estado brasileiro deve ser estritamente laico, sem qualquer influência de igrejas em decisões públicas.",
        "tags": ["religiao", "laicidade"],
        "dims": [("laicidade", +1.0)],
    },
    {
        "id": "q24",
        "text": "A reforma da previdência que aumentou a idade mínima de aposentadoria foi necessária para o equilíbrio fiscal.",
        "tags": ["economia", "previdencia"],
        "dims": [("economico", -0.7)],
    },
    {
        "id": "q25",
        "text": "O teto de gastos públicos é importante para garantir a estabilidade econômica do país.",
        "tags": ["economia", "fiscal"],
        "dims": [("economico", -0.8)],
    },
]

ALL_DIMENSIONS = [
    "economico",
    "social",
    "ambiental",
    "seguranca",
    "federalismo",
    "anticorrupcao",
    "exterior",
    "laicidade",
]

# Profiles for Brazilian parties (simplified 8D vectors).
# Scale: -1.0 to +1.0 for each dimension.
PARTY_PROFILES = [
    {
        "nome": "Partido dos Trabalhadores",
        "sigla": "PT",
        "tipo": "partido",
        "vetor": {
            "economico": +0.8,
            "social": +0.7,
            "ambiental": +0.6,
            "seguranca": +0.6,
            "federalismo": +0.4,
            "anticorrupcao": +0.3,
            "exterior": +0.7,
            "laicidade": +0.5,
        },
    },
    {
        "nome": "Partido Liberal",
        "sigla": "PL",
        "tipo": "partido",
        "vetor": {
            "economico": -0.7,
            "social": -0.9,
            "ambiental": -0.7,
            "seguranca": -0.9,
            "federalismo": -0.5,
            "anticorrupcao": +0.4,
            "exterior": -0.8,
            "laicidade": -0.9,
        },
    },
    {
        "nome": "Partido Social Democrático",
        "sigla": "PSD",
        "tipo": "partido",
        "vetor": {
            "economico": -0.3,
            "social": -0.2,
            "ambiental": +0.1,
            "seguranca": -0.3,
            "federalismo": -0.2,
            "anticorrupcao": +0.5,
            "exterior": +0.2,
            "laicidade": -0.1,
        },
    },
    {
        "nome": "União Brasil",
        "sigla": "UNIÃO",
        "tipo": "partido",
        "vetor": {
            "economico": -0.4,
            "social": -0.5,
            "ambiental": -0.2,
            "seguranca": -0.5,
            "federalismo": -0.3,
            "anticorrupcao": +0.3,
            "exterior": -0.3,
            "laicidade": -0.5,
        },
    },
    {
        "nome": "MDB",
        "sigla": "MDB",
        "tipo": "partido",
        "vetor": {
            "economico": -0.1,
            "social": +0.1,
            "ambiental": +0.3,
            "seguranca": -0.1,
            "federalismo": -0.3,
            "anticorrupcao": +0.4,
            "exterior": +0.3,
            "laicidade": +0.1,
        },
    },
    {
        "nome": "Partido dos Trabalhadores Democratas",
        "sigla": "PDT",
        "tipo": "partido",
        "vetor": {
            "economico": +0.5,
            "social": +0.5,
            "ambiental": +0.5,
            "seguranca": +0.4,
            "federalismo": +0.2,
            "anticorrupcao": +0.5,
            "exterior": +0.5,
            "laicidade": +0.4,
        },
    },
    {
        "nome": "Partido Socialismo e Liberdade",
        "sigla": "PSOL",
        "tipo": "partido",
        "vetor": {
            "economico": +1.0,
            "social": +1.0,
            "ambiental": +0.9,
            "seguranca": +1.0,
            "federalismo": +0.5,
            "anticorrupcao": +0.9,
            "exterior": +0.9,
            "laicidade": +1.0,
        },
    },
    {
        "nome": "Partido Progressistas",
        "sigla": "PP",
        "tipo": "partido",
        "vetor": {
            "economico": -0.5,
            "social": -0.6,
            "ambiental": -0.4,
            "seguranca": -0.6,
            "federalismo": -0.4,
            "anticorrupcao": +0.1,
            "exterior": -0.4,
            "laicidade": -0.6,
        },
    },
    {
        "nome": "Partido da Social Democracia Brasileira",
        "sigla": "PSDB",
        "tipo": "partido",
        "vetor": {
            "economico": -0.4,
            "social": +0.2,
            "ambiental": +0.3,
            "seguranca": -0.2,
            "federalismo": -0.3,
            "anticorrupcao": +0.7,
            "exterior": +0.4,
            "laicidade": +0.2,
        },
    },
    {
        "nome": "Partido Socialista Brasileiro",
        "sigla": "PSB",
        "tipo": "partido",
        "vetor": {
            "economico": +0.6,
            "social": +0.7,
            "ambiental": +0.6,
            "seguranca": +0.5,
            "federalismo": +0.2,
            "anticorrupcao": +0.6,
            "exterior": +0.6,
            "laicidade": +0.7,
        },
    },
    {
        "nome": "Republicanos",
        "sigla": "REPUBLICANOS",
        "tipo": "partido",
        "vetor": {
            "economico": -0.5,
            "social": -0.7,
            "ambiental": -0.3,
            "seguranca": -0.6,
            "federalismo": -0.4,
            "anticorrupcao": +0.2,
            "exterior": -0.3,
            "laicidade": -0.8,
        },
    },
]


def get_question_by_id(qid: str) -> Optional[dict]:
    for q in QUESTIONS:
        if q["id"] == qid:
            return q
    return None
