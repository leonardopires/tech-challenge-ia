SITEMAP: dict = {
    "processamento": {
        "viniferas": {"resource": "ProcessaViniferas", "delimiter": "\t"},
        "americanasehibridas": {"resource": "ProcessaAmericanas", "delimiter": "\t"},
        "americanas": {"resource": "ProcessaAmericanas", "delimiter": "\t"},
        "hibridas": {"resource": "ProcessaAmericanas", "delimiter": "\t"},
        "uvasdemesa": {"resource": "ProcessaMesa", "delimiter": "\t"},
        "mesa": {"resource": "ProcessaMesa", "delimiter": "\t"},
        "semclassificacao": {"resource": "ProcessaSemclass", "delimiter": "\t"},
    },
    "comercializacao": {
        "todos": {"resource": "Comercio", "delimiter": ";"},
    },
    "importacao": {
        "vinhosdemesa": {"resource": "ImpVinhos", "delimiter": ";"},
        "vinhos": {"resource": "ImpVinhos", "delimiter": ";"},
        "espumantes": {"resource": "ImpEspumantes", "delimiter": ";"},
        "uvasfrescas": {"resource": "ImpFrescas", "delimiter": ";"},
        "uvas": {"resource": "ImpFrescas", "delimiter": ";"},
        "frescas": {"resource": "ImpFrescas", "delimiter": ";"},
        "uvaspassas": {"resource": "ImpPassas", "delimiter": ";"},
        "passas": {"resource": "ImpPassas", "delimiter": ";"},
        "sucodeuva": {"resource": "ImpSuco", "delimiter": ";"},
        "suco": {"resource": "ImpSuco", "delimiter": ";"},
    },
    "exportacao": {
        "vinhosdemesa": {"resource": "ExpVinho", "delimiter": ";"},
        "vinhos": {"resource": "ExpVinho", "delimiter": ";"},
        "espumantes": {"resource": "ExpEspumantes", "delimiter": ";"},
        "uvasfrescas": {"resource": "ExpUva", "delimiter": ";"},
        "uvas": {"resource": "ExpUva", "delimiter": ";"},
        "frescas": {"resource": "ExpUva", "delimiter": ";"},
        "sucodeuva": {"resource": "ExpSuco", "delimiter": ";"},
        "suco": {"resource": "ExpSuco", "delimiter": ";"},
    }
}
