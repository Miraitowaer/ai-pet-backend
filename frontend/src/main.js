import './style.css'

const authScreen = document.getElementById('auth-screen');
const appScreen = document.getElementById('app');
const actionBtn = document.getElementById('action-btn');
const authMsg = document.getElementById('auth-msg');

const tabLogin = document.getElementById('tab-login');
const tabRegister = document.getElementById('tab-register');
const registerExpansion = document.getElementById('register-expansion');

const accountInput = document.getElementById('account-input');
const passwordInput = document.getElementById('password-input');
const petnameInput = document.getElementById('petname-input');
const avatarOptions = document.querySelectorAll('.avatar-option');

// 状态机核心参数
let mode = 'login'; // 'login' or 'register'
let currentAvatarSelection = 'boy';
let finalPetName = null;

// Tab 切换逻辑
tabLogin.addEventListener('click', () => {
    mode = 'login';
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
    registerExpansion.style.display = 'none';
    actionBtn.innerText = "唤醒登录";
    authMsg.innerText = "";
});

tabRegister.addEventListener('click', () => {
    mode = 'register';
    tabRegister.classList.add('active');
    tabLogin.classList.remove('active');
    registerExpansion.style.display = 'block';
    actionBtn.innerText = "完成注册";
    authMsg.innerText = "";
});

// 头像选择
avatarOptions.forEach(opt => {
    opt.addEventListener('click', () => {
        avatarOptions.forEach(o => o.classList.remove('selected'));
        opt.classList.add('selected');
        currentAvatarSelection = opt.getAttribute('data-avatar');
    });
});

// 渲染游戏界面（通过下发的躯壳名）
function renderMainGameView(realPetName, realAvatarId) {
    // 兼容原有的命名映射
    const imageMap = {
        'pig': 'cute_cyber_pet',
        'boy': 'cyber_boy',
        'girl': 'cyber_girl'
    };
    const imageName = imageMap[realAvatarId] || 'cyber_boy';

    appScreen.innerHTML = `
      <div id="chat-bubble">校验成功~，主人！我是你的专属宠物 [${realPetName}]！</div>
      <div id="pet-container">
        <img id="pet-image" src="/${imageName}.png" alt="Pet"/>
      </div>
      <input type="text" id="input-box" placeholder="敲击回车和我通信..." autocomplete="off"/>
    `;
    
    const bubble = document.getElementById('chat-bubble');
    const inputBox = document.getElementById('input-box');
    
    // 使用独特的 pet_name 也就是数据库绑定名字建连接，保持隔离！
    const ws = new WebSocket(`ws://127.0.0.1:8000/ws?session_id=${realPetName}`);
    
    ws.onopen = () => { bubble.classList.add('show'); };
    ws.onmessage = (event) => {
        bubble.classList.remove('show');
        setTimeout(() => {
            bubble.innerText = event.data;
            bubble.classList.add('show');
        }, 100); 
    };

    inputBox.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && inputBox.value.trim() !== '') {
            const msg = inputBox.value.trim();
            bubble.classList.remove('show');
            ws.send(msg);
            inputBox.value = '';
        }
    });
}

// 核心网络请求
actionBtn.addEventListener('click', async () => {
    const acc = accountInput.value.trim();
    const pwd = passwordInput.value.trim();
    
    if (!acc || !pwd) {
        authMsg.innerText = "账号密码缺一不可！";
        return;
    }

    authMsg.innerText = "正在穿越防火墙连接微服务...";
    authMsg.style.color = "#88ccff";

    try {
        if (mode === 'login') {
            // [执行登录]
            const res = await fetch("http://127.0.0.1:8000/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ account_name: acc, password: pwd })
            });
            const data = await res.json();
            if (data.success) {
                authMsg.innerText = data.message;
                authMsg.style.color = "#00ff00";
                setTimeout(() => {
                    authScreen.style.display = 'none';
                    appScreen.style.display = 'flex';
                    // 登录成功时，后端必须把宠物的名字和装扮下发，恢复出原始状态！
                    renderMainGameView(data.pet_name, data.avatar);
                }, 1000);
            } else {
                authMsg.innerText = data.message;
                authMsg.style.color = "#ff4444";
            }
        } 
        else {
            // [执行注册]
            const petn = petnameInput.value.trim();
            if (!petn) {
                authMsg.innerText = "必须给新宠物取个名字！";
                return;
            }
            const res = await fetch("http://127.0.0.1:8000/api/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    account_name: acc,
                    password: pwd,
                    pet_name: petn,
                    avatar: currentAvatarSelection
                })
            });
            const data = await res.json();
            if (data.success) {
                authMsg.innerText = data.message;
                authMsg.style.color = "#00ff00";
                // 注册成功，提示回到登录页面
                setTimeout(() => {
                    tabLogin.click();
                    authMsg.innerText = "请使用刚注册的账号进行登录！";
                    authMsg.style.color = "#88ccff";
                }, 1500);
            } else {
                authMsg.innerText = data.message;
                authMsg.style.color = "#ff4444";
            }
        }
    } catch(err) {
        authMsg.innerText = "网络阻断，请确保 main.py 启动！";
        authMsg.style.color = "#ff4444";
        console.error(err);
    }
});
