/* global Papa, math, Chart */

(function () {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const fileInfo = document.getElementById('fileInfo');
  const availableColumnsEl = document.getElementById('availableColumns');
  const featuresZone = document.getElementById('featuresZone');
  const targetZone = document.getElementById('targetZone');
  const trainBtn = document.getElementById('trainBtn');
  const resetBtn = document.getElementById('resetBtn');
  const previewEl = document.getElementById('preview');
  const metricsEl = document.getElementById('metrics');
  const coefficientsEl = document.getElementById('coefficients');
  const scatterCanvas = document.getElementById('scatterChart');
  const alphaRange = document.getElementById('alphaRange');
  const alphaValue = document.getElementById('alphaValue');

  let rawRows = [];
  let columnNames = [];
  let numericColumns = [];
  let selectedFeatures = [];
  let selectedTarget = null;
  let chartInstance = null;

  // ---- File input / drop ----
  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });

  ['dragenter', 'dragover'].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ;['dragleave', 'drop'].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (file) parseCsvFile(file);
  });

  fileInput.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (file) parseCsvFile(file);
  });

  // ---- Ridge alpha ----
  alphaRange.addEventListener('input', () => {
    alphaValue.textContent = Number(alphaRange.value).toFixed(2);
  });
  alphaValue.textContent = Number(alphaRange.value).toFixed(2);

  // ---- Reset ----
  resetBtn.addEventListener('click', () => {
    selectedFeatures = [];
    selectedTarget = null;
    renderSelectionZones();
    updateTrainButtonState();
  });

  // ---- Train ----
  trainBtn.addEventListener('click', () => {
    try {
      const alpha = Number(alphaRange.value) || 0;
      const { X, y, usedRowCount } = buildDesignMatrix(rawRows, selectedFeatures, selectedTarget);
      if (usedRowCount < 2) {
        notify('Not enough valid rows to train.', true);
        return;
      }

      const beta = solveLinearRegression(X, y, alpha);
      const yHat = math.multiply(X, beta).map((row) => row[0]);
      const yArr = y.map((row) => row[0]);

      const metrics = computeMetrics(yArr, yHat);
      renderMetrics(metrics);
      renderCoefficients(beta, selectedFeatures);
      renderScatter(yArr, yHat);
      notify('Training completed successfully.');
    } catch (err) {
      console.error(err);
      notify('Training failed: ' + err.message, true);
    }
  });

  // ---- CSV parsing ----
  function parseCsvFile(file) {
    fileInfo.classList.add('hidden');
    fileInfo.textContent = '';
    notify('Parsing CSV...');
    Papa.parse(file, {
      header: true,
      dynamicTyping: true,
      worker: true,
      skipEmptyLines: true,
      complete: (results) => {
        const rows = results.data.filter((r) => r && typeof r === 'object');
        rawRows = rows;
        columnNames = inferColumnNames(rows);
        numericColumns = detectNumericColumns(rows, columnNames);
        renderAvailableColumns(numericColumns);
        renderPreview(rows, columnNames);
        selectedFeatures = [];
        selectedTarget = null;
        renderSelectionZones();
        updateTrainButtonState();
        fileInfo.textContent = `${file.name} • ${rows.length} rows • ${numericColumns.length} numeric columns`;
        fileInfo.classList.remove('hidden');
        notify('CSV parsed. Choose features and target.');
      },
      error: (error) => {
        notify('Failed to parse CSV: ' + error.message, true);
      }
    });
  }

  function inferColumnNames(rows) {
    const first = rows[0] || {};
    return Object.keys(first);
  }

  function detectNumericColumns(rows, cols) {
    const sampleCount = Math.min(rows.length, 1000);
    const numeric = [];
    for (const col of cols) {
      let valid = 0;
      let seen = 0;
      for (let i = 0; i < sampleCount; i++) {
        const v = rows[i]?.[col];
        if (v === null || v === undefined || v === '') continue;
        seen++;
        if (typeof v === 'number' && Number.isFinite(v)) valid++;
        else if (typeof v === 'string') {
          const num = Number(v);
          if (Number.isFinite(num)) valid++;
        }
      }
      if (seen > 0 && valid / seen >= 0.9) numeric.push(col);
    }
    return numeric;
  }

  // ---- Chips and DnD ----
  function renderAvailableColumns(cols) {
    availableColumnsEl.innerHTML = '';
    cols.forEach((col) => {
      const chip = createChip(col);
      chip.setAttribute('data-zone', 'pool');
      chip.draggable = true;
      chip.addEventListener('dragstart', (e) => onChipDragStart(e, col));
      availableColumnsEl.appendChild(chip);
    });
  }

  function createChip(label, withRemove = false, zone = 'pool') {
    const div = document.createElement('div');
    div.className = 'chip';
    div.textContent = label;
    div.setAttribute('data-col', label);
    div.setAttribute('data-zone', zone);
    if (withRemove) {
      const btn = document.createElement('button');
      btn.className = 'chip__remove';
      btn.setAttribute('aria-label', `Remove ${label}`);
      btn.textContent = '×';
      btn.addEventListener('click', () => removeFromZone(label, zone));
      div.appendChild(btn);
    }
    return div;
  }

  function onChipDragStart(e, col) {
    e.dataTransfer.setData('text/plain', col);
    e.dataTransfer.effectAllowed = 'move';
  }

  function setupZoneDnD(zoneEl, zoneType) {
    zoneEl.addEventListener('dragover', (e) => {
      e.preventDefault();
      zoneEl.classList.add('dragover');
    });
    zoneEl.addEventListener('dragleave', () => zoneEl.classList.remove('dragover'));
    zoneEl.addEventListener('drop', (e) => {
      e.preventDefault();
      zoneEl.classList.remove('dragover');
      const col = e.dataTransfer.getData('text/plain');
      if (!numericColumns.includes(col)) return;
      if (zoneType === 'features') addFeature(col);
      else if (zoneType === 'target') setTarget(col);
    });
  }

  setupZoneDnD(featuresZone, 'features');
  setupZoneDnD(targetZone, 'target');

  function addFeature(col) {
    if (selectedFeatures.includes(col)) return;
    if (selectedTarget === col) return;
    selectedFeatures = [...selectedFeatures, col];
    renderSelectionZones();
    updateTrainButtonState();
  }

  function setTarget(col) {
    if (selectedTarget === col) return;
    if (selectedFeatures.includes(col)) return;
    selectedTarget = col;
    renderSelectionZones();
    updateTrainButtonState();
  }

  function removeFromZone(col, zone) {
    if (zone === 'features') {
      selectedFeatures = selectedFeatures.filter((c) => c !== col);
    } else if (zone === 'target') {
      if (selectedTarget === col) selectedTarget = null;
    }
    renderSelectionZones();
    updateTrainButtonState();
  }

  function renderSelectionZones() {
    featuresZone.innerHTML = '';
    targetZone.innerHTML = '';
    selectedFeatures.forEach((f) => {
      const chip = createChip(f, true, 'features');
      featuresZone.appendChild(chip);
    });
    if (selectedTarget) {
      const chip = createChip(selectedTarget, true, 'target');
      targetZone.appendChild(chip);
    }
  }

  function updateTrainButtonState() {
    trainBtn.disabled = !(selectedTarget && selectedFeatures.length > 0 && rawRows.length > 0);
  }

  // ---- Preview ----
  function renderPreview(rows, cols) {
    const count = Math.min(rows.length, 12);
    const table = document.createElement('table');
    const thead = document.createElement('thead');
    const thr = document.createElement('tr');
    cols.forEach((c) => {
      const th = document.createElement('th'); th.textContent = c; thr.appendChild(th);
    });
    thead.appendChild(thr);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    for (let i = 0; i < count; i++) {
      const r = document.createElement('tr');
      cols.forEach((c) => {
        const td = document.createElement('td');
        const v = rows[i]?.[c];
        td.textContent = formatValue(v);
        r.appendChild(td);
      });
      tbody.appendChild(r);
    }
    table.appendChild(tbody);

    previewEl.innerHTML = '';
    previewEl.appendChild(table);
  }

  function formatValue(v) {
    if (typeof v === 'number') {
      if (!Number.isFinite(v)) return 'NaN';
      const abs = Math.abs(v);
      if ((abs !== 0 && (abs < 0.001 || abs > 1e6))) return v.toExponential(3);
      return String(Math.round(v * 1000) / 1000);
    }
    return String(v ?? '');
  }

  // ---- Linear regression engine ----
  function buildDesignMatrix(rows, features, target) {
    const X = [];
    const y = [];
    let used = 0;

    for (const row of rows) {
      const targetValRaw = row[target];
      const targetVal = toNumber(targetValRaw);
      if (!Number.isFinite(targetVal)) continue;

      const featureVals = [];
      let ok = true;
      for (const f of features) {
        const v = toNumber(row[f]);
        if (!Number.isFinite(v)) { ok = false; break; }
        featureVals.push(v);
      }
      if (!ok) continue;

      X.push([1, ...featureVals]); // intercept
      y.push([targetVal]);
      used++;
    }

    return { X, y, usedRowCount: used };
  }

  function toNumber(v) {
    if (typeof v === 'number') return v;
    if (typeof v === 'string') {
      const n = Number(v.trim());
      return Number.isFinite(n) ? n : NaN;
    }
    return NaN;
  }

  function solveLinearRegression(X, y, alpha) {
    if (!Array.isArray(X) || X.length === 0) throw new Error('Empty design matrix');
    const Xt = math.transpose(X);
    const XtX = math.multiply(Xt, X);
    const XtY = math.multiply(Xt, y);

    let A = XtX;
    if (alpha && alpha > 0) {
      A = addRidgeToXtX(A, alpha);
    }

    // Try direct inverse; if it fails, add small ridge and retry
    try {
      const inv = math.inv(A);
      return math.multiply(inv, XtY);
    } catch (e) {
      const inv = math.inv(addRidgeToXtX(XtX, Math.max(alpha || 0, 1e-6)));
      return math.multiply(inv, XtY);
    }
  }

  function addRidgeToXtX(XtX, alpha) {
    const A = XtX.map((row) => row.slice());
    for (let i = 0; i < A.length; i++) {
      // Do not regularize the intercept term (index 0)
      if (i === 0) continue;
      A[i][i] = A[i][i] + alpha;
    }
    return A;
  }

  function computeMetrics(yTrue, yPred) {
    const n = Math.min(yTrue.length, yPred.length);
    let sse = 0, mae = 0;
    let sum = 0;
    for (let i = 0; i < n; i++) { sum += yTrue[i]; }
    const mean = sum / n;

    let sst = 0;
    for (let i = 0; i < n; i++) {
      const err = yTrue[i] - yPred[i];
      sse += err * err;
      mae += Math.abs(err);
      const d = yTrue[i] - mean;
      sst += d * d;
    }
    const rmse = Math.sqrt(sse / n);
    const r2 = 1 - (sse / (sst || Number.EPSILON));
    return { n, r2, rmse, mae: mae / n };
  }

  function renderMetrics({ n, r2, rmse, mae }) {
    const table = document.createElement('table');
    const tbody = document.createElement('tbody');
    const rows = [
      ['Rows used', n],
      ['R²', formatNumber(r2)],
      ['RMSE', formatNumber(rmse)],
      ['MAE', formatNumber(mae)]
    ];
    rows.forEach(([k, v]) => {
      const tr = document.createElement('tr');
      const td1 = document.createElement('td'); td1.textContent = k; tr.appendChild(td1);
      const td2 = document.createElement('td'); td2.textContent = String(v); tr.appendChild(td2);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    metricsEl.innerHTML = '';
    metricsEl.appendChild(table);
  }

  function renderCoefficients(beta, features) {
    const table = document.createElement('table');
    const thead = document.createElement('thead');
    const thr = document.createElement('tr');
    ;['Term', 'Coefficient'].forEach((h) => { const th = document.createElement('th'); th.textContent = h; thr.appendChild(th); });
    thead.appendChild(thr);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    const rows = [['Intercept', beta[0][0]]];
    for (let i = 0; i < features.length; i++) {
      rows.push([features[i], beta[i + 1][0]]);
    }
    rows.forEach(([name, val]) => {
      const tr = document.createElement('tr');
      const td1 = document.createElement('td'); td1.textContent = name; tr.appendChild(td1);
      const td2 = document.createElement('td'); td2.textContent = formatNumber(val); tr.appendChild(td2);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    coefficientsEl.innerHTML = '';
    coefficientsEl.appendChild(table);
  }

  function formatNumber(v) {
    if (!Number.isFinite(v)) return String(v);
    const abs = Math.abs(v);
    if (abs !== 0 && (abs < 0.0001 || abs > 1e6)) return v.toExponential(6);
    return String(Math.round(v * 1e6) / 1e6);
  }

  function renderScatter(actual, predicted) {
    if (chartInstance) { chartInstance.destroy(); chartInstance = null; }

    const n = Math.min(actual.length, predicted.length);
    const points = [];
    let minV = Infinity, maxV = -Infinity;
    for (let i = 0; i < n; i++) {
      const a = actual[i];
      const p = predicted[i];
      points.push({ x: a, y: p });
      if (Number.isFinite(a)) { minV = Math.min(minV, a); maxV = Math.max(maxV, a); }
      if (Number.isFinite(p)) { minV = Math.min(minV, p); maxV = Math.max(maxV, p); }
    }
    if (!Number.isFinite(minV) || !Number.isFinite(maxV)) { minV = 0; maxV = 1; }
    const pad = (maxV - minV) * 0.05 || 1;
    const minAxis = minV - pad;
    const maxAxis = maxV + pad;

    const ctx = scatterCanvas.getContext('2d');
    chartInstance = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [
          {
            label: 'Predicted vs Actual',
            data: points,
            pointRadius: 3,
            pointBackgroundColor: '#7aa2f7',
            pointBorderColor: '#7aa2f7',
          },
          {
            label: 'Ideal',
            data: [ { x: minAxis, y: minAxis }, { x: maxAxis, y: maxAxis } ],
            type: 'line',
            borderColor: '#58a6ff',
            borderDash: [5, 5],
            fill: false,
            pointRadius: 0,
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: '#e6edf3' } },
          tooltip: { mode: 'nearest', intersect: false }
        },
        scales: {
          x: {
            type: 'linear',
            title: { text: 'Actual', display: true, color: '#a3b1c6' },
            grid: { color: 'rgba(255,255,255,0.06)' },
            ticks: { color: '#a3b1c6' },
            min: minAxis,
            max: maxAxis,
          },
          y: {
            title: { text: 'Predicted', display: true, color: '#a3b1c6' },
            grid: { color: 'rgba(255,255,255,0.06)' },
            ticks: { color: '#a3b1c6' },
            min: minAxis,
            max: maxAxis,
          }
        }
      }
    });
  }

  // ---- Notifications ----
  function notify(message, isError = false) {
    console[isError ? 'warn' : 'log'](message);
  }
})();
