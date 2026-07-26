/* ==========================================================================
   LÓGICA PRINCIPAL JAVASCRIPT - CONTROLE DE ESTOQUE MS ACCESS
   ========================================================================== */

let currentUser = null;
let selectedUnitId = null;
let produtosCache = [];
let categoriasCache = [];
let unidadesCache = [];

// Inicialização da aplicação ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    checarSessaoUsuario();
    configurarNavegacao();
});

// --- AUTENTICAÇÃO E SESSÃO ---

function checarSessaoUsuario() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'login' || urlParams.get('logout') === 'true') {
        localStorage.removeItem('stock_user');
        currentUser = null;
        exibirTelaAuth();
        return;
    }

    const savedUser = localStorage.getItem('stock_user');
    if (savedUser) {
        try {
            currentUser = JSON.parse(savedUser);
            iniciarAplicacao();
        } catch (e) {
            localStorage.removeItem('stock_user');
            exibirTelaAuth();
        }
    } else {
        exibirTelaAuth();
    }
}

function toggleAuthMode(mode) {
    const loginBox = document.getElementById('login-box');
    const registerBox = document.getElementById('register-box');
    
    if (mode === 'register') {
        loginBox.classList.remove('active');
        registerBox.classList.add('active');
    } else {
        registerBox.classList.remove('active');
        loginBox.classList.add('active');
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const usuario = document.getElementById('login-usuario').value.trim();
    const senha = document.getElementById('login-senha').value.trim();

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario, senha })
        });
        const data = await response.json();

        if (data.success) {
            currentUser = data.user;
            localStorage.setItem('stock_user', JSON.stringify(currentUser));
            showToast(data.message, 'success');
            iniciarAplicacao();
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Erro ao se conectar ao servidor.', 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const nome_usuario = document.getElementById('reg-nome').value.trim();
    const usuario = document.getElementById('reg-usuario').value.trim();
    const senha = document.getElementById('reg-senha').value.trim();

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome_usuario, usuario, senha })
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            document.getElementById('form-register').reset();
            toggleAuthMode('login');
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Erro ao cadastrar usuário.', 'error');
    }
}

function handleLogout() {
    localStorage.removeItem('stock_user');
    currentUser = null;
    document.getElementById('main-app').classList.add('hidden');
    document.getElementById('auth-screen').classList.remove('hidden');
    showToast('Você saiu do sistema.', 'info');
}

function exibirTelaAuth() {
    document.getElementById('auth-screen').classList.remove('hidden');
    document.getElementById('main-app').classList.add('hidden');
}

async function iniciarAplicacao() {
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('main-app').classList.remove('hidden');

    // Atualizar UI do Usuário no Sidebar
    document.getElementById('user-display-name').textContent = currentUser.nome_usuario;
    document.getElementById('user-display-role').textContent = currentUser.nivel_acesso;
    
    const unitEl = document.getElementById('user-display-unit');
    if (unitEl) {
        unitEl.textContent = currentUser.nome_unidade ? `Unidade: ${currentUser.nome_unidade}` : '';
    }

    // Configurar Seletor Global de Unidades Operacionais
    const selectGlobal = document.getElementById('select-global-unidade');
    if (currentUser.nivel_acesso === 'Administrador') {
        try {
            const resU = await fetch('/api/unidades');
            const dataU = await resU.json();
            if (dataU.success) {
                unidadesCache = dataU.unidades;
                selectGlobal.innerHTML = '<option value="">Todas as Unidades (Visão Global)</option>' +
                    unidadesCache.map(u => `<option value="${u.id_unidade}">${u.nome_unidade}</option>`).join('');
                
                const savedAdminUnit = localStorage.getItem('admin_selected_unit') || '';
                selectGlobal.value = savedAdminUnit;
                selectedUnitId = savedAdminUnit ? parseInt(savedAdminUnit) : null;
                selectGlobal.disabled = false;
            }
        } catch (e) {}
    } else {
        selectedUnitId = currentUser.id_unidade ? parseInt(currentUser.id_unidade) : null;
        if (selectGlobal) {
            selectGlobal.innerHTML = `<option value="${currentUser.id_unidade || ''}">${currentUser.nome_unidade || 'Sua Unidade'}</option>`;
            selectGlobal.disabled = true;
        }
    }

    // Mostrar ou ocultar opções exclusivas de Admin
    const adminElements = document.querySelectorAll('.admin-only');
    adminElements.forEach(el => {
        if (currentUser.nivel_acesso === 'Administrador') {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    });

    if (currentUser.nivel_acesso !== 'Administrador') {
        navegarParaView('view-dashboard');
    }

    // Carregar dados iniciais
    carregarCategoriasEFornecedores();
    carregarDashboard();
    carregarProdutos();
}

function trocarUnidadeAtiva(unitId) {
    if (currentUser && currentUser.nivel_acesso === 'Administrador') {
        selectedUnitId = unitId ? parseInt(unitId) : null;
        localStorage.setItem('admin_selected_unit', unitId || '');
        
        const activeView = document.querySelector('.app-view.active');
        if (activeView) {
            const viewId = activeView.id;
            if (viewId === 'view-dashboard') carregarDashboard();
            if (viewId === 'view-produtos') carregarProdutos();
            if (viewId === 'view-movimentacoes') carregarMovimentacoes();
        }
        showToast(unitId ? 'Filtro atualizado para a unidade selecionada.' : 'Visualizando estoque de todas as unidades.', 'info');
    }
}

// --- NAVEGAÇÃO ENTRE TELAS ---

function configurarNavegacao() {
    const navItems = document.querySelectorAll('.sidebar-nav li');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetViewId = item.getAttribute('data-target');
            if (targetViewId) {
                if (item.classList.contains('admin-only') && currentUser.nivel_acesso !== 'Administrador') {
                    showToast('Apenas administradores podem acessar esta seção.', 'warning');
                    return;
                }
                navItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                navegarParaView(targetViewId);
            }
        });
    });
}

function navegarParaView(viewId) {
    const views = document.querySelectorAll('.app-view');
    views.forEach(v => v.classList.remove('active'));
    
    const targetView = document.getElementById(viewId);
    if (targetView) {
        targetView.classList.add('active');

        const titles = {
            'view-dashboard': 'Dashboard de Estoque',
            'view-produtos': 'Cadastro e Gestão de Produtos',
            'view-movimentacoes': 'Movimentação de Entradas e Saídas',
            'view-cadastros': 'Gestão de Categorias, Fornecedores e Unidades',
            'view-usuarios': 'Usuários e Aprovações'
        };
        document.getElementById('page-title').textContent = titles[viewId] || 'Controle de Estoque';

        if (viewId === 'view-dashboard') carregarDashboard();
        if (viewId === 'view-produtos') carregarProdutos();
        if (viewId === 'view-movimentacoes') carregarMovimentacoes();
        if (viewId === 'view-cadastros') carregarCadastrosGerais();
        if (viewId === 'view-usuarios') carregarUsuarios();
    }
}

// --- DASHBOARD ---

async function carregarDashboard() {
    try {
        let url = '/api/dashboard';
        if (selectedUnitId) {
            url += `?id_unidade=${selectedUnitId}`;
        }

        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            document.getElementById('kpi-total-produtos').textContent = data.total_produtos;
            document.getElementById('kpi-total-itens').textContent = data.total_estoque_itens;
            document.getElementById('kpi-valor-total').textContent = formatarMoeda(data.valor_total_custo);
            document.getElementById('kpi-baixo-estoque').textContent = data.qtd_baixo_estoque;

            const tbodyBaixo = document.getElementById('table-baixo-estoque');
            if (data.produtos_baixo_estoque.length === 0) {
                tbodyBaixo.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhum produto em nível crítico de estoque!</td></tr>';
            } else {
                tbodyBaixo.innerHTML = data.produtos_baixo_estoque.map(p => `
                    <tr>
                        <td><strong>${p.nome_produto}</strong></td>
                        <td>${p.estoque_minimo}</td>
                        <td><strong>${p.estoque_atual}</strong></td>
                        <td><span class="badge ${p.status_estoque === 'Zerado' ? 'badge-danger' : 'badge-warning'}">${p.status_estoque}</span></td>
                    </tr>
                `).join('');
            }

            const tbodyMovs = document.getElementById('table-dash-movs');
            if (data.movimentacoes_recentes.length === 0) {
                tbodyMovs.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Nenhuma movimentação registrada.</td></tr>';
            } else {
                tbodyMovs.innerHTML = data.movimentacoes_recentes.map(m => `
                    <tr>
                        <td><small>${formatarData(m.data_movimentacao)}</small></td>
                        <td>${m.nome_produto}</td>
                        <td><span class="badge ${m.tipo_movimentacao === 'ENTRADA' ? 'badge-success' : 'badge-warning'}">${m.tipo_movimentacao}</span></td>
                        <td><strong>${m.quantidade}</strong></td>
                    </tr>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
    }
}

// --- UNIDADES OPERACIONAIS ---

async function carregarUnidades() {
    try {
        const response = await fetch('/api/unidades');
        const result = await response.json();

        if (result.success) {
            unidadesCache = result.unidades;
            const tbody = document.getElementById('table-unidades-body');
            if (!tbody) return;
            if (unidadesCache.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhuma unidade cadastrada.</td></tr>';
                return;
            }

            tbody.innerHTML = unidadesCache.map(u => `
                <tr>
                    <td>#${u.id_unidade}</td>
                    <td><strong>${u.nome_unidade}</strong></td>
                    <td>${u.endereco || '-'}</td>
                    <td><code>${u.cnpj || '-'}</code></td>
                    <td class="text-right">
                        <button class="btn btn-sm btn-outline" onclick="abrirModalUnidade(${u.id_unidade})" title="Editar">
                            <i class="fa-solid fa-pen"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        showToast('Erro ao carregar unidades operacionais.', 'error');
    }
}

function abrirModalUnidade(id_unidade = null) {
    document.getElementById('form-unidade').reset();
    document.getElementById('unidade-id').value = '';
    document.getElementById('modal-unidade-title').textContent = id_unidade ? 'Editar Unidade Operacional' : 'Cadastrar Unidade Operacional';

    if (id_unidade) {
        const u = unidadesCache.find(x => x.id_unidade == id_unidade);
        if (u) {
            document.getElementById('unidade-id').value = u.id_unidade;
            document.getElementById('unidade-nome').value = u.nome_unidade;
            document.getElementById('unidade-endereco').value = u.endereco;
            document.getElementById('unidade-cnpj').value = u.cnpj;
        }
    }

    document.getElementById('modal-unidade').classList.remove('hidden');
}

async function salvarUnidade(event) {
    event.preventDefault();
    const payload = {
        id_unidade: document.getElementById('unidade-id').value || null,
        nome_unidade: document.getElementById('unidade-nome').value.trim(),
        endereco: document.getElementById('unidade-endereco').value.trim(),
        cnpj: document.getElementById('unidade-cnpj').value.trim()
    };

    try {
        const response = await fetch('/api/unidades', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');
            fecharModal('modal-unidade');
            carregarCadastrosGerais();
            iniciarAplicacao();
        } else {
            showToast(result.message, 'error');
        }
    } catch (e) {
        showToast('Erro ao salvar unidade.', 'error');
    }
}

// --- GESTÃO DE PRODUTOS ---

async function carregarProdutos() {
    const busca = document.getElementById('filter-produto-busca').value;
    const catId = document.getElementById('filter-produto-categoria').value;

    let url = `/api/produtos?busca=${encodeURIComponent(busca)}&categoria_id=${encodeURIComponent(catId)}`;
    if (selectedUnitId) {
        url += `&id_unidade=${selectedUnitId}`;
    }

    try {
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            produtosCache = result.produtos;
            renderizarTabelaProdutos(produtosCache);
        }
    } catch (error) {
        showToast('Erro ao carregar lista de produtos.', 'error');
    }
}

function renderizarTabelaProdutos(produtos) {
    const tbody = document.getElementById('table-produtos-body');
    if (produtos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="text-center text-muted">Nenhum produto cadastrado.</td></tr>';
        return;
    }

    tbody.innerHTML = produtos.map(p => {
        let badgeClass = 'badge-success';
        if (p.status_estoque === 'Baixo') badgeClass = 'badge-warning';
        if (p.status_estoque === 'Zerado') badgeClass = 'badge-danger';

        return `
            <tr>
                <td><code>${p.codigo_barras || '-'}</code></td>
                <td><strong>${p.nome_produto}</strong></td>
                <td>${p.nome_categoria}</td>
                <td>${p.nome_fornecedor}</td>
                <td>${p.nome_unidade || 'Todas'}</td>
                <td>${p.estoque_minimo}</td>
                <td>${formatarMoeda(p.preco_custo)}</td>
                <td>${formatarMoeda(p.preco_venda)}</td>
                <td><strong style="font-size: 15px;">${p.estoque_atual}</strong></td>
                <td><span class="badge ${badgeClass}">${p.status_estoque}</span></td>
                <td class="text-right">
                    ${currentUser.nivel_acesso === 'Administrador' ? `
                    <button class="btn btn-sm btn-outline" onclick="abrirModalProduto(${p.id_produto})" title="Editar">
                        <i class="fa-solid fa-pen"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="excluirProduto(${p.id_produto})" title="Excluir">
                        <i class="fa-solid fa-trash"></i>
                    </button>` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

async function abrirModalProduto(id_produto = null) {
    document.getElementById('form-produto').reset();
    document.getElementById('prod-id').value = '';
    document.getElementById('modal-produto-title').textContent = id_produto ? 'Editar Produto' : 'Cadastrar Novo Produto';

    await carregarCategoriasEFornecedores();

    try {
        const resU = await fetch('/api/unidades');
        const dataU = await resU.json();
        if (dataU.success) {
            const selectU = document.getElementById('prod-unidade');
            selectU.innerHTML = '<option value="">Todas / Padrão</option>' +
                dataU.unidades.map(u => `<option value="${u.id_unidade}">${u.nome_unidade}</option>`).join('');
        }
    } catch (e) {}

    if (id_produto) {
        try {
            let pUrl = `/api/produtos/${id_produto}`;
            if (selectedUnitId) pUrl += `?id_unidade=${selectedUnitId}`;
            const res = await fetch(pUrl);
            const data = await res.json();
            if (data.success) {
                const p = data.produto;
                document.getElementById('prod-id').value = p.id_produto;
                document.getElementById('prod-codigo').value = p.codigo_barras;
                document.getElementById('prod-nome').value = p.nome_produto;
                document.getElementById('prod-categoria').value = p.id_categoria || '';
                document.getElementById('prod-fornecedor').value = p.id_fornecedor || '';
                document.getElementById('prod-unidade').value = p.id_unidade || '';
                document.getElementById('prod-minimo').value = p.estoque_minimo;
                document.getElementById('prod-custo').value = p.preco_custo;
                document.getElementById('prod-venda').value = p.preco_venda;
            }
        } catch (e) {
            showToast('Erro ao carregar dados do produto.', 'error');
        }
    }

    document.getElementById('modal-produto').classList.remove('hidden');
}

async function salvarProduto(event) {
    event.preventDefault();
    const payload = {
        id_produto: document.getElementById('prod-id').value || null,
        codigo_barras: document.getElementById('prod-codigo').value.trim(),
        nome_produto: document.getElementById('prod-nome').value.trim(),
        id_categoria: document.getElementById('prod-categoria').value || null,
        id_fornecedor: document.getElementById('prod-fornecedor').value || null,
        id_unidade: document.getElementById('prod-unidade').value || null,
        estoque_minimo: document.getElementById('prod-minimo').value,
        preco_custo: document.getElementById('prod-custo').value,
        preco_venda: document.getElementById('prod-venda').value
    };

    try {
        const response = await fetch('/api/produtos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');
            fecharModal('modal-produto');
            carregarProdutos();
            carregarDashboard();
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        showToast('Erro ao salvar produto.', 'error');
    }
}

async function excluirProduto(id_produto) {
    if (!confirm('Tem certeza que deseja excluir este produto e todo seu histórico?')) return;

    try {
        const response = await fetch(`/api/produtos/${id_produto}`, { method: 'DELETE' });
        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');
            carregarProdutos();
            carregarDashboard();
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        showToast('Erro ao excluir produto.', 'error');
    }
}

// --- MOVIMENTAÇÕES DE ESTOQUE ---

function getFormattedLocalDateTime() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

async function carregarMovimentacoes() {
    let url = '/api/movimentacoes';
    if (selectedUnitId) {
        url += `?id_unidade=${selectedUnitId}`;
    }

    try {
        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            const tbody = document.getElementById('table-movimentacoes-body');
            if (result.movimentacoes.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Nenhuma movimentação registrada.</td></tr>';
                return;
            }

            tbody.innerHTML = result.movimentacoes.map(m => {
                const total = m.quantidade * m.valor_unitario;
                return `
                    <tr>
                        <td>#${m.id_movimentacao}</td>
                        <td><small>${formatarData(m.data_movimentacao)}</small></td>
                        <td><span class="badge badge-info"><i class="fa-solid fa-building"></i> ${m.nome_unidade || 'Sem Unidade'}</span></td>
                        <td><strong>${m.nome_produto}</strong></td>
                        <td><span class="badge ${m.tipo_movimentacao === 'ENTRADA' ? 'badge-success' : 'badge-warning'}">${m.tipo_movimentacao}</span></td>
                        <td><strong>${m.quantidade}</strong></td>
                        <td>${formatarMoeda(m.valor_unitario)}</td>
                        <td><strong>${formatarMoeda(total)}</strong></td>
                        <td><small class="text-muted">${m.observacao || '-'}</small></td>
                    </tr>
                `;
            }).join('');
        }
    } catch (error) {
        showToast('Erro ao carregar histórico de movimentações.', 'error');
    }
}

async function abrirModalMovimentacao(tipo) {
    document.getElementById('form-movimentacao').reset();
    document.getElementById('mov-tipo').value = tipo;
    
    // Pré-preencher data atual
    document.getElementById('mov-data').value = getFormattedLocalDateTime();

    const title = tipo === 'ENTRADA' ? 'Registrar Nova ENTRADA de Estoque' : 'Registrar Nova SAÍDA de Estoque';
    document.getElementById('modal-movimentacao-title').textContent = title;
    
    const btnSubmit = document.getElementById('btn-submit-mov');
    btnSubmit.className = tipo === 'ENTRADA' ? 'btn btn-primary' : 'btn btn-warning';
    btnSubmit.innerHTML = tipo === 'ENTRADA' ? '<i class="fa-solid fa-circle-plus"></i> Confirmar Entrada' : '<i class="fa-solid fa-circle-minus"></i> Confirmar Saída';

    document.getElementById('mov-saldo-info').classList.add('hidden');

    // Carregar unidades operacionais
    const selectU = document.getElementById('mov-unidade');
    try {
        const resU = await fetch('/api/unidades');
        const dataU = await resU.json();
        if (dataU.success) {
            unidadesCache = dataU.unidades;
            selectU.innerHTML = '<option value="">Selecione a Unidade...</option>' +
                unidadesCache.map(u => `<option value="${u.id_unidade}">${u.nome_unidade}</option>`).join('');
            
            const defaultUnit = selectedUnitId || (currentUser ? currentUser.id_unidade : null);
            if (defaultUnit) {
                selectU.value = defaultUnit;
            }

            if (currentUser.nivel_acesso !== 'Administrador') {
                selectU.value = currentUser.id_unidade;
                selectU.disabled = true;
            } else {
                selectU.disabled = false;
            }
        }
    } catch (e) {}

    await atualizarProdutosPorUnidadeMovimentacao();
    document.getElementById('modal-movimentacao').classList.remove('hidden');
}

async function atualizarProdutosPorUnidadeMovimentacao() {
    const movUnid = document.getElementById('mov-unidade').value;
    const selectProd = document.getElementById('mov-produto');
    document.getElementById('mov-saldo-info').classList.add('hidden');

    try {
        let prodUrl = '/api/produtos';
        if (movUnid) {
            prodUrl += `?id_unidade=${movUnid}`;
        }
        const response = await fetch(prodUrl);
        const data = await response.json();
        if (data.success) {
            produtosCache = data.produtos;
            selectProd.innerHTML = '<option value="">Selecione um produto...</option>' +
                produtosCache.map(p => `<option value="${p.id_produto}">${p.nome_produto} (Saldo na Unidade: ${p.estoque_atual})</option>`).join('');
        }
    } catch (e) {
        showToast('Erro ao carregar produtos para a unidade.', 'error');
    }
}

function atualizarDadosProdutoMovimentacao() {
    const prodId = document.getElementById('mov-produto').value;
    const tipo = document.getElementById('mov-tipo').value;

    if (!prodId) {
        document.getElementById('mov-saldo-info').classList.add('hidden');
        return;
    }

    const prod = produtosCache.find(p => p.id_produto == prodId);
    if (prod) {
        document.getElementById('mov-saldo-qtd').textContent = prod.estoque_atual;
        document.getElementById('mov-saldo-info').classList.remove('hidden');

        const valorInput = document.getElementById('mov-valor');
        if (tipo === 'ENTRADA') {
            valorInput.value = prod.preco_custo || 0;
        } else {
            valorInput.value = prod.preco_venda || 0;
        }
    }
}

async function salvarMovimentacao(event) {
    event.preventDefault();
    const movUnid = document.getElementById('mov-unidade').value;

    if (!movUnid) {
        showToast('Selecione uma Unidade Operacional para esta movimentação.', 'warning');
        return;
    }

    const payload = {
        id_produto: document.getElementById('mov-produto').value,
        tipo_movimentacao: document.getElementById('mov-tipo').value,
        quantidade: document.getElementById('mov-quantidade').value,
        valor_unitario: document.getElementById('mov-valor').value,
        observacao: document.getElementById('mov-obs').value.trim(),
        data_movimentacao: document.getElementById('mov-data').value,
        id_unidade: parseInt(movUnid)
    };

    try {
        const response = await fetch('/api/movimentacoes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');
            fecharModal('modal-movimentacao');
            carregarMovimentacoes();
            carregarProdutos();
            carregarDashboard();
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        showToast('Erro ao registrar movimentação.', 'error');
    }
}

// --- CATEGORIAS, FORNECEDORES & UNIDADES ---

async function carregarCategoriasEFornecedores() {
    try {
        const [resCat, resForn] = await Promise.all([
            fetch('/api/categorias'),
            fetch('/api/fornecedores')
        ]);
        
        const dataCat = await resCat.json();
        const dataForn = await resForn.json();

        if (dataCat.success) {
            categoriasCache = dataCat.categorias;
            const selectProdCat = document.getElementById('prod-categoria');
            const selectFilterCat = document.getElementById('filter-produto-categoria');
            
            const optionsHtml = categoriasCache.map(c => `<option value="${c.id_categoria}">${c.nome_categoria}</option>`).join('');
            if (selectProdCat) selectProdCat.innerHTML = '<option value="">Selecione...</option>' + optionsHtml;
            if (selectFilterCat) selectFilterCat.innerHTML = '<option value="">Todas as Categorias</option>' + optionsHtml;
        }

        if (dataForn.success) {
            const selectForn = document.getElementById('prod-fornecedor');
            if (selectForn) {
                selectForn.innerHTML = '<option value="">Selecione...</option>' +
                    dataForn.fornecedores.map(f => `<option value="${f.id_fornecedor}">${f.nome_fornecedor}</option>`).join('');
            }
        }
    } catch (e) {
        console.error('Erro ao carregar listas de apoio:', e);
    }
}

async function carregarCadastrosGerais() {
    carregarUnidades();
    carregarCategoriasEFornecedores();

    fetch('/api/categorias').then(res => res.json()).then(data => {
        if (data.success) {
            const tbody = document.getElementById('table-categorias-body');
            if (tbody) {
                tbody.innerHTML = data.categorias.map(c => `
                    <tr>
                        <td>#${c.id_categoria}</td>
                        <td><strong>${c.nome_categoria}</strong></td>
                    </tr>
                `).join('');
            }
        }
    });

    fetch('/api/fornecedores').then(res => res.json()).then(data => {
        if (data.success) {
            const tbody = document.getElementById('table-fornecedores-body');
            if (tbody) {
                tbody.innerHTML = data.fornecedores.map(f => `
                    <tr>
                        <td><strong>${f.nome_fornecedor}</strong></td>
                        <td>${f.cnpj_cpf || '-'}</td>
                        <td>${f.telefone || '-'}</td>
                        <td>${f.email || '-'}</td>
                    </tr>
                `).join('');
            }
        }
    });
}

function abrirModalCategoria() {
    document.getElementById('form-categoria').reset();
    document.getElementById('modal-categoria').classList.remove('hidden');
}

async function salvarCategoria(event) {
    event.preventDefault();
    const nome_categoria = document.getElementById('cat-nome').value.trim();

    try {
        const response = await fetch('/api/categorias', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome_categoria })
        });
        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');
            fecharModal('modal-categoria');
            carregarCadastrosGerais();
        } else {
            showToast(result.message, 'error');
        }
    } catch (e) {
        showToast('Erro ao salvar categoria.', 'error');
    }
}

function abrirModalFornecedor() {
    document.getElementById('form-fornecedor').reset();
    document.getElementById('modal-fornecedor').classList.remove('hidden');
}

async function salvarFornecedor(event) {
    event.preventDefault();
    const payload = {
        nome_fornecedor: document.getElementById('forn-nome').value.trim(),
        cnpj_cpf: document.getElementById('forn-cnpj').value.trim(),
        telefone: document.getElementById('forn-tel').value.trim(),
        email: document.getElementById('forn-email').value.trim()
    };

    try {
        const response = await fetch('/api/fornecedores', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');
            fecharModal('modal-fornecedor');
            carregarCadastrosGerais();
        } else {
            showToast(result.message, 'error');
        }
    } catch (e) {
        showToast('Erro ao salvar fornecedor.', 'error');
    }
}

// --- USUÁRIOS E APROVAÇÃO ---

async function carregarUsuarios() {
    try {
        const response = await fetch('/api/auth/users');
        const result = await response.json();

        if (result.success) {
            const tbody = document.getElementById('table-usuarios-body');
            tbody.innerHTML = result.users.map(u => {
                let statusBadge = 'badge-success';
                if (u.status_aprovacao === 'Pendente') statusBadge = 'badge-warning';
                if (u.status_aprovacao === 'Rejeitado') statusBadge = 'badge-danger';

                let acoesHtml = '';
                if (u.status_aprovacao === 'Pendente') {
                    acoesHtml = `
                        <button class="btn btn-sm btn-success" onclick="abrirModalUsuario(${u.id_usuario}, '${u.nome_usuario}', ${u.id_unidade || 'null'}, '${u.nivel_acesso}', 'aprovar')" title="Aprovar Cadastro">
                            <i class="fa-solid fa-check"></i> Aprovar
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="rejeitarUsuario(${u.id_usuario})" title="Rejeitar Cadastro">
                            <i class="fa-solid fa-xmark"></i> Rejeitar
                        </button>
                    `;
                } else {
                    acoesHtml = `
                        <button class="btn btn-sm btn-outline" onclick="abrirModalUsuario(${u.id_usuario}, '${u.nome_usuario}', ${u.id_unidade || 'null'}, '${u.nivel_acesso}', 'editar')" title="Editar Unidade / Nível">
                            <i class="fa-solid fa-pen-to-square"></i> Editar
                        </button>
                    `;
                }

                return `
                    <tr>
                        <td>#${u.id_usuario}</td>
                        <td><strong>${u.nome_usuario}</strong></td>
                        <td><code>${u.usuario}</code></td>
                        <td><span class="badge ${u.nivel_acesso === 'Administrador' ? 'badge-info' : 'badge-secondary'}">${u.nivel_acesso}</span></td>
                        <td>${u.nome_unidade || 'Sem Unidade'}</td>
                        <td><span class="badge ${statusBadge}">${u.status_aprovacao || 'Aprovado'}</span></td>
                        <td class="text-right">${acoesHtml}</td>
                    </tr>
                `;
            }).join('');
        }
    } catch (e) {
        showToast('Erro ao carregar lista de usuários.', 'error');
    }
}

async function abrirModalUsuario(id_usuario, nome_usuario, id_unidade_atual, nivel_atual, modo = 'editar') {
    document.getElementById('aprovar-user-id').value = id_usuario;
    document.getElementById('aprovar-user-nome').textContent = nome_usuario;
    document.getElementById('aprovar-user-modo').value = modo;

    const title = modo === 'aprovar' ? 'Aprovar e Vincular Usuário' : 'Editar Unidade e Nível de Acesso';
    document.getElementById('modal-user-title').textContent = title;

    try {
        const res = await fetch('/api/unidades');
        const data = await res.json();
        if (data.success) {
            unidadesCache = data.unidades;
            const selectU = document.getElementById('aprovar-unidade');
            selectU.innerHTML = '<option value="">Selecione a Unidade...</option>' +
                data.unidades.map(u => `<option value="${u.id_unidade}">${u.nome_unidade}</option>`).join('');
            
            if (id_unidade_atual && id_unidade_atual !== 'null') {
                selectU.value = id_unidade_atual;
            }
        }
    } catch (e) {}

    if (nivel_atual) {
        document.getElementById('aprovar-nivel').value = nivel_atual;
    }

    document.getElementById('modal-aprovar-usuario').classList.remove('hidden');
}

async function salvarAprovacaoOuEdicaoUsuario(event) {
    event.preventDefault();
    const userId = document.getElementById('aprovar-user-id').value;
    const modo = document.getElementById('aprovar-user-modo').value;
    const id_unidade = document.getElementById('aprovar-unidade').value;
    const nivel_acesso = document.getElementById('aprovar-nivel').value;

    if (!id_unidade) {
        showToast('Selecione uma Unidade Operacional.', 'warning');
        return;
    }

    const endpoint = modo === 'aprovar' 
        ? `/api/auth/users/${userId}/aprovar` 
        : `/api/auth/users/${userId}/editar`;

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_unidade, nivel_acesso })
        });
        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');
            fecharModal('modal-aprovar-usuario');
            carregarUsuarios();

            if (currentUser && currentUser.id_usuario == userId) {
                currentUser.id_unidade = id_unidade;
                currentUser.nivel_acesso = nivel_acesso;
                const unitObj = unidadesCache.find(u => u.id_unidade == id_unidade);
                if (unitObj) currentUser.nome_unidade = unitObj.nome_unidade;
                localStorage.setItem('stock_user', JSON.stringify(currentUser));
                iniciarAplicacao();
            }
        } else {
            showToast(result.message, 'error');
        }
    } catch (e) {
        showToast('Erro ao salvar alterações do usuário.', 'error');
    }
}

async function rejeitarUsuario(id_usuario) {
    if (!confirm('Deseja rejeitar este usuário?')) return;

    try {
        const response = await fetch(`/api/auth/users/${id_usuario}/rejeitar`, { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');
            carregarUsuarios();
        } else {
            showToast(result.message, 'error');
        }
    } catch (e) {
        showToast('Erro ao rejeitar usuário.', 'error');
    }
}

// --- UTILITÁRIOS ---

function fecharModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor || 0);
}

function formatarData(strData) {
    if (!strData) return '-';
    try {
        const d = new Date(strData);
        if (isNaN(d.getTime())) return strData;
        return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        return strData;
    }
}

function showToast(mensagem, tipo = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    
    let icon = 'fa-check-circle';
    if (tipo === 'error') icon = 'fa-circle-xmark';
    if (tipo === 'warning') icon = 'fa-triangle-exclamation';
    if (tipo === 'info') icon = 'fa-circle-info';

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${mensagem}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
