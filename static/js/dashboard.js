/* dashboard.js */

const MAX_POINTS = 60;
const fatigueLabels = [];
const fatigueData   = [];

const fatigueChart = new Chart(document.getElementById('fatigueChart'), {
  type: 'line',
  data: {
    labels: fatigueLabels,
    datasets: [{
      label: 'Fatigue Score',
      data: fatigueData,
      borderColor: '#58a6ff',
      backgroundColor: 'rgba(88,166,255,0.08)',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.35,
      fill: true,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    scales: {
      x: { ticks: { color: '#484f58', maxTicksLimit: 6, font: { size: 10 } }, grid: { color: '#21262d' } },
      y: { min: 0, max: 100, ticks: { color: '#484f58', stepSize: 20, font: { size: 10 } }, grid: { color: '#21262d' } }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1c2128', borderColor: '#30363d', borderWidth: 1,
        titleColor: '#8b949e', bodyColor: '#c9d1d9',
        callbacks: { title: items => 'Time: ' + items[0].label }
      }
    }
  }
});

const MAX_ALERTS = 6;
const alertQueue = [];

function pushAlert(msg, cls) {
  alertQueue.unshift({ msg, cls });
  if (alertQueue.length > MAX_ALERTS) alertQueue.pop();
  const list = document.getElementById('alerts-list');
  list.innerHTML = alertQueue.map(a => `<li class="alert-item ${a.cls}">${a.msg}</li>`).join('');
}

function fmtSeconds(s) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return [h, m, sec].map(v => String(v).padStart(2, '0')).join(':');
}

let lastState = '';

function updateUI(d) {
  document.getElementById('m-ear').textContent     = d.camera_active ? d.ear.toFixed(3) : '--';
  document.getElementById('m-avg-ear').textContent = d.camera_active ? d.avg_ear.toFixed(3) : '--';
  document.getElementById('m-fatigue').textContent = d.camera_active ? d.fatigue_score.toFixed(1) : '--';
  document.getElementById('m-closure').textContent = d.camera_active ? d.closure_duration.toFixed(2) + 's' : '--';
  document.getElementById('m-blink').textContent   = d.camera_active ? d.blink_rate.toFixed(1) : '--';
  document.getElementById('m-fps').textContent     = d.camera_active ? d.fps.toFixed(1) : '--';
  document.getElementById('m-session').textContent = fmtSeconds(d.session_seconds || 0);

  const statusEl = document.getElementById('m-status');
  statusEl.textContent = d.status || 'IDLE';
  statusEl.className   = 'metric-value status-text ' + (d.status_state || 'idle');

  document.getElementById('m-trend').textContent = 'Trend: ' + (d.trend || '--');

  const badge = document.getElementById('camera-badge');
  if (d.camera_active) {
    badge.textContent = 'LIVE'; badge.className = 'badge badge-safe';
    document.getElementById('video-offline').classList.add('hidden');
    document.getElementById('video-feed').style.opacity = '1';
  } else {
    badge.textContent = 'OFFLINE'; badge.className = 'badge badge-idle';
    document.getElementById('video-offline').classList.remove('hidden');
    document.getElementById('video-feed').style.opacity = '0';
  }

  const banner = document.getElementById('alert-banner');
  if (d.status_state === 'critical') {
    banner.textContent = '⚠  CRITICAL — Drowsiness Detected. Pull over safely.';
    banner.className   = 'alert-banner critical';
  } else if (d.status_state === 'warning') {
    banner.textContent = '⚡  WARNING — Fatigue rising. Remain vigilant.';
    banner.className   = 'alert-banner warning';
  } else {
    banner.className   = 'alert-banner hidden';
  }

  const newState = d.status_state;
  if (newState !== lastState && d.camera_active) {
    const msgs = {
      safe:     ['Driver alertness stable.', 'safe'],
      warning:  ['Fatigue trend rising. Stay alert.', 'warning'],
      critical: ['DROWSINESS DETECTED — immediate action required.', 'critical'],
      idle:     ['Monitoring idle.', 'info'],
    };
    const [msg, cls] = msgs[newState] || ['Status updated.', 'info'];
    pushAlert(`[${d.timestamp}] ${msg}`, cls);
    lastState = newState;
  }

  if (d.camera_active) {
    fatigueLabels.push(d.timestamp || '');
    fatigueData.push(d.fatigue_score);
    if (fatigueLabels.length > MAX_POINTS) { fatigueLabels.shift(); fatigueData.shift(); }
    fatigueChart.data.datasets[0].borderColor =
      d.status_state === 'critical' ? '#f85149' :
      d.status_state === 'warning'  ? '#d29922' : '#58a6ff';
    fatigueChart.update('none');
  }

  document.getElementById('btn-start').disabled = d.monitoring;
  document.getElementById('btn-stop').disabled  = !d.monitoring;
  document.getElementById('btn-pause').textContent = d.paused ? 'Resume' : 'Pause';
  document.getElementById('btn-pause').onclick     = d.paused
    ? () => apiCall('/api/resume')
    : togglePause;
}

async function apiCall(url) {
  try {
    const r = await fetch(url, { method: 'POST' });
    const d = await r.json();
    if (d.message) pushAlert(d.message, 'info');
  } catch (e) {
    pushAlert('Request failed: ' + url, 'warning');
  }
}

async function togglePause() {
  const paused = document.getElementById('btn-pause').textContent === 'Resume';
  await apiCall(paused ? '/api/resume' : '/api/pause');
}

async function poll() {
  try {
    const r = await fetch('/api/metrics');
    const d = await r.json();
    updateUI(d);
  } catch {}
}

setInterval(poll, 500);
poll();
pushAlert('Dashboard loaded. Press Start to begin monitoring.', 'info');
