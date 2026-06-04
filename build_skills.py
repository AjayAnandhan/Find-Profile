import sqlite3
import json
import re
from collections import Counter

conn = sqlite3.connect(
    "candidate.db"
)

cursor = conn.cursor()

cursor.execute(
    """
    SELECT resume_text
    FROM candidates
    """
)

rows = cursor.fetchall()

conn.close()

# ----------------------------
# Known Technologies
# ----------------------------

TECH_KEYWORDS = [

    # Cloud
    "aws",
    "azure",
    "gcp",

    # DevOps
    "terraform",
    "ansible",
    "chef",
    "puppet",
    "docker",
    "kubernetes",
    "openshift",
    "jenkins",
    "argocd",
    "helm",

    # Programming
    "python",
    "java",
    "c#",
    "golang",
    "nodejs",
    "javascript",
    "typescript",

    # Data
    "spark",
    "databricks",
    "snowflake",
    "airflow",
    "hadoop",
    "kafka",

    # CRM / ERP
    "salesforce",
    "netsuite",
    "servicenow",
    "pega",
    "guidewire",
    "mulesoft",

    # Frontend
    "react",
    "angular",
    "vue",

    # Database
    "oracle",
    "mysql",
    "postgresql",
    "mongodb",
    "sql server",

    # AI
    "machine learning",
    "generative ai",
    "llm",
    "ml"
    "ai",    
    "langchain",
    "rag",
    "openai",
    "cisco",
    "nexus",
    "catalyst",
    "bgp",
    "ospf",
    "eigrp",
    "mpls",
    "sdwan",
    "vpn",
    "netscaler",
    "citrix adc"
]

counter = Counter()

for row in rows:

    text = row[0]

    if not text:
        continue

    text = text.lower()

    for tech in TECH_KEYWORDS:

        if tech in text:

            counter[tech] += 1

# ----------------------------
# Save
# ----------------------------

with open(
    "skills.json",
    "w"
) as f:

    json.dump(
        dict(counter),
        f,
        indent=4
    )

print(
    f"Found {len(counter)} technologies"
)