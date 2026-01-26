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
    targetDB: 'postgres',
    deploymentMode: "1" // 1=Service, 2=Tray
};

function switchDataTab(tabId, btn) {
    // 1. Hide all panes
    document.querySelectorAll('.tab-pane').forEach(p => {
        p.classList.remove('active');
        p.classList.add('hidden');
    });

    // 2. Deactivate all buttons
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    // 3. Activate target
    const target = document.getElementById(tabId);
    if (target) {
        target.classList.remove('hidden');
        target.classList.add('active');
    }
    btn.classList.add('active');
}

function filterTable(tableId, query) {
    const filter = query.toUpperCase();
    const rows = document.getElementById(tableId).getElementsByTagName("tr");

    for (let i = 0; i < rows.length; i++) {
        // Skip header or empty message row if needed, but usually we filter logic rows
        // If row has no cells (e.g. empty) skip
        const cells = rows[i].getElementsByTagName("td");
        if (cells.length < 2) continue; // Skip header/message rows

        let found = false;
        // Check all cells
        for (let j = 0; j < cells.length; j++) {
            const txt = cells[j].textContent || cells[j].innerText;
            if (txt.toUpperCase().indexOf(filter) > -1) {
                found = true;
                break;
            }
        }

        // Toggle visibility
        rows[i].style.display = found ? "" : "none";
    }
}

function getVal(id, fallback = "") {
    const el = document.getElementById(id);
    return el ? el.value : fallback;
}

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const trigger = input.nextElementSibling;
    if (input.type === 'password') {
        input.type = 'text';
        if (trigger) trigger.innerText = '🙈';
    } else {
        input.type = 'password';
        if (trigger) trigger.innerText = '👁️';
    }
}

function generateUsername(str) {
    if (!str) return "";

    const trMap = {
        'ç': 'c', 'Ç': 'c', 'ğ': 'g', 'Ğ': 'g', 'ı': 'i', 'İ': 'i',
        'ö': 'o', 'Ö': 'o', 'ş': 's', 'Ş': 's', 'ü': 'u', 'Ü': 'u'
    };

    const arMap = {
        'ا': 'a', 'أ': 'a', 'إ': 'a', 'آ': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h', 'خ': 'kh',
        'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z',
        'ع': 'aa', 'غ': 'gh', 'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w',
        'ي': 'y', 'ة': 'h', 'ى': 'y', 'ء': 'a', 'ؤ': 'u', 'ئ': 'i', 'پ': 'p', 'چ': 'ch', 'ژ': 'zh', 'گ': 'g'
    };

    let cleaned = str.trim().split('').map(c => trMap[c] || arMap[c] || c).join('').toLowerCase();

    // Replace non-alphanumeric with space to separate words
    cleaned = cleaned.replace(/[^a-z0-9]/g, ' ');

    // Split into parts by space
    let parts = cleaned.split(/\s+/).filter(p => p.length > 0);

    // Strategy: Take first part + first letter of last part (if exists)
    // Avoid repeating name if it's already in the code or description

    let result = "user";

    if (parts.length > 0) {
        if (parts.length === 1) {
            result = parts[0];
        } else {
            // e.g. "abu zaenab" -> "abu.z"
            result = `${parts[0]}.${parts[parts.length - 1][0]}`;
        }
    }

    return result.slice(0, 15); // Limit length
}

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
    const backupArea = document.getElementById('backup-db-area');
    const migArea = document.getElementById('migration-db-area');
    const tabLocal = document.getElementById('tab-local');
    const tabBackup = document.getElementById('tab-backup');
    const tabMig = document.getElementById('tab-migration');

    // Hide all
    localArea.classList.add('hidden');
    backupArea.classList.add('hidden');
    migArea.classList.add('hidden');

    // Deactivate all tabs
    tabLocal.classList.remove('active');
    tabBackup.classList.remove('active');
    tabMig.classList.remove('active');

    if (tab === 'local') {
        localArea.classList.remove('hidden');
        tabLocal.classList.add('active');
        appState.migrationMode = false;
    } else if (tab === 'backup') {
        backupArea.classList.remove('hidden');
        tabBackup.classList.add('active');
    } else {
        migArea.classList.remove('hidden');
        tabMig.classList.add('active');
        appState.migrationMode = true;
    }
}

function toggleBackupOptions() {
    const interval = document.getElementById('backup-interval').value;
    const timeGroup = document.getElementById('backup-time-group');
    const hourGroup = document.getElementById('backup-hour-group');
    const daysGroup = document.getElementById('backup-days-group');

    timeGroup.classList.add('hidden');
    hourGroup.classList.add('hidden');
    daysGroup.classList.add('hidden');

    if (interval === 'hourly') {
        hourGroup.classList.remove('hidden');
    } else if (interval === 'daily') {
        timeGroup.classList.remove('hidden');
    } else if (interval === 'weekly') {
        timeGroup.classList.remove('hidden');
        daysGroup.classList.remove('hidden');
    }
}

async function openPreview(type) {
    const modal = document.getElementById('preview-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');

    modal.classList.remove('hidden');
    title.innerText = type === 'companies' ? 'Logo Firmaları Önizlemesi' :
        (type === 'salesmen' ? 'Satış Elemanları Önizlemesi' :
            (type === 'warehouses' ? 'Ambarlar Önizlemesi' : 'Müşteriler (Cari Hesaplar) Önizlemesi'));

    body.innerHTML = '<div class="pulsing">> Veriler yükleniyor...</div>';

    try {
        const msConfig = {
            host: getVal('ms-host'),
            port: getVal('ms-port'),
            username: getVal('ms-user'),
            password: getVal('ms-pass'),
            database: getVal('ms-db')
        };
        const res = await fetch('/api/preview-logo-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ms_config: msConfig,
                firm_id: document.getElementById('logo-firm-select').value || "001",
                data_type: type
            })
        });
        const data = await res.json();

        if (data.success) {
            let html = '<table class="selection-table"><thead><tr>';
            if (type === 'companies') {
                html += '<th>No</th><th>Firma Adı</th><th>Vergi No</th>';
            } else if (type === 'salesmen') {
                html += '<th>Ref</th><th>Kod</th><th>İsim</th><th>E-posta</th>';
            } else {
                html += '<th>No</th><th>Ambar Adı</th>';
            }
            html += '</tr></thead><tbody>';

            data.data.forEach(item => {
                html += '<tr>';
                if (type === 'companies') {
                    html += `<td>${item.nr}</td><td>${item.name}</td><td>${item.tax_nr || '-'}</td>`;
                } else if (type === 'salesmen') {
                    html += `<td>${item.logo_ref || '-'}</td><td>${item.code}</td><td>${item.name}</td><td>${item.email || '-'}</td>`;
                } else if (type === 'customers') {
                    html += `<td>${item.code}</td><td>${item.name}</td><td>${item.city || '-'}</td>`;
                } else {
                    html += `<td>${item.nr}</td><td>${item.name}</td>`;
                }
                html += '</tr>';
            });
            html += '</tbody></table>';
            body.innerHTML = html;
        } else {
            body.innerHTML = `<div class="text-danger">> Hata: ${data.error}</div>`;
        }
    } catch (e) {
        body.innerHTML = '<div class="text-danger">> Bağlantı Hatası: Veriler alınamadı.</div>';
    }
}

function closeModal() {
    document.getElementById('preview-modal').classList.add('hidden');
}

async function generateSSL() {
    const btn = document.getElementById('btn-ssl');
    const logBox = document.getElementById('install-logs');

    btn.disabled = true;
    logBox.innerHTML += '\n> SSL Sertifikası oluşturuluyor...';

    try {
        const res = await fetch('/api/generate-ssl', { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            logBox.innerHTML += `\n> SSL Başarılı! ✅\n> Sertifika: ${data.cert_file}\n> .env güncellendi.`;
            alert("SSL Sertifikası başarıyla oluşturuldu ve etkinleştirildi!");
        } else {
            logBox.innerHTML += `\n> SSL Hatası: ${data.error} ❌`;
            alert("Hata: " + data.error);
        }
    } catch (e) {
        logBox.innerHTML += '\n> SSL Kritik Hata! ❌';
    }
    btn.disabled = false;
}

async function fetchSupabaseProjects() {
    const token = document.getElementById('supabase-token').value;
    const select = document.getElementById('supabase-project-select');
    const logBox = document.getElementById('migration-log');

    if (!token) { alert("Lütfen token giriniz."); return; }

    logBox.innerHTML = '<div class="pulsing">> Projeler alınıyor...</div>';
    try {
        const res = await fetch('/api/supabase-projects/', {
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
        'CAFE': 'EXFIN_CAFE',
        'BEATPY': 'EXFIN_BEATPY',
        'EXCHANGE': 'EXFIN_EXCHANGE',
        'WHATSAPP': 'EVOLUTION_API'
    };
    if (dbMap[appId]) {
        const pgDbInput = document.getElementById('pg-db');
        if (pgDbInput) pgDbInput.value = dbMap[appId];
    }

    // Toggle WhatsApp Settings Panel
    const waPanel = document.getElementById('wa-settings-area');
    if (waPanel) {
        if (appId === 'WHATSAPP') waPanel.classList.remove('hidden');
        else waPanel.classList.add('hidden');
    }
}


// --- Step 1: Init & Checks ---
document.addEventListener('DOMContentLoaded', async () => {
    runPrerequisiteChecks();
});

async function runPrerequisiteChecks() {
    const adminIcon = document.querySelector('#chk-admin .icon');
    if (adminIcon) adminIcon.innerHTML = '🟡';

    try {
        const res = await fetch('/api/check-prerequisites');
        const data = await res.json();

        updateCheck('chk-admin', data.is_admin);
        updateCheck('chk-python', parseFloat(data.python_version) >= 3.1);
        updateCheck('chk-ram', data.ram_gb >= 2);

        if (data.deployment_mode) {
            appState.deploymentMode = data.deployment_mode;
        }

        // Always enable start for exploration, but can warn later
        const startBtn = document.getElementById('btn-start');
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.onclick = () => goToStep(3);
        }

        const adminItem = document.getElementById('chk-admin');
        if (!data.is_admin) {
            console.warn("DİKKAT: Yönetici yetkisi yok. Servis kurulumu aşamasında hata alabilirsiniz.");
            if (adminItem) {
                // Remove existing small tags if any (to avoid duplicates on refresh)
                const existingSmall = adminItem.querySelector('small');
                if (existingSmall) existingSmall.remove();

                adminItem.innerHTML += ' <small style="display:block; font-size:11px; color:var(--danger); margin-top:5px; line-height:1.4;">' +
                    '<b>Çözüm:</b> Terminali (CMD veya PowerShell) <b>sağ tıklayıp "Yönetici Olarak Çalıştır"</b> seçeneğiyle açın ' +
                    've <code>python main.py</code> komutunu orada çalıştırın.</small>';
            }
        } else {
            // Success state - remove warnings
            if (adminItem) {
                const existingSmall = adminItem.querySelector('small');
                if (existingSmall) existingSmall.remove();
            }
        }

    } catch (e) {
        console.error("Connection Error", e);
    }
}

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
    for (let i = 1; i <= 5; i++) {
        const sEl = document.getElementById(`s${i}`);
        if (!sEl) continue;

        if (i <= step) {
            sEl.classList.add('active');
        } else {
            sEl.classList.remove('active');
        }

        // Make previous steps clickable
        if (i < appState.step) {
            sEl.classList.add('clickable');
            sEl.onclick = () => goToStep(i);
        } else {
            sEl.classList.remove('clickable');
            sEl.onclick = null;
        }
    }

    // Mark global state
    if (step > appState.step) {
        appState.step = step;
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
    const statusEl = document.getElementById('db-status');

    if (statusEl) statusEl.innerHTML += ' <span style="color:yellow">(Firmalar alınıyor...)</span>';

    const payload = {
        type: 'MSSQL',
        host: getVal('ms-host'),
        port: parseInt(getVal('ms-port', "1433")),
        username: getVal('ms-user'),
        password: getVal('ms-pass'),
        password: getVal('ms-pass'),
        database: getVal('ms-db'),
        method: getVal('ms-method', 'direct'),
        app_type: appState.selectedApp || "OPS"
    };

    try {
        const res = await fetch('/api/logo-firms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json();
            if (statusEl) statusEl.innerHTML = `<span style="color:var(--error)">API Hatası (${res.status}): ${JSON.stringify(errData.detail || errData)}</span>`;
            return;
        }

        const result = await res.json();
        if (result.success && result.firms) {
            if (firmSelect) {
                firmSelect.innerHTML = '<option value="">Firma Seçin...</option>';
                if (result.firms.length === 0) {
                    firmSelect.innerHTML += '<option value="">Firma Kaydı Bulunamadı!</option>';
                } else {
                    result.firms.forEach(f => {
                        firmSelect.innerHTML += `<option value="${f.id}">${f.id} - ${f.name}</option>`;
                    });
                }
            }
            if (firmArea) {
                firmArea.classList.remove('hidden');
                firmArea.style.display = 'block';
            }
            if (statusEl) statusEl.innerHTML = `<span style="color:var(--success)">Bağlantı Başarılı! Firmalar listelendi. ✅</span>`;
        } else {
            if (statusEl) statusEl.innerHTML = `<span style="color:var(--error)">Hata: ${result.error || "Firmalar alınamadı."}</span>`;
        }
    } catch (e) {
        console.error("Logo firms fetch error", e);
        if (statusEl) statusEl.innerHTML = `<span style="color:var(--error)">Bağlantı Hatası: ${e.message}</span>`;
    }
}

async function testDB(type) {
    const statusEl = document.getElementById('db-status');
    if (statusEl) statusEl.innerHTML = `<span style="color:yellow">Test ediliyor...</span>`;

    const prefix = type === 'postgres' ? 'pg' : 'ms';
    const payload = {
        type: type === 'postgres' ? 'PostgreSQL' : 'MSSQL',
        host: getVal(`${prefix}-host`),
        port: parseInt(getVal(`${prefix}-port`, type === 'postgres' ? "5432" : "1433")),
        username: getVal(`${prefix}-user`),
        password: getVal(`${prefix}-pass`),
        database: getVal(`${prefix}-db`),
        method: type === 'mssql' ? getVal('ms-method', 'direct') : 'direct',
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
            if (type === 'postgres') {
                appState.config.pg = payload;
                // AUTOMATIC SETUP: If connection is successful, trigger schema creation immediately
                console.log("Postgres connection successful, triggering automatic setup...");
                statusEl.innerHTML = `<span style="color:yellow">Bağlantı Başarılı. Veritabanı ve şemalar otomatik oluşturuluyor...</span>`;

                try {
                    const setupRes = await fetch('/api/setup-postgresql', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const setupData = await setupRes.json();

                    if (setupData.success) {
                        statusEl.innerHTML = `<span style="color:var(--success)">${setupData.message} ✅</span>`;
                        const nextBtn = document.getElementById('btn-next-db');
                        if (nextBtn) {
                            nextBtn.disabled = false;
                            nextBtn.onclick = () => handleDBFinish();
                        }
                    } else {
                        statusEl.innerHTML = `<span style="color:var(--error)">Kurulum Hatası: ${setupData.error}</span>`;
                    }
                } catch (setupErr) {
                    statusEl.innerHTML = `<span style="color:var(--error)">Otomatik kurulum sırasında hata oluştu.</span>`;
                }
            } else {
                appState.config.ms = payload;
                if (typeof fetchLogoFirms === 'function') fetchLogoFirms();
            }
        } else if ((result.db_missing || result.db_empty) && type === 'postgres') {
            statusEl.innerHTML = `<span style="color:yellow">Veritabanı hazır değil (Eksik veya Boş). Otomatik hazırlanıyor...</span>`;
            try {
                const setupRes = await fetch('/api/setup-postgresql', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const setupData = await setupRes.json();

                if (setupData.success) {
                    statusEl.innerHTML = `<span style="color:var(--success)">${setupData.message} ✅</span>`;
                    appState.config.pg = payload;
                    const nextBtn = document.getElementById('btn-next-db');
                    if (nextBtn) {
                        nextBtn.disabled = false;
                        nextBtn.onclick = () => handleDBFinish();
                    }
                } else {
                    statusEl.innerHTML = `<span style="color:var(--error)">Hata: ${setupData.error}</span>`;
                }
            } catch (setupErr) {
                statusEl.innerHTML = `<span style="color:var(--error)">Kurulum hatası oluştu.</span>`;
            }
        } else {
            statusEl.innerHTML = `<span style="color:var(--error)">Hata: ${result.error}</span>`;
        }
    } catch (e) {
        statusEl.innerHTML = `<span style="color:var(--error)">Bağlantı Hatası: ${e.message}</span>`;
    }
}

async function fetchLogoFirms() {
    const firmArea = document.getElementById('logo-firm-area');
    const firmCards = document.getElementById('logo-firm-cards');
    const firmSelect = document.getElementById('logo-firm-select');

    if (!firmCards || !appState.config.ms) return;

    try {
        const res = await fetch('/api/logo-firms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(appState.config.ms)
        });
        const data = await res.json();

        if (data.success && data.firms && data.firms.length > 0) {
            firmCards.innerHTML = data.firms.map(f => `
                <div class="firm-card" onclick="selectFirm('${f.id}', this)">
                    <div class="firm-info">
                        <div class="firm-number">Firma ${f.id}</div>
                        <div class="firm-name">${f.name}</div>
                    </div>
                    <div class="firm-check">✓</div>
                </div>
            `).join('');

            if (firmArea) firmArea.classList.remove('hidden');
        } else {
            firmCards.innerHTML = '<p style="text-align:center; color:var(--text-muted);">Firma bulunamadı</p>';
            if (firmArea) firmArea.classList.add('hidden');
        }
    } catch (e) {
        console.error('Logo firmalar alınamadı:', e);
        firmCards.innerHTML = '<p style="text-align:center; color:var(--danger);">Hata: Firmalar yüklenemedi</p>';
    }
}

function selectFirm(firmId, cardElement) {
    console.log('selectFirm called with firmId:', firmId);

    // Remove selection from all cards
    document.querySelectorAll('.firm-card').forEach(card => card.classList.remove('selected'));

    // Select clicked card
    cardElement.classList.add('selected');

    // Update hidden input
    const hiddenInput = document.getElementById('logo-firm-select');
    if (hiddenInput) {
        hiddenInput.value = firmId;
        console.log('Hidden input updated to:', hiddenInput.value);
    } else {
        console.error('Hidden input logo-firm-select not found!');
    }
}

async function handleDBFinish() {
    const firmId = document.getElementById('logo-firm-select')?.value;
    const msHost = appState.config.ms?.host;

    console.log('handleDBFinish called - firmId:', firmId, 'msHost:', msHost);

    // IF MSSQL is configured, we MUST have a firm selection
    if (msHost && !firmId) {
        alert("MSSQL bağlantısı yapıldı. Lütfen devam etmek için bir Logo Firması seçin.");
        return;
    }

    // If a firm is selected, we ALWAYS go to the selection page (Step 4)
    if (firmId) {
        console.log('Fetching Logo schema info for firm:', firmId);
        const success = await fetchLogoSchemaInfo();
        if (success) {
            goToStep(4);
        } else {
            alert("Logo verileri (Satışçılar/Ambarlar) alınamadı. Lütfen bağlantınızı veya firma yetkileri kontrol edin.");
        }
    } else {
        // No firm and no MSSQL? Skip to final install
        goToStep(5);
    }
}

async function fetchLogoSchemaInfo() {
    const listSales = document.getElementById('list-salesmen');
    const listWare = document.getElementById('list-warehouses');
    const listCust = document.getElementById('list-customers');
    if (listSales) listSales.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px;">Yükleniyor...</td></tr>';
    if (listWare) listWare.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:20px;">Yükleniyor...</td></tr>';
    if (listCust) listCust.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px;">Yükleniyor...</td></tr>';

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

        if (!res.ok) {
            const errText = await res.text();
            console.error("Schema Fetch HTTP Error:", res.status, errText);
            throw new Error(`HTTP ${res.status}: ${errText}`);
        }

        const data = await res.json();
        console.log("Schema data received:", {
            salesmen: data.salesmen?.length,
            warehouses: data.warehouses?.length,
            customers: data.customers?.length
        });

        if (data.success) {
            const usedUsernames = new Set();

            // 1. Render Salesmen
            if (listSales) {
                const salesmen = data.salesmen || [];
                listSales.innerHTML = salesmen.map(s => {
                    const sid = s.id || '';
                    const sname = s.name || '';
                    let suggested = generateUsername(sid || sname);
                    if (usedUsernames.has(suggested)) {
                        suggested = `${suggested}.${sid}`;
                    }
                    usedUsernames.add(suggested);
                    return `
                        <tr>
                            <td><input type="checkbox" id="sls-${sid}" value="${sid}" checked></td>
                            <td style="color:var(--text-muted); font-family:monospace; font-size:12px;">${s.logo_ref || '-'}</td>
                            <td style="font-weight:bold; color:var(--primary);">${sid}</td>
                            <td><label for="sls-${sid}">${sname}</label></td>
                            <td><input type="text" class="credential-input username-input" data-id="${sid}" value="${suggested}" placeholder="Kullanıcı Adı"></td>
                            <td><input type="text" class="credential-input password-input" data-id="${sid}" value="123456" placeholder="Şifre"></td>
                        </tr>
                    `;
                }).join('') || '<tr><td colspan="5" style="text-align:center;">Kayıt bulunamadı.</td></tr>';
            }

            // 2. Render Warehouses
            if (listWare) {
                const warehouses = data.warehouses || [];
                listWare.innerHTML = warehouses.map(w => {
                    const wid = w.id || '';
                    const wname = w.name || '';
                    return `
                        <tr>
                            <td><input type="checkbox" id="wh-${wid}" value="${wid}" checked></td>
                            <td style="font-weight:bold; color:var(--accent);">${wid}</td>
                            <td><label for="wh-${wid}">${wname}</label></td>
                        </tr>
                    `;
                }).join('') || '<tr><td colspan="3" style="text-align:center;">Kayıt bulunamadı.</td></tr>';
            }

            // 3. Render Customers (Limited to 1000 for display performance)
            if (listCust) {
                const customers = data.customers || [];
                const displayLimit = 1000;
                const displayList = customers.slice(0, displayLimit);

                listCust.innerHTML = displayList.map(c => {
                    const cid = c.id || '';
                    const cname = c.name || '';
                    const specode = c.specode || '-';
                    const cyphcode = c.cyphcode || '-';
                    return `
                        <tr>
                            <td><input type="checkbox" id="cust-${cid}" value="${cid}" checked></td>
                            <td style="font-weight:bold; color:var(--success);">${cid}</td>
                            <td title="${cname}">${cname.length > 40 ? cname.substring(0, 40) + '...' : cname}</td>
                            <td>${specode}</td>
                            <td>${cyphcode}</td>
                            <td>
                                <input type="text" 
                                    class="credential-input map-link-input" 
                                    data-id="${cid}" 
                                    placeholder="Harita Linki (Opsiyonel)"
                                    style="max-width: 100%;"
                                >
                            </td>
                        </tr>
                    `;
                }).join('') || '<tr><td colspan="6" style="text-align:center;">Kayıt bulunamadı.</td></tr>';

                if (customers.length > displayLimit) {
                    listCust.innerHTML += `<tr><td colspan="6" style="text-align:center; color:var(--warning); padding:10px;">Uyarı: Toplam ${customers.length} kayıt var, sadece ilk ${displayLimit} kayıt gösteriliyor. Arama kutusunu kullanın.</td></tr>`;
                }
            }
            return true;
        } else {
            console.error("Logo Schema Error:", data.error);
            listSales.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--danger);">Hata: ' + data.error + '</td></tr>';
            listWare.innerHTML = '';
            return false;
        }
    } catch (e) {
        console.error("Schema Fetch Exception Detail:", e);
        alert("Bağlantı Hatası: Logo verileri çekilemedi.\nDetay: " + e.message);
        return false;
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

    // 2. Save Backup Config
    const backupInterval = document.getElementById('backup-interval').value;
    if (backupInterval !== 'off') {
        log("Yedekleme yapılandırması kaydediliyor...");
        const backupDays = Array.from(document.querySelectorAll('#backup-days-group input:checked')).map(cb => cb.value);
        try {
            await fetch('/api/save-backup-config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    backup_dir: document.getElementById('backup-dir').value,
                    backup_interval: backupInterval,
                    backup_time: document.getElementById('backup-time').value,
                    backup_hours: document.getElementById('backup-hours').value,
                    backup_days: backupDays
                })
            });
            log("Yedekleme ayarları kaydedildi. ✅");
        } catch (e) {
            log("Yedekleme ayarları kaydedilemedi.");
        }
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

    // 4. Logo Sync (only if a firm was selected in Step 3)
    const firmId = document.getElementById('logo-firm-select')?.value;
    if (!appState.migrationMode && appState.config.ms?.host && firmId) {
        log("Logo veri aktarımı başlatılıyor...");

        // Collect MAP LINKS for customers
        const customerInputs = Array.from(document.querySelectorAll('.map-link-input'));
        const customerMap = {};
        customerInputs.forEach(inp => {
            const val = inp.value.trim();
            if (val) customerMap[inp.getAttribute('data-id')] = val;
        });

        const salesmen = Array.from(document.querySelectorAll('#list-salesmen input[type="checkbox"]:checked')).map(cb => {
            const id = cb.value;
            const row = cb.closest('tr');
            return {
                id: id,
                username: row.querySelector('.username-input').value.trim() || id,
                password: row.querySelector('.password-input').value.trim() || "123456"
            };
        });

        // Prepare selected customers list with map links
        const selectedCustomers = Array.from(document.querySelectorAll('#list-customers input[type="checkbox"]:checked')).map(cb => {
            return {
                id: cb.value,
                map_link: customerMap[cb.value] || null
            };
        });

        // Validation: Unique Usernames
        const usernames = salesmen.map(s => s.username);
        const hasDuplicates = usernames.some((item, index) => usernames.indexOf(item) !== index);
        if (hasDuplicates) {
            log("HATA: Tekrarlanan kullanıcı adları var. Lütfen her satışçı için benzersiz bir kullanıcı adı belirleyin.");
            return;
        }

        if (salesmen.length === 0 && warehouses.length === 0) {
            log("UYARI: Aktarılacak kalem seçilmedi, bu adım atlanıyor.");
        } else {
            try {
                const res = await fetch('/api/sync-logo-selective', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        pg_config: appState.config.pg,
                        ms_config: appState.config.ms,
                        firm_id: selectedFirm,
                        salesmen: salesmen,
                        warehouses: warehouses,
                        customers: customers
                    })
                });
                const syncData = await res.json();

                // Display detailed logs
                if (syncData.logs && Array.from(syncData.logs).length > 0) {
                    syncData.logs.forEach(l => log(l));
                }

                if (syncData.success) {
                    log("Logo senkronizasyonu tamamlandı. ✅");

                    // Trigger PDF download
                    if (syncData.pdf_url) {
                        log("Kullanıcı bilgileri PDF raporu hazırlanıyor...");
                        const link = document.createElement('a');
                        link.href = syncData.pdf_url;
                        link.download = 'salesman_credentials.pdf';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        log("PDF Raporu indirildi. 📄✅");
                    }
                } else {
                    log("UYARI: " + syncData.error);
                }
            } catch (e) {
                log("UYARI: Logo senkronizasyonu tamamlanamadı.");
            }
        }
    }

    // 5. Deployment Step
    if (appState.selectedApp === 'WHATSAPP') {
        log("BerqenasCloud WhatsApp Api kurulumu başlatıldı (Bu işlem birkaç dakika sürebilir)...");
        try {
            const waRes = await fetch('/api/install-whatsapp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pg: appState.config.pg,
                    wa: {
                        port: getVal('wa-port', '8080'),
                        instance: getVal('wa-instance', 'EXFIN'),
                        key: getVal('wa-key', '42247726A7F14310B30A3CA655148D32')
                    }
                })
            });

            if (!waRes.ok) {
                const text = await waRes.text();
                log("HATA: Sunucu yanıtı başarısız (" + waRes.status + ")");
                log(text.substring(0, 100));
                return;
            }

            const waData = await waRes.json();
            if (waData.success) {
                log(waData.message || "Kurulum tamamlandı! ✅");
                finishAndShowSuccess();
            } else {
                log("HATA: Kurulum başarısız.");
                log(waData.error || "Bilinmeyen bir hata oluştu.");
                if (waData.logs) {
                    console.error("Installation Logs:", waData.logs);
                    log("Detaylar console loglarında (F12).");
                }
            }
        } catch (e) {
            log("KRİTİK HATA: " + e.message);
        }
    } else if (appState.deploymentMode === "1") {
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
                finishAndShowSuccess();
            } else {
                log("HATA: Servis kurulamadı.");
                log(instData.error);
            }
        } catch (e) {
            log("Kritik sunucu hatası (Install).");
        }
    } else {
        log("Hızlı başlatma (Tray) modu seçildi.");
        try {
            const res = await fetch('/api/launch-tray', { method: 'POST' });
            log("Yönetim paneli (Tray) başlatılıyor...");
            finishAndShowSuccess();
        } catch (e) {
            log("Tray başlatma hatası.");
        }
    }
}

function finishAndShowSuccess() {
    setTimeout(() => {
        document.querySelector('.progress-container').style.display = 'none';
        document.getElementById('install-logs').style.display = 'none';

        const appNameSpan = document.getElementById('success-app-name');
        if (appNameSpan) appNameSpan.innerText = appState.selectedApp || "OPS";

        // Show WhatsApp QR Addon if selected
        if (appState.selectedApp === 'WHATSAPP') {
            const waAddon = document.getElementById('wa-success-addon');
            if (waAddon) waAddon.classList.remove('hidden');
        }

        document.getElementById('success-screen').classList.remove('hidden');
    }, 2000);
}

async function fetchWhatsAppQR() {
    const btn = document.getElementById('btn-show-qr');
    const qrImageDiv = document.getElementById('wa-qr-image');

    btn.disabled = true;
    btn.innerText = "Yükleniyor...";

    try {
        const payload = {
            port: getVal('wa-port', '8080'),
            instance: getVal('wa-instance', 'EXFIN'),
            key: getVal('wa-key', '42247726A7F14310B30A3CA655148D32')
        };

        const res = await fetch('/api/whatsapp-qr', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.qrcode && data.qrcode.base64) {
            qrImageDiv.innerHTML = `<img src="${data.qrcode.base64}" style="width: 250px; height: 250px; display: block;">`;
            qrImageDiv.classList.remove('hidden');
            btn.innerText = "Yenile";
        } else if (data.status === "CONNECTED") {
            qrImageDiv.innerHTML = `<div style="padding: 20px; color: var(--success); font-weight: bold;">WhatsApp Zaten Bağlı! ✅</div>`;
            qrImageDiv.classList.remove('hidden');
            btn.classList.add('hidden');
        } else {
            alert("QR Kod alınamadı: " + (data.error || "Bilinmeyen hata"));
            btn.innerText = "Tekrar Dene";
        }
    } catch (e) {
        alert("Bağlantı Hatası: Servis henüz hazır olmayabilir.");
        btn.innerText = "Tekrar Dene";
    }
    btn.disabled = false;
}

async function launchTray() {
    try {
        const res = await fetch('/api/launch-tray', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            alert(data.message || "Tray App başlatıldı. Saatin yanındaki simgeyi kontrol edin.");
        } else {
            console.error("Tray Error:", data.error);
            alert("Tray App başlatılamadı: " + data.error);
        }
    } catch (e) {
        alert("Tray App başlatılamadı.");
    }
}

function selectAll(type, checked) {
    let listId = 'list-salesmen';
    if (type === 'warehouses') listId = 'list-warehouses';
    if (type === 'customers') listId = 'list-customers';

    const container = document.getElementById(listId);
    if (!container) return;

    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.checked = checked;
    });
}
