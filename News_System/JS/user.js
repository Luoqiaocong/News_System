// SHA1加密函数
function sha1(str) {
    const buffer = new TextEncoder('utf-8').encode(str);
    return crypto.subtle.digest('SHA-1', buffer).then(hash => {
        return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
    });
}

// 邮箱校验
function validateEmail(email) {
    const emailRegex = /^[\w.-]+@[\w.-]+\.\w{2,}$/;
    return emailRegex.test(email);
}

// 密码校验（至少8位，包含大小写字母和特殊字符）
function validatePassword(password) {
    const hasLength = password.length >= 8;
    const hasLower = /[a-z]/.test(password);
    const hasUpper = /[A-Z]/.test(password);
    const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]/.test(password);
    return hasLength && hasLower && hasUpper && hasSpecial;
}

// 密码实时验证 - 显示密码强度条
function validatePasswordRealTime() {
    const password = document.getElementById('password').value;
    
    // 计算密码强度
    let score = 0;
    const hasLength = password.length >= 8;
    const hasLower = /[a-z]/.test(password);
    const hasUpper = /[A-Z]/.test(password);
    const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?]/.test(password);
    
    if (hasLength) score++;
    if (hasLower) score++;
    if (hasUpper) score++;
    if (hasSpecial) score++;
    
    // 更新强度条
    updateStrengthBar(score);
    
    // 更新强度文字
    const strengthText = document.getElementById('strength-text');
    const texts = ['请输入密码', '弱', '一般', '良好', '强'];
    const colors = ['#999', '#ee5a5a', '#f39c12', '#3498db', '#00c091'];
    strengthText.textContent = texts[score];
    strengthText.style.color = colors[score];
}

// 更新密码强度条
function updateStrengthBar(score) {
    const bars = ['bar1', 'bar2', 'bar3', 'bar4'];
    const colors = ['#ee5a5a', '#f39c12', '#3498db', '#00c091'];
    
    bars.forEach((barId, index) => {
        const bar = document.getElementById(barId);
        if (index < score) {
            bar.style.background = colors[score - 1];
            bar.style.width = '25%';
        } else {
            bar.style.background = '#ddd';
            bar.style.width = '25%';
        }
    });
}

async function doRegister() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    // 基础验证
    if (!email || !password || !confirmPassword) {
        showModal('提示', '请填写所有必填字段！', 'error');
        return;
    }
    
    // 邮箱校验
    if (!validateEmail(email)) {
        showModal('提示', '请输入有效的邮箱地址！', 'error');
        return;
    }
    
    // 密码长度校验
    if (!validatePassword(password)) {
        showModal('提示', '密码长度至少需要8位！', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showModal('提示', '两次输入的密码不一致！', 'error');
        return;
    }

    try {
        // 直接加密密码（salt由后端生成）
        const passwordHash = await sha1(password);

        const response = await fetch('http://localhost:8000/api/user/reg', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                email: email, 
                password: passwordHash
            })
        });

        const result = await response.json();
        if (response.ok && result.code==20100) {
            showModal('注册成功', '恭喜您注册成功！请登录', 'success');
            // 3秒后切换到登录界面
            setTimeout(() => {
                closeModal();
                document.getElementById('container').classList.remove("right-panel-active");
            }, 2000);
        } else {
            showModal('注册失败', result.msg || result.message || '未知错误', 'error');
        }
    } catch (error) {
        console.error('注册请求失败:', error);
        showModal('错误', '网络错误，请稍后重试', 'error');
    }
}

async function doLogin() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    // 基础验证
    if (!email || !password) {
        showModal('提示', '请填写邮箱和密码！', 'error');
        return;
    }

    // 邮箱校验
    if (!validateEmail(email)) {
        showModal('提示', '请输入有效的邮箱地址！', 'error');
        return;
    }

    // 密码长度校验
    if (!validatePassword(password)) {
        showModal('提示', '密码长度至少需要8位！', 'error');
        return;
    }

    try {
        // 登录时也加密密码（与注册时使用相同的加密方式）
        const passwordHash = await sha1(password);

        const response = await fetch('http://localhost:8000/api/user/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, password: passwordHash })
        });
        
        const result = await response.json();

        if (response.ok) {
            // 核心：把后端生成的那个长长的 Token 存在浏览器里
            localStorage.setItem('access_token', result.data.token); 
            showModal('登录成功', '欢迎回来！正在跳转...', 'success');
            // 2秒后跳转到首页
            setTimeout(() => {
                window.location.href = "../HTML/index.html";
            }, 1500);
        } else {
            showModal('登录失败', result.msg || result.message || '用户名或密码错误', 'error');
        }
    } catch (error) {
        console.error('登录请求失败:', error);
        showModal('错误', '网络错误，请稍后重试', 'error');
    }
}

async function deleteMyAccount() {
    const token = localStorage.getItem('access_token');

    const response = await fetch('http://localhost:8000/api/user/delete', {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`, // 格式必须是 Bearer 空格 Token
            'Content-Type': 'application/json'
        }
    });
    // ... 处理返回
}