from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
import databases
import sqlalchemy
import re
import random
import asyncio

# Tenta usar UserAgent rotativo, se falhar usa fixo
try:
    from fake_useragent import UserAgent
    ua = UserAgent()
    UA_ATIVO = True
except:
    print("⚠️ AVISO: 'fake-useragent' falhou. Usando User-Agent fixo.")
    UA_ATIVO = False

# --- FUNÇÃO DE CAMUFLAGEM MANUAL (SUBSTITUI A BIBLIOTECA) ---
async def aplicar_stealth(page):
    """
    Injeta scripts JS para esconder que é um robô.
    Baseado nas técnicas do StackOverflow e puppeteer-stealth.
    """
    await page.add_init_script("""
        // 1. Remove a propriedade 'webdriver' que entrega o robô
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // 2. Finge ter plugins (Chrome Headless não tem plugins)
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // 3. Finge ter idiomas
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt']
        });

        // 4. Mascara permissões de notificação (comum em testes de bot)
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );

        // 5. Adiciona objeto window.chrome (faltante em headless)
        window.chrome = { runtime: {} };
    """)

# --- CONFIGURAÇÃO DO BANCO ---
DB_USER = "admin_imob"
DB_PASSWORD = "senha_segura_producao_123"
DB_HOST = "imob_postgres"
DB_PORT = "5432"
DB_NAME = "imobiliaria_db"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

imoveis = sqlalchemy.Table(
    "imoveis_encontrados",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("url_origem", sqlalchemy.String, unique=True),
    sqlalchemy.Column("titulo", sqlalchemy.String),
    sqlalchemy.Column("tipo_negocio", sqlalchemy.String),
    sqlalchemy.Column("tipo_imovel", sqlalchemy.String),
    sqlalchemy.Column("endereco", sqlalchemy.String),
    sqlalchemy.Column("preco", sqlalchemy.Numeric(15, 2)),
    sqlalchemy.Column("area_m2", sqlalchemy.Numeric(10, 2)),
    sqlalchemy.Column("quartos", sqlalchemy.Integer),
    sqlalchemy.Column("banheiros", sqlalchemy.Integer),
    sqlalchemy.Column("vagas", sqlalchemy.Integer),
    sqlalchemy.Column("custo_condominio", sqlalchemy.Numeric(15, 2)),
    sqlalchemy.Column("custo_iptu", sqlalchemy.Numeric(15, 2)),
    sqlalchemy.Column("contato_responsavel", sqlalchemy.String),
    sqlalchemy.Column("features", sqlalchemy.String),
    sqlalchemy.Column("data_captura", sqlalchemy.DateTime, server_default=sqlalchemy.func.now()),
)

app = FastAPI()

class RequestURL(BaseModel):
    url: str

@app.on_event("startup")
async def startup():
    await database.connect()
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# --- HELPER FUNCTIONS ---
def limpar_moeda_br(texto):
    if not texto: return 0.00
    sujo = str(texto).strip()
    limpo = re.sub(r'[^\d,.]', '', sujo)
    if not limpo: return 0.00
    if ',' in limpo:
        limpo = limpo.replace('.', '').replace(',', '.')
    else:
        limpo = limpo.replace('.', '')
    try: return float(limpo)
    except: return 0.00

def extrair_contatos_reais(texto_completo):
    contatos = []
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', texto_completo)
    contatos.extend(emails)
    phones = re.findall(r'(?:(?:\+|00)?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\d{4}|\d{4})[-.\s]?\d{4}', texto_completo)
    validos = [p for p in phones if len(re.sub(r'\D','',p)) >= 10 and not p.startswith("202")]
    contatos.extend(validos)
    uniques = list(set(contatos))
    return ", ".join(uniques[:5]) if uniques else "Verificar no site"

def buscar_valor_por_proximidade(linhas, chaves):
    for i, linha in enumerate(linhas):
        if any(c in linha.lower() for c in chaves):
            nums = re.findall(r'\d+', linha)
            if nums: return int(nums[0])
            if i+1 < len(linhas):
                nx = re.findall(r'^\d+$', linhas[i+1].strip())
                if nx: return int(nx[0])
            if i-1 >= 0:
                pr = re.findall(r'^\d+$', linhas[i-1].strip())
                if pr: return int(pr[0])
    return 0

@app.post("/scrape-imovel")
async def scrape_imovel(request: RequestURL):
    async with async_playwright() as p:
        # User-Agent Rotativo
        agente = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        if UA_ATIVO:
            try: agente = ua.random
            except: pass
            
        print(f"--> V14 (Manual Stealth) em: {request.url}")

        # Inicia com argumentos para remover barras de automação
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = await browser.new_context(
            user_agent=agente,
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR"
        )
        
        page = await context.new_page()
        
        # APLICA A CAMUFLAGEM MANUAL AQUI
        await aplicar_stealth(page)
        
        try:
            # Acessa a página
            await page.goto(request.url, timeout=90000, wait_until="domcontentloaded")
            
            # Simula comportamento humano
            await page.wait_for_timeout(random.randint(2000, 4000))
            try:
                await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                await page.mouse.wheel(0, 300)
            except: pass

            # Verificações de bloqueio
            titulo_pag = await page.title()
            if "Attention Required" in titulo_pag or "Just a moment" in titulo_pag:
                print("!!! BLOQUEIO DETECTADO (Mesmo com Stealth) !!!")
            
            # Extração de dados (V11 logic)
            texto_body = await page.inner_text("body")
            linhas = [l.strip() for l in texto_body.split('\n') if l.strip()]
            texto_completo = "\n".join(linhas)

            preco = 0.00
            condominio = 0.00
            iptu = 0.00
            valores = []
            
            for linha in linhas:
                match = re.search(r"(?:R\$|R\s\$)\s*([\d\.,]+)", linha, re.IGNORECASE)
                if match:
                    val = limpar_moeda_br(match.group(1))
                    if val > 0:
                        low = linha.lower()
                        if "condom" in low or "mensal" in low: condominio = val
                        elif "iptu" in low: iptu = val
                        else: valores.append(val)
            
            is_aluguel = "aluguel" in request.url.lower() or "locacao" in request.url.lower()
            if valores:
                limpos = [v for v in valores if v != condominio and v != iptu]
                if limpos:
                    if is_aluguel:
                        cands = [v for v in limpos if 500 < v < 50000]
                        preco = max(cands) if cands else max(limpos)
                    else:
                        preco = max(limpos)

            quartos = buscar_valor_por_proximidade(linhas, ["quarto", "dormitório", "suíte"])
            banheiros = buscar_valor_por_proximidade(linhas, ["banheiro", "bwc", "banho"])
            vagas = buscar_valor_por_proximidade(linhas, ["vaga", "garagem", "box"])
            
            area = 0.00
            for linha in linhas:
                if "m²" in linha or "area" in linha.lower():
                    m = re.search(r"([\d.,]+)\s*(?:m²|m2|metros)", linha)
                    if m:
                        a = limpar_moeda_br(m.group(1))
                        if 10 < a < 10000: area = a; break

            end_final = "Endereço não visível"
            m_end = re.search(r"(?i)(Rua|Avenida|Av\.|Travessa|Alameda|Praça)\s+([^\n,]+)", texto_completo)
            if m_end:
                cand = m_end.group(0).strip()
                if len(cand) < 100 and "creci" not in cand.lower(): end_final = cand

            tipo_negocio = "Aluguel" if is_aluguel else "Venda"
            tipo_imovel = "Outro"
            if "apartamento" in texto_completo.lower(): tipo_imovel = "Apartamento"
            elif "casa" in texto_completo.lower(): tipo_imovel = "Casa"
            
            contatos = extrair_contatos_reais(texto_completo)
            feats = [f for f in ["Piscina", "Churrasqueira", "Academia", "Elevador", "Portaria"] if f.lower() in texto_completo.lower()]

            dados = {
                "url_origem": request.url,
                "titulo": titulo_pag.strip()[:200],
                "tipo_negocio": tipo_negocio,
                "tipo_imovel": tipo_imovel,
                "endereco": end_final,
                "preco": preco,
                "area_m2": area,
                "quartos": quartos,
                "banheiros": banheiros,
                "vagas": vagas,
                "custo_condominio": condominio,
                "custo_iptu": iptu,
                "contato_responsavel": contatos,
                "features": ", ".join(feats)
            }

            # DB Save
            q = imoveis.select().where(imoveis.c.url_origem == request.url)
            reg = await database.fetch_one(q)
            if reg:
                await database.execute(imoveis.update().where(imoveis.c.url_origem == request.url).values(**dados))
            else:
                await database.execute(imoveis.insert().values(**dados))

            await browser.close()
            return {"status": "Sucesso", "dados": dados}

        except Exception as e:
            if browser: await browser.close()
            print(f"Erro V14: {e}")
            raise HTTPException(status_code=500, detail=str(e))
