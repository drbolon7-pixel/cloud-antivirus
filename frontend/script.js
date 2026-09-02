let currentUser = null;
let authToken = null;
let selectedFile = null;
let currentPage = 1;

// Page navigation
function showPage(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    
    // Show selected page
    const pageMap = {
        'home': 'homePage',
        'login': 'loginPage',
        'register': 'registerPage',
        'scanner': 'scannerPage',
        'history': 'historyPage',
        'dashboard': 'dashboardPage'
    };
    
    const targetPage = document.getElementById(pageMap[page]);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // Update navigation based on auth status
    updateNav();
    
    if (page === 'history' && authToken) {
        loadHistory();
    }
    
    if (page === 'dashboard' && authToken) {
        loadDashboard();
    }
}

// Update navigation based on auth status
function updateNav() {
    const authButtons = document.getElementById('authButtons');
    const userInfo = document.getElementById('userInfo');
    const usernameDisplay = document.getElementById('usernameDisplay');
    const scanNav = document.getElementById('scanNav');
    const historyNav = document.getElementById('historyNav');
    const dashboardNav = document.getElementById('dashboardNav');
    
    if (authToken && currentUser) {
        authButtons.style.display = 'none';
        userInfo.style.display = 'flex';
        usernameDisplay.textContent = currentUser.username;
        scanNav.style.display = 'inline';
        historyNav.style.display = 'inline';
        dashboardNav.style.display = 'inline';
    } else {
        authButtons.style.display = 'flex';
        userInfo.style.display = 'none';
        scanNav.style.display = 'none';
        historyNav.style.display = 'none';
        dashboardNav.style.display = 'none';
    }
}

// Register
async function register(event) {
    event.preventDefault();
    
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Registration successful! Please login.');
            showPage('login');
        } else {
            alert(data.message || 'Registration failed');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}

// Login
async function login(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('user', JSON.stringify(currentUser));
            showPage('home');
            updateNav();
        } else {
            alert(data.message || 'Login failed');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}

// Logout
function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    showPage('home');
    updateNav();
}

// File handling
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        selectedFile = file;
        document.getElementById('fileInfo').style.display = 'flex';
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
        document.getElementById('scanResults').style.display = 'none';
        document.getElementById('scanProgress').style.display = 'none';
    }
}

// Drag and drop
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#667eea';
        uploadArea.style.background = '#f0f1ff';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#d0d0d0';
        uploadArea.style.background = '#f8f9ff';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#d0d0d0';
        uploadArea.style.background = '#f8f9ff';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            selectedFile = files[0];
            document.getElementById('fileInfo').style.display = 'flex';
            document.getElementById('fileName').textContent = selectedFile.name;
            document.getElementById('fileSize').textContent = `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`;
            document.getElementById('scanResults').style.display = 'none';
            document.getElementById('scanProgress').style.display = 'none';
        }
    });
    
    // Check for saved session
    const savedToken = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('user');
    if (savedToken && savedUser) {
        authToken = savedToken;
        currentUser = JSON.parse(savedUser);
        updateNav();
    }
    
    // Show home page by default
    showPage('home');
});

// Start scan
async function startScan() {
    if (!authToken) {
        alert('Please login first');
        showPage('login');
        return;
    }
    
    if (!selectedFile) {
        alert('Please select a file first');
        return;
    }
    
    // Show progress
    document.getElementById('scanProgress').style.display = 'block';
    document.getElementById('scanResults').style.display = 'none';
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressText').textContent = 'Uploading file...';
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            document.getElementById('progressFill').style.width = `${progress}%`;
            if (progress > 50) {
                document.getElementById('progressText').textContent = 'Scanning for threats...';
            }
        }, 300);
        
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        clearInterval(progressInterval);
        document.getElementById('progressFill').style.width = '100%';
        document.getElementById('progressText').textContent = 'Scan complete!';
        
        const data = await response.json();
        
        if (response.ok) {
            // Display results
            document.getElementById('scanResults').style.display = 'block';
            
            const isClean = data.status === 'clean';
            document.getElementById('resultIcon').textContent = isClean ? '✅' : '⚠️';
            document.getElementById('resultStatus').textContent = isClean ? 'Clean - No threats detected' : 'Threat Detected!';
            document.getElementById('resultStatus').style.color = isClean ? '#2e7d32' : '#c62828';
            
            document.getElementById('threatName').textContent = data.threat_name || 'None detected';
            document.getElementById('fileHash').textContent = data.file_hash || '-';
            document.getElementById('scanDuration').textContent = `${data.scan_duration?.toFixed(2) || 0} seconds`;
            
            const severityMap = {
                'low': '🟢 Low',
                'medium': '🟡 Medium',
                'high': '🔴 High',
                'critical': '🚨 Critical'
            };
            document.getElementById('severity').textContent = severityMap[data.severity] || 'Unknown';
            
            setTimeout(() => {
                document.getElementById('scanProgress').style.display = 'none';
            }, 1000);
        } else {
            alert(data.message || 'Scan failed');
            document.getElementById('scanProgress').style.display = 'none';
        }
    } catch (error) {
        alert('Network error. Please try again.');
        document.getElementById('scanProgress').style.display = 'none';
    }
}

// Load scan history
async function loadHistory(page = 1) {
    if (!authToken) return;
    
    try {
        const response = await fetch(`/api/scans?page=${page}&per_page=10`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const historyList = document.getElementById('historyList');
            
            if (data.scans.length === 0) {
                historyList.innerHTML = '<p style="text-align:center;color:#888;padding:2rem;">No scan history found</p>';
                return;
            }
            
            let html = '';
            data.scans.forEach(scan => {
                const statusClass = scan.status === 'clean' ? 'status-clean' : 
                                   scan.status === 'infected' ? 'status-infected' : 'status-suspicious';
                const statusLabel = scan.status.charAt(0).toUpperCase() + scan.status.slice(1);
                
                html += `
                    <div class="history-item">
                        <div>
                            <strong>${scan.filename}</strong>
                            <div style="font-size:0.8rem;color:#888;margin-top:0.2rem;">
                                ${new Date(scan.scanned_at).toLocaleString()}
                            </div>
                        </div>
                        <div>
                            <span class="status-badge ${statusClass}">${statusLabel}</span>
                            ${scan.threat_name ? `<span style="margin-left:0.5rem;font-size:0.8rem;color:#c62828;">${scan.threat_name}</span>` : ''}
                            <span style="margin-left:0.5rem;font-size:0.8rem;color:#888;">${(scan.file_size / 1024).toFixed(1)} KB</span>
                        </div>
                    </div>
                `;
            });
            
            historyList.innerHTML = html;
            
            // Pagination
            const pagination = document.getElementById('pagination');
            if (data.pages > 1) {
                pagination.style.display = 'flex';
                pagination.style.justifyContent = 'center';
                pagination.style.gap = '0.5rem';
                pagination.style.marginTop = '1rem';
                
                let paginationHtml = '';
                for (let i = 1; i <= data.pages; i++) {
                    paginationHtml += `
                        <button onclick="loadHistory(${i})" class="btn ${i === data.page ? 'btn-primary' : 'btn-outline'}" style="padding:0.3rem 0.8rem;">
                            ${i}
                        </button>
                    `;
                }
                pagination.innerHTML = paginationHtml;
            } else {
                pagination.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Load dashboard
async function loadDashboard() {
    if (!authToken) return;
    
    try {
        // Get scan statistics
        const response = await fetch('/api/scans?per_page=1', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // For demo purposes, generate mock statistics
            const totalScans = data.total || 0;
            const threatsDetected = Math.floor(Math.random() * 10);
            const cleanFiles = totalScans - threatsDetected;
            const apiUsage = Math.floor(Math.random() * 1000);
            
            document.getElementById('totalScans').textContent = totalScans;
            document.getElementById('threatsDetected').textContent = threatsDetected;
            document.getElementById('cleanFiles').textContent = cleanFiles;
            document.getElementById('apiUsage').textContent = apiUsage;
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Additional initialization
    console.log('Cloud Antivirus App initialized');
});
