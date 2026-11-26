# CND_lab：藍隊資安監控網站實驗室

從零開始打造一套小型藍隊監控系統，練習收集 Linux 主機與網站日誌、解析事件、偵測可疑活動、製作儀表板，最後在隔離且自己擁有的實驗環境中驗證偵測效果。

> 僅在自己擁有或明確獲准的系統上進行測試。攻擊演練只對自己的 lab 目標執行。

## 我的環境

- 主機：Windows 11
- 虛擬化：VMware
- Linux VM：Ubuntu，4 vCPU、4 GB RAM、30 GB 磁碟
- 編輯方式：VS Code Remote SSH
- 語言與版本控制：Python、Git、GitHub

先以單台 Ubuntu VM 完成日誌收集與解析。這樣比較容易學習，也適合目前的資源；之後若要模擬攻防，再加入隔離網路中的 Kali VM。

## 學習路線

| 階段 | 目標 | 預計成果 |
| --- | --- | --- |
| 1. 日誌收集與解析 | 持續讀取 SSH 認證與 Nginx 存取日誌，轉成一致事件格式 | Python 日誌監控程式、JSON Lines 事件輸出 |
| 2. 偵測規則 | 偵測 SSH 暴力嘗試、網站掃描、常見 Web 攻擊特徵與異常登入 | YAML 規則、告警與 MITRE ATT&CK 對應 |
| 3. 儀表板 | 查看告警、攻擊來源、趨勢及攻擊類型 | 簡單易懂的監控頁面，之後再評估離線 GeoLite2 |
| 4. 通知與回應 | 通知分析者，提供人工確認後的封鎖流程 | Webhook 通知與可審核的 IP 封鎖操作 |
| 5. 藍隊演練 | 在隔離的自有 lab 驗證偵測效果並記錄處置 | 含時間線、IOC、調查與改善項目的事件報告 |

## 事件資料格式

解析後的每筆事件使用以下欄位，方便後續偵測與儀表板共用：

- `timestamp`：事件時間，採 ISO 8601 格式並保留時區
- `source_ip`：來源 IP；無法解析時為 `null`
- `event_type`：事件類型，例如 `ssh_failed_login`、`ssh_successful_login`、`nginx_access`
- `source`：日誌來源，例如 `auth.log` 或 `nginx_access.log`
- `message`：原始日誌內容，保留調查線索

## 專案進度

### 第 1 階段：日誌收集與解析

- [x] 建立 Python 專案骨架與執行方式
- [x] 解析 Ubuntu SSH 認證日誌中的成功與失敗登入
- [x] 解析 Nginx combined 格式 access log
- [x] 持續讀取新增日誌並輸出統一事件 JSON
- [ ] 在 Ubuntu VM 驗證安裝、檔案權限與實際輸出

## 目錄

```text
CND_lab/
├── README.md
├── pyproject.toml
├── requirements.txt
└── src/
    └── cnd_lab/
        ├── __init__.py
        ├── __main__.py
        ├── models.py
        ├── parsers.py
        └── tailer.py
```

## 第一次在 Ubuntu 執行

先在 Ubuntu VM 安裝 Python 虛擬環境工具，並下載專案：

```bash
sudo apt update
sudo apt install -y python3 python3-venv git
git clone https://github.com/xmasheng/CND_lab.git
cd CND_lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

啟動監控：

```bash
python -m cnd_lab
```

程式預設監控 `/var/log/auth.log` 和 `/var/log/nginx/access.log`，從啟動後新增的行開始讀取。每筆解析成功的事件會輸出一行 JSON；按 `Ctrl+C` 停止。若只想先讀取現有內容再繼續監控：

```bash
python -m cnd_lab --from-start
```

如果 Nginx 尚未安裝或尚未建立 access log，程式會略過該檔案並繼續監控存在的日誌。也可以用 `--auth-log` 和 `--nginx-log` 指定自己的日誌路徑。

## 日誌讀取權限

不要用 `sudo python -m cnd_lab` 執行整個程式。Ubuntu 通常用 `adm` 群組管理系統日誌讀取權限。先查看權限：

```bash
ls -l /var/log/auth.log /var/log/nginx/access.log
```

若檔案群組是 `adm`，可將自己的帳號加入該群組，再登出 Ubuntu 並重新登入：

```bash
sudo usermod -aG adm "$USER"
```

重新登入後再執行程式。只在確認日誌檔案的群組及權限後才套用這個方式；若 Nginx 日誌不屬於 `adm`，應只調整該日誌的讀取權限，不要開放成所有使用者可讀。

## 開發原則

- 每次只增加一小段功能，先看懂再繼續。
- 第一階段使用 Python 標準函式庫，沒有額外執行期套件。
- 程式以一般使用者權限執行；只授予讀取日誌所需的權限，不要用 root 執行整個程式。
- 先記錄與告警；封鎖 IP 等會影響系統的動作，必須經過明確確認。
- 演練只對隔離環境中自己控制的目標進行，並記錄測試時間與結果。

## 第一階段目前的限制

- SSH 解析支援 Ubuntu 常見的 `sshd` 成功與失敗登入訊息。
- Nginx 解析器預期使用常見的 combined access log 格式。
- 事件輸出到終端機；下一步再加入保存至檔案與在你的 VM 上驗證。
- 尚未涵蓋所有 Linux 發行版、客製化日誌格式或多行事件。
