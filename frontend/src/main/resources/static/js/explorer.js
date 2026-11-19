(() => {
    'use strict';
    const app = document.getElementById('datalaw-explorer');
    if (!app) return;
    const find = selector => app.querySelector(selector);
    const all = selector => [...app.querySelectorAll(selector)];
    const number = value => Number(value).toLocaleString('pt-BR');
    const percent = value => Number(value).toLocaleString('pt-BR', {
        minimumFractionDigits: 1, maximumFractionDigits: 1
    }) + '%';
    let activeList = 'topics';
    let page = 0;
    const pageSize = 6;
    let pendingRequest = null;

    function cancelRequest() {
        pendingRequest?.abort();
        pendingRequest = null;
    }

    function renderList() {
        const panel = find(`[data-list-panel="${activeList}"]`);
        const rows = [...panel.querySelectorAll('.collection-row')];
        const query = find('#list-filter').value.trim().toLocaleLowerCase('pt-BR');
        const matches = rows.filter(row => row.dataset.name.toLocaleLowerCase('pt-BR').includes(query));
        page = Math.max(0, Math.min(page, Math.ceil(matches.length / pageSize) - 1));
        const visible = new Set(matches.slice(page * pageSize, (page + 1) * pageSize));
        rows.forEach(row => { row.hidden = !visible.has(row); });
        find('#list-no-match').hidden = !query || matches.length > 0 || rows.length === 0;
        find('#page-range').textContent = matches.length
            ? `${page * pageSize + 1}–${Math.min((page + 1) * pageSize, matches.length)} de ${number(matches.length)} ${matches.length === 1 ? 'grupo' : 'grupos'}`
            : 'Nenhum grupo';
        find('#page-previous').disabled = page === 0;
        find('#page-next').disabled = (page + 1) * pageSize >= matches.length;
    }

    function showDetail(view) {
        cancelRequest();
        find('#topic-detail').hidden = view !== 'topic';
        find('#rate-detail').hidden = view !== 'rate';
        find('#selection-placeholder').hidden = view !== 'placeholder';
    }

    function switchList(name) {
        activeList = name;
        page = 0;
        find('#list-filter').value = '';
        all('[data-list-tab]').forEach(tab => {
            const selected = tab.dataset.listTab === name;
            tab.setAttribute('aria-selected', String(selected));
            tab.tabIndex = selected ? 0 : -1;
        });
        all('[data-list-panel]').forEach(panel => { panel.hidden = panel.dataset.listPanel !== name; });
        if (name === 'topics') {
            showDetail('topic');
        } else {
            showDetail('placeholder');
            find('#selection-instruction').textContent = name === 'classes'
                ? 'Selecione uma classe.' : 'Selecione um órgão julgador.';
            all('.collection-row[aria-pressed]').forEach(row => row.setAttribute('aria-pressed', 'false'));
        }
        renderList();
    }

    function switchDetail(name, focus = false) {
        all('[data-detail-tab]').forEach(tab => {
            const selected = tab.dataset.detailTab === name;
            tab.setAttribute('aria-selected', String(selected));
            tab.tabIndex = selected ? 0 : -1;
            if (selected && focus) tab.focus();
        });
        all('[data-detail-panel]').forEach(panel => { panel.hidden = panel.dataset.detailPanel !== name; });
    }

    function renderPrecedents(precedents) {
        const list = find('#precedents-list');
        list.replaceChildren();
        find('#precedents').hidden = !precedents.length;
        precedents.forEach(row => {
            const details = document.createElement('details');
            details.className = 'precedent';
            const summary = document.createElement('summary');
            summary.textContent = [row[0], row[1], row[2]].filter(Boolean).join(' · ');
            details.appendChild(summary);
            [row[3] ? 'Tese: ' + row[3] : '', row[4]].filter(Boolean).forEach(text => {
                const paragraph = document.createElement('p');
                paragraph.textContent = text;
                details.appendChild(paragraph);
            });
            list.appendChild(details);
        });
    }

    async function openSelection(button) {
        showDetail('rate');
        const kind = button.dataset.kind;
        const name = button.dataset.name;
        find('#rate-name').textContent = name;
        find('#rate-count').textContent = button.dataset.count
            ? `${number(button.dataset.count)} processos públicos no grupo` : '';
        find('#rate-status').textContent = '';
        find('#rate-value').textContent = '—';
        find('#rate-explanation').textContent = '';
        find('#precedents').hidden = true;
        find('#precedents-list').replaceChildren();
        find('#apply-class').hidden = kind !== 'classe';
        all('.collection-row[aria-pressed]').forEach(row => row.setAttribute('aria-pressed', String(row === button)));

        if (kind === 'orgao') {
            const total = all('#list-bodies .collection-row').reduce((sum, row) => sum + Number(row.dataset.count), 0);
            find('#rate-kind').textContent = 'Participação entre os órgãos carregados';
            find('#rate-value').textContent = total > 0 ? percent(100 * Number(button.dataset.count) / total) : 'Dados insuficientes';
            find('#rate-explanation').textContent = `${number(button.dataset.count)} de ${number(total)} processos somados nos órgãos carregados. A lista contém até 50 grupos; esta participação não representa todo o acervo.`;
            return;
        }

        find('#rate-kind').textContent = kind === 'classe' ? 'Taxa de resultado por classe' : 'Taxa de resultado por assunto';
        find('#rate-explanation').textContent = 'Resultado favorável ao autor, com peso 0,5 para decisões parciais. Consulta pelo nome exato, independente da tese e dos demais filtros de volume.';
        if (kind === 'classe') {
            const link = new URL('/processos/orgaos-julgadores', window.location.origin);
            link.searchParams.set('classeNome', name);
            link.searchParams.set('assuntoNome', find('#theme-search').value);
            link.searchParams.set('temaSelecionado', find('#analysis-detail').dataset.selectedTopic);
            find('#apply-class').href = link.pathname + link.search;
        }
        const request = new AbortController();
        pendingRequest = request;
        find('#rate-status').textContent = 'Carregando resultado…';
        const url = new URL(kind === 'classe' ? '/processos/taxa-sucesso' : '/processos/taxa-sucesso-tema', window.location.origin);
        url.searchParams.set(kind === 'classe' ? 'classeNome' : 'assuntoNome', name);
        try {
            const response = await fetch(url, { signal: request.signal });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            if (pendingRequest !== request) return;
            find('#rate-value').textContent = data.taxa == null ? 'Dados insuficientes' : percent(data.taxa);
            find('#rate-status').textContent = data.taxa == null ? 'Sem resultado calculável para este nome exato.' : '';
            if (kind === 'assunto') renderPrecedents(Array.isArray(data.precedentes) ? data.precedentes : []);
        } catch (error) {
            if (error.name === 'AbortError' || pendingRequest !== request) return;
            find('#rate-value').textContent = 'Indisponível';
            find('#rate-status').textContent = 'Não foi possível consultar o resultado. Selecione o item novamente para tentar outra vez.';
        } finally {
            if (pendingRequest === request) pendingRequest = null;
        }
    }

    app.addEventListener('click', event => {
        const button = event.target.closest('button');
        if (!button) return;
        if (button.dataset.listTab) switchList(button.dataset.listTab);
        if (button.dataset.detailTab) switchDetail(button.dataset.detailTab);
        if (button.dataset.showSection) switchDetail(button.dataset.showSection, true);
        if (button.dataset.kind) openSelection(button);
        if (button.id === 'page-previous') { page--; renderList(); }
        if (button.id === 'page-next') { page++; renderList(); }
        if (button.id === 'return-topic') switchList('topics');
    });
    app.addEventListener('keydown', event => {
        if (event.altKey || event.ctrlKey || event.metaKey) return;
        if (!event.target.matches('[role="tab"]')) return;
        const tabs = [...event.target.closest('[role="tablist"]').querySelectorAll('[role="tab"]')];
        let index = tabs.indexOf(event.target);
        if (event.key === 'ArrowRight') index = (index + 1) % tabs.length;
        else if (event.key === 'ArrowLeft') index = (index + tabs.length - 1) % tabs.length;
        else if (event.key === 'Home') index = 0;
        else if (event.key === 'End') index = tabs.length - 1;
        else return;
        event.preventDefault();
        tabs[index].click();
        tabs[index].focus();
    });
    find('#list-filter').addEventListener('input', () => { page = 0; renderList(); });
    const selectedIndex = all('#list-topics .collection-row').findIndex(row => row.getAttribute('aria-current') === 'true');
    if (selectedIndex >= 0) page = Math.floor(selectedIndex / pageSize);
    renderList();
    if (window.location.hash === '#evidencias' || find('#analysis-detail').dataset.initialSection === 'evidence') {
        switchDetail('evidence');
    }
})();
