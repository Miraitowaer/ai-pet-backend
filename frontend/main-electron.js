const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 450,
    height: 600,
    transparent: true,          // 绝对不能删的第一核心：开启无边框透明
    frame: false,               // 第二核心：隐藏标题栏和 X 按钮
    alwaysOnTop: true,          // 永远悬浮于桌面软件之上（这就是桌宠的魅力）
    resizable: false,
    hasShadow: false,           // 避免 Electron 在透明边缘绘制丑陋的黑框
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  // 在开发期间，我们使用 Vite 的热更新服务器地址
  mainWindow.loadURL('http://localhost:5173');
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});
