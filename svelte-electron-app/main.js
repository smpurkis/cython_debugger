// Modules to control application life and create native browser window
const { app, BrowserWindow, Menu, dialog } = require('electron')
const path = require('path')
const fs = require('fs');
let mainWindow;

const template = [
  {
    label: 'File',
    submenu: [
      {
        label: "Refresh Page",
        accelerator: "CmdOrCtrl+R",
        click() {
          this.mainWindow.reload();
        }
      },
      {
        label: 'Open File...',
        accelerator: 'CmdOrCtrl+O',
        click() { openFile() }
      },
      {
        label: 'Open Folder...',
        accelerator: 'CmdOrCtrl+Alt+O',
        click() { openFolder() }
      },
      {
        label: 'Save File...',
        accelerator: 'CmdOrCtrl+S',
        click() {
          // We can't call saveFile(content) directly because we need to get
          // the content from the renderer process. So, send a message to the
          // renderer, telling it we want to save the file.
          this.mainWindow.webContents.send('save-file')
        }
      }
    ]
  },
  {
    label: 'Edit',
    submenu: [
      {
        label: 'Undo',
        accelerator: 'CmdOrCtrl+Z',
        role: 'undo'
      },
      {
        label: 'Redo',
        accelerator: 'Shift+CmdOrCtrl+Z',
        role: 'redo'
      },
      {
        type: 'separator'
      },
      {
        label: 'Cut',
        accelerator: 'CmdOrCtrl+X',
        role: 'cut'
      },
      {
        label: 'Copy',
        accelerator: 'CmdOrCtrl+C',
        role: 'copy'
      },
      {
        label: 'Paste',
        accelerator: 'CmdOrCtrl+V',
        role: 'paste'
      },
      {
        label: 'Select All',
        accelerator: 'CmdOrCtrl+A',
        role: 'selectall'
      }
    ]
  },
  {
    label: 'Developer',
    submenu: [
      {
        label: 'Toggle Developer Tools',
        accelerator: process.platform === 'darwin'
          ? 'Alt+Command+I'
          : 'Ctrl+Shift+I',
        click() { this.mainWindow.webContents.toggleDevTools() }
      }
    ]
  }
]
if (process.platform === 'darwin') {
  const name = app.getName()
  template.unshift({
    label: name,
    submenu: [
      {
        label: 'About ' + name,
        role: 'about'
      },
      {
        type: 'separator'
      },
      {
        label: 'Services',
        role: 'services',
        submenu: []
      },
      {
        type: 'separator'
      },
      {
        label: 'Hide ' + name,
        accelerator: 'Command+H',
        role: 'hide'
      },
      {
        label: 'Hide Others',
        accelerator: 'Command+Alt+H',
        role: 'hideothers'
      },
      {
        label: 'Show All',
        role: 'unhide'
      },
      {
        type: 'separator'
      },
      {
        label: 'Quit',
        accelerator: 'Command+Q',
        click() { app.quit() }
      }
    ]
  })
}

async function openFile() {
  const files = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
  })
  console.log(files);

  if (!files) return
  const file = files.filePaths[0]
  console.log(file);
  const content = fs.readFileSync(file).toString()

  console.log(content);

  app.addRecentDocument(file)


  this.mainWindow.webContents.send('file-opened', file, content)
}

async function openFolder() {
  const folders = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
  })
  console.log(folders);

  if (!folders) return
  const folder = folders.filePaths[0]
  console.log(folder);
  const folderContent = fs.readdirSync(folder)

  console.log(folderContent);

  // app.addRecentDocument(file)


  this.mainWindow.webContents.send('folder-opened', folder, folderContent)
}

function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      // preload: path.join(__dirname, 'preload.js')
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  // and load the index.html of the app.
  mainWindow.loadFile('./public/index.html')
  // mainWindow.loadURL('http://localhost:5000')

  // Open the DevTools.
  // mainWindow.webContents.openDevTools()
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
  this.mainWindow = mainWindow
}


// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  createWindow()

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit()
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.