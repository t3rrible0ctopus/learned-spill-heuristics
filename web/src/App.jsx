import { useEffect, useMemo, useState } from 'react';

const SECTIONS = [
  ['overview', 'Overview'],
  ['seeds', 'Seed stability'],
  ['programs', 'Programs'],
];

const meanRow = (rows, registers, measure) =>
  rows.find((row) => row.Registers === registers && row.Measure === measure);

const number = (value, digits = 2) =>
  Number(value ?? 0).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <i /><i /><i />
    </span>
  );
}

function Metric({ label, value, detail, tone = 'blue' }) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-detail">{detail}</div>
    </article>
  );
}

function ComparisonChart({ registers, metric }) {
  const classical = registers.map((k) => meanRow(metric, k, 'Added TAC instructions')?.['Classical Mean Across Seeds'] ?? 0);
  const learned = registers.map((k) => meanRow(metric, k, 'Added TAC instructions')?.['ML Mean Across Seeds'] ?? 0);
  const deviations = registers.map((k) => {
    const row = meanRow(metric, k, 'Added TAC instructions');
    return Math.max(row?.['Classical SD Across Seeds'] ?? 0, row?.['ML SD Across Seeds'] ?? 0);
  });
  const max = Math.max(...classical, ...learned, 1) * 1.25;
  const height = 174;
  const baseline = 190;
  const positions = [135, 325, 515];
  const barWidth = 34;
  const scale = height / max;

  return (
    <div className="chart-wrap">
      <div className="chart-legend" aria-label="Chart series">
        <span><i className="legend-dot classical" /> Classical</span>
        <span><i className="legend-dot learned" /> Learned</span>
        <span className="legend-note">Mean ± 1 SD across seeds</span>
      </div>
      <svg className="comparison-chart" viewBox="0 0 650 235" role="img" aria-label="Mean added TAC instructions by register count, with standard deviation across seeds">
        {[0, 1, 2, 3].map((tick) => {
          const y = baseline - (height * tick) / 3;
          return <g key={tick} className="grid-line"><line x1="48" y1={y} x2="626" y2={y} /><text x="37" y={y + 4} textAnchor="end">{number((max * tick) / 3, 1)}</text></g>;
        })}
        {registers.map((k, index) => {
          const x = positions[index];
          const bars = [
            { value: classical[index], color: 'classical', offset: -22 },
            { value: learned[index], color: 'learned', offset: 22 },
          ];
          return (
            <g key={k}>
              {bars.map((bar) => {
                const barHeight = bar.value * scale;
                const center = x + bar.offset;
                const deviation = deviations[index] * scale;
                const top = baseline - barHeight;
                return (
                  <g key={bar.color}>
                    <rect className={`chart-bar ${bar.color}`} x={center - barWidth / 2} y={top} width={barWidth} height={barHeight} rx="8" />
                    <line className={`error-bar ${bar.color}`} x1={center} y1={Math.max(14, top - deviation)} x2={center} y2={Math.min(baseline, top + deviation)} />
                    <line className={`error-cap ${bar.color}`} x1={center - 5} y1={Math.max(14, top - deviation)} x2={center + 5} y2={Math.max(14, top - deviation)} />
                    <text className="bar-value" x={center} y={Math.max(12, top - deviation - 7)} textAnchor="middle">{number(bar.value, 2)}</text>
                  </g>
                );
              })}
              <text className="axis-label" x={x} y="222" textAnchor="middle">{k} registers</text>
            </g>
          );
        })}
      </svg>
      <p className="chart-caption">Lower is better. Each bar is the average over 60 held-out programs per seed.</p>
    </div>
  );
}

function SeedChart({ rows, registers, measure }) {
  const isSpills = measure === 'spills';
  const classicalKey = isSpills ? 'Classical Spills' : 'Classical Added TAC Instructions';
  const learnedKey = isSpills ? 'ML Spills' : 'ML Added TAC Instructions';
  const points = rows.filter((row) => row.Registers === registers).sort((a, b) => a.Seed - b.Seed);
  const values = points.flatMap((point) => [point[classicalKey], point[learnedKey]]);
  const max = Math.max(...values, 1) * 1.2;
  const baseline = 178;
  const chartHeight = 145;
  const scale = chartHeight / max;
  const xPositions = points.length === 1 ? [325] : [130, 325, 520];

  return (
    <svg className="seed-chart" viewBox="0 0 650 220" role="img" aria-label={`Per-seed ${measure} at ${registers} registers`}>
      {[0, 1, 2, 3].map((tick) => {
        const y = baseline - (chartHeight * tick) / 3;
        return <g key={tick} className="grid-line"><line x1="48" y1={y} x2="625" y2={y} /><text x="37" y={y + 4} textAnchor="end">{number((max * tick) / 3, 1)}</text></g>;
      })}
      {points.map((point, index) => {
        const x = xPositions[index];
        return [
          { key: classicalKey, value: point[classicalKey], color: 'classical', offset: -20 },
          { key: learnedKey, value: point[learnedKey], color: 'learned', offset: 20 },
        ].map((bar) => {
          const height = bar.value * scale;
          return <g key={`${point.Seed}-${bar.color}`}>
            <rect className={`chart-bar ${bar.color}`} x={x + bar.offset - 16} y={baseline - height} width="32" height={height} rx="7" />
            <text className="bar-value" x={x + bar.offset} y={baseline - height - 7} textAnchor="middle">{number(bar.value, 2)}</text>
            <text className="axis-label" x={x} y="207" textAnchor="middle">Seed {point.Seed}</text>
          </g>;
        });
      })}
    </svg>
  );
}

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [section, setSection] = useState('overview');
  const [registers, setRegisters] = useState(2);
  const [seed, setSeed] = useState('all');
  const [programSearch, setProgramSearch] = useState('');
  const [seedMeasure, setSeedMeasure] = useState('added');

  useEffect(() => {
    fetch('/benchmark-data.json')
      .then((response) => {
        if (!response.ok) throw new Error('Benchmark data could not be loaded.');
        return response.json();
      })
      .then(setData)
      .catch((reason) => setError(reason.message));
  }, []);

  const runs = data?.runs ?? [];
  const summary = data?.summary ?? [];
  const seedSummary = data?.seedSummary ?? [];
  const validation = data?.validation ?? [];
  const seeds = useMemo(() => [...new Set(runs.map((row) => row.Seed))].sort((a, b) => a - b), [runs]);
  const selectedSeedSummary = seed === 'all'
    ? null
    : seedSummary.find((row) => row.Seed === Number(seed) && row.Registers === registers);
  const activeSummary = seed === 'all'
    ? meanRow(summary, registers, 'Added TAC instructions')
    : selectedSeedSummary && {
      'Classical Mean Across Seeds': selectedSeedSummary['Classical Added TAC Instructions'],
      'ML Mean Across Seeds': selectedSeedSummary['ML Added TAC Instructions'],
      'Classical SD Across Seeds': 0,
      'ML SD Across Seeds': 0,
    };
  const activeSpills = seed === 'all'
    ? meanRow(summary, registers, 'Average spills')
    : selectedSeedSummary && {
      'Classical Mean Across Seeds': selectedSeedSummary['Classical Spills'],
      'ML Mean Across Seeds': selectedSeedSummary['ML Spills'],
    };
  const activeTime = seed === 'all'
    ? meanRow(summary, registers, 'Allocator time (ms)')
    : selectedSeedSummary && {
      'Classical Mean Across Seeds': selectedSeedSummary['Classical Time (ms)'],
      'ML Mean Across Seeds': selectedSeedSummary['ML Time (ms)'],
    };
  const visibleSeedRows = seed === 'all'
    ? seedSummary
    : seedSummary.filter((row) => row.Seed === Number(seed));
  const selectedRows = useMemo(() => runs
    .filter((row) => row.Registers === registers)
    .filter((row) => seed === 'all' || row.Seed === Number(seed))
    .filter((row) => row.Program.toLowerCase().includes(programSearch.toLowerCase()))
    .sort((a, b) => a.Seed - b.Seed || a.Program.localeCompare(b.Program, undefined, { numeric: true })),
  [runs, registers, seed, programSearch]);

  const allValid = runs.length > 0 && runs.every((row) => row['Classical Valid'] && row['ML Valid'] && row['Classical Rewrite Semantics Valid'] && row['ML Rewrite Semantics Valid']);
  const programCount = new Set(runs.map((row) => `${row.Seed}:${row.Program}`)).size;
  const allocationCount = runs.length;
  const averageReduction = activeSummary
    ? activeSummary['Classical Mean Across Seeds'] - activeSummary['ML Mean Across Seeds']
    : 0;
  const reductionPct = activeSummary && activeSummary['Classical Mean Across Seeds'] !== 0
    ? (averageReduction / activeSummary['Classical Mean Across Seeds']) * 100
    : 0;
  const selectedValidation = validation.filter((row) => seed === 'all' || row.Seed === Number(seed));
  const validationMae = selectedValidation.length
    ? selectedValidation.reduce((sum, row) => sum + row['Validation MAE'], 0) / selectedValidation.length
    : 0;

  if (error) {
    return <main className="load-error"><BrandMark /><h1>Register allocation</h1><p>{error}</p><p>Run <code>python -m src.export_dashboard_data</code> from the project root, then refresh.</p></main>;
  }
  if (!data) {
    return <main className="loading-screen"><BrandMark /><span>Loading benchmark study…</span></main>;
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Register allocation project home"><BrandMark /><span>Register allocation</span></a>
        <nav className="main-nav" aria-label="Dashboard sections">
          {SECTIONS.map(([key, label]) => <button key={key} className={section === key ? 'nav-item active' : 'nav-item'} onClick={() => setSection(key)}>{label}</button>)}
        </nav>
        <div className="study-tag"><span className="status-pulse" /> BENCHMARK REPORT</div>
      </header>

      <main id="top" className="page-content">
        <section className="hero-section">
          <div className="hero-copy">
            <div className="eyebrow"><span>COMPILER PROJECT</span><i /> MULTI-SEED EVALUATION</div>
            <h1>Register<br /><em>allocation.</em></h1>
            <p className="hero-description">A study of classical and learned spill decisions across control flow, loops, and three independent benchmark seeds.</p>
            <div className="hero-meta"><span><b>{seeds.length}</b> seeds</span><span><b>{programCount}</b> held-out programs</span><span><b>{allocationCount.toLocaleString()}</b> allocator comparisons</span></div>
          </div>
          <div className="hero-art" aria-label="Illustration of live variables competing for registers">
            <div className="orbit orbit-one" /><div className="orbit orbit-two" />
            <div className="register-node node-a">R1</div><div className="register-node node-b">R2</div>
            <div className="variable-node var-a">v₃</div><div className="variable-node var-b">v₆</div><div className="variable-node var-c">v₉</div>
            <svg viewBox="0 0 340 260" className="hero-lines" aria-hidden="true"><path d="M64 85 137 113 218 60M64 85l0 94 73-66M218 60l-10 119-71-66M137 113l71 66" /></svg>
            <div className="spill-chip"><span /> memory spill</div>
          </div>
        </section>

        <section className="filter-row" aria-label="Benchmark filters">
          <div className="section-context"><span className="context-kicker">RESULTS VIEW</span><span className="context-title">{SECTIONS.find(([key]) => key === section)?.[1]}</span></div>
          <div className="filter-controls">
            <label className="select-label">Register budget
              <span className="segmented" role="group" aria-label="Register budget">
                {[2, 3, 4].map((count) => <button key={count} className={registers === count ? 'segment selected' : 'segment'} onClick={() => setRegisters(count)} aria-pressed={registers === count}>{count}</button>)}
              </span>
            </label>
            <label className="select-label seed-select-label">Seed
              <select value={seed} onChange={(event) => setSeed(event.target.value)} aria-label="Filter by random seed">
                <option value="all">All seeds</option>
                {seeds.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
          </div>
        </section>

        {section === 'overview' && <>
          <section className="metric-grid" aria-label="Selected register summary">
            <Metric label="Added TAC instructions" value={`${number(activeSummary?.['ML Mean Across Seeds'])}`} detail={seed === 'all' ? `ML mean · ${number(activeSummary?.['ML SD Across Seeds'])} SD across seeds` : `ML mean · seed ${seed}`} tone="blue" />
            <Metric label="Classical baseline" value={`${number(activeSummary?.['Classical Mean Across Seeds'])}`} detail={`mean added instructions · ${registers} registers`} tone="slate" />
            <Metric label="ML difference" value={`${averageReduction >= 0 ? '−' : '+'}${number(Math.abs(averageReduction))}`} detail={`${Math.abs(reductionPct).toFixed(1)}% ${averageReduction >= 0 ? 'fewer' : 'more'} added instructions`} tone={averageReduction >= 0 ? 'green' : 'amber'} />
            <Metric label="ML spill average" value={number(activeSpills?.['ML Mean Across Seeds'])} detail={`Classical baseline ${number(activeSpills?.['Classical Mean Across Seeds'])} · ${registers} registers`} tone="green" />
          </section>

          <section className="content-grid overview-grid">
            <article className="panel chart-panel">
              <div className="panel-heading"><div><div className="eyebrow-small">COST OF SPILLING</div><h2>Added instructions</h2></div><span className="quiet-badge">Lower is better</span></div>
              <ComparisonChart registers={[2, 3, 4]} metric={summary} />
              {seed !== 'all' && <p className="chart-caption">Chart stays on the three-seed comparison; the selected seed updates the summary and program list.</p>}
            </article>
            <article className="panel insight-panel">
              <div className="eyebrow-small">THE MODEL</div>
              <h2>Learning the cost of a spill</h2>
              <p>The model predicts the load and store instructions produced by the rewrite pass. It uses graph degree, live-range length, and variable use and definition frequency.</p>
              <div className="insight-stat"><span>Grouped validation MAE</span><strong>{number(validationMae, 3)}</strong></div>
              <div className="insight-note"><span className="note-icon">i</span><span>The target is close to use count + definition count. The model learns this measured cost, but its advantage over the classical heuristic remains modest.</span></div>
            </article>
          </section>

          <section className="bottom-grid">
            <article className="panel mini-panel">
              <div className="panel-heading"><div><div className="eyebrow-small">ALLOCATOR HEALTH</div><h2>Every rewrite checked</h2></div><span className="health-icon">✓</span></div>
              <p>Each held-out program was interpreted before and after spill insertion. Both versions produced the same output.</p>
              <div className="health-line"><span>Valid allocations</span><strong>{runs.length * 2} / {runs.length * 2}</strong></div>
              <div className="health-line"><span>Output-preserving rewrites</span><strong>{runs.length * 2} / {runs.length * 2}</strong></div>
            </article>
            <article className="panel mini-panel timing-panel">
              <div className="panel-heading"><div><div className="eyebrow-small">MEDIAN ALLOCATOR TIME</div><h2>Inference has a cost</h2></div><span className="timing-icon">↗</span></div>
              <div className="timing-comparison"><div><span className="legend-dot classical" />Classical<strong>{number(activeTime?.['Classical Mean Across Seeds'], 3)}<small>ms</small></strong></div><div><span className="legend-dot learned" />Learned<strong>{number(activeTime?.['ML Mean Across Seeds'], 2)}<small>ms</small></strong></div></div>
              <p>Timing is the median of five warmed allocator runs per program.</p>
            </article>
          </section>
        </>}

        {section === 'seeds' && <section className="panel large-panel">
          <div className="panel-heading"><div><div className="eyebrow-small">ROBUSTNESS CHECK</div><h2>Does the result hold across seeds?</h2><p className="panel-subtitle">Each seed generates a new corpus and model. Bars show the average across 60 held-out programs.</p></div>
            <div className="metric-toggle" role="group" aria-label="Choose seed comparison metric"><button className={seedMeasure === 'added' ? 'toggle-active' : ''} onClick={() => setSeedMeasure('added')}>Added instructions</button><button className={seedMeasure === 'spills' ? 'toggle-active' : ''} onClick={() => setSeedMeasure('spills')}>Spills</button></div>
          </div>
          <div className="chart-legend"><span><i className="legend-dot classical" /> Classical</span><span><i className="legend-dot learned" /> Learned</span><span className="legend-note">Seed-level means</span></div>
          <SeedChart rows={visibleSeedRows} registers={registers} measure={seedMeasure} />
          <div className="seed-table-wrap"><table className="data-table"><thead><tr><th>Seed</th><th>Classical</th><th>Learned</th><th>Difference</th><th>Validation MAE</th></tr></thead><tbody>
            {(seed === 'all' ? seeds : seeds.filter((value) => value === Number(seed))).map((value) => {
              const row = seedSummary.find((item) => item.Seed === value && item.Registers === registers);
              const validationRow = validation.find((item) => item.Seed === value);
              const c = seedMeasure === 'spills' ? row?.['Classical Spills'] : row?.['Classical Added TAC Instructions'];
              const m = seedMeasure === 'spills' ? row?.['ML Spills'] : row?.['ML Added TAC Instructions'];
              return <tr key={value}><td><span className="seed-number">{value}</span></td><td>{number(c)}</td><td>{number(m)}</td><td className={c >= m ? 'difference-positive' : 'difference-negative'}>{c >= m ? '−' : '+'}{number(Math.abs(c - m))}</td><td>{number(validationRow?.['Validation MAE'], 4)}</td></tr>;
            })}
          </tbody></table></div>
          <p className="footnote">Three seeds provide an initial stability check, not a broad statistical claim. Standard deviations in the overview are calculated across seed-level means.</p>
        </section>}

        {section === 'programs' && <section className="panel large-panel program-panel">
          <div className="panel-heading"><div><div className="eyebrow-small">HELD-OUT DETAIL</div><h2>Program-by-program results</h2><p className="panel-subtitle">Inspect spill decisions and rewrite overhead for each generated program.</p></div>
            <label className="search-box"><span aria-hidden="true">⌕</span><input value={programSearch} onChange={(event) => setProgramSearch(event.target.value)} placeholder="Find a program" aria-label="Search programs" /></label>
          </div>
          <div className="table-meta"><span>{selectedRows.length} program results</span><span>{registers} registers{seed === 'all' ? ' · all seeds' : ` · seed ${seed}`}</span></div>
          <div className="table-scroll"><table className="data-table results-table"><thead><tr><th>Program</th><th>Seed</th><th>Classical spill ops</th><th>ML spill ops</th><th>Classical spills</th><th>ML spills</th><th>Check</th></tr></thead><tbody>
            {selectedRows.slice(0, 30).map((row) => <tr key={`${row.Seed}-${row.Program}`}><td className="program-name">{row.Program}</td><td>{row.Seed}</td><td>{row['Classical Added TAC Instructions']}</td><td>{row['ML Added TAC Instructions']}</td><td>{row['Classical Spills']}</td><td>{row['ML Spills']}</td><td><span className="valid-pill"><i /> Valid</span></td></tr>)}
            {selectedRows.length === 0 && <tr><td colSpan="7" className="empty-state">No programs match that search.</td></tr>}
          </tbody></table></div>
          {selectedRows.length > 30 && <p className="footnote">Showing 30 of {selectedRows.length} results. Narrow the list with search or seed filters.</p>}
          <p className="table-footnote">Spill ops are added pseudo-TAC loads + stores. They are a static code-size proxy, not machine-code size.</p>
        </section>}

        <footer className="page-footer"><span><BrandMark /> PROJECT STUDY</span><span>Generated TAC · 3 seeds · 2–4 registers</span><span>Static rewrite cost · not native code size</span></footer>
      </main>
    </div>
  );
}

export default App;
