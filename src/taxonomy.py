class LiteratureReview:
    """
    """
    literature_style_taxonomy = ['Literature review',
                        'Empirical Study',
                        'Case Study',
                        'Conceptual Paper',
                        'Other']

class RetentionTaxonomy:
    """
    Reference Source: Nonaka and Takeuchi, 1995
    """
    SECI_taxonomy = [
        "Socialization",
        "Externalization",
        "Combination",
        "Internalization"]

    """
    Reference Source:
    """
    collins_based_tacit_knowledge_taxonomy = [
        "Somatic Tacit Knowledge",
        "Relational Tacit Knowledge",
        "Collective Tacit Knowledge",
        "Intellectual Tacit Knowledge"]

    """
    Reference Source: Igoa-Iraola, E., & Díez, F. (2024). Procedures for transferring organizational knowledge during generational change: A systematic review. 
    Heliyon, 10(5). https://doi.org/10.1016/j.heliyon.2024.e27092
    """
    knowledge_retention_activities_taxonomy = [
        "Job shadowing",
        "Job Rotation",
        "Deliberate Practice",
        "Knowledge Cafés",
        "Knowledge Harvesting Workshops",
        "Critical Incident Technique",
        "Mentoring",
        "Storytelling",
        "After-Action Reviews",
        "Communities of practice"]

    kr_activities_taxonomy_prompt = {
        "prompt": f"According to the knowledge retention activity list : {knowledge_retention_activities_taxonomy}"
                  f"identify the knowledge retention activities discussed"
    }

    tacit_enum = [
        "Somatic tacit knowledge",
        "Cognitive tacit knowledge",
        "Collective and relational",
        "Adaptive tacit knowledge"
    ]

    digital_enum = [
        "Artificial Intelligence and Intelligent Computation",
        "Human–Computer Interaction and Immersive Technologies",
        "Cyber-Physical Systems, IoT, and Smart Environments",
        "Data, Information, and Knowledge Systems",
        "Imaging, Sensing, and Perception Technologies",
        "Distributed, Secure, and Trust Technologies",
        "Mobile, Social, and Communication Technologies",
        "Rule-Based, Decision, and Expert Systems"
    ]


class SectorKnowledgeGraph:

    technology_enable_practice = [
        "Artificial Intelligence and Intelligent Computation",
        "Human–Computer Interaction and Immersive Technologies",
        "Cyber-Physical Systems, IoT, and Smart Environments",
        "Data, Information, and Knowledge Systems",
        "Imaging, Sensing, and Perception Technologies",
        "Distributed, Secure, and Trust Technologies",
        "Mobile, Social, and Communication Technologies",
        "Rule-Based, Decision, and Expert Systems"
    ]

    knowledge_capture_activities_taxonomy = [
        "Job shadowing",
        "Job Rotation",
        "Deliberate Practice",
        "Knowledge Cafés",
        "Knowledge Harvesting Workshops",
        "Critical Incident Technique",
        "Mentoring",
        "Storytelling",
        "After-Action Reviews",
        "Communities of practice",
        "Other"
    ]

class IndustryTaxonomy:

    """
    Reference Source: Viana, F. (2024). GLOBAL INDUSTRY CLASSIFICATION STANDARD (GICS®) METHODOLOGY.
    """
    sic_dict = {
        "0109": "Agriculture, Forestry, And Fishing (Agriculture, Forestry, And Fishing)",
        "1014": "Mining (Mining)",
        "15": "Construction (Building Construction—General Contractors And Operative Builders)",
        "16": "Construction (Heavy Construction Other Than Building Construction—Contractors)",
        "17": "Construction (Construction—Special Trade Contractors)",
        "2039": "Manufacturing",
        "20": "Manufacturing (Food And Kindred Products)",
        "21": "Manufacturing (Tobacco Products)",
        "22": "Manufacturing (Textile Mill Products)",
        "23": "Manufacturing (Apparel And Other Finished Products Made From Fabrics And Similar Materials)",
        "24": "Manufacturing (Lumber And Wood Products, Except Furniture)",
        "25": "Manufacturing (Furniture And Fixtures)",
        "26": "Manufacturing (Paper And Allied Products)",
        "27": "Manufacturing (Printing, Publishing, And Allied Industries)",
        "28": "Manufacturing (Chemicals And Allied Products)",
        "29": "Manufacturing (Petroleum Refining And Related Industries)",
        "30": "Manufacturing (Rubber And Miscellaneous Plastics Products)",
        "31": "Manufacturing (Leather And Leather Products)",
        "32": "Manufacturing (Stone, Clay, Glass, And Concrete Products)",
        "33": "Manufacturing (Primary Metal Industries)",
        "34": "Manufacturing (Fabricated Metal Products, Except Machinery And Transportation Equipment)",
        "35": "Manufacturing (Industrial And Commercial Machinery And Computer Equipment)",
        "36": "Manufacturing (Electronic And Other Electrical Equipment And Components, Except Computer Equipment)",
        "37": "Manufacturing (Transportation Equipment)",
        "38": "Manufacturing (Measuring, Analyzing, And Controlling Instruments; Photographic, Medical And Optical Goods; Watches And Clocks)",
        "39": "Manufacturing (Miscellaneous Manufacturing Industries)",
        "40": "Transportation, Communications, Electric, Gas, And Sanitary Services (Railroad Transportation)",
        "41": "Transportation, Communications, Electric, Gas, And Sanitary Services (Local And Suburban Transit And Interurban Highway Passenger Transportation)",
        "42": "Transportation, Communications, Electric, Gas, And Sanitary Services (Motor Freight Transportation And Warehousing)",
        "43": "Transportation, Communications, Electric, Gas, And Sanitary Services (United States Postal Service)",
        "44": "Transportation, Communications, Electric, Gas, And Sanitary Services (Water Transportation)",
        "45": "Transportation, Communications, Electric, Gas, And Sanitary Services (Transportation By Air)",
        "46": "Transportation, Communications, Electric, Gas, And Sanitary Services (Pipelines, Except Natural Gas)",
        "47": "Transportation, Communications, Electric, Gas, And Sanitary Services (Transportation Services)",
        "48": "Transportation, Communications, Electric, Gas, And Sanitary Services (Communications)",
        "49": "Transportation, Communications, Electric, Gas, And Sanitary Services (Electric, Gas, And Sanitary Services)",
        "50": "Wholesale Trade (Wholesale Trade—Durable Goods)",
        "51": "Wholesale Trade (Wholesale Trade—Nondurable Goods)",
        "52": "Retail Trade (Building Materials, Hardware, Garden Supply, And Mobile Home Dealers)",
        "53": "Retail Trade (General Merchandise Stores)",
        "54": "Retail Trade (Food Stores)",
        "55": "Retail Trade (Automotive Dealers And Gasoline Service Stations)",
        "56": "Retail Trade (Apparel And Accessory Stores)",
        "57": "Retail Trade (Home Furniture, Furnishings, And Equipment Stores)",
        "58": "Retail Trade (Eating And Drinking Places)",
        "59": "Retail Trade (Miscellaneous Retail)",
        "6067": "Finance, Insurance, And Real Estate",
        "60": "Finance, Insurance, And Real Estate (Depository Institutions)",
        "61": "Finance, Insurance, And Real Estate (Nondepository Credit Institutions)",
        "62": "Finance, Insurance, And Real Estate (Security And Commodity Brokers, Dealers, Exchanges, And Services)",
        "63": "Finance, Insurance, And Real Estate (Insurance Carriers)",
        "64": "Finance, Insurance, And Real Estate (Insurance Agents, Brokers, And Service)",
        "65": "Finance, Insurance, And Real Estate (Real Estate)",
        "67": "Finance, Insurance, And Real Estate (Holding And Other Investment Offices)",
        "70": "Services (Hotels, Rooming Houses, Camps, And Other Lodging Places)",
        "72": "Services (Personal Services)",
        "73": "Services (Business Services)",
        "75": "Services (Automotive Repair, Services, And Parking)",
        "76": "Services (Miscellaneous Repair Services)",
        "78": "Services (Motion Pictures)",
        "79": "Services (Amusement And Recreation Services)",
        "80": "Services (Health Services)",
        "81": "Services (Legal Services)",
        "82": "Services (Educational Services)",
        "83": "Services (Social Services)",
        "84": "Services (Museums, Art Galleries, And Botanical And Zoological Gardens)",
        "86": "Services (Membership Organizations)",
        "87": "Services (Engineering, Accounting, Research, Management, And Related Services)",
        "88": "Services (Private Households)",
        "89": "Services (Miscellaneous Services)",
        "9197": "Public Administration",
        "91": "Public Administration (Executive, Legislative, And General Government, Except Finance)",
        "92": "Public Administration (Justice, Public Order, And Safety)",
        "93": "Public Administration (Public Finance, Taxation, And Monetary Policy)",
        "94": "Public Administration (Administration Of Human Resource Programs)",
        "95": "Public Administration (Administration Of Environmental Quality And Housing Programs)",
        "96": "Public Administration (Administration Of General Economic Programs)",
        "97": "Public Administration (National Security And International Affairs)",
        "99": "Nonclassifiable Establishments (Nonclassifiable Establishments)"
    }

    industry_taxonomy_gics = ["Energy",
                              "Materials",
                              "Industrials",
                              "Consumer Discretionary",
                              "Consumer Staples",
                              "Health Care",
                              "Financials",
                              "Information Technology",
                              "Communication Services",
                              "Utilities",
                              "Real Estate"]

    industry_taxonomy_gics_prompt = {
        "prompt": f"based on the GLOBAL INDUSTRY CLASSIFICATION STANDARD (GICS) METHODOLOGY {industry_taxonomy_gics}, "
                  f"identify the primary and secondary industrial divisions discussed",
        "output": {
            "primary_division": "Division Name",
            "primary_reasoning": "A brief sentence explaining why this classification fits, referencing keywords from the abstract.",
            "secondary_division": "Division Name",
            "secondary_reasoning": "A brief sentence explaining why this classification fits, referencing keywords from the abstract."
        }
    }

    """
    Reference Source: SIC Manual | Occupational Safety and Health Administration. (n.d.). Retrieved February 15, 2026, from https://www.osha.gov/data/sic-manual
    """

    industry_taxonomy_sci = [
        {
            "division": "A: Agriculture, Forestry, And Fishing",
            "majorGroups": [
                "Major Group 01: Agricultural Production Crops",
                "Major Group 02: Agriculture production livestock and animal specialties",
                "Major Group 07: Agricultural Services",
                "Major Group 08: Forestry",
                "Major Group 09: Fishing, hunting, and trapping"
            ]
        },
        {
            "division": "B: Mining",
            "majorGroups": [
                "Major Group 10: Metal Mining",
                "Major Group 11: Gold and silver ores",
                "Major Group 12: Coal Mining",
                "Major Group 13: Oil And Gas Extraction",
                "Major Group 14: Mining And Quarrying Of Nonmetallic Minerals, Except Fuels"
            ]
        },
        {
            "division": "C: Construction",
            "majorGroups": [
                "Major Group 15: Building Construction General Contractors And Operative Builders",
                "Major Group 16: Heavy Construction Other Than Building Construction Contractors",
                "Major Group 17: Construction Special Trade Contractors"
            ]
        },
        {
            "division": "D: Manufacturing",
            "majorGroups": [
                "Major Group 20: Food And Kindred Products",
                "Major Group 21: Tobacco Products",
                "Major Group 22: Textile Mill Products",
                "Major Group 23: Apparel And Other Finished Products Made From Fabrics And Similar Materials",
                "Major Group 24: Lumber And Wood Products, Except Furniture",
                "Major Group 25: Furniture And Fixtures",
                "Major Group 26: Paper And Allied Products",
                "Major Group 27: Printing, Publishing, And Allied Industries",
                "Major Group 28: Chemicals And Allied Products",
                "Major Group 29: Petroleum Refining And Related Industries",
                "Major Group 30: Rubber And Miscellaneous Plastics Products",
                "Major Group 31: Leather And Leather Products",
                "Major Group 32: Stone, Clay, Glass, And Concrete Products",
                "Major Group 33: Primary Metal Industries",
                "Major Group 34: Fabricated Metal Products, Except Machinery And Transportation Equipment",
                "Major Group 35: Industrial And Commercial Machinery And Computer Equipment",
                "Major Group 36: Electronic And Other Electrical Equipment And Components, Except Computer Equipment",
                "Major Group 37: Transportation Equipment",
                "Major Group 38: Measuring, Analyzing, And Controlling Instruments; Photographic, Medical And Optical Goods; Watches And Clocks",
                "Major Group 39: Miscellaneous Manufacturing Industries"
            ]
        },
        {
            "division": "E: Transportation, Communications, Electric, Gas, And Sanitary Services",
            "majorGroups": [
                "Major Group 40: Railroad Transportation",
                "Major Group 41: Local And Suburban Transit And Interurban Highway Passenger Transportation",
                "Major Group 42: Motor Freight Transportation And Warehousing",
                "Major Group 43: United States Postal Service",
                "Major Group 44: Water Transportation",
                "Major Group 45: Transportation By Air",
                "Major Group 46: Pipelines, Except Natural Gas",
                "Major Group 47: Transportation Services",
                "Major Group 48: Communications",
                "Major Group 49: Electric, Gas, And Sanitary Services"
            ]
        },
        {
            "division": "F: Wholesale Trade",
            "majorGroups": [
                "Major Group 50: Wholesale Trade-durable Goods",
                "Major Group 51: Wholesale Trade-non-durable Goods"
            ]
        },
        {
            "division": "G: Retail Trade",
            "majorGroups": [
                "Major Group 52: Building Materials, Hardware, Garden Supply, And Mobile Home Dealers",
                "Major Group 53: General Merchandise Stores",
                "Major Group 54: Food Stores",
                "Major Group 55: Automotive Dealers And Gasoline Service Stations",
                "Major Group 56: Apparel And Accessory Stores",
                "Major Group 57: Home Furniture, Furnishings, And Equipment Stores",
                "Major Group 58: Eating And Drinking Places",
                "Major Group 59: Miscellaneous Retail"
            ]
        },
        {
            "division": "H: Finance, Insurance, And Real Estate",
            "majorGroups": [
                "Major Group 60: Depository Institutions",
                "Major Group 61: Non-depository Credit Institutions",
                "Major Group 62: Security And Commodity Brokers, Dealers, Exchanges, And Services",
                "Major Group 63: Insurance Carriers",
                "Major Group 64: Insurance Agents, Brokers, And Service",
                "Major Group 65: Real Estate",
                "Major Group 67: Holding And Other Investment Offices"
            ]
        },
        {
            "division": "I: Services",
            "majorGroups": [
                "Major Group 70: Hotels, Rooming Houses, Camps, And Other Lodging Places",
                "Major Group 72: Personal Services",
                "Major Group 73: Business Services",
                "Major Group 75: Automotive Repair, Services, And Parking",
                "Major Group 76: Miscellaneous Repair Services",
                "Major Group 78: Motion Pictures",
                "Major Group 79: Amusement And Recreation Services",
                "Major Group 80: Health Services",
                "Major Group 81: Legal Services",
                "Major Group 82: Educational Services",
                "Major Group 83: Social Services",
                "Major Group 84: Museums, Art Galleries, And Botanical And Zoological Gardens",
                "Major Group 86: Membership Organizations",
                "Major Group 87: Engineering, Accounting, Research, Management, And Related Services",
                "Major Group 88: Private Households",
                "Major Group 89: Miscellaneous Services"
            ]
        },
        {
            "division": "J: Public Administration",
            "majorGroups": [
                "Major Group 91: Executive, Legislative, And General Government, Except Finance",
                "Major Group 92: Justice, Public Order, And Safety",
                "Major Group 93: Public Finance, Taxation, And Monetary Policy",
                "Major Group 94: Administration Of Human Resource Programs",
                "Major Group 95: Administration Of Environmental Quality And Housing Programs",
                "Major Group 96: Administration Of Economic Programs",
                "Major Group 97: National Security And International Affairs"
            ]
        },
        {
            "division": "K: Nonclassifiable Establishments",
            "majorGroups": [
                "Major Group 99: Nonclassifiable Establishments"
            ]
        }
    ]

    industry_taxonomy_sci_prompt = {
        "prompt": f"based on the Standard Industrial Classification (SIC) system {industry_taxonomy_sci}, "
                  f"identify industrial division and majorGroup",
        "output": {
            "primary_division": "Division Name",
            "primary_reasoning": "A brief sentence explaining why this classification fits, referencing keywords from the abstract.",
            "secondary_division": "Division Name",
            "secondary_reasoning": "A brief sentence explaining why this classification fits, referencing keywords from the abstract."
        }
    }


