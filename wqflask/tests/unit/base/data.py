gen_menu_json = """
{
  "datasets": {
    "human": {
      "HLC": {
        "Liver mRNA": [
          [
            "320",
            "HLC_0311",
            "GSE9588 Human Liver Normal (Mar11) Both Sexes"
          ]
        ],
        "Phenotypes": [
          [
            "635",
            "HLCPublish",
            "HLC Published Phenotypes"
          ]
        ]
      }
    },
    "mouse": {
      "BXD": {
        "Genotypes": [
          [
            "600",
            "BXDGeno",
            "BXD Genotypes"
          ]
        ],
        "Hippocampus mRNA": [
          [
            "112",
            "HC_M2_0606_P",
            "Hippocampus Consortium M430v2 (Jun06) PDNN"
          ]
        ],
        "Phenotypes": [
          [
            "602",
            "BXDPublish",
            "BXD Published Phenotypes"
          ]
        ]
      }
    }
  },
  "groups": {
    "human": [
      [
        "HLC",
        "Liver: Normal Gene Expression with Genotypes (Merck)",
        "Family:None"
      ]
    ],
    "mouse": [
      [
        "BXD",
        "BXD",
        "Family:None"
      ]
    ]
  },
  "species": [
    [
      "human",
      "Human"
    ],
    [
      "mouse",
      "Mouse"
    ]
  ],
  "types": {
    "human": {
      "HLC": [
        [
          "Phenotypes",
          "Traits and Cofactors",
          "Phenotypes"
        ],
        [
          "Liver mRNA",
          "Liver mRNA",
          "Molecular Trait Datasets"
        ]
      ]
    },
    "mouse": {
      "BXD": [
        [
          "Phenotypes",
          "Traits and Cofactors",
          "Phenotypes"
        ],
        [
          "Genotypes",
          "DNA Markers and SNPs",
          "Genotypes"
        ],
        [
          "Hippocampus mRNA",
          "Hippocampus mRNA",
          "Molecular Trait Datasets"
        ]
      ]
    }
  }
}
"""
