const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1000,
    minHeight: 700,
    backgroundColor: '#0f172a', // Koyu uzay grisi
    autoHideMenuBar: true, // Üstteki çirkin Dosya/Düzenle menüsünü gizler
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false // CORS engelini aşmak için BUNU EKLEDİK
    }
  });

  mainWindow.loadFile('home.html');
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});