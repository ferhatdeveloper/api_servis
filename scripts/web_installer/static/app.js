const appState = {
    step: 1,
    selectedApp: null,
    canProceed: false,
    config: {
        pg: {},
        ms: {}
    },
    migrationMode: false,
    remoteConnStr: null,
    targetDB: 'postgres'
};

function updateMigrationTargetInfo() {
    const target = document.getElementById('migration-target')?.value || 'postgres';
    const infoBox = document.getElementById('local-db-info');
    if (!infoBox) return;

    const config = target === 'postgres' ? appState.config.pg : appState.config.ms;
    if (config && config.host) {
        infoBox.innerHTML = `${target.toUpperCase()}: ${config.username}@${config.host}:${config.port || ''} (Hazır ✅)`;
        infoBox.style.color = 'var(--success)';
        appState.targetDB = target;
    } else {
        infoBox.innerHTML = `${target.toUpperCase()}: Henüz yapılandırılmadı (Step 3'e dönün)`;
        infoBox.style.color = 'var(--warning)';
    }
}

function switchDBTab(tab) {
    const localArea = document.getElementById('local-db-area');
    const migArea = document.getElementById('migration-db-area');
    const tabLocal = document.getElementById('tab-local');
    const tabMig = document.getElementById('tab-migration');

    if (tab === 'local') {
        localArea.classList.remove('hidden');
        migArea.classList.add('hidden');
        tabLocal.classList.add('active');
        tabMig.classList.remove('active');
        appState.migrationMode = false;
    } else {
        localArea.classList.add('hidden');
        migArea.classList.remove('hidden');
        tabLocal.classList.remove('active');
        tabMig.classList.add('active');
        appState.migrationMode = true;
    }
}

async function fetchSupabaseProjects() {
    const token = document.getElementById('supabase-token').value;
    const select = document.getElementById('supabase-project-select');
    const logBox = document.getElementById('migration-log');

    if (!token) { alert("Lütfen token giriniz."); return; }

    logBox.innerHTML = '<div class="pulsing">> Projeler alınıyor...</div>';
    try {
        const res = await fetch('/api/supabase-projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            select.innerHTML = '<option value="">Proje Seçin...</option>';
            data.projects.forEach(p => {
                select.innerHTML += `<option value="${p.id}" data-host="${p.id}.supabase.co">${p.name}</option>`;
            });
            document.getElementById('supabase-project-list').classList.remove('hidden');
            logBox.innerHTML = '<div class="text-success">> Projeler listelendi. Lütfen seçim yapın.</div>';
            appState.supabaseToken = token;
        } else {
            const errMsg = data.error || data.detail || "Sunucu hatası oluştu.";
            logBox.innerHTML = `<div class="text-danger">> Hata: ${errMsg}</div>`;
        }
    } catch (e) {
        logBox.innerHTML = '<div class="text-danger">> Bağlantı Hatası: Servis cevap vermiyor.</div>';
    }
}

function fillMigrationDefaults() {
    document.getElementById('supabase-token').value = 'sbp_6e8b5a242da67bd8a703e20e01d84cfe4b85018a';
    document.getElementById('migration-log').innerHTML = '<div class="text-success">> Varsayılan token yüklendi.</div>';
}

function selectSupabaseProject() {
    const select = document.getElementById('supabase-project-select');
    const selected = select.options[select.selectedIndex];
    const host = selected.getAttribute('data-host');
    const connStrInput = document.getElementById('remote-conn-str');

    if (host) {
        // Use 1993 as default password as requested
        connStrInput.value = `postgresql://postgres:1993@db.${host}:5432/postgres`;
        document.getElementById('migration-log').innerHTML = '<div>> Proje seçildi. Bağlantı dizesi hazır (Varsayılan şifre: 1993).</div>';
    }
}

function toggleMigrationType() {
    const type = document.getElementById('remote-db-type').value;
    const connField = document.getElementById('remote-conn-field');
    const supLogin = document.getElementById('supabase-api-login');
    const supList = document.getElementById('supabase-project-list');
    const label = document.getElementById('remote-conn-label');
    const input = document.getElementById('remote-conn-str');

    // Reset UI
    supLogin.classList.add('hidden');
    supList.classList.add('hidden');
    connField.classList.remove('hidden');

    if (type === 'supabase_api') {
        supLogin.classList.remove('hidden');
        label.innerText = "Bağlantı Dizesi (Otomatik Oluşturulacak)";
    } else if (type === 'mssql') {
        label.innerText = "MS SQL Server Bağlantı Dizesi";
        input.placeholder = "mssql+pymssql://user:pass@host:port/db";
    } else if (type === 'mysql') {
        label.innerText = "MySQL Bağlantı Dizesi";
        input.placeholder = "mysql+pymysql://user:pass@host:port/db";
    } else {
        label.innerText = "PostgreSQL Bağlantı Dizesi";
        input.placeholder = "postgresql://user:pass@host:port/db";
    }
}

async function analyzeRemoteDB() {
    const connStr = document.getElementById('remote-conn-str').value;
    const logBox = document.getElementById('migration-log');
    const tabView = document.getElementById('remote-tables-view');

    if (!connStr || connStr.includes('[PASSWORD]')) {
        alert("Lütfen bağlantı dizesini kontrol edin ve geçerli bir şifre girin.");
        return;
    }

    logBox.innerHTML = '<div class="pulsing">> Uzak sunucu analiz ediliyor...</div>';
    tabView.classList.add('hidden');

    try {
        const targetType = document.getElementById('migration-target').value;
        const targetConfig = targetType === 'postgres' ? appState.config.pg : appState.config.ms;

        const res = await fetch('/api/analyze-remote-db', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                connection_string: connStr,
                local_config: targetConfig
            })
        });
        const data = await res.json();

        if (data.success) {
            logBox.innerHTML = `<div class="text-success">> Analiz Başarılı!</div>`;
            logBox.innerHTML += `<div>> Kaynak: ${data.analysis.source_dialect.toUpperCase()}</div>`;
            logBox.innerHTML += `<div>> Toplam Tablo: ${data.tables.length}</div>`;
            logBox.innerHTML += `<div>> Yeni Tablo: ${data.analysis.missing_tables.length}</div>`;

            tabView.innerHTML = '<div class="selection-header" style="margin-top:15px; font-weight:bold; font-size:12px; border-bottom:1px solid #333; padding-bottom:5px;">AKTARMALIK TABLOLAR</div>';
            tabView.innerHTML += data.tables.map(t => `
                <div class="selection-item">
                    <input type="checkbox" id="tbl-${t}" value="${t}" checked>
                    <label for="tbl-${t}">${t} ${data.analysis.missing_tables.includes(t) ? '<small class="text-danger">(Yeni)</small>' : '<small class="text-success">(Eşitlenecek)</small>'}</label>
                </div>
            `).join('');
            tabView.classList.remove('hidden');

            document.getElementById('btn-next-db').disabled = false;
            appState.remoteConnStr = connStr;
            appState.migrationMode = true;
        } else {
            logBox.innerHTML = `<div class="text-danger">> Hata: ${data.error}</div>`;
        }
    } catch (e) {
        logBox.innerHTML = `<div class="text-danger">> Sunucu bağlantı hatası veya zaman aşımı.</div>`;
    }
}

function selectApp(appId, el) {
    appState.selectedApp = appId;

    // UI Update
    document.querySelectorAll('.app-card').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');

    // Enable Next
    const nextBtn = document.getElementById('btn-next-1');
    if (nextBtn) nextBtn.disabled = false;

    // Update default DB name based on app
    const dbMap = {
        'OPS': 'EXFINOPS',
        'RETAIL': 'EXFIN_RETAIL',
        'HRM': 'EXFIN_HRM',
        'REST': 'EXFIN_REST',
        'BEATPY': 'EXFIN_BEATPY',
        'EXCHANGE': 'EXFIN_EXCHANGE'
    };
    if (dbMap[appId]) {
        const pgDbInput = document.getElementById('pg-db');
        if (pgDbInput) pgDbInput.value = dbMap[appId];
    }
}


// --- Step 1: Init & Checks ---
document.addEventListener('DOMContentLoaded', async () => {
    // Run Checks
    try {
        const res = await fetch('/api/check-prerequisites');
        const data = await res.json();

        updateCheck('chk-admin', data.is_admin);
        updateCheck('chk-python', parseFloat(data.python_version) >= 3.1);
        updateCheck('chk-ram', data.ram_gb >= 2);

        // Always enable start for exploration, but can warn later
        const startBtn = document.getElementById('btn-start');
        startBtn.disabled = false;
        startBtn.onclick = () => goToStep(3);

        if (!data.is_admin) {
            console.warn("DİKKAT: Yönetici yetkisi yok. Servis kurulumu aşamasında hata alabilirsiniz.");
            const adminItem = document.getElementById('chk-admin');
            if (adminItem) {
                adminItem.innerHTML += ' <small style="display:block; font-size:10px; opacity:0.7">Lütfen "Yönetici Olarak Çalıştır" ile başlatın.</small>';
            }
        }

    } catch (e) {
        console.error("Connection Error", e);
    }
});

function updateCheck(id, success) {
    const el = document.getElementById(id);
    if (success) {
        el.classList.add('success');
        el.querySelector('.icon').innerText = '✅';
    } else {
        el.classList.add('error');
        el.querySelector('.icon').innerText = '❌';
    }
}

// --- Navigation ---
function goToStep(step) {
    // Hide all
    document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));

    // Show target
    const card = document.getElementById(`card-${step}`);
    if (card) card.classList.add('active');

    // Light up indicators
    for (let i = 1; i <= step; i++) {
        const sEl = document.getElementById(`s${i}`);
        if (sEl) sEl.classList.add('active');
    }

    // Update Migration Panel Info whenever we go back/forth
    updateMigrationTargetInfo();

    if (step === 4) {
        // If we migrated everything, maybe Logo is redundant
        const card4 = document.getElementById('card-4');
        if (appState.migrationMode && !document.getElementById('skip-logo-btn')) {
            const skipBtn = document.createElement('button');
            skipBtn.id = 'skip-logo-btn';
            skipBtn.className = 'btn btn-secondary';
            skipBtn.style.marginLeft = '10px';
            skipBtn.innerText = 'Logo Veri Aktarımını Atla (Zaten Taşındı)';
            skipBtn.onclick = () => goToStep(5);
            card4.querySelector('.card-footer').appendChild(skipBtn);
        }
    }

    if (step === 5) {
        startInstallation();
    }
}

function goBack(step) {
    goToStep(step);
}

// --- Step 2: Database ---
async function fetchLogoFirms() {
    const firmArea = document.getElementById('logo-firm-area');
    const firmSelect = document.getElementById('logo-firm-select');

    const payload = {
        host: document.getElementById('ms-host').value,
        username: document.getElementById('ms-user').value,
        password: document.getElementById('ms-pass').value,
        database: document.getElementById('ms-db').value
    };

    try {
        const res = await fetch('/api/logo-firms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.success && result.firms) {
            firmSelect.innerHTML = '<option value="">Firma Seçin...</option>';
            result.firms.forEach(f => {
                firmSelect.innerHTML += `<option value="${f.id}">${f.id} - ${f.name}</option>`;
            });
            firmArea.classList.remove('hidden');
        }
    } catch (e) {
        console.error("Logo firms fetch error", e);
    }
}

async function testDB(type) {
    const statusEl = document.getElementById('db-status');
    statusEl.innerHTML = `<span style="color:yellow">Test ediliyor...</span>`;

    const prefix = type === 'postgres' ? 'pg' : 'ms';
    const payload = {
        type: type === 'postgres' ? 'PostgreSQL' : 'MSSQL',
        host: document.getElementById(`${prefix}-host`).value,
        port: parseInt(document.getElementById(`${prefix}-port`)?.value || "1433"),
        username: document.getElementById(`${prefix}-user`).value,
        password: document.getElementById(`${prefix}-pass`).value,
        database: document.getElementById(`${prefix}-db`).value,
        app_type: appState.selectedApp || "OPS",
        load_demo: document.getElementById('load-demo')?.checked || false
    };

    try {
        const res = await fetch('/api/test-db', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.success) {
            statusEl.innerHTML = `<span style="color:var(--success)">${result.message}</span>`;

            // Save to state
            if (type === 'postgres') appState.config.pg = payload;
            else {
                appState.config.ms = payload;
                fetchLogoFirms(); // Load firms on success
            }

            // Enable Next if PG is verified
            if (type === 'postgres') {
                const nextBtn = document.getElementById('btn-next-db');
                if (nextBtn) {
                    nextBtn.disabled = false;
                    nextBtn.onclick = () => handleDBFinish();
                }
            }
        } else {
            statusEl.innerHTML = `<span style="color:var(--danger)">Hata: ${result.error}</span>`;
        }
    } catch (e) {
        statusEl.innerHTML = `Bağlantı Hatası`;
    }
}

async function handleDBFinish() {
    const syncCheck = document.getElementById('sync-logo-check');
    if (syncCheck && syncCheck.checked) {
        await fetchLogoSchemaInfo();
        goToStep(4);
    } else {
        goToStep(5);
    }
}

async function fetchLogoSchemaInfo() {
    const listSales = document.getElementById('list-salesmen');
    const listWare = document.getElementById('list-warehouses');
    listSales.innerHTML = '<div class="selection-item">Yükleniyor...</div>';
    listWare.innerHTML = '<div class="selection-item">Yükleniyor...</div>';

    try {
        const res = await fetch('/api/logo-schema-info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pg_config: appState.config.pg,
                ms_config: appState.config.ms,
                firm_id: document.getElementById('logo-firm-select').value
            })
        });
        const data = await res.json();

        if (data.success) {
            listSales.innerHTML = data.salesmen.map(s => `
                <div class="selection-item">
                    <input type="checkbox" id="sls-${s.id}" value="${s.id}" checked>
                    <label for="sls-${s.id}">${s.id} - ${s.name}</label>
                </div>
            `).join('') || '<div class="selection-item">Kayıt bulunamadı.</div>';

            listWare.innerHTML = data.warehouses.map(w => `
                <div class="selection-item">
                    <input type="checkbox" id="wh-${w.id}" value="${w.id}" checked>
                    <label for="wh-${w.id}">${w.id} - ${w.name}</label>
                </div>
            `).join('') || '<div class="selection-item">Kayıt bulunamadı.</div>';
        } else {
            listSales.innerHTML = '<div class="selection-item text-danger">Hata: ' + data.error + '</div>';
            listWare.innerHTML = '';
        }
    } catch (e) {
        console.error("Schema Fetch Error:", e);
    }
}

// --- Step 3: Install ---
async function startInstallation() {
    const logBox = document.getElementById('install-logs');

    function log(msg) {
        logBox.innerHTML += `<div>> ${msg}</div>`;
        logBox.scrollTop = logBox.scrollHeight;
    }

    log("Konfigürasyon dökümü yapılıyor...");

    // 1. Prepare Save Payload
    const savePayload = {
        settings: {
            "Api_Port": "8000",
            "DeveloperMode": "True",
            "AppType": appState.selectedApp || "OPS"
        },
        connections: [
            { id: 1, name: "Postgres_Main", ...appState.config.pg },
            ...(appState.config.ms.host ? [{ id: 2, name: "LOGO_Database", ...appState.config.ms }] : [])
        ]
    };

    // 2. Save Config
    try {
        const saveRes = await fetch('/api/save-config', {
            method: 'POST',
            body: JSON.stringify(savePayload),
            headers: { 'Content-Type': 'application/json' }
        });
        if ((await saveRes.json()).success) {
            log("Ayarlar api.db'ye kaydedildi. ✅");
        } else {
            log("HATA: Ayarlar kaydedilemedi.");
            return;
        }
    } catch (e) {
        log("Kritik sunucu hatası (Save).");
        return;
    }

    // 3. Cloud Migration sync if active
    if (appState.migrationMode && appState.remoteConnStr) {
        log("Bulut verileri yerel sisteme aktarılıyor...");
        const tables = Array.from(document.querySelectorAll('#remote-tables-view input:checked')).map(i => i.value);
        const targetType = document.getElementById('migration-target').value;
        const targetConfig = targetType === 'postgres' ? appState.config.pg : appState.config.ms;

        try {
            const migRes = await fetch('/api/migrate-cloud-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    connection_string: appState.remoteConnStr,
                    local_config: targetConfig,
                    tables: tables
                })
            });
            const migData = await migRes.json();
            if (migData.success) {
                log(`Bulut aktarımı tamamlandı (${tables.length} tablo). ✅`);
            } else {
                log("UYARI: Bulut aktarımı hatası: " + migData.error);
            }
        } catch (e) {
            log("Kritik Bulut aktarım hatası.");
        }
    }

    // 4. Logo Sync if requested (and not in full cloud mode or as secondary)
    if (!appState.migrationMode && appState.config.ms && appState.config.ms.host && document.getElementById('sync-logo-check')?.checked) {
        log("Seçili Logo verileri aktarılıyor...");

        const salesmen = Array.from(document.querySelectorAll('#list-salesmen input:checked')).map(i => i.value);
        const warehouses = Array.from(document.querySelectorAll('#list-warehouses input:checked')).map(i => i.value);

        try {
            const res = await fetch('/api/sync-logo-selective', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pg_config: appState.config.pg,
                    ms_config: appState.config.ms,
                    firm_id: document.getElementById('logo-firm-select').value,
                    salesmen,
                    warehouses
                })
            });
            const syncData = await res.json();
            if (syncData.success) {
                log("Logo senkronizasyonu tamamlandı. ✅");
            } else {
                log("UYARI: " + syncData.error);
            }
        } catch (e) {
            log("UYARI: Logo senkronizasyonu tamamlanamadı.");
        }
    }

    // 5. Install Service
    log("Windows Servisi kuruluyor...");

    try {
        const instRes = await fetch('/api/install-service', { method: 'POST' });
        const instData = await instRes.json();

        if (instData.success) {
            log(instData.message);

            // 6. Create Shortcuts
            try {
                await fetch('/api/create-shortcuts', { method: 'POST' });
                log("Masaüstü kısayolu oluşturuldu. 🖥️");
            } catch (shortE) {
                log("UYARI: Kısayol oluşturulamadı.");
            }

            log("Lütfen bekleyin...");

            setTimeout(() => {
                document.querySelector('.progress-container').style.display = 'none';
                document.getElementById('install-logs').style.display = 'none';

                const appNameSpan = document.getElementById('success-app-name');
                if (appNameSpan) appNameSpan.innerText = appState.selectedApp || "OPS";

                document.getElementById('success-screen').classList.remove('hidden');
            }, 2000);

        } else {
            log("HATA: Servis kurulamadı.");
            log(instData.error);
        }
    } catch (e) {
        log("Kritik sunucu hatası (Install).");
    }
}

async function launchTray() {
    try {
        await fetch('/api/launch-tray', { method: 'POST' });
        alert("Tray App başlatıldı. Saatin yanındaki simgeyi kontrol edin.");
    } catch (e) {
        alert("Tray App başlatılamadı.");
    }
}
