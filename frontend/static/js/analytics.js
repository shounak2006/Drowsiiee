/* analytics.js */

let hourlyChart = null;
let distChart   = null;

function initHourlyChart(labels, values) {
  const colors = values.map(v =>
    v >= 65 ? 'rgba(248,81,73,0.7)'  :
    v >= 35 ? 'rgba(210,153,34,0.7)' : 'rgba(63,185,80,0.7)'
  );
  if (hourlyChart) hourlyChart.destroy();
  hourlyChart = new Chart(document.getElementById('hourlyChart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Avg Fatigue', data: values,
        backgroundColor: colors,
        borderColor: colors.map(c => c.replace('0.7','1')),
        borderWidth: 1, borderRadius: 4,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: '#1c2128', borderColor: '#30363d', borderWidth: 1, titleColor: '#8b949e', bodyColor: '#c9d1d9' }
      },
      scales: {
        x: { ticks: { color: '#8b949e', font: { size: 11 } }, grid: { color: '#21262d' } },
        y: { min: 0, max: 100, ticks: { color: '#8b949e', font: { size: 11 } }, grid: { color: '#21262d' } }
      }
    }
  });
}

function initDistChart(values) {
  const buckets = { '0–20': 0, '21–40': 0, '41–60': 0, '61–80': 0, '81–100': 0 };
  values.forEach(v => {
    if (v <= 20) buckets['0–20']++;
    else if (v <= 40) buckets['21–40']++;
    else if (v <= 60) buckets['41–60']++;
    else if (v <= 80) buckets['61–80']++;
    else buckets['81–100']++;
  });
  if (distChart) distChart.destroy();
  distChart = new Chart(document.getElementById('distChart'), {
    type: 'doughnut',
    data: {
      labels: Object.keys(buckets),
      datasets: [{
        data: Object.values(buckets),
        backgroundColor: [
          'rgba(63,185,80,0.7)', 'rgba(88,166,255,0.7)',
          'rgba(210,153,34,0.7)', 'rgba(248,81,73,0.5)', 'rgba(248,81,73,0.85)',
        ],
        borderColor: '#161b22', borderWidth: 2,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#8b949e', font: { size: 11 }, padding: 10, boxWidth: 12 } },
        tooltip: { backgroundColor: '#1c2128', borderColor: '#30363d', borderWidth: 1, titleColor: '#8b949e', bodyColor: '#c9d1d9' }
      }
    }
  });
}

async function loadAnalytics() {
  try {
    const [trendRes, logRes] = await Promise.all([
      fetch('/api/trend'),
      fetch('/api/logs?limit=2000'),
    ]);
    const trend = await trendRes.json();
    const logs  = await logRes.json();

    const hourly = trend.hourly_fatigue || {};
    const hours  = Object.keys(hourly).sort();
    const values = hours.map(h => hourly[h]);

    document.getElementById('an-fatigued-hour').textContent =
      trend.most_fatigued_hour !== '--' ? trend.most_fatigued_hour + ':00' : '--';
    document.getElementById('an-alert-hour').textContent =
      trend.most_alert_hour !== '--' ? trend.most_alert_hour + ':00' : '--';
    document.getElementById('an-hours-tracked').textContent = hours.length || '--';

    const allFatigue = logs.map(e => e.fatigue_score).filter(v => v !== undefined);
    const avgFatigue = allFatigue.length
      ? (allFatigue.reduce((a, b) => a + b, 0) / allFatigue.length).toFixed(1) : '--';
    document.getElementById('an-avg-fatigue').textContent = avgFatigue;

    if (hours.length) {
      initHourlyChart(hours.map(h => h + ':00'), values);
      initDistChart(allFatigue);
    }

    renderObservations(trend, values, hours, allFatigue, logs);
  } catch (e) {
    console.error('Analytics load error:', e);
  }
}

function renderObservations(trend, values, hours, allFatigue, logs) {
  const obs = [];
  if (!hours.length) {
    obs.push({ text: 'No session data available yet. Start monitoring to collect analytics.', cls: '' });
  } else {
    const avg = allFatigue.length ? allFatigue.reduce((a,b)=>a+b,0)/allFatigue.length : 0;
    if (avg < 30)       obs.push({ text: `Overall session average fatigue is low (${avg.toFixed(1)}/100). Driver alertness maintained.`, cls: 'positive' });
    else if (avg < 60)  obs.push({ text: `Session average fatigue is moderate (${avg.toFixed(1)}/100). Monitor closely during long drives.`, cls: 'caution' });
    else                obs.push({ text: `High average fatigue detected (${avg.toFixed(1)}/100). Consider a break.`, cls: 'danger' });

    if (trend.most_fatigued_hour !== '--') {
      obs.push({ text: `Peak fatigue recorded at ${trend.most_fatigued_hour}:00 with score ${values[hours.indexOf(trend.most_fatigued_hour)]?.toFixed(1)}.`, cls: 'caution' });
    }
    if (trend.most_alert_hour !== '--' && trend.most_alert_hour !== trend.most_fatigued_hour) {
      obs.push({ text: `Driver was most alert at ${trend.most_alert_hour}:00.`, cls: 'positive' });
    }
    const criticalEvents = logs.filter(e => e.status === 'CRITICAL').length;
    if (criticalEvents > 0) obs.push({ text: `${criticalEvents} CRITICAL event(s) logged this session.`, cls: 'danger' });
    else obs.push({ text: 'No critical drowsiness events recorded this session.', cls: 'positive' });

    if (hours.length >= 2) {
      const first = values[0], last = values[values.length-1];
      if (last > first + 10) obs.push({ text: 'Fatigue is trending upward across the session.', cls: 'caution' });
      else if (last < first - 10) obs.push({ text: 'Fatigue decreased over the session — driver recovered well.', cls: 'positive' });
    }
  }
  document.getElementById('trend-obs').innerHTML =
    obs.map(o => `<li class="obs-item ${o.cls}">${o.text}</li>`).join('');
}

loadAnalytics();
setInterval(loadAnalytics, 15000);
