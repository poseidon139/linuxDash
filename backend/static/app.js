const UI = {
    cpu: { val: document.getElementById('cpu-val'), bar: document.getElementById('cpu-bar'), cores: document.getElementById('cpu-cores') },
    mem: { val: document.getElementById('mem-val'), bar: document.getElementById('mem-bar'), text: document.getElementById('mem-text'), swap: document.getElementById('swap-info') },
    disk: { val: document.getElementById('disk-val'), bar: document.getElementById('disk-bar'), text: document.getElementById('disk-text'), io: document.getElementById('disk-io'), partitions: document.getElementById('disk-partitions') },
    net: { sent: document.getElementById('net-sent'), recv: document.getElementById('net-recv'), interfaces: document.getElementById('net-interfaces') },
    load: { avg: document.getElementById('load-avg') },
    freq: { mhz: document.getElementById('cpu-freq') },
    processes: { list: document.getElementById('top-processes') },
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

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function updateMetrics(data) {
    // Load Average & CPU Frequency
    if (data.cpu.load_avg) {
        UI.load.avg.textContent = data.cpu.load_avg['1m'];
    }
    if (data.cpu.frequency_mhz) {
        UI.freq.mhz.textContent = data.cpu.frequency_mhz;
    }

    // CPU
    UI.cpu.val.textContent = `${data.cpu.total}%`;
    UI.cpu.bar.style.width = `${data.cpu.total}%`;
    UI.cpu.bar.style.backgroundColor = getColorForPercent(data.cpu.total);
    
    if (data.cpu.per_core && data.cpu.per_core.length > 0) {
        UI.cores.textContent = `${data.cpu.core_count || data.cpu.per_core.length} cores | Avg: ${Math.round(data.cpu.total)}%`;
    }

    // Memory
    UI.mem.val.textContent = `${data.memory.percent}%`;
    UI.mem.bar.style.width = `${data.memory.percent}%`;
    UI.mem.bar.style.backgroundColor = getColorForPercent(data.memory.percent);
    
    const memUsedGB = (data.memory.used / 1024 / 1024 / 1024).toFixed(2);
    const memTotalGB = (data.memory.total / 1024 / 1024 / 1024).toFixed(2);
    UI.mem.text.textContent = `${memUsedGB} / ${memTotalGB} GB`;
    
    if (data.memory.swap_total > 0) {
        const swapPercent = data.memory.swap_percent || 0;
        const swapUsedGB = (data.memory.swap_used / 1024 / 1024 / 1024).toFixed(2);
        const swapTotalGB = (data.memory.swap_total / 1024 / 1024 / 1024).toFixed(2);
        UI.mem.swap.textContent = `Swap: ${swapPercent}% (${swapUsedGB}/${swapTotalGB} GB)`;
    }

    // Disk - Use first partition for main display
    if (data.disk.partitions && data.disk.partitions.length > 0) {
        const rootPartition = data.disk.partitions.find(p => p.mountpoint === '/') || data.disk.partitions[0];
        UI.disk.val.textContent = `${rootPartition.percent}%`;
        UI.disk.bar.style.width = `${rootPartition.percent}%`;
        UI.disk.bar.style.backgroundColor = getColorForPercent(rootPartition.percent);
        
        const usedGB = (rootPartition.used / 1024 / 1024 / 1024).toFixed(2);
        const totalGB = (rootPartition.total / 1024 / 1024 / 1024).toFixed(2);
        UI.disk.text.textContent = `${usedGB} / ${totalGB} GB (${rootPartition.mountpoint})`;
        
        // Disk I/O
        if (data.disk.io_stats && data.disk.io_stats.read_mb_s !== undefined) {
            UI.disk.io.textContent = `I/O: ↑${data.disk.io_stats.write_mb_s} MB/s ↓${data.disk.io_stats.read_mb_s} MB/s`;
        }
        
        // Update partitions list
        updatePartitions(data.disk.partitions);
    }

    // Network
    if (data.network.bandwidth) {
        UI.net.sent.textContent = `${data.network.bandwidth.sent_mb_s} MB/s`;
        UI.net.recv.textContent = `${data.network.bandwidth.recv_mb_s} MB/s`;
    }
    
    // Update interfaces list
    if (data.network.interfaces) {
        updateInterfaces(data.network.interfaces);
    }

    // Top Processes
    if (data.memory.top_processes) {
        updateProcesses(data.memory.top_processes);
    }
}

function updateProcesses(processes) {
    if (!processes || processes.length === 0) {
        UI.processes.list.innerHTML = '<div class="empty-state">No process data available</div>';
        return;
    }
    
    UI.processes.list.innerHTML = processes.map(proc => `
        <div class="process-item">
            <span class="process-name">${proc.name} (PID: ${proc.pid})</span>
            <span class="process-mem">${proc.memory_mb} MB (${proc.percent}%)</span>
        </div>
    `).join('');
}

function updatePartitions(partitions) {
    if (!partitions || partitions.length === 0) {
        UI.disk.partitions.innerHTML = '<div class="empty-state">No partitions found</div>';
        return;
    }
    
    UI.disk.partitions.innerHTML = partitions.map(part => {
        const usedGB = (part.used / 1024 / 1024 / 1024).toFixed(2);
        const totalGB = (part.total / 1024 / 1024 / 1024).toFixed(2);
        const barColor = part.percent > 90 ? 'var(--critical)' : part.percent > 70 ? 'var(--warning)' : 'var(--success)';
        
        return `
            <div class="partition-item">
                <span class="partition-name">${part.device} → ${part.mountpoint}</span>
                <span class="partition-usage">${part.percent}%</span>
                <div class="partition-bar">
                    <div class="partition-fill" style="width: ${part.percent}%; background: ${barColor}"></div>
                </div>
                <span style="font-size: 0.75rem; color: var(--text-secondary); margin-left: 0.5rem;">${usedGB}/${totalGB} GB</span>
            </div>
        `;
    }).join('');
}

function updateInterfaces(interfaces) {
    const activeIfaces = interfaces.filter(iface => iface.is_up);
    if (activeIfaces.length === 0) {
        UI.net.interfaces.textContent = 'No active interfaces';
        return;
    }
    
    const ifaceNames = activeIfaces.map(i => `${i.name} (${i.speed >= 1000 ? (i.speed/1000).toFixed(0) + 'G' : i.speed + 'M'})`).join(', ');
    UI.net.interfaces.textContent = `Active: ${ifaceNames}`;
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
