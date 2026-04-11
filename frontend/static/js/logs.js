/* logs.js */

let allLogs = [];

async function loadLogs() {
  try {
    const r = await fetch('/api/logs?limit=2000');
    allLogs  = await r.json();
    renderLogs(allLogs);
    updateSummary(allLogs);
  } catch (e) {
    console.error('Log load error:', e);
  }
}

function updateSummary(logs) {
  document.getElementById('log-count').textContent = logs.length;
  document.getElementById('log-safe').textContent  = logs.filter(l => l.status === 'SAFE').length;
  document.getElementById('log-warn').textContent  = logs.filter(l => l.status === 'WARNING').length;
  document.getElementById('log-crit').textContent  = logs.filter(l => l.status === 'CRITICAL').length;
  document.getElementById('log-badge').textContent = logs.length + ' entries';
}

function renderLogs(logs) {
  const tbody = document.getElementById('log-tbody');
  if (!logs.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="table-empty">No log entries found.</td></tr>';
    return;
  }
  const rows = [...logs].reverse().map((entry, i) => {
    const statusCls =
      entry.status === 'CRITICAL' ? 'critical' :
      entry.status === 'WARNING'  ? 'warning'  :
      entry.status === 'SAFE'     ? 'safe'      : '';
    const earVal     = entry.ear      !== undefined ? entry.ear.toFixed(3) : '--';
    const fatigueVal = entry.fatigue_score !== undefined ? entry.fatigue_score.toFixed(1) : '--';
    const barWidth   = Math.min(100, parseFloat(fatigueVal) || 0);
    const barColor   =
      parseFloat(fatigueVal) >= 65 ? 'var(--critical)' :
      parseFloat(fatigueVal) >= 35 ? 'var(--warning)'  : 'var(--safe)';
    return `<tr>
      <td class="mono" style="color:var(--text-faint)">${logs.length - i}</td>
      <td class="mono">${entry.timestamp || '--'}</td>
      <td class="mono">${earVal}</td>
      <td>
        <div style="display:flex;align-items:center;gap:0.5rem;">
          <div style="width:${barWidth}px;height:4px;border-radius:2px;background:${barColor};"></div>
          <span>${fatigueVal}</span>
        </div>
      </td>
      <td><span class="${statusCls}" style="font-weight:600;">${entry.status || '--'}</span></td>
    </tr>`;
  });
  tbody.innerHTML = rows.join('');
}

function filterLogs() {
  const q = document.getElementById('log-search').value.toLowerCase().trim();
  if (!q) { renderLogs(allLogs); return; }
  const filtered = allLogs.filter(entry =>
    Object.values(entry).some(v => String(v).toLowerCase().includes(q))
  );
  renderLogs(filtered);
  document.getElementById('log-badge').textContent = filtered.length + ' entries (filtered)';
}

loadLogs();
setInterval(loadLogs, 5000);
