const API_URL = "http://localhost:8000";

let chart = null;
let areaSeries = null;
let vixSeries = null;

// DOM Elements
const regimeBadge = document.getElementById('regime-badge');
const regimeExplanation = document.getElementById('regime-explanation');
const riskValue = document.getElementById('risk-value');
const riskProgress = document.getElementById('risk-progress');
const kpiSp500 = document.getElementById('kpi-sp500');
const kpiVix = document.getElementById('kpi-vix');
const kpiGold = document.getElementById('kpi-gold');
const kpiBtc = document.getElementById('kpi-btc');
const kpiIbov = document.getElementById('kpi-ibov');
const kpiSelic = document.getElementById('kpi-selic');
const kpiUsdbrl = document.getElementById('kpi-usdbrl');
const kpiFng = document.getElementById('kpi-fng');
const newsFeed = document.getElementById('news-feed');
const btnEtl = document.getElementById('btn-etl');
const toast = document.getElementById('toast');
const navItems = document.querySelectorAll('.nav-item');
const tabContents = document.querySelectorAll('.tab-content');
const macroContent = document.getElementById('macro-content');
const marketsGrid = document.getElementById('markets-grid');
const fullNewsFeed = document.getElementById('full-news-feed');
const intelligenceAnalysis = document.getElementById('intelligence-analysis');
const infoModal = document.getElementById('info-modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const closeModal = document.getElementById('close-modal');

// Indicator definitions
const INDICATOR_GUIDE = {
    sp500: {
        title: "S&P 500 Index",
        content: `
            <div class="guide-item">
                <p>O <strong>Standard & Poor's 500</strong> é o principal termômetro das 500 maiores empresas dos EUA. É o indicador número 1 de "Risk-On" ou "Risk-Off".</p>
                <ul>
                    <li><strong>Alta:</strong> Indica apetite por risco e otimismo econômico.</li>
                    <li><strong>Baixa:</strong> Indica pessimismo e fuga para ativos de proteção.</li>
                </ul>
            </div>
        `
    },
    vix: {
        title: "VIX (Fear Index)",
        content: `
            <div class="guide-item">
                <p>O <strong>Índice de Volatilidade CBOE (VIX)</strong> mede a expectativa de volatilidade do mercado. É conhecido como o "Índice do Medo".</p>
                <ul>
                    <li><strong>Abaixo de 20:</strong> Mercado calmo, baixa percepção de risco.</li>
                    <li><strong>Acima de 30:</strong> Pânico ou estresse severo, alta volatilidade.</li>
                </ul>
            </div>
        `
    },
    gold: {
        title: "Gold (XAU/USD)",
        content: `
            <div class="guide-item">
                <p>O <strong>Ouro</strong> é o ativo de reserva de valor milenar. Funciona como proteção contra inflação e crises geopolíticas.</p>
                <ul>
                    <li><strong>Alta:</strong> Indica que investidores estão buscando segurança (Safe Haven).</li>
                    <li><strong>Valor intrínseco:</strong> Não depende de bancos centrais, por isso sobe quando a confiança no Fiat (dinheiro papel) cai.</li>
                </ul>
            </div>
        `
    },
    flights: {
        title: "Global Air Traffic",
        content: `
            <div class="guide-item">
                <p>O tráfego aéreo é um indicador de <strong>atividade econômica real</strong> e mobilidade global.</p>
                <ul>
                    <li><strong>Correlação:</strong> Quedas abruptas (como em 2020) precedem crises severas de consumo e PIB.</li>
                    <li><strong>Turismo e Negócios:</strong> Reflete a saúde financeira das famílias e empresas.</li>
                </ul>
            </div>
        `
    },
    btc: {
        title: "Bitcoin (BTC/USD)",
        content: `
            <div class="guide-item">
                <p>O <strong>Bitcoin</strong> é o "Ouro Digital". É o benchmark de ativos digitais e reflete liquidez e apetite por risco tecnológico.</p>
                <ul>
                    <li><strong>Alta:</strong> Geralmente correlacionado com liquidez global abundante.</li>
                    <li><strong>Baixa:</strong> Indica aperto monetário ou fuga para "qualidade" (Fixed Income).</li>
                </ul>
            </div>
        `
    },
    fng: {
        title: "Fear & Greed Index",
        content: `
            <div class="guide-item">
                <p>O <strong>Índice de Medo e Ganância</strong> cristaliza o sentimento do mercado em um número de 0 a 100.</p>
                <ul>
                    <li><strong>0-25 (Extreme Fear):</strong> Pode sinalizar uma oportunidade de compra (o mercado está pessimista demais).</li>
                    <li><strong>75-100 (Extreme Greed):</strong> Sinal de alerta para correção (euforia irracional).</li>
                </ul>
            </div>
        `
    },
    ibov: {
        title: "Ibovespa (IBOV)",
        content: `
            <div class="guide-item">
                <p>O <strong>Índice Bovespa</strong> é o principal indicador de desempenho das ações negociadas na B3. Reúne as empresas mais importantes do mercado brasileiro.</p>
                <ul>
                    <li><strong>Alta:</strong> Reflete otimismo com a economia local e fluxo de capital estrangeiro.</li>
                    <li><strong>Baixa:</strong> Indica aversão ao risco Brasil ou deterioração do cenário fiscal/econômico.</li>
                </ul>
            </div>
        `
    },
    selic: {
        title: "Taxa SELIC",
        content: `
            <div class="guide-item">
                <p>A <strong>Selic</strong> é a taxa básica de juros da economia brasileira, definida pelo COPOM.</p>
                <ul>
                    <li><strong>Juros Altos:</strong> Controlam a inflação, mas encarecem o crédito e podem frear o crescimento.</li>
                    <li><strong>Juros Baixos:</strong> Estimulam o consumo e o investimento, mas podem aumentar a inflação.</li>
                </ul>
            </div>
        `
    },
    usdbrl: {
        title: "USD / BRL (Câmbio)",
        content: `
            <div class="guide-item">
                <p>O valor do <strong>Dólar em Reais</strong>. É um termômetro direto da confiança do investidor estrangeiro no Brasil.</p>
                <ul>
                    <li><strong>Alta do Dólar:</strong> Pode indicar fuga de capital ou inflação importada.</li>
                    <li><strong>Dólar Baixo:</strong> Ajuda a controlar a inflação e reflete maior apetite pelo Real.</li>
                </ul>
            </div>
        `
    },
    ipca: {
        title: "IPCA (Inflação)",
        content: `
            <div class="guide-item">
                <p>O <strong>Índice Nacional de Preços ao Consumidor Amplo</strong> mede a inflação oficial do Brasil.</p>
                <ul>
                    <li><strong>Meta:</strong> O Banco Central usa a Selic para manter este índice dentro da meta.</li>
                    <li><strong>Impacto:</strong> Afeta o poder de compra da população e as decisões de investimento.</li>
                </ul>
            </div>
        `
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log("MacroPulse Initializing...");
    initChart();
    initNavigation();
    fetchData();
    setInterval(fetchData, 60000); // 1 minute refresh

    btnEtl.addEventListener('click', triggerETL);

    // Modal Events
    closeModal.addEventListener('click', () => infoModal.classList.remove('show'));
    window.addEventListener('click', (e) => { if (e.target === infoModal) infoModal.classList.remove('show'); });

    // Info Buttons
    document.querySelectorAll('.info-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const type = btn.getAttribute('data-info');
            if (INDICATOR_GUIDE[type]) {
                modalTitle.textContent = INDICATOR_GUIDE[type].title;
                modalBody.innerHTML = INDICATOR_GUIDE[type].content;
                infoModal.classList.add('show');
            }
        });
    });
    
    window.addEventListener('resize', () => {
        if (chart) {
            const container = document.getElementById('mainChart');
            if (container) {
                chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
            }
        }
    });

    // Asset Search Logic Initialization
    initAssetSearch();
});

let allTickers = [];

function initAssetSearch() {
    const searchInput = document.getElementById('asset-search');
    const searchResults = document.getElementById('search-results');
    if (!searchInput || !searchResults) return;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toUpperCase();
        if (!query) {
            searchResults.classList.add('hidden');
            return;
        }

        const filtered = allTickers.filter(t => t.ticker.includes(query));
        renderSearchResults(filtered, searchResults);
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchResults.classList.add('hidden');
            searchInput.blur();
        }
    });

    searchResults.addEventListener('click', (e) => {
        const item = e.target.closest('.search-result-item');
        if (item && item.dataset.ticker) {
            navigateToAsset(item.dataset.ticker);
            searchInput.value = '';
            searchResults.classList.add('hidden');
        }
    });

    // CMD+K to focus search (Cross-platform)
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }
    });

    // Close results when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            searchResults.classList.add('hidden');
        }
    });
}

function updateSearchIndex(data) {
    if (!data) return;
    const uniqueTickers = [...new Set(data.map(item => item.series_type))];
    allTickers = uniqueTickers.map(ticker => {
        const latestPoints = data.filter(d => d.series_type === ticker);
        const latestValue = latestPoints.length > 0 ? latestPoints[latestPoints.length - 1].value : 0;
        return {
            ticker: ticker,
            price: latestValue
        };
    });
}

function renderSearchResults(results, container) {
    if (results.length === 0) {
        container.innerHTML = '<div class="search-result-item">NO MATCHES FOUND</div>';
    } else {
        container.innerHTML = results.map(t => `
            <div class="search-result-item" data-ticker="${t.ticker}">
                <span class="ticker">${t.ticker}</span>
                <span class="price">${t.price.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
            </div>
        `).join('');
    }
    container.classList.remove('hidden');
}

function navigateToAsset(ticker) {
    // Check if it's on Dashboard (KPI Cards)
    const dashboardKPI = document.getElementById(`kpi-${ticker.toLowerCase()}`) || 
                         document.querySelector(`[data-info="${ticker.toLowerCase()}"]`);
    
    // Check Markets View
    const marketCards = Array.from(document.querySelectorAll('.market-mini-card'));
    const marketCard = marketCards.find(c => c.textContent.includes(ticker));

    if (marketCard) {
        switchTab('markets');
        setTimeout(() => {
            marketCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            marketCard.classList.add('highlight-asset');
            setTimeout(() => marketCard.classList.remove('highlight-asset'), 2000);
        }, 300);
    } else if (dashboardKPI) {
        switchTab('dashboard');
        const card = dashboardKPI.closest('.kpi-card');
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            card.classList.add('highlight-asset');
            setTimeout(() => card.classList.remove('highlight-asset'), 2000);
        }
    }
}

function switchTab(tab) {
    const navItem = document.querySelector(`.nav-item[data-tab="${tab}"]`);
    if (navItem) navItem.click();
}

function initNavigation() {
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute('data-tab');
            
            // Update Nav
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Update Views
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `view-${targetTab}`) {
                    content.classList.add('active');
                }
            });

            // Re-render chart if switching to dashboard
            if (targetTab === 'dashboard' && chart) {
                setTimeout(() => {
                    const container = document.getElementById('mainChart');
                    chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
                }, 100);
            }
        });
    });
}

function initChart() {
    const container = document.getElementById('mainChart');
    if (!container) return;

    const width = container.clientWidth || 600;
    const height = container.clientHeight || 400;

    chart = LightweightCharts.createChart(container, {
        width: width,
        height: height,
        layout: {
            background: { type: 'solid', color: 'transparent' },
            textColor: '#94a3b8',
        },
        grid: {
            vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
            horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: 'rgba(255, 255, 255, 0.1)',
        },
        timeScale: {
            borderColor: 'rgba(255, 255, 255, 0.1)',
        },
    });

    try {
        areaSeries = chart.addAreaSeries({
            lineColor: '#38bdf8',
            topColor: 'rgba(56, 189, 248, 0.4)',
            bottomColor: 'rgba(56, 189, 248, 0)',
            lineWidth: 3,
            priceFormat: { type: 'price', precision: 2, minMove: 0.01 },
        });

        vixSeries = chart.addLineSeries({
            color: '#f59e0b',
            lineWidth: 2,
            lineStyle: 2, // Dashed
            priceScaleId: 'vix_scale',
        });

        chart.priceScale('vix_scale').applyOptions({
            position: 'left',
            borderColor: 'rgba(255, 255, 255, 0.1)',
        });
    } catch (e) {
        console.error("Error adding series to chart:", e);
    }
}

// ── Last-updated tracking ──────────────────────────────────────────────────
let lastUpdateTime = null;
let lastRiskScore  = null;

function startLastUpdatedTicker() {
    const el = document.getElementById('last-updated-label');
    if (!el) return;
    setInterval(() => {
        if (!lastUpdateTime) { el.textContent = 'Awaiting data...'; return; }
        const secs = Math.round((Date.now() - lastUpdateTime) / 1000);
        if (secs < 60)  el.textContent = `Updated ${secs}s ago`;
        else if (secs < 3600) el.textContent = `Updated ${Math.round(secs/60)}m ago`;
        else el.textContent = `Updated ${Math.round(secs/3600)}h ago`;
    }, 1000);
}

function pulseElement(el) {
    if (!el) return;
    el.classList.remove('data-pulse');
    void el.offsetWidth; // force reflow
    el.classList.add('data-pulse');
}

async function fetchData() {
    try {
        const [intellResponse, tsResponse] = await Promise.all([
            fetch(`${API_URL}/intelligence/global`).catch(e => ({ok: false, error: e})),
            fetch(`${API_URL}/timeseries/global`).catch(e => ({ok: false, error: e}))
        ]);

        if (intellResponse.ok) {
            const intell = await intellResponse.json();
            window.lastIntelligence = intell;

            // Pulse risk score only when value changes
            const newRisk = intell.risk_score;
            if (newRisk !== lastRiskScore) {
                pulseElement(riskValue);
                lastRiskScore = newRisk;
            }

            updateUI(intell);
            updateIntelligenceView(intell);
            lastUpdateTime = Date.now();

            window.dispatchEvent(new CustomEvent('macropulse:alerts', { detail: intell.alerts || [] }));
        } else {
            console.warn("Intelligence API error. Try running ETL.");
        }

        if (tsResponse.ok) {
            const tsData = await tsResponse.json();
            updateChartData(tsData.data);
            updateMarketsView(tsData.data);
            updateMacroView(tsData.data);
            updateSearchIndex(tsData.data);
        }
    } catch (error) {
        console.error("Error in fetchData loop:", error);
    }
}

function updateUI(data) {
    if (!data || !data.kpis) return;
    const { kpis, news, activity } = data;

    // Regime & Risk
    if (regimeBadge) {
        regimeBadge.textContent = kpis.regime || 'Unknown';
        regimeBadge.style.backgroundColor = getBadgeColor(kpis.regime_color, 0.2);
        regimeBadge.style.color = getBadgeColor(kpis.regime_color, 1);
    }
    if (regimeExplanation) regimeExplanation.textContent = kpis.regime_explanation || '--';
    
    if (riskValue) riskValue.textContent = kpis.risk_score || '--';
    if (riskProgress) riskProgress.style.width = `${kpis.risk_score || 0}%`;

    // Dashboard KPIs (Standard path)
    if (kpiSp500) {
        const spRet = kpis.sp500_daily_change || 0;
        kpiSp500.textContent = `${spRet >= 0 ? '+' : ''}${spRet.toFixed(2)}%`;
        kpiSp500.className = `kpi-value ${spRet >= 0 ? 'text-success' : 'text-danger'}`;
    }
    
    if (kpiVix) kpiVix.textContent = kpis.vix ? kpis.vix.toFixed(2) : '0.00';
    if (kpiGold) kpiGold.textContent = kpis.gold_price ? `$${kpis.gold_price.toLocaleString(undefined, {maximumFractionDigits: 2})}` : '$0';
    
    // Update Bitcoin & Brasil (New Intelligence path)
    const brData = data.brasil || {};
    
    if (kpiBtc) {
        const btcPrice = brData.btc || 0;
        const btcRet = (brData.btc_ret || 0) * 100;
        if (btcPrice > 0) {
            kpiBtc.innerHTML = `<span style="display:block; font-size: 0.9rem;">$${btcPrice.toLocaleString()}</span>
                                <span style="font-size: 0.7rem;" class="${btcRet >= 0 ? 'text-success' : 'text-danger'}">
                                    ${btcRet >= 0 ? '▲' : '▼'} ${Math.abs(btcRet).toFixed(2)}%
                                </span>`;
        } else {
            kpiBtc.textContent = '---';
        }
    }

    if (kpiIbov) {
        const ibovRet = (brData.ibov_ret || 0) * 100;
        kpiIbov.textContent = `${ibovRet >= 0 ? '+' : ''}${ibovRet.toFixed(2)}%`;
        kpiIbov.className = `kpi-value ${ibovRet >= 0 ? 'text-success' : 'text-danger'}`;
    }

    if (kpiSelic) kpiSelic.textContent = brData.selic ? `${brData.selic.toFixed(2)}%` : '---';
    if (kpiUsdbrl) kpiUsdbrl.textContent = brData.usdbrl ? `R$ ${brData.usdbrl.toFixed(3)}` : '---';
    
    if (kpiFng) {
        const fng = brData.fng || 0;
        kpiFng.textContent = fng || '---';
        if (fng > 0) {
            kpiFng.className = `kpi-value ${fng < 30 ? 'text-danger' : fng > 70 ? 'text-success' : 'text-warning'}`;
        }
    }

    // News
    if (news) updateNews(news);

    // Strategic Upgrades
    updateStrategy(data.positioning, data.ai_thesis);
    updateRiskBreakdown(data.risk_breakdown);
}

function updateStrategy(positioning, thesis) {
    const title = document.getElementById('strategy-title');
    const badge = document.getElementById('strategy-signal-badge');
    const thesisEl = document.getElementById('ai-thesis-text');
    const actionsList = document.getElementById('strategy-actions');

    if (!positioning || !title) return;

    title.textContent = positioning.strategy;
    badge.textContent = positioning.signal;
    thesisEl.textContent = `"${thesis}"`;

    // Strategy Colors
    const sig = positioning.signal.toLowerCase();
    if (sig.includes('bullish') || sig.includes('risk-on')) {
        badge.style.borderColor = 'var(--neon-green)';
        badge.style.color = 'var(--neon-green)';
    } else if (sig.includes('bearish') || sig.includes('risk-off')) {
        badge.style.borderColor = 'var(--neon-red)';
        badge.style.color = 'var(--neon-red)';
    }

    if (positioning.actions) {
        actionsList.innerHTML = positioning.actions.map(a => `<li>${a}</li>`).join('');
    }

    // Correlation Signals (Extra logic)
    if (window.lastIntelligence && window.lastIntelligence.correlations) {
        const anomalies = window.lastIntelligence.correlations.filter(c => c.status === 'Anomaly Detected');
        if (anomalies.length > 0) {
            const anomalyText = anomalies.map(a => `⚠️ Alert: ${a.pair} correlation anomaly detected (${a.corr}).`).join(' ');
            thesisEl.innerHTML += `<br><span class="text-warning" style="font-size: 0.85rem; font-weight: bold;">${anomalyText}</span>`;
        }
    }
}

function updateRiskBreakdown(breakdown) {
    const container = document.getElementById('risk-composition-bars');
    if (!container || !breakdown) return;

    container.innerHTML = Object.entries(breakdown).map(([label, value]) => `
        <div class="comp-item">
            <div style="display: flex; justify-content: space-between;">
                <span class="comp-label">${label}</span>
                <span class="comp-label" style="color: white; opacity: 0.8;">${value.toFixed(1)}%</span>
            </div>
            <div class="comp-bar-bg">
                <div class="comp-bar" style="width: ${value}%"></div>
            </div>
        </div>
    `).join('');
}

function getBadgeColor(colorKey, alpha) {
    const colors = {
        success: `rgba(16, 185, 129, ${alpha})`,
        warning: `rgba(245, 158, 11, ${alpha})`,
        danger: `rgba(239, 68, 68, ${alpha})`,
        info: `rgba(56, 189, 248, ${alpha})`,
        dark: `rgba(148, 163, 184, ${alpha})`
    };
    return colors[colorKey] || colors.info;
}

function updateNews(news) {
    newsFeed.innerHTML = '';
    fullNewsFeed.innerHTML = '';

    const impactColors = { HIGH: 'var(--neon-red)', MEDIUM: 'var(--neon-yellow)', LOW: 'var(--text-muted)' };
    const sentColors   = { Bearish: 'var(--neon-red)', Bullish: 'var(--neon-green)', Neutral: 'var(--text-muted)' };

    news.forEach(item => {
        const impact  = item.impact  || 'LOW';
        const sent    = item.sentiment || 'Neutral';
        const impl    = item.implication || '';

        const div = document.createElement('div');
        div.className = `news-item ${sent.toLowerCase()}`;
        div.innerHTML = `
            <div class="news-meta-row">
                <span class="news-sentiment-badge" style="color:${sentColors[sent]};border-color:${sentColors[sent]}">${sent}</span>
                <span class="news-impact-badge" style="color:${impactColors[impact]};border-color:${impactColors[impact]}">${impact} IMPACT</span>
            </div>
            <h4>${item.title}</h4>
            ${impl ? `<p class="news-implication">→ ${impl}</p>` : ''}
            <a href="${item.url}" target="_blank" class="news-link">Source &rarr;</a>
        `;
        newsFeed.appendChild(div.cloneNode(true));
        fullNewsFeed.appendChild(div);
    });
}

function updateMarketsView(data) {
    if (!data || !marketsGrid) return;
    marketsGrid.innerHTML = '';

    // Build: latest + previous value per series for % change
    const byTicker = {};
    data.forEach(d => {
        if (!byTicker[d.series_type]) byTicker[d.series_type] = [];
        byTicker[d.series_type].push(d);
    });

    // Ticker display names
    const LABELS = {
        '^GSPC': 'S&P 500', '^VIX': 'VIX', 'GC=F': 'Gold',
        'BTC-USD': 'Bitcoin', '^BVSP': 'Ibovespa', 'USDBRL=X': 'USD/BRL',
        'T10Y2Y': 'Yield Curve', 'FEDFUNDS': 'Fed Funds', 'CPIAUCSL': 'CPI (US)',
        'BCB_SELIC': 'Selic Rate', 'BCB_IPCA': 'IPCA', 'FEAR_GREED': 'Fear & Greed',
    };
    const REGIMES = window.lastIntelligence;

    Object.keys(byTicker).forEach(ticker => {
        const sorted = byTicker[ticker].sort((a,b) => a.date > b.date ? 1 : -1);
        const last   = sorted[sorted.length - 1];
        const prev   = sorted.length > 1 ? sorted[sorted.length - 2] : null;
        const pct    = prev && prev.value ? (last.value / prev.value - 1) * 100 : null;
        const up     = pct !== null ? pct >= 0 : null;

        const card = document.createElement('div');
        card.className = 'market-mini-card glass';
        card.setAttribute('data-ticker', ticker);

        const changeHtml = pct !== null ? `
            <div class="market-change ${up ? 'pos' : 'neg'}">
                ${up ? '▲' : '▼'} ${Math.abs(pct).toFixed(2)}%
            </div>` : '';

        card.innerHTML = `
            <div class="market-ticker-label">${LABELS[ticker] || ticker}</div>
            <div class="market-ticker-code">${ticker}</div>
            <div class="market-price">${last.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
            ${changeHtml}
            <div class="market-date">${last.date}</div>
        `;
        marketsGrid.appendChild(card);
    });
}

function updateIntelligenceView(data) {
    if (!intelligenceAnalysis) return;
    intelligenceAnalysis.innerHTML = `
        <div class="analysis-card glass">
            <h2 style="color: var(--neon-cyan); margin-bottom: 1rem;">Regime Analysis: ${data.kpis.regime}</h2>
            <p style="font-size: 1.1rem; line-height: 1.6;">${data.kpis.regime_explanation}</p>
            <div style="margin-top: 2rem; border-top: 1px solid var(--border-glow); padding-top: 1rem;">
                <div class="risk-meter">
                    <span class="label">Systemic Risk Score: ${data.kpis.risk_score}/100</span>
                    <div class="progress-bar" style="width: 100%; height: 10px; margin-top: 0.5rem; background: rgba(255,255,255,0.05);">
                        <div class="progress" style="width: ${data.kpis.risk_score}%; background: var(--neon-magenta); box-shadow: 0 0 10px var(--neon-magenta);"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function updateMacroView(data) {
    if (!data || !macroContent) return;
    macroContent.innerHTML = '';

    const macroSeries = ['T10Y2Y', 'FEDFUNDS', 'CPIAUCSL'];
    const latest = {};
    
    data.forEach(d => {
        if (macroSeries.includes(d.series_type)) {
            if (!latest[d.series_type] || d.date > latest[d.series_type].date) {
                latest[d.series_type] = d;
            }
        }
    });

    const grid = document.createElement('div');
    grid.className = 'markets-grid-container';
    
    const descriptions = {
        'T10Y2Y': 'Yield Curve Spread (10Y-2Y)',
        'FEDFUNDS': 'Effective Federal Funds Rate',
        'CPIAUCSL': 'Consumer Price Index (CPI)'
    };

    Object.keys(latest).forEach(ticker => {
        const d = latest[ticker];
        const card = document.createElement('div');
        card.className = 'market-mini-card glass';
        card.innerHTML = `
            <div class="market-ticker" style="color: var(--neon-magenta)">${ticker}</div>
            <div style="font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.5rem;">${descriptions[ticker]}</div>
            <div class="market-price">${d.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
            <div class="market-date" style="font-size: 0.6rem; color: var(--text-muted)">Updated: ${d.date}</div>
        `;
        grid.appendChild(card);
    });

    macroContent.appendChild(grid);
}

function updateChartData(data) {
    if (!data || data.length === 0) return;

    // Filter Series
    const sp500Data = data
        .filter(d => d.series_type === '^GSPC')
        .map(d => ({ time: d.date, value: d.value }))
        .sort((a, b) => a.time.localeCompare(b.time));

    const vixData = data
        .filter(d => d.series_type === '^VIX')
        .map(d => ({ time: d.date, value: d.value }))
        .sort((a, b) => a.time.localeCompare(b.time));

    if (areaSeries && sp500Data.length > 0) {
        areaSeries.setData(sp500Data);
    }
    
    if (vixSeries && vixData.length > 0) {
        vixSeries.setData(vixData);
    }

    chart.timeScale().fitContent();
}

async function triggerETL() {
    showToast();
    try {
        await fetch(`${API_URL}/etl/run`, { method: 'POST' });
    } catch (error) {
        console.error("Error triggering ETL:", error);
    }
}

function showToast() {
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}
