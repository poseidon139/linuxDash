const UI = {
    cpu: { val: document.getElementById('cpu-val'), bar: document.getElementById('cpu-bar') },
    mem: { val: document.getElementById('mem-val'), bar: document.getElementById('mem-bar'), text: document.getElementById('mem-text') },
    disk: { val: document.getElementById('disk-val'), bar: document.getElementById('disk-bar'), text: document.getElementById('disk-text') },
    net: { sent: document.getElementById('net-sent'), recv: document.getElementById('net-recv') },
    status: { dot: document.querySelector('.status-dot'), text: document.getElementById('connection-status') },
    alerts: { container: document.getElementById('alerts-container'), count: document.getElementById('alerts-count') },
    security: { container: document.getElementById('security-container') }
};

let alertsCount = 0;

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        UI.status.dot.className = 'status-dot online';
        UI.status.text.textContent = 'Connected';
    };

    ws.onclose = () => {
        UI.status.dot.className = 'status-dot offline';
        UI.status.text.textContent = 'Disconnected (Retrying...)';
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'metrics') {
                updateMetrics(msg.data);
            } else if (msg.type === 'alert') {
                addAlert(msg.data);
            } else if (msg.type === 'security_event') {
                addSecurityEvent(msg.data);
            }
        } catch (e) {
            console.error('Error parsing message', e);
        }
    };
}

function getColorForPercent(percent) {
    if (percent < 70) return 'var(--success)';
    if (percent < 90) return 'var(--warning)';
    return 'var(--critical)';
}

function updateMetrics(data) {
    // CPU
    UI.cpu.val.textContent = `${data.cpu.percent}%`;
    UI.cpu.bar.style.width = `${data.cpu.percent}%`;
    UI.cpu.bar.style.backgroundColor = getColorForPercent(data.cpu.percent);

    // Memory
    UI.mem.val.textContent = `${data.memory.percent}%`;
    UI.mem.bar.style.width = `${data.memory.percent}%`;
    UI.mem.bar.style.backgroundColor = getColorForPercent(data.memory.percent);
    UI.mem.text.textContent = `${data.memory.used_gb} / ${data.memory.total_gb} GB`;

    // Disk
    UI.disk.val.textContent = `${data.disk.percent}%`;
    UI.disk.bar.style.width = `${data.disk.percent}%`;
    UI.disk.bar.style.backgroundColor = getColorForPercent(data.disk.percent);
    UI.disk.text.textContent = `${data.disk.used_gb} / ${data.disk.total_gb} GB`;

    // Network
    UI.net.sent.textContent = `${data.network.sent_mb} MB`;
    UI.net.recv.textContent = `${data.network.recv_mb} MB`;
}

function createListItem(time, message, levelClass = '') {
    const div = document.createElement('div');
    div.className = `list-item ${levelClass}`;
    div.innerHTML = `
        <div class="item-time">${time}</div>
        <div class="item-msg">${message}</div>
    `;
    return div;
}

function addAlert(alert) {
    if (alertsCount === 0) {
        UI.alerts.container.innerHTML = ''; // Remove empty state
    }
    
    const item = createListItem(alert.timestamp, alert.message, alert.level);
    UI.alerts.container.prepend(item);
    
    alertsCount++;
    UI.alerts.count.textContent = alertsCount;
    
    // Keep only last 20 alerts
    if (UI.alerts.container.children.length > 20) {
        UI.alerts.container.removeChild(UI.alerts.container.lastChild);
    }
}

function addSecurityEvent(event) {
    if (UI.security.container.querySelector('.empty-state')) {
        UI.security.container.innerHTML = '';
    }
    
    const item = createListItem(event.timestamp, event.message, 'security-item');
    UI.security.container.prepend(item);
    
    // Keep only last 20 events
    if (UI.security.container.children.length > 20) {
        UI.security.container.removeChild(UI.security.container.lastChild);
    }
}

// Start connection
connectWebSocket();
