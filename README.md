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

- [ ] 建立 Python 專案骨架與執行方式
- [ ] 解析 Ubuntu SSH 認證日誌
- [ ] 解析 Nginx access log
- [ ] 持續讀取新增日誌並輸出統一事件 JSON
- [ ] 在自己的 Ubuntu VM 驗證檔案權限與實際輸出

## 目錄規劃

```text
CND_lab/
├── README.md
├── requirements.txt
├── src/
│   └── cnd_lab/
│       ├── __init__.py
│       ├── __main__.py
│       ├── models.py
│       ├── parsers.py
│       └── tailer.py
└── docs/
    └── reports/
```

## 開發原則

- 每次只增加一小段功能，先看懂再繼續。
- 第一階段先使用 Python 標準函式庫，減少安裝負擔。
- 程式以一般使用者權限執行；只授予讀取日誌所需的權限，不要用 root 執行整個程式。
- 先記錄與告警；封鎖 IP 等會影響系統的動作，必須經過明確確認。
- 演練只對隔離環境中自己控制的目標進行，並記錄測試時間與結果。

## 第一階段預計使用方式

完成後，在 Ubuntu VM 以專案目錄執行：

```bash
python3 -m cnd_lab --auth-log /var/log/auth.log --nginx-log /var/log/nginx/access.log
```

程式會從啟動後新增的日誌行開始讀取，將成功解析的事件逐行輸出為 JSON。若 Ubuntu 日誌檔案無法讀取，請依 README 後續說明，為執行帳號設定最小必要的讀取權限。
