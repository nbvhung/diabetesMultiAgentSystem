"""Generate local ignored Compose secrets; never replace existing settings."""
from pathlib import Path
import secrets
import argparse

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--path',type=Path,default=ROOT/'.env.compose');args=parser.parse_args()
    with args.path.open('x',encoding='utf-8') as output:
        output.write('POSTGRES_USER=diabetes_demo\nPOSTGRES_DB=diabetes_mas\nPOSTGRES_PASSWORD='+secrets.token_hex(24)+'\nNEO4J_PASSWORD='+secrets.token_hex(24)+'\nGROQ_API_KEY=\nGROQ_MODEL=openai/gpt-oss-20b\nDIABETES_LLM_ENABLED=true\nDEMO_PORT=8080\n')
    print('Created local environment file. Add GROQ_API_KEY locally; credentials were not printed.')
