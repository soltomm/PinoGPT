// ============================================================
// PinoGPT Dashboard - Frontend Logic
// ============================================================

let allPlayers = [];

// ---- INIT ----
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupForms();
    loadPlayers();
});

// ---- NAVIGATION ----
function setupNavigation() {
    const links = document.querySelectorAll('.nav-link, .mobile-link');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = link.dataset.tab;
            switchTab(tab);
            document.getElementById('mobileMenu').classList.remove('open');
        });
    });

    document.getElementById('hamburger').addEventListener('click', () => {
        document.getElementById('mobileMenu').classList.toggle('open');
    });
}

function switchTab(tab) {
    document.querySelectorAll('.nav-link, .mobile-link').forEach(l => l.classList.remove('active'));
    document.querySelectorAll(`[data-tab="${tab}"]`).forEach(l => l.classList.add('active'));

    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    const target = document.getElementById(`tab-${tab}`);
    target.classList.add('active');

    if (tab === 'leaderboard' || tab === 'players' || tab === 'teams') loadPlayers();
    if (tab === 'games') { loadPendingGames(); loadPlayers(); }
    if (tab === 'history') loadHistory();
}

// ---- FORMS ----
function setupForms() {
    document.getElementById('addPlayerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('playerName').value.trim();
        if (!name) return;

        const res = await apiPost('/api/players', { name });
        if (res.success) {
            showToast(res.message, 'success');
            document.getElementById('playerName').value = '';
            loadPlayers();
        } else {
            showToast(res.message || res.error, 'error');
        }
    });
}

// Tri-state picker state: maps player name -> 'none' | 'team1' | 'team2'
let manualPickState = {};

function updateManualCounts() {
    const t1 = Object.entries(manualPickState).filter(([,v]) => v === 'team1').map(([k]) => k);
    const t2 = Object.entries(manualPickState).filter(([,v]) => v === 'team2').map(([k]) => k);
    document.getElementById('manualT1Count').textContent = t1.length;
    document.getElementById('manualT2Count').textContent = t2.length;
    document.getElementById('manualT1Names').textContent = t1.join(', ') || '-';
    document.getElementById('manualT2Names').textContent = t2.join(', ') || '-';
}

function getManualTeam(team) {
    return Object.entries(manualPickState).filter(([,v]) => v === team).map(([k]) => k);
}

// ---- LOADING HELPERS ----
function showLoading(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
}

function hideLoading(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}

// ---- API HELPERS ----
async function apiFetch(url) {
    try {
        const res = await fetch(url);
        return await res.json();
    } catch (e) {
        console.error('API error:', e);
        return null;
    }
}

async function apiPost(url, data) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await res.json();
    } catch (e) {
        console.error('API error:', e);
        return { success: false, error: 'Errore di connessione' };
    }
}

async function apiDelete(url) {
    try {
        const res = await fetch(url, { method: 'DELETE' });
        return await res.json();
    } catch (e) {
        console.error('API error:', e);
        return { success: false, error: 'Errore di connessione' };
    }
}

// ---- LOAD PLAYERS ----
async function loadPlayers() {
    showLoading('leaderboardLoading');
    showLoading('playersLoading');
    showLoading('teamsLoading');

    const players = await apiFetch('/api/players');

    hideLoading('leaderboardLoading');
    hideLoading('playersLoading');
    hideLoading('teamsLoading');

    if (!players) return;
    allPlayers = players;

    renderLeaderboard(players);
    renderPlayerList(players);
    renderPlayerCheckboxes(players);
    renderManualPicker(players);
}

function renderLeaderboard(players) {
    const tbody = document.querySelector('#leaderboardTable tbody');
    const empty = document.getElementById('leaderboardEmpty');

    if (players.length === 0) {
        tbody.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    tbody.innerHTML = players.map((p, i) => {
        const rankClass = p.rank <= 3 ? `rank-${p.rank}` : '';
        const rankIcon = p.rank === 1 ? '&#129351;' : p.rank === 2 ? '&#129352;' : p.rank === 3 ? '&#129353;' : p.rank;
        const eloClass = p.elo >= 1600 ? 'elo-high' : p.elo >= 1300 ? 'elo-mid' : 'elo-low';
        return `<tr class="stagger-in" style="animation-delay:${i * 30}ms" onclick="showPlayerModal('${escapeHtml(p.name)}')">
            <td class="${rankClass}">${rankIcon}</td>
            <td><strong>${escapeHtml(p.name)}</strong></td>
            <td><span class="elo-badge ${eloClass}">${p.elo}</span></td>
            <td>${p.games_played}</td>
            <td>${p.wins}</td>
            <td>${p.losses}</td>
            <td>${p.win_rate}%</td>
        </tr>`;
    }).join('');
}

function renderPlayerList(players) {
    const container = document.getElementById('playerList');
    const empty = document.getElementById('playersEmpty');

    const sorted = [...players].sort((a, b) => a.name.localeCompare(b.name, 'it', { sensitivity: 'base' }));

    if (sorted.length === 0) {
        container.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    container.innerHTML = sorted.map((p, i) => `
        <div class="player-card stagger-in" style="animation-delay:${i * 40}ms" onclick="showPlayerModal('${escapeHtml(p.name)}')">
            <div class="player-card-info">
                <span class="player-card-name">${escapeHtml(p.name)}</span>
                <span class="player-card-meta">ELO ${p.elo} &middot; ${p.games_played} partite &middot; ${p.win_rate}% vittorie</span>
            </div>
            <div class="player-card-actions">
                <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); removePlayer('${escapeHtml(p.name)}')">Rimuovi</button>
            </div>
        </div>
    `).join('');
}

function filterPlayerList(query) {
    const q = query.toLowerCase();
    const filtered = allPlayers.filter(p => p.name.toLowerCase().includes(q));
    const container = document.getElementById('playerList');
    const empty = document.getElementById('playersEmpty');

    const sorted = [...filtered].sort((a, b) => a.name.localeCompare(b.name, 'it', { sensitivity: 'base' }));

    if (sorted.length === 0) {
        container.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    container.innerHTML = sorted.map((p, i) => `
        <div class="player-card stagger-in" style="animation-delay:${i * 40}ms" onclick="showPlayerModal('${escapeHtml(p.name)}')">
            <div class="player-card-info">
                <span class="player-card-name">${escapeHtml(p.name)}</span>
                <span class="player-card-meta">ELO ${p.elo} &middot; ${p.games_played} partite &middot; ${p.win_rate}% vittorie</span>
            </div>
            <div class="player-card-actions">
                <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); removePlayer('${escapeHtml(p.name)}')">Rimuovi</button>
            </div>
        </div>
    `).join('');
}

function renderPlayerCheckboxes(players) {
    const container = document.getElementById('playerCheckboxes');
    const sorted = [...players].sort((a, b) => a.name.localeCompare(b.name, 'it', { sensitivity: 'base' }));
    container.innerHTML = sorted.map(p => `
        <label class="checkbox-item" id="cb-${escapeHtml(p.name)}">
            <input type="checkbox" value="${escapeHtml(p.name)}" onchange="updateCheckboxSelection(this)">
            <span>${escapeHtml(p.name)} (${p.elo})</span>
        </label>
    `).join('');
}

function filterTeamsCheckboxes(query) {
    const q = query.toLowerCase();
    const filtered = allPlayers.filter(p => p.name.toLowerCase().includes(q));
    const sorted = [...filtered].sort((a, b) => a.name.localeCompare(b.name, 'it', { sensitivity: 'base' }));
    const container = document.getElementById('playerCheckboxes');
    // Preserve checked state
    const checked = new Set(Array.from(document.querySelectorAll('#playerCheckboxes input:checked')).map(cb => cb.value));
    container.innerHTML = sorted.map(p => {
        const isChecked = checked.has(p.name);
        const checkedCount = checked.size;
        const isDisabled = !isChecked && checkedCount >= 10;
        return `
        <label class="checkbox-item${isChecked ? ' selected' : ''}" id="cb-${escapeHtml(p.name)}">
            <input type="checkbox" value="${escapeHtml(p.name)}" onchange="updateCheckboxSelection(this)"
                ${isChecked ? 'checked' : ''} ${isDisabled ? 'disabled' : ''}>
            <span>${escapeHtml(p.name)} (${p.elo})</span>
        </label>`;
    }).join('');
}

function updateCheckboxSelection(cb) {
    const checked = document.querySelectorAll('#playerCheckboxes input:checked');
    const count = checked.length;
    document.getElementById('selectedCount').textContent = count;
    document.getElementById('createTeamsBtn').disabled = count !== 10;

    cb.closest('.checkbox-item').classList.toggle('selected', cb.checked);

    document.querySelectorAll('#playerCheckboxes input').forEach(input => {
        if (!input.checked) {
            input.disabled = count >= 10;
        }
    });
}

function renderManualPicker(players) {
    const container = document.getElementById('manualPlayerPicker');
    const oldState = { ...manualPickState };
    manualPickState = {};
    players.forEach(p => {
        manualPickState[p.name] = oldState[p.name] || 'none';
    });

    const sorted = [...players].sort((a, b) => a.name.localeCompare(b.name, 'it', { sensitivity: 'base' }));
    container.innerHTML = sorted.map(p => {
        const state = manualPickState[p.name];
        const cls = state !== 'none' ? state : '';
        const label = state === 'team1' ? 'T1' : state === 'team2' ? 'T2' : '';
        return `<div class="checkbox-item ${cls}" data-player="${escapeHtml(p.name)}" onclick="cycleManualPick(this)">
            <span class="pick-indicator">${label}</span>
            <span>${escapeHtml(p.name)} (${p.elo})</span>
        </div>`;
    }).join('');
    updateManualCounts();
}

function filterManualPicker(query) {
    const q = query.toLowerCase();
    const filtered = allPlayers.filter(p => p.name.toLowerCase().includes(q));
    const sorted = [...filtered].sort((a, b) => a.name.localeCompare(b.name, 'it', { sensitivity: 'base' }));
    const container = document.getElementById('manualPlayerPicker');
    container.innerHTML = sorted.map(p => {
        const state = manualPickState[p.name] || 'none';
        const cls = state !== 'none' ? state : '';
        const label = state === 'team1' ? 'T1' : state === 'team2' ? 'T2' : '';
        return `<div class="checkbox-item ${cls}" data-player="${escapeHtml(p.name)}" onclick="cycleManualPick(this)">
            <span class="pick-indicator">${label}</span>
            <span>${escapeHtml(p.name)} (${p.elo})</span>
        </div>`;
    }).join('');
}

function cycleManualPick(el) {
    const name = el.dataset.player;
    const current = manualPickState[name] || 'none';
    const t1Count = getManualTeam('team1').length;
    const t2Count = getManualTeam('team2').length;

    let next;
    if (current === 'none') {
        next = t1Count < 5 ? 'team1' : t2Count < 5 ? 'team2' : 'none';
    } else if (current === 'team1') {
        next = t2Count < 5 ? 'team2' : 'none';
    } else {
        next = 'none';
    }

    manualPickState[name] = next;

    el.className = 'checkbox-item' + (next !== 'none' ? ' ' + next : '');
    const indicator = el.querySelector('.pick-indicator');
    indicator.textContent = next === 'team1' ? 'T1' : next === 'team2' ? 'T2' : '';

    updateManualCounts();
}

// ---- REMOVE PLAYER ----
async function removePlayer(name) {
    const password = prompt(`Password admin per rimuovere ${name}:`);
    if (password === null) return;
    const res = await fetch(`/api/players/${encodeURIComponent(name)}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    }).then(r => r.json()).catch(() => ({ success: false, error: 'Errore di connessione' }));
    if (res.success) {
        showToast(res.message, 'success');
        loadPlayers();
    } else {
        showToast(res.error || res.message || 'Password errata', 'error');
    }
}

// ---- CREATE TEAMS (two-step: propose → confirm) ----
let proposedTeams = null;

async function createTeams() {
    const checked = document.querySelectorAll('#playerCheckboxes input:checked');
    const names = Array.from(checked).map(cb => cb.value);

    if (names.length !== 10) {
        showToast('Seleziona esattamente 10 giocatori', 'error');
        return;
    }

    const res = await apiPost('/api/games/propose-teams', { players: names });
    if (res.success) {
        proposedTeams = res.teams;
        displayTeams(res.teams);
        document.getElementById('confirmTeamsBtn').classList.remove('hidden');
        showToast('Squadre proposte — conferma per creare la partita', 'success');
    } else {
        showToast(res.message || res.error, 'error');
    }
}

async function confirmTeams() {
    if (!proposedTeams) return;

    const res = await apiPost('/api/games/confirm-teams', {
        team1: proposedTeams.team1,
        team2: proposedTeams.team2
    });

    if (res.success) {
        showToast('Partita creata!', 'success');
        proposedTeams = null;
        document.getElementById('confirmTeamsBtn').classList.add('hidden');
        document.getElementById('teamsResult').classList.add('hidden');
        // Reset checkboxes
        document.querySelectorAll('#playerCheckboxes input:checked').forEach(cb => {
            cb.checked = false;
            cb.closest('.checkbox-item').classList.remove('selected');
        });
        document.querySelectorAll('#playerCheckboxes input').forEach(cb => cb.disabled = false);
        document.getElementById('selectedCount').textContent = '0';
        document.getElementById('createTeamsBtn').disabled = true;
    } else {
        showToast(res.message || res.error, 'error');
    }
}

function displayTeams(teams) {
    const container = document.getElementById('teamsResult');
    container.classList.remove('hidden');

    document.getElementById('team1Elo').textContent = teams.team1_avg_elo;
    document.getElementById('team2Elo').textContent = teams.team2_avg_elo;

    const playerMap = {};
    allPlayers.forEach(p => playerMap[p.name] = p);

    document.getElementById('team1List').innerHTML = teams.team1.map(name => {
        const p = playerMap[name];
        return `<li>${escapeHtml(name)} ${p ? `(${p.elo})` : ''}</li>`;
    }).join('');

    document.getElementById('team2List').innerHTML = teams.team2.map(name => {
        const p = playerMap[name];
        return `<li>${escapeHtml(name)} ${p ? `(${p.elo})` : ''}</li>`;
    }).join('');
}

// ---- PENDING GAMES ----
async function loadPendingGames() {
    showLoading('pendingLoading');
    const games = await apiFetch('/api/games/pending');
    hideLoading('pendingLoading');

    if (!games) return;

    const container = document.getElementById('pendingGamesContainer');
    const empty = document.getElementById('pendingEmpty');

    if (games.length === 0) {
        container.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    container.innerHTML = games.map(g => {
        const date = g.timestamp ? new Date(g.timestamp).toLocaleDateString('it-IT') : 'N/A';
        return `
        <div class="pending-game-card">
            <div class="game-header">
                <span class="game-id">ID: ${escapeHtml(g.game_id)}</span>
                <span class="game-date">${date}</span>
            </div>
            <div class="game-teams">
                <div>
                    <strong style="color:var(--accent-blue)">Team 1</strong> (${g.team1_avg_elo})<br>
                    ${g.team1.map(n => escapeHtml(n)).join(', ')}
                </div>
                <div>
                    <strong style="color:var(--accent-red)">Team 2</strong> (${g.team2_avg_elo})<br>
                    ${g.team2.map(n => escapeHtml(n)).join(', ')}
                </div>
            </div>
            <div class="score-form">
                <div class="form-group">
                    <label>Gol Team 1</label>
                    <input type="number" id="score1-${g.game_id}" min="0" max="99" value="0">
                </div>
                <div class="form-group">
                    <label>Gol Team 2</label>
                    <input type="number" id="score2-${g.game_id}" min="0" max="99" value="0">
                </div>
                <button class="btn btn-primary" onclick="recordScore('${escapeHtml(g.game_id)}')">Registra</button>
                <button class="btn btn-danger btn-sm" onclick="deletePendingGame('${escapeHtml(g.game_id)}')">Elimina</button>
            </div>
        </div>`;
    }).join('');
}

async function recordScore(gameId) {
    const t1 = parseInt(document.getElementById(`score1-${gameId}`).value) || 0;
    const t2 = parseInt(document.getElementById(`score2-${gameId}`).value) || 0;

    const res = await apiPost('/api/games/record-score', {
        game_id: gameId,
        team1_score: t1,
        team2_score: t2
    });

    if (res.success) {
        showToast('Risultato registrato!', 'success');
        loadPendingGames();
        loadPlayers();
    } else {
        showToast(res.message || res.error, 'error');
    }
}

// ---- DELETE PENDING GAME ----
async function deletePendingGame(gameId) {
    const password = prompt('Password admin per eliminare la partita:');
    if (password === null) return;
    const res = await fetch(`/api/games/pending/${encodeURIComponent(gameId)}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    }).then(r => r.json()).catch(() => ({ success: false, error: 'Errore di connessione' }));
    if (res.success) {
        showToast(res.message, 'success');
        loadPendingGames();
    } else {
        showToast(res.error || res.message || 'Password errata', 'error');
    }
}

// ---- MANUAL GAME ----
async function recordManualGame() {
    const team1 = getManualTeam('team1');
    const team2 = getManualTeam('team2');
    const t1Score = parseInt(document.getElementById('manualScore1').value) || 0;
    const t2Score = parseInt(document.getElementById('manualScore2').value) || 0;

    if (team1.length !== 5 || team2.length !== 5) {
        showToast(`Seleziona 5 giocatori per squadra (Team 1: ${team1.length}, Team 2: ${team2.length})`, 'error');
        return;
    }

    const res = await apiPost('/api/games/manual', {
        team1, team2,
        team1_score: t1Score,
        team2_score: t2Score
    });

    if (res.success) {
        showToast('Partita registrata!', 'success');
        manualPickState = {};
        document.getElementById('manualScore1').value = 0;
        document.getElementById('manualScore2').value = 0;
        loadPlayers();
    } else {
        showToast(res.message || res.error, 'error');
    }
}

// ---- HISTORY ----
async function loadHistory() {
    showLoading('historyLoading');
    const games = await apiFetch('/api/games/history');
    hideLoading('historyLoading');

    if (!games) return;

    const container = document.getElementById('historyContainer');
    const empty = document.getElementById('historyEmpty');

    if (games.length === 0) {
        container.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    empty.classList.add('hidden');

    container.innerHTML = games.map((g, i) => {
        const date = g.played_at ? new Date(g.played_at).toLocaleDateString('it-IT') : 'N/A';
        const winnerClass = g.winner === 'Team 1' ? 'winner-team1'
            : g.winner === 'Team 2' ? 'winner-team2'
            : 'winner-draw';
        const winnerLabel = g.winner === 'Draw' ? 'Pareggio' : g.winner;
        return `
        <div class="history-card stagger-in" style="animation-delay:${i * 40}ms">
            <span class="history-date">${date}</span>
            <div class="history-teams">
                <span style="color:var(--accent-blue)">${g.team1.map(n => escapeHtml(n)).join(', ')}</span>
                <br>
                <span style="color:var(--accent-red)">${g.team2.map(n => escapeHtml(n)).join(', ')}</span>
            </div>
            <span class="history-score">${g.team1_score} - ${g.team2_score}</span>
            <span class="history-winner ${winnerClass}">${winnerLabel}</span>
        </div>`;
    }).join('');
}

// ---- PLAYER MODAL ----
function showPlayerModal(name) {
    const player = allPlayers.find(p => p.name === name);
    if (!player) return;

    document.getElementById('modalPlayerName').textContent = player.name;
    document.getElementById('modalGames').textContent = player.games_played;
    document.getElementById('modalWins').textContent = player.wins;
    document.getElementById('modalLosses').textContent = player.losses;
    document.getElementById('modalWinRate').textContent = player.win_rate + '%';

    // ELO bar
    document.getElementById('modalEloValue').textContent = player.elo;
    const bar = document.getElementById('modalEloBar');
    const pct = Math.min(Math.max((player.elo - 800) / 1200 * 100, 0), 100);
    bar.style.width = '0%';
    // Animate after a frame
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            bar.style.width = pct + '%';
        });
    });
    // Color based on ELO tier
    if (player.elo >= 1600) {
        bar.style.background = 'linear-gradient(90deg, var(--accent-green-dim), var(--accent-green))';
    } else if (player.elo >= 1300) {
        bar.style.background = 'linear-gradient(90deg, #3b82f6, var(--accent-blue))';
    } else {
        bar.style.background = 'linear-gradient(90deg, #ef4444, var(--accent-red))';
    }

    document.getElementById('playerModal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('playerModal').classList.add('hidden');
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) closeModal();
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

// ---- TOAST ----
let toastTimer = null;
function showToast(message, type) {
    const toast = document.getElementById('toast');
    // Clear any existing timer
    if (toastTimer) clearTimeout(toastTimer);

    const cleanMsg = message.replace(/^[^\w\s]*\s*/, '');
    toast.textContent = cleanMsg;
    toast.className = `toast ${type}`;

    toastTimer = setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => {
            toast.className = 'toast hidden';
        }, 300);
    }, 3200);
}

// ---- UTILS ----
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
