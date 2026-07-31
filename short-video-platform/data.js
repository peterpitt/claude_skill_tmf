/* ============================================================
 *  一站式短影音變現平台 — 核心資料定義
 *  workflow stages / AI 工具箱 / prompt 範本 / 種子專案
 * ============================================================ */

/* ---- 製作流水線階段（對應圖中工具的實際分工） ---- */
const STAGES = [
  {
    id: "idea",
    name: "選題靈感",
    icon: "💡",
    desc: "找出高流量、易變現的題目與鉤子",
    tools: ["chatgpt", "gemini", "notebooklm"],
  },
  {
    id: "script",
    name: "腳本撰寫",
    icon: "✍️",
    desc: "寫出 30–60 秒的口播腳本與分鏡",
    tools: ["chatgpt", "gemini"],
  },
  {
    id: "voice",
    name: "AI 配音",
    icon: "🎙️",
    desc: "用 AI 生成自然人聲旁白",
    tools: ["elevenlabs"],
  },
  {
    id: "video",
    name: "影片生成",
    icon: "🎬",
    desc: "文字/圖片轉影片、B-roll 素材",
    tools: ["hailuo"],
  },
  {
    id: "avatar",
    name: "數位人口播",
    icon: "🧑‍💼",
    desc: "AI 分身出鏡，免真人上鏡",
    tools: ["heygen"],
  },
  {
    id: "design",
    name: "封面設計",
    icon: "🎨",
    desc: "縮圖、字卡、排版與品牌視覺",
    tools: ["canva"],
  },
  {
    id: "publish",
    name: "發布變現",
    icon: "🚀",
    desc: "多平台分發、自動化與收益追蹤",
    tools: ["coze", "manus"],
  },
];

/* ---- AI 工具箱（價格 = 圖中月費 美金） ---- */
const TOOLS = {
  chatgpt: {
    name: "ChatGPT",
    price: 20,
    role: "選題 / 腳本 / 文案",
    color: "#10a37f",
    url: "https://chat.openai.com",
    note: "腳本、標題、Hook、留言回覆的主力大腦",
  },
  coze: {
    name: "coze",
    price: 39,
    role: "工作流自動化 / Bot",
    color: "#4b6ef5",
    url: "https://www.coze.com",
    note: "把整條流程串成自動化 Agent 與排程",
  },
  hailuo: {
    name: "Hailuo 海螺",
    price: 199.99,
    role: "AI 影片生成",
    color: "#c33bb0",
    url: "https://hailuoai.video",
    note: "文字/圖片生影片，成本最高、產出最關鍵",
  },
  elevenlabs: {
    name: "ElevenLabs",
    price: 22,
    role: "AI 配音 / 語音克隆",
    color: "#e2e2e2",
    url: "https://elevenlabs.io",
    note: "自然人聲旁白、可克隆自己的聲音",
  },
  canva: {
    name: "Canva",
    price: 19.9,
    role: "封面 / 字卡設計",
    color: "#7d2ae8",
    url: "https://www.canva.com",
    note: "縮圖、片頭、品牌視覺一站搞定",
  },
  gemini: {
    name: "Gemini",
    price: 19.9,
    role: "研究 / 多模態",
    color: "#4285f4",
    url: "https://gemini.google.com",
    note: "長文研究、圖片理解、跨模態備援",
  },
  manus: {
    name: "manus",
    price: 20,
    role: "自動化 Agent",
    color: "#d97706",
    url: "https://manus.im",
    note: "自動蒐集資料、跑重複性任務",
  },
  notebooklm: {
    name: "NotebookLM",
    price: 19.9,
    role: "資料研究 / 摘要",
    color: "#1a73e8",
    url: "https://notebooklm.google.com",
    note: "餵資料源、萃取重點與洞見做選題",
  },
  heygen: {
    name: "HeyGen",
    price: 29,
    role: "數位人 / 口播分身",
    color: "#0f9d58",
    url: "https://www.heygen.com",
    note: "AI 分身出鏡口播，免真人拍攝",
  },
};

/* ---- 各階段的 Prompt 範本（可一鍵複製貼進對應工具） ---- */
const PROMPTS = {
  idea: {
    tool: "chatgpt",
    title: "選題靈感產生器",
    template: `你是短影音爆款選題專家。主題領域：「{topic}」，目標平台：{platform}。
請給我 10 個「3 秒內抓住注意力」的選題，每個包含：
1. 影片標題（含情緒鉤子）
2. 開場第一句話（Hook）
3. 為什麼會爆（受眾痛點）
4. 變現角度（帶貨 / 導流 / 廣告分潤）
用表格輸出，繁體中文。`,
  },
  script: {
    tool: "chatgpt",
    title: "口播腳本產生器",
    template: `幫我寫一支 {seconds} 秒的短影音口播腳本，主題：「{topic}」。
要求：
- 開場 3 秒必須有強 Hook
- 中間 3 個資訊點，口語、短句
- 結尾 CTA（引導追蹤/留言/購買）
輸出格式：逐句分鏡（畫面 | 旁白 | 秒數），繁體中文。`,
  },
  voice: {
    tool: "elevenlabs",
    title: "配音設定建議",
    template: `把下方腳本貼進 ElevenLabs：
- 語音：選擇符合「{topic}」調性的聲線（活潑/專業/療癒）
- Stability 40 / Similarity 75，語速依情緒微調
- 匯出 mp3，命名：{topic}_vo.mp3

【腳本旁白貼這裡】`,
  },
  video: {
    tool: "hailuo",
    title: "影片生成提示詞",
    template: `用 Hailuo 生成分鏡影片，主題：「{topic}」。
每個鏡頭給一段英文 prompt（畫面主體 + 鏡頭運動 + 光線氛圍 + 風格），
比例 9:16，時長依分鏡表。範例：
"A young creator talking to camera, cinematic lighting, slow zoom in, vertical 9:16, vibrant"`,
  },
  avatar: {
    tool: "heygen",
    title: "數位人口播設定",
    template: `在 HeyGen 建立分身影片：
- Avatar：選擇/上傳你的數位分身
- Voice：貼上 ElevenLabs 匯出的音檔或用內建語音
- Script：貼入「{topic}」腳本
- 輸出 9:16，加上自動字幕`,
  },
  design: {
    tool: "canva",
    title: "封面/字卡設計指引",
    template: `在 Canva 做「{topic}」的短影音封面：
- 尺寸 1080x1920（9:16）
- 大標：{topic} 的爆點關鍵字（≤8 字）
- 高對比配色、人臉/表情特寫
- 建立品牌範本，之後每支沿用`,
  },
  publish: {
    tool: "coze",
    title: "發布與自動化",
    template: `用 coze 建立發布工作流：
1. 上傳成品到 YouTube Shorts / TikTok / IG Reels / 抖音
2. 依平台自動改寫標題與 hashtag（可接 ChatGPT 節點）
3. 排程最佳發布時段
4. 回收數據（觀看/互動/收益）寫回本平台變現追蹤`,
  },
};

/* ---- 種子專案（首次開啟的示範資料） ---- */
const SEED_PROJECTS = [
  {
    id: "p1",
    title: "3 個被低估的 AI 賺錢副業",
    topic: "AI 副業",
    platform: "YouTube Shorts",
    stage: "publish",
    revenue: 180,
    createdAt: Date.now() - 86400000 * 6,
  },
  {
    id: "p2",
    title: "月薪 3 萬如何存到第一桶金",
    topic: "理財",
    platform: "抖音",
    stage: "video",
    revenue: 0,
    createdAt: Date.now() - 86400000 * 3,
  },
  {
    id: "p3",
    title: "這 5 個 App 讓你效率翻倍",
    topic: "生產力工具",
    platform: "IG Reels",
    stage: "script",
    revenue: 0,
    createdAt: Date.now() - 86400000 * 1,
  },
];
