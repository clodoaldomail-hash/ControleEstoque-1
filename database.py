import os
import pyodbc
from datetime import datetime

# Definir caminho do banco de dados MS Access (.accdb)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

# Tenta encontrar o arquivo accdb na pasta atual ou na pasta pai
DB_PATH = os.path.join(BASE_DIR, "ControleEstoque.accdb")
if not os.path.exists(DB_PATH) and os.path.exists(os.path.join(PARENT_DIR, "ControleEstoque.accdb")):
    DB_PATH = os.path.join(PARENT_DIR, "ControleEstoque.accdb")

CONN_STR = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_PATH};"

def get_db_connection():
    """Retorna uma conexão ativa com o banco Access pyodbc."""
    if not os.path.exists(DB_PATH):
        init_db()
    return pyodbc.connect(CONN_STR, autocommit=True)

def init_db():
    """Verifica e inicializa o banco de dados e as tabelas se necessário."""
    try:
        if not os.path.exists(DB_PATH):
            import win32com.client
            cat = win32com.client.Dispatch("ADOX.Catalog")
            cat.Create(f"Provider=Microsoft.ACE.OLEDB.12.0;Data Source={DB_PATH};")
            cat = None

        conn = pyodbc.connect(CONN_STR, autocommit=True)
        cursor = conn.cursor()

        # 1. Criar tabela de Unidades Operacionais
        try:
            cursor.execute("SELECT 1 FROM tbl_UnidadesOperacionais")
        except:
            cursor.execute("""
                CREATE TABLE tbl_UnidadesOperacionais (
                    id_unidade AUTOINCREMENT PRIMARY KEY,
                    nome_unidade VARCHAR(150) NOT NULL,
                    endereco VARCHAR(255),
                    cnpj VARCHAR(30)
                )
            """)
            cursor.execute("""
                INSERT INTO tbl_UnidadesOperacionais (nome_unidade, endereco, cnpj)
                VALUES ('Unidade Matriz', 'Av. Principal, 1000 - Centro', '00.000.000/0001-00')
            """)

        # 2. Criar tabela de usuários
        try:
            cursor.execute("SELECT 1 FROM tbl_Usuarios")
        except:
            cursor.execute("""
                CREATE TABLE tbl_Usuarios (
                    id_usuario AUTOINCREMENT PRIMARY KEY,
                    usuario VARCHAR(50) NOT NULL,
                    senha VARCHAR(100) NOT NULL,
                    nome_usuario VARCHAR(100) NOT NULL,
                    nivel_acesso VARCHAR(30) DEFAULT 'Operador',
                    id_unidade INTEGER,
                    status_aprovacao VARCHAR(20) DEFAULT 'Pendente'
                )
            """)
            cursor.execute("""
                INSERT INTO tbl_Usuarios (usuario, senha, nome_usuario, nivel_acesso, id_unidade, status_aprovacao)
                VALUES ('admin', 'admin123', 'Administrador do Sistema', 'Administrador', 1, 'Aprovado')
            """)

        # Migração de colunas para tbl_Usuarios se a tabela já existia sem elas
        try:
            cursor.execute("ALTER TABLE tbl_Usuarios ADD COLUMN id_unidade INTEGER")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE tbl_Usuarios ADD COLUMN status_aprovacao VARCHAR(20)")
        except:
            pass

        # Garantir que admin esteja Aprovado e na Unidade 1
        try:
            cursor.execute("UPDATE tbl_Usuarios SET status_aprovacao = 'Aprovado', id_unidade = 1 WHERE usuario = 'admin'")
            cursor.execute("UPDATE tbl_Usuarios SET status_aprovacao = 'Aprovado' WHERE status_aprovacao IS NULL")
            cursor.execute("UPDATE tbl_Usuarios SET id_unidade = 1 WHERE id_unidade IS NULL")
        except Exception as e:
            print(f"Aviso atualização colunas usuarios: {e}")

        # 3. Criar tabela de categorias
        try:
            cursor.execute("SELECT 1 FROM tbl_Categorias")
        except:
            cursor.execute("""
                CREATE TABLE tbl_Categorias (
                    id_categoria AUTOINCREMENT PRIMARY KEY,
                    nome_categoria VARCHAR(100) NOT NULL
                )
            """)
            cursor.execute("INSERT INTO tbl_Categorias (nome_categoria) VALUES ('Eletrônicos')")
            cursor.execute("INSERT INTO tbl_Categorias (nome_categoria) VALUES ('Escritório')")
            cursor.execute("INSERT INTO tbl_Categorias (nome_categoria) VALUES ('Informática')")

        # 4. Criar tabela de fornecedores
        try:
            cursor.execute("SELECT 1 FROM tbl_Fornecedores")
        except:
            cursor.execute("""
                CREATE TABLE tbl_Fornecedores (
                    id_fornecedor AUTOINCREMENT PRIMARY KEY,
                    nome_fornecedor VARCHAR(150) NOT NULL,
                    cnpj_cpf VARCHAR(20),
                    telefone VARCHAR(20),
                    email VARCHAR(100)
                )
            """)
            cursor.execute("""
                INSERT INTO tbl_Fornecedores (nome_fornecedor, cnpj_cpf, telefone, email)
                VALUES ('Tech Brasil LTDA', '12.345.678/0001-90', '(11) 98888-7777', 'contato@techbrasil.com')
            """)

        # 5. Criar tabela de produtos
        try:
            cursor.execute("SELECT 1 FROM tbl_Produtos")
        except:
            cursor.execute("""
                CREATE TABLE tbl_Produtos (
                    id_produto AUTOINCREMENT PRIMARY KEY,
                    codigo_barras VARCHAR(50),
                    nome_produto VARCHAR(150) NOT NULL,
                    id_categoria INTEGER,
                    id_fornecedor INTEGER,
                    id_unidade INTEGER,
                    estoque_minimo INTEGER DEFAULT 5,
                    preco_custo CURRENCY DEFAULT 0,
                    preco_venda CURRENCY DEFAULT 0,
                    data_cadastro DATETIME
                )
            """)

        try:
            cursor.execute("ALTER TABLE tbl_Produtos ADD COLUMN id_unidade INTEGER")
        except:
            pass

        # 6. Criar tabela de movimentações
        try:
            cursor.execute("SELECT 1 FROM tbl_Movimentacoes")
        except:
            cursor.execute("""
                CREATE TABLE tbl_Movimentacoes (
                    id_movimentacao AUTOINCREMENT PRIMARY KEY,
                    id_produto INTEGER NOT NULL,
                    tipo_movimentacao VARCHAR(10) NOT NULL,
                    quantidade INTEGER NOT NULL,
                    valor_unitario CURRENCY DEFAULT 0,
                    data_movimentacao DATETIME,
                    observacao MEMO,
                    id_unidade INTEGER
                )
            """)

        try:
            cursor.execute("ALTER TABLE tbl_Movimentacoes ADD COLUMN id_unidade INTEGER")
        except:
            pass

        conn.close()
    except Exception as e:
        print(f"Erro na inicialização do banco MS Access: {e}")

# --- UNIDADES OPERACIONAIS ---

def listar_unidades():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_unidade, nome_unidade, endereco, cnpj FROM tbl_UnidadesOperacionais ORDER BY nome_unidade ASC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id_unidade": r[0],
            "nome_unidade": r[1],
            "endereco": r[2] or "",
            "cnpj": r[3] or ""
        }
        for r in rows
    ]

def cadastrar_unidade(nome_unidade, endereco="", cnpj=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tbl_UnidadesOperacionais (nome_unidade, endereco, cnpj)
        VALUES (?, ?, ?)
    """, (nome_unidade, endereco, cnpj))
    conn.close()
    return True

def atualizar_unidade(id_unidade, nome_unidade, endereco="", cnpj=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tbl_UnidadesOperacionais
        SET nome_unidade = ?, endereco = ?, cnpj = ?
        WHERE id_unidade = ?
    """, (nome_unidade, endereco, cnpj, id_unidade))
    conn.close()
    return True

def obter_unidade_por_id(id_unidade):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_unidade, nome_unidade, endereco, cnpj FROM tbl_UnidadesOperacionais WHERE id_unidade = ?", (id_unidade,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id_unidade": row[0],
            "nome_unidade": row[1],
            "endereco": row[2] or "",
            "cnpj": row[3] or ""
        }
    return None

# --- AUTENTICAÇÃO E USUÁRIOS ---

def autenticar_usuario(usuario, senha):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id_usuario, u.usuario, u.senha, u.nome_usuario, u.nivel_acesso, u.id_unidade, u.status_aprovacao, un.nome_unidade
        FROM tbl_Usuarios u
        LEFT JOIN tbl_UnidadesOperacionais un ON u.id_unidade = un.id_unidade
        WHERE u.usuario = ? AND u.senha = ?
    """, (usuario, senha))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        status = row[6] or "Aprovado"
        if status != "Aprovado":
            raise Exception("Sua conta aguarda aprovação do administrador.")
        
        return {
            "id_usuario": row[0],
            "usuario": row[1],
            "nome_usuario": row[3],
            "nivel_acesso": row[4],
            "id_unidade": row[5],
            "status_aprovacao": status,
            "nome_unidade": row[7] or "Não Atrelado"
        }
    return None

def cadastrar_usuario(usuario, senha, nome_usuario, nivel_acesso="Operador", id_unidade=None, status_aprovacao="Pendente"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se usuário já existe
    cursor.execute("SELECT id_usuario FROM tbl_Usuarios WHERE usuario = ?", (usuario,))
    if cursor.fetchone():
        conn.close()
        raise Exception("Nome de usuário já está em uso!")
        
    cursor.execute("""
        INSERT INTO tbl_Usuarios (usuario, senha, nome_usuario, nivel_acesso, id_unidade, status_aprovacao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (usuario, senha, nome_usuario, nivel_acesso, id_unidade, status_aprovacao))
    conn.close()
    return True

def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id_usuario, u.usuario, u.nome_usuario, u.nivel_acesso, u.status_aprovacao, u.id_unidade, un.nome_unidade
        FROM tbl_Usuarios u
        LEFT JOIN tbl_UnidadesOperacionais un ON u.id_unidade = un.id_unidade
        ORDER BY u.nome_usuario ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id_usuario": r[0],
            "usuario": r[1],
            "nome_usuario": r[2],
            "nivel_acesso": r[3],
            "status_aprovacao": r[4] or "Aprovado",
            "id_unidade": r[5],
            "nome_unidade": r[6] or "Sem Unidade"
        }
        for r in rows
    ]

def aprovar_usuario(id_usuario, id_unidade, nivel_acesso="Operador"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tbl_Usuarios
        SET status_aprovacao = 'Aprovado', id_unidade = ?, nivel_acesso = ?
        WHERE id_usuario = ?
    """, (id_unidade, nivel_acesso, id_usuario))
    conn.close()
    return True

def atualizar_usuario(id_usuario, id_unidade, nivel_acesso="Operador"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tbl_Usuarios
        SET id_unidade = ?, nivel_acesso = ?
        WHERE id_usuario = ?
    """, (id_unidade, nivel_acesso, id_usuario))
    conn.close()
    return True

def rejeitar_usuario(id_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tbl_Usuarios
        SET status_aprovacao = 'Rejeitado'
        WHERE id_usuario = ?
    """, (id_usuario,))
    conn.close()
    return True

# --- CATEGORIAS E FORNECEDORES ---

def listar_categorias():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_categoria, nome_categoria FROM tbl_Categorias ORDER BY nome_categoria ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id_categoria": r[0], "nome_categoria": r[1]} for r in rows]

def cadastrar_categoria(nome_categoria):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tbl_Categorias (nome_categoria) VALUES (?)", (nome_categoria,))
    conn.close()
    return True

def listar_fornecedores():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_fornecedor, nome_fornecedor, cnpj_cpf, telefone, email FROM tbl_Fornecedores ORDER BY nome_fornecedor ASC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id_fornecedor": r[0], "nome_fornecedor": r[1], "cnpj_cpf": r[2], "telefone": r[3], "email": r[4]}
        for r in rows
    ]

def cadastrar_fornecedor(nome, cnpj_cpf="", telefone="", email=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tbl_Fornecedores (nome_fornecedor, cnpj_cpf, telefone, email)
        VALUES (?, ?, ?, ?)
    """, (nome, cnpj_cpf, telefone, email))
    conn.close()
    return True

# --- PRODUTOS & SALDO DE ESTOQUE ---

def calcular_estoque_produto(id_produto, id_unidade=None, cursor=None):
    """Calcula o saldo atual de estoque de um produto para uma unidade específica ou geral (Soma Entradas - Soma Saídas)."""
    close_conn = False
    if cursor is None:
        conn = get_db_connection()
        cursor = conn.cursor()
        close_conn = True

    if id_unidade:
        cursor.execute("""
            SELECT 
                SUM(IIF(tipo_movimentacao = 'ENTRADA', quantidade, 0)) AS total_entradas,
                SUM(IIF(tipo_movimentacao = 'SAIDA', quantidade, 0)) AS total_saidas
            FROM tbl_Movimentacoes
            WHERE id_produto = ? AND id_unidade = ?
        """, (id_produto, id_unidade))
    else:
        cursor.execute("""
            SELECT 
                SUM(IIF(tipo_movimentacao = 'ENTRADA', quantidade, 0)) AS total_entradas,
                SUM(IIF(tipo_movimentacao = 'SAIDA', quantidade, 0)) AS total_saidas
            FROM tbl_Movimentacoes
            WHERE id_produto = ?
        """, (id_produto,))
    
    row = cursor.fetchone()
    total_entradas = row[0] if row and row[0] is not None else 0
    total_saidas = row[1] if row and row[1] is not None else 0
    estoque_atual = total_entradas - total_saidas

    if close_conn:
        conn.close()
        
    return estoque_atual

def listar_produtos(filtro_busca="", id_categoria=None, id_unidade=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT p.id_produto, p.codigo_barras, p.nome_produto, p.id_categoria, c.nome_categoria,
               p.id_fornecedor, f.nome_fornecedor, p.estoque_minimo, p.preco_custo, p.preco_venda, p.data_cadastro,
               p.id_unidade, u.nome_unidade
        FROM ((tbl_Produtos p
        LEFT JOIN tbl_Categorias c ON p.id_categoria = c.id_categoria)
        LEFT JOIN tbl_Fornecedores f ON p.id_fornecedor = f.id_fornecedor)
        LEFT JOIN tbl_UnidadesOperacionais u ON p.id_unidade = u.id_unidade
        WHERE 1=1
    """
    params = []

    if filtro_busca:
        sql += " AND (p.nome_produto LIKE ? OR p.codigo_barras LIKE ?)"
        params.extend([f"%{filtro_busca}%", f"%{filtro_busca}%"])
        
    if id_categoria:
        sql += " AND p.id_categoria = ?"
        params.append(id_categoria)

    if id_unidade:
        sql += " AND (p.id_unidade = ? OR p.id_unidade IS NULL)"
        params.append(id_unidade)

    sql += " ORDER BY p.nome_produto ASC"
    cursor.execute(sql, params)
    rows = cursor.fetchall()

    produtos = []
    for r in rows:
        prod_id = r[0]
        estoque_atual = calcular_estoque_produto(prod_id, id_unidade=id_unidade, cursor=cursor)
        estoque_min = r[7] if r[7] is not None else 0
        
        status = "Normal"
        if estoque_atual <= 0:
            status = "Zerado"
        elif estoque_atual <= estoque_min:
            status = "Baixo"

        produtos.append({
            "id_produto": prod_id,
            "codigo_barras": r[1] or "",
            "nome_produto": r[2],
            "id_categoria": r[3],
            "nome_categoria": r[4] or "Sem Categoria",
            "id_fornecedor": r[5],
            "nome_fornecedor": r[6] or "Sem Fornecedor",
            "estoque_minimo": estoque_min,
            "preco_custo": float(r[8]) if r[8] else 0.0,
            "preco_venda": float(r[9]) if r[9] else 0.0,
            "data_cadastro": str(r[10]) if r[10] else "",
            "id_unidade": r[11],
            "nome_unidade": r[12] or "Sem Unidade",
            "estoque_atual": estoque_atual,
            "status_estoque": status
        })

    conn.close()
    return produtos

def obter_produto_por_id(id_produto, id_unidade=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_produto, codigo_barras, nome_produto, id_categoria, id_fornecedor,
               estoque_minimo, preco_custo, preco_venda, id_unidade
        FROM tbl_Produtos
        WHERE id_produto = ?
    """, (id_produto,))
    r = cursor.fetchone()
    if not r:
        conn.close()
        return None

    estoque_atual = calcular_estoque_produto(id_produto, id_unidade=id_unidade, cursor=cursor)
    conn.close()

    return {
        "id_produto": r[0],
        "codigo_barras": r[1] or "",
        "nome_produto": r[2],
        "id_categoria": r[3],
        "id_fornecedor": r[4],
        "estoque_minimo": r[5] or 0,
        "preco_custo": float(r[6]) if r[6] else 0.0,
        "preco_venda": float(r[7]) if r[7] else 0.0,
        "id_unidade": r[8],
        "estoque_atual": estoque_atual
    }

def salvar_produto(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()

    id_produto = data.get("id_produto")
    codigo_barras = data.get("codigo_barras", "")
    nome_produto = data.get("nome_produto")
    id_categoria = data.get("id_categoria") or None
    id_fornecedor = data.get("id_fornecedor") or None
    id_unidade = data.get("id_unidade") or None
    estoque_minimo = int(data.get("estoque_minimo") or 5)
    preco_custo = float(data.get("preco_custo") or 0.0)
    preco_venda = float(data.get("preco_venda") or 0.0)

    if id_produto:
        cursor.execute("""
            UPDATE tbl_Produtos
            SET codigo_barras = ?, nome_produto = ?, id_categoria = ?, id_fornecedor = ?,
                estoque_minimo = ?, preco_custo = ?, preco_venda = ?, id_unidade = ?
            WHERE id_produto = ?
        """, (codigo_barras, nome_produto, id_categoria, id_fornecedor, estoque_minimo, preco_custo, preco_venda, id_unidade, id_produto))
    else:
        cursor.execute("""
            INSERT INTO tbl_Produtos (codigo_barras, nome_produto, id_categoria, id_fornecedor, estoque_minimo, preco_custo, preco_venda, data_cadastro, id_unidade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (codigo_barras, nome_produto, id_categoria, id_fornecedor, estoque_minimo, preco_custo, preco_venda, now, id_unidade))
    
    conn.close()
    return True

def excluir_produto(id_produto):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tbl_Movimentacoes WHERE id_produto = ?", (id_produto,))
    cursor.execute("DELETE FROM tbl_Produtos WHERE id_produto = ?", (id_produto,))
    conn.close()
    return True

# --- MOVIMENTAÇÕES DE ESTOQUE (ENTRADA E SAÍDA) ---

def registrar_movimentacao(id_produto, tipo_movimentacao, quantidade, valor_unitario, observacao="", data_movimentacao=None, id_unidade=None):
    quantidade = int(quantidade)
    valor_unitario = float(valor_unitario)
    tipo_movimentacao = tipo_movimentacao.upper()

    if tipo_movimentacao not in ["ENTRADA", "SAIDA"]:
        raise Exception("Tipo de movimentação inválido! Use ENTRADA ou SAIDA.")

    if quantidade <= 0:
        raise Exception("A quantidade deve ser maior que zero!")

    conn = get_db_connection()
    cursor = conn.cursor()

    if tipo_movimentacao == "SAIDA":
        estoque_atual = calcular_estoque_produto(id_produto, id_unidade=id_unidade, cursor=cursor)
        if quantidade > estoque_atual:
            conn.close()
            msg_unid = " nesta unidade" if id_unidade else ""
            raise Exception(f"Estoque insuficiente{msg_unid}! Saldo disponível: {estoque_atual} unidade(s). Tentativa de saída: {quantidade}.")

    if data_movimentacao:
        try:
            if "T" in str(data_movimentacao):
                dt_obj = datetime.strptime(str(data_movimentacao), "%Y-%m-%dT%H:%M")
            else:
                dt_obj = datetime.strptime(str(data_movimentacao), "%Y-%m-%d %H:%M:%S")
        except:
            dt_obj = datetime.now()
    else:
        dt_obj = datetime.now()

    cursor.execute("""
        INSERT INTO tbl_Movimentacoes (id_produto, tipo_movimentacao, quantidade, valor_unitario, data_movimentacao, observacao, id_unidade)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (id_produto, tipo_movimentacao, quantidade, valor_unitario, dt_obj, observacao, id_unidade))

    conn.close()
    return True

def listar_movimentacoes(limit=100, id_unidade=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    where_clause = ""
    params = []
    if id_unidade:
        where_clause = " WHERE m.id_unidade = ?"
        params = [id_unidade]

    query = f"""
        SELECT TOP {limit} m.id_movimentacao, m.id_produto, p.nome_produto, m.tipo_movimentacao,
               m.quantidade, m.valor_unitario, m.data_movimentacao, m.observacao, m.id_unidade, u.nome_unidade
        FROM (tbl_Movimentacoes m
        INNER JOIN tbl_Produtos p ON m.id_produto = p.id_produto)
        LEFT JOIN tbl_UnidadesOperacionais u ON m.id_unidade = u.id_unidade
        {where_clause}
        ORDER BY m.data_movimentacao DESC, m.id_movimentacao DESC
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id_movimentacao": r[0],
            "id_produto": r[1],
            "nome_produto": r[2],
            "tipo_movimentacao": r[3],
            "quantidade": r[4],
            "valor_unitario": float(r[5]) if r[5] else 0.0,
            "data_movimentacao": str(r[6]) if r[6] else "",
            "observacao": r[7] or "",
            "id_unidade": r[8],
            "nome_unidade": r[9] or "Sem Unidade"
        }
        for r in rows
    ]

# --- DASHBOARD & METRICAS ---

def obter_dados_dashboard(id_unidade=None):
    produtos = listar_produtos(id_unidade=id_unidade)
    
    total_produtos = len(produtos)
    total_estoque_itens = sum(p["estoque_atual"] for p in produtos)
    valor_total_custo = sum(p["estoque_atual"] * p["preco_custo"] for p in produtos if p["estoque_atual"] > 0)
    valor_total_venda = sum(p["estoque_atual"] * p["preco_venda"] for p in produtos if p["estoque_atual"] > 0)
    
    produtos_baixo_estoque = [p for p in produtos if p["status_estoque"] in ["Baixo", "Zerado"]]
    
    movimentacoes_recentes = listar_movimentacoes(limit=10, id_unidade=id_unidade)

    return {
        "total_produtos": total_produtos,
        "total_estoque_itens": total_estoque_itens,
        "valor_total_custo": valor_total_custo,
        "valor_total_venda": valor_total_venda,
        "qtd_baixo_estoque": len(produtos_baixo_estoque),
        "produtos_baixo_estoque": produtos_baixo_estoque[:5],
        "movimentacoes_recentes": movimentacoes_recentes
    }
