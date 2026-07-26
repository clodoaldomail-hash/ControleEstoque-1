import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

# Caminhos dos bancos
ACCDB_PATH = os.path.join(BASE_DIR, "ControleEstoque.accdb")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "ControleEstoque.db")

IS_SQLITE = True
pyodbc = None

# Tenta carregar pyodbc e MS Access se estiver em ambiente Windows com driver instalado
try:
    import pyodbc as pyodbc_module
    pyodbc = pyodbc_module
    conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={ACCDB_PATH};"
    test_conn = pyodbc.connect(conn_str, autocommit=True)
    test_conn.close()
    IS_SQLITE = False
    print("[BANCO] Usando banco de dados MS Access (.accdb)")
except Exception:
    IS_SQLITE = True
    print("[BANCO] Usando banco de dados SQLite (.db) para ambiente de Nuvem")

def get_db_connection():
    """Retorna uma conexão ativa com o banco de dados (SQLite ou Access)."""
    if IS_SQLITE:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={ACCDB_PATH};"
        return pyodbc.connect(conn_str, autocommit=True)

def init_db():
    """Inicializa tabelas e dados padrões caso não existam."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if IS_SQLITE:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_UnidadesOperacionais (
                id_unidade INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_unidade TEXT NOT NULL,
                endereco TEXT,
                cnpj TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_Usuarios (
                id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                nome_usuario TEXT NOT NULL,
                nivel_acesso TEXT DEFAULT 'Operador',
                id_unidade INTEGER,
                status_aprovacao TEXT DEFAULT 'Pendente'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_Categorias (
                id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_categoria TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_Fornecedores (
                id_fornecedor INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_fornecedor TEXT NOT NULL,
                cnpj_cpf TEXT,
                telefone TEXT,
                email TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_Produtos (
                id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras TEXT,
                nome_produto TEXT NOT NULL,
                id_categoria INTEGER,
                id_fornecedor INTEGER,
                id_unidade INTEGER,
                estoque_minimo INTEGER DEFAULT 5,
                preco_custo REAL DEFAULT 0,
                preco_venda REAL DEFAULT 0,
                data_cadastro TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tbl_Movimentacoes (
                id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
                id_produto INTEGER NOT NULL,
                tipo_movimentacao TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                valor_unitario REAL DEFAULT 0,
                data_movimentacao TEXT,
                observacao TEXT,
                id_unidade INTEGER
            )
        """)

        # Dados Padrões para SQLite se vazios
        cursor.execute("SELECT COUNT(*) FROM tbl_UnidadesOperacionais")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO tbl_UnidadesOperacionais (nome_unidade, endereco, cnpj)
                VALUES ('Unidade Matriz', 'Av. Principal, 1000 - Centro', '00.000.000/0001-00')
            """)

        cursor.execute("SELECT COUNT(*) FROM tbl_Usuarios")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO tbl_Usuarios (usuario, senha, nome_usuario, nivel_acesso, id_unidade, status_aprovacao)
                VALUES ('admin', 'admin123', 'Administrador do Sistema', 'Administrador', 1, 'Aprovado')
            """)

        cursor.execute("SELECT COUNT(*) FROM tbl_Categorias")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO tbl_Categorias (nome_categoria) VALUES ('Eletrônicos')")
            cursor.execute("INSERT INTO tbl_Categorias (nome_categoria) VALUES ('Escritório')")
            cursor.execute("INSERT INTO tbl_Categorias (nome_categoria) VALUES ('Informática')")

        cursor.execute("SELECT COUNT(*) FROM tbl_Fornecedores")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO tbl_Fornecedores (nome_fornecedor, cnpj_cpf, telefone, email)
                VALUES ('Tech Brasil LTDA', '12.345.678/0001-90', '(11) 98888-7777', 'contato@techbrasil.com')
            """)

        conn.commit()
        conn.close()

    else:
        # Access DB Init
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

        conn.close()

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
    if IS_SQLITE: conn.commit()
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
    if IS_SQLITE: conn.commit()
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
    
    cursor.execute("SELECT id_usuario FROM tbl_Usuarios WHERE usuario = ?", (usuario,))
    if cursor.fetchone():
        conn.close()
        raise Exception("Nome de usuário já está em uso!")
        
    cursor.execute("""
        INSERT INTO tbl_Usuarios (usuario, senha, nome_usuario, nivel_acesso, id_unidade, status_aprovacao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (usuario, senha, nome_usuario, nivel_acesso, id_unidade, status_aprovacao))
    if IS_SQLITE: conn.commit()
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
    if IS_SQLITE: conn.commit()
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
    if IS_SQLITE: conn.commit()
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
    if IS_SQLITE: conn.commit()
    conn.close()
    return True

# --- CATEGORIAS E FORNECEDORES ---

def listar_categorias():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_categoria, nome_categoria FROM tbl_Categorias ORDER BY nome_categoria ASC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id_categoria": r[0], "nome_categoria": r[1]}
        for r in rows
    ]

def cadastrar_categoria(nome_categoria):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tbl_Categorias (nome_categoria) VALUES (?)", (nome_categoria,))
    if IS_SQLITE: conn.commit()
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
    if IS_SQLITE: conn.commit()
    conn.close()
    return True

# --- PRODUTOS & SALDO DE ESTOQUE ---

def calcular_estoque_produto(id_produto, id_unidade=None, cursor=None):
    """Calcula o saldo atual de estoque de um produto para uma unidade específica ou geral."""
    close_conn = False
    if cursor is None:
        conn = get_db_connection()
        cursor = conn.cursor()
        close_conn = True

    if id_unidade:
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN tipo_movimentacao = 'ENTRADA' THEN quantidade ELSE 0 END) AS total_entradas,
                SUM(CASE WHEN tipo_movimentacao = 'SAIDA' THEN quantidade ELSE 0 END) AS total_saidas
            FROM tbl_Movimentacoes
            WHERE id_produto = ? AND id_unidade = ?
        """, (id_produto, id_unidade))
    else:
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN tipo_movimentacao = 'ENTRADA' THEN quantidade ELSE 0 END) AS total_entradas,
                SUM(CASE WHEN tipo_movimentacao = 'SAIDA' THEN quantidade ELSE 0 END) AS total_saidas
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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
    
    if IS_SQLITE: conn.commit()
    conn.close()
    return True

def excluir_produto(id_produto):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tbl_Movimentacoes WHERE id_produto = ?", (id_produto,))
    cursor.execute("DELETE FROM tbl_Produtos WHERE id_produto = ?", (id_produto,))
    if IS_SQLITE: conn.commit()
    conn.close()
    return True

# --- MOVIMENTAÇÕES DE ESTOQUE ---

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

    dt_str = str(data_movimentacao) if data_movimentacao else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO tbl_Movimentacoes (id_produto, tipo_movimentacao, quantidade, valor_unitario, data_movimentacao, observacao, id_unidade)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (id_produto, tipo_movimentacao, quantidade, valor_unitario, dt_str, observacao, id_unidade))

    if IS_SQLITE: conn.commit()
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

    if IS_SQLITE:
        query = f"""
            SELECT m.id_movimentacao, m.id_produto, p.nome_produto, m.tipo_movimentacao,
                   m.quantidade, m.valor_unitario, m.data_movimentacao, m.observacao, m.id_unidade, u.nome_unidade
            FROM (tbl_Movimentacoes m
            INNER JOIN tbl_Produtos p ON m.id_produto = p.id_produto)
            LEFT JOIN tbl_UnidadesOperacionais u ON m.id_unidade = u.id_unidade
            {where_clause}
            ORDER BY m.data_movimentacao DESC, m.id_movimentacao DESC
            LIMIT {limit}
        """
    else:
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
