/*
 * 30 天 Google 面試英語衝刺課程資料
 * 每一天結構：
 *   day, week, titleZh, titleEn, goalZh
 *   vocab:   [{ en, zh, ipa, ex }]              重點字彙 + 例句
 *   patterns:[{ en, zh }]                        句型 / 常用句
 *   dialogue:[{ role, en, zh }]                  情境對話（可朗讀 / 跟讀）
 *   interview:[{ q, tip, sample }]               面試題 + 回答技巧 + 範例
 *   task: string                                 今日挑戰任務
 */
const CURRICULUM = [
  // ===================== WEEK 1：打底 — 開口說、自我介紹 =====================
  {
    day: 1, week: 1,
    titleZh: "破冰：讓嘴巴先動起來",
    titleEn: "Breaking the Ice",
    goalZh: "克服開口恐懼，學會最實用的問候與回應，今天就開口說出第一句英文。",
    vocab: [
      { en: "How's it going?", zh: "最近如何？（口語問候）", ipa: "/haʊz ɪt ˈɡoʊɪŋ/", ex: "Hey, how's it going today?" },
      { en: "I appreciate it", zh: "我很感激 / 謝謝你", ipa: "/aɪ əˈpriʃieɪt ɪt/", ex: "Thanks for your help, I really appreciate it." },
      { en: "No worries", zh: "沒關係 / 不用客氣", ipa: "/noʊ ˈwɜːriz/", ex: "No worries, take your time." },
      { en: "Sounds good", zh: "聽起來不錯 / 好的", ipa: "/saʊndz ɡʊd/", ex: "Sounds good, let's do that." },
      { en: "Got it", zh: "我懂了 / 收到", ipa: "/ˈɡɑːt ɪt/", ex: "Got it, I'll take care of it." },
    ],
    patterns: [
      { en: "Nice to meet you. I'm ___.", zh: "很高興認識你，我是 ___。" },
      { en: "Could you say that again, please?", zh: "可以請你再說一次嗎？" },
      { en: "Let me make sure I understand.", zh: "讓我確認一下我理解對不對。" },
    ],
    dialogue: [
      { role: "A", en: "Hi, how's it going?", zh: "嗨，最近如何？" },
      { role: "B", en: "Pretty good, thanks! How about you?", zh: "還不錯，謝謝！你呢？" },
      { role: "A", en: "Can't complain. Ready for the interview?", zh: "還行。準備好面試了嗎？" },
      { role: "B", en: "A little nervous, but excited. Let's do it.", zh: "有點緊張，但很期待。開始吧。" },
    ],
    interview: [
      { q: "How are you today?", tip: "面試開場最常見的暖場問題，回答要簡短、正向，再把球丟回去。", sample: "I'm doing great, thank you. I'm really excited to be here. How are you?" },
    ],
    task: "對著鏡子或手機，大聲說出今天的 5 個字彙各 3 次，並用語音辨識練習「Nice to meet you, I'm ___」。",
  },
  {
    day: 2, week: 1,
    titleZh: "自我介紹骨架（30 秒版）",
    titleEn: "Your 30-Second Pitch",
    goalZh: "建立一段可重複使用的自我介紹，涵蓋『你是誰 + 你會什麼 + 你想要什麼』。",
    vocab: [
      { en: "background", zh: "背景、經歷", ipa: "/ˈbækɡraʊnd/", ex: "I have a background in software engineering." },
      { en: "specialize in", zh: "專精於", ipa: "/ˈspeʃəlaɪz ɪn/", ex: "I specialize in backend development." },
      { en: "passionate about", zh: "熱衷於", ipa: "/ˈpæʃənət əˈbaʊt/", ex: "I'm passionate about building great products." },
      { en: "currently", zh: "目前", ipa: "/ˈkɜːrəntli/", ex: "I'm currently working as a developer." },
      { en: "looking for", zh: "尋找、想要", ipa: "/ˈlʊkɪŋ fɔːr/", ex: "I'm looking for a role where I can grow." },
    ],
    patterns: [
      { en: "I'm a ___ with ___ years of experience in ___.", zh: "我是一位 ___，在 ___ 領域有 ___ 年經驗。" },
      { en: "I specialize in ___, and I'm passionate about ___.", zh: "我專精於 ___，並且熱衷於 ___。" },
      { en: "I'm looking for a role where I can ___.", zh: "我在尋找一個能讓我 ___ 的職位。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Tell me a little about yourself.", zh: "簡單介紹一下你自己。" },
      { role: "You", en: "Sure! I'm a software developer with three years of experience. I specialize in web applications, and I'm passionate about solving real problems for users. I'm looking for a role where I can grow and work on large-scale systems.", zh: "好的！我是一位有三年經驗的軟體開發者。我專精於網頁應用，熱衷於為使用者解決真實問題。我在尋找一個能讓我成長、參與大型系統的職位。" },
    ],
    interview: [
      { q: "Tell me about yourself.", tip: "用『現在 → 過去 → 未來』三段式：目前做什麼、過去累積了什麼、為何想要這個職位。控制在 60 秒內。", sample: "I'm currently a developer focused on backend systems. Over the past few years, I've built APIs that serve millions of requests. Now I'm looking to join a team like Google where I can work on problems at a much larger scale." },
    ],
    task: "寫下並錄音你自己的 30 秒自我介紹，用語音辨識檢查每個字是否清楚。",
  },
  {
    day: 3, week: 1,
    titleZh: "數字、時間與拼字（口說地雷區）",
    titleEn: "Numbers, Dates & Spelling",
    goalZh: "面試常需講電話、Email、年份、數量——把最容易卡住的數字時間練到反射。",
    vocab: [
      { en: "a couple of", zh: "幾個、兩三個", ipa: "/ə ˈkʌpəl əv/", ex: "I worked there for a couple of years." },
      { en: "roughly", zh: "大約", ipa: "/ˈrʌfli/", ex: "Roughly ten thousand users." },
      { en: "quarter", zh: "季 / 四分之一", ipa: "/ˈkwɔːrtər/", ex: "We shipped it last quarter." },
      { en: "double", zh: "兩倍 / 重複的（唸字母時）", ipa: "/ˈdʌbəl/", ex: "My email has a double L." },
      { en: "per", zh: "每", ipa: "/pɜːr/", ex: "About five deploys per week." },
    ],
    patterns: [
      { en: "It's spelled ___.", zh: "它的拼法是 ___。" },
      { en: "My number is ___, that's ___.", zh: "我的號碼是 ___，也就是 ___。" },
      { en: "We grew by around ___ percent.", zh: "我們成長了大約 ___ 個百分比。" },
    ],
    dialogue: [
      { role: "A", en: "Could you spell your last name for me?", zh: "可以幫我拼一下你的姓嗎？" },
      { role: "B", en: "Sure, it's L-I-N, Lin.", zh: "好的，是 L-I-N，Lin。" },
      { role: "A", en: "And how many people were on your team?", zh: "你的團隊有幾個人？" },
      { role: "B", en: "Roughly eight, including two designers.", zh: "大約八個，包含兩位設計師。" },
    ],
    interview: [
      { q: "How large was the impact of your project?", tip: "用具體數字讓回答有說服力：使用者數、成長百分比、節省的時間。", sample: "The feature reached roughly fifty thousand users and cut load time by about forty percent." },
    ],
    task: "大聲唸出你的手機號碼、Email、生日年份各 3 次；再唸出 3 個含百分比的句子。",
  },
  {
    day: 4, week: 1,
    titleZh: "描述你的工作與日常",
    titleEn: "Describing What You Do",
    goalZh: "學會用現在式流暢說出你每天的工作內容與職責。",
    vocab: [
      { en: "responsible for", zh: "負責", ipa: "/rɪˈspɑːnsəbəl fɔːr/", ex: "I'm responsible for the payment module." },
      { en: "in charge of", zh: "主管、掌管", ipa: "/ɪn tʃɑːrdʒ əv/", ex: "I'm in charge of the release process." },
      { en: "collaborate with", zh: "與…合作", ipa: "/kəˈlæbəreɪt wɪð/", ex: "I collaborate with designers daily." },
      { en: "on a daily basis", zh: "每天、日常地", ipa: "/ɑːn ə ˈdeɪli ˈbeɪsɪs/", ex: "I review code on a daily basis." },
      { en: "stakeholder", zh: "利害關係人 / 專案相關方", ipa: "/ˈsteɪkhoʊldər/", ex: "I keep stakeholders updated." },
    ],
    patterns: [
      { en: "In my current role, I ___.", zh: "在我目前的職位，我 ___。" },
      { en: "On a typical day, I ___.", zh: "一般的一天，我會 ___。" },
      { en: "I work closely with ___ to ___.", zh: "我和 ___ 密切合作，以 ___。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "What does a typical day look like for you?", zh: "你一般的一天是什麼樣子？" },
      { role: "You", en: "On a typical day, I review pull requests in the morning, then work on new features. I collaborate with designers and product managers to make sure we're building the right thing.", zh: "一般的一天，我早上會審查程式碼，然後開發新功能。我和設計師、產品經理密切合作，確保我們做對的東西。" },
    ],
    interview: [
      { q: "What are your main responsibilities?", tip: "先講最重要的一兩項職責，再補充你如何與人協作。", sample: "I'm mainly responsible for our backend APIs. On top of that, I collaborate with the front-end team and keep our stakeholders updated on progress." },
    ],
    task: "用『On a typical day, I ___』說出 5 句你真實的工作內容。",
  },
  {
    day: 5, week: 1,
    titleZh: "聊你的過去經歷（過去式）",
    titleEn: "Talking About Your Past",
    goalZh: "掌握過去式動詞，能自然講述曾經做過的專案與成就。",
    vocab: [
      { en: "led", zh: "帶領（lead 過去式）", ipa: "/lɛd/", ex: "I led a team of four." },
      { en: "built", zh: "建造（build 過去式）", ipa: "/bɪlt/", ex: "I built the notification system." },
      { en: "improved", zh: "改善", ipa: "/ɪmˈpruːvd/", ex: "I improved performance significantly." },
      { en: "launched", zh: "推出、上線", ipa: "/lɔːntʃt/", ex: "We launched the app in June." },
      { en: "achieved", zh: "達成", ipa: "/əˈtʃiːvd/", ex: "We achieved our goal ahead of schedule." },
    ],
    patterns: [
      { en: "In my previous role, I ___.", zh: "在我之前的職位，我 ___。" },
      { en: "I was responsible for ___ing.", zh: "我當時負責 ___。" },
      { en: "As a result, we ___.", zh: "結果，我們 ___。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Tell me about a project you're proud of.", zh: "說說一個你引以為傲的專案。" },
      { role: "You", en: "In my previous role, I led a small team to rebuild our search feature. We improved response time by half, and as a result, user engagement went up.", zh: "在我之前的職位，我帶領一個小團隊重建搜尋功能。我們把回應時間縮短一半，結果使用者互動也上升了。" },
    ],
    interview: [
      { q: "What's an accomplishment you're proud of?", tip: "用『情境 → 我做了什麼 → 成果』，結果要有可衡量的數字。", sample: "I'm proud of a project where I redesigned our checkout flow. I built a simpler two-step process, and we increased conversions by about fifteen percent." },
    ],
    task: "列出你 3 個過去的成就，各用『In my previous role, I ___. As a result, we ___』講一遍並錄音。",
  },
  {
    day: 6, week: 1,
    titleZh: "談你的未來與動機（為什麼是 Google）",
    titleEn: "Your Goals & Motivation",
    goalZh: "能清楚說出職涯目標，以及為什麼想加入這家公司。",
    vocab: [
      { en: "grow", zh: "成長", ipa: "/ɡroʊ/", ex: "I want to grow as an engineer." },
      { en: "impact", zh: "影響力", ipa: "/ˈɪmpækt/", ex: "I want to make a real impact." },
      { en: "scale", zh: "規模 / 擴展", ipa: "/skeɪl/", ex: "I'm drawn to problems at scale." },
      { en: "mission", zh: "使命", ipa: "/ˈmɪʃən/", ex: "I believe in the company's mission." },
      { en: "challenge", zh: "挑戰", ipa: "/ˈtʃælɪndʒ/", ex: "I'm looking for a new challenge." },
    ],
    patterns: [
      { en: "In the next few years, I'd like to ___.", zh: "未來幾年，我希望 ___。" },
      { en: "What excites me about this role is ___.", zh: "這個職位讓我興奮的是 ___。" },
      { en: "I admire how your company ___.", zh: "我很欣賞貴公司如何 ___。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Why do you want to work here?", zh: "你為什麼想在這裡工作？" },
      { role: "You", en: "What excites me about this role is the scale of the problems. I admire how your team builds products used by billions of people, and I'd love to grow as an engineer in that kind of environment.", zh: "這個職位讓我興奮的是問題的規模。我很欣賞你們打造出被數十億人使用的產品，我很想在那樣的環境裡成長為更好的工程師。" },
    ],
    interview: [
      { q: "Why Google? / Why do you want this job?", tip: "連結三件事：公司的使命、這個職位的內容、你的個人目標。避免只說『因為它很有名』。", sample: "Two reasons. First, I'm passionate about building products at scale, and few places do that like Google. Second, this role would let me grow toward becoming a systems expert, which is exactly my goal." },
    ],
    task: "寫出你自己版本的『Why this company?』並練習說出，至少提到公司使命 + 你的目標。",
  },
  {
    day: 7, week: 1,
    titleZh: "第一週複習 + 小測驗",
    titleEn: "Week 1 Review",
    goalZh: "整合前六天的自我介紹段落，串成一段流暢的 2 分鐘個人開場。",
    vocab: [
      { en: "to sum up", zh: "總結來說", ipa: "/tə sʌm ʌp/", ex: "To sum up, I'm a builder at heart." },
      { en: "in short", zh: "簡單說", ipa: "/ɪn ʃɔːrt/", ex: "In short, I love solving problems." },
      { en: "that's why", zh: "這就是為什麼", ipa: "/ðæts waɪ/", ex: "That's why I applied here." },
      { en: "on top of that", zh: "除此之外", ipa: "/ɑːn tɑːp əv ðæt/", ex: "On top of that, I mentor juniors." },
      { en: "overall", zh: "整體而言", ipa: "/ˌoʊvərˈɔːl/", ex: "Overall, it was a great experience." },
    ],
    patterns: [
      { en: "To sum up, I'm someone who ___.", zh: "總結來說，我是一個 ___ 的人。" },
      { en: "That's why I'm excited about ___.", zh: "這就是為什麼我對 ___ 感到興奮。" },
      { en: "In short, I bring ___ to the table.", zh: "簡單說，我能帶來 ___。" },
    ],
    dialogue: [
      { role: "You", en: "Hi, I'm Alex. I'm a developer with three years of experience, and I specialize in backend systems. In my previous role, I led a project that cut load time in half. What excites me about this role is the scale. To sum up, I'm a builder who loves solving hard problems, and that's why I'm here.", zh: "嗨，我是 Alex。我是有三年經驗的開發者，專精後端系統。在之前的職位，我帶領一個把載入時間縮短一半的專案。這個職位讓我興奮的是它的規模。總結來說，我是一個熱愛解決難題的實作者，這就是我來到這裡的原因。" },
    ],
    interview: [
      { q: "Walk me through your resume.", tip: "把 Day1–6 串起來：問候 → 現在 → 過去成就 → 未來動機 → 收尾。這是你整場面試的地基。", sample: "Sure. I'm currently a backend developer. Over the past three years, I've led projects and improved performance across our services. Now I'm looking for a bigger challenge, and that's why I'm excited about this role." },
    ],
    task: "把整段 2 分鐘個人開場一口氣錄音，聽回放找出卡住的地方，重錄到順為止。",
  },

  // ===================== WEEK 2：職場英語 + STAR 行為面試 =====================
  {
    day: 8, week: 2,
    titleZh: "STAR 法則：行為面試的萬用架構",
    titleEn: "The STAR Method",
    goalZh: "學會用 Situation–Task–Action–Result 結構回答任何『說一次你…』的題目。",
    vocab: [
      { en: "situation", zh: "情境、背景", ipa: "/ˌsɪtʃuˈeɪʃən/", ex: "Let me set up the situation." },
      { en: "task", zh: "任務、目標", ipa: "/tæsk/", ex: "My task was to fix the bug quickly." },
      { en: "action", zh: "行動", ipa: "/ˈækʃən/", ex: "Here's the action I took." },
      { en: "result", zh: "結果", ipa: "/rɪˈzʌlt/", ex: "The result was a faster system." },
      { en: "outcome", zh: "成果、結局", ipa: "/ˈaʊtkʌm/", ex: "The outcome exceeded our goal." },
    ],
    patterns: [
      { en: "The situation was that ___.", zh: "當時的情況是 ___。" },
      { en: "My task was to ___.", zh: "我的任務是 ___。" },
      { en: "So I ___ (action).", zh: "所以我 ___（行動）。" },
      { en: "As a result, ___.", zh: "結果，___。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Tell me about a time you solved a difficult problem.", zh: "說一次你解決了困難問題的經驗。" },
      { role: "You", en: "The situation was that our app kept crashing under heavy traffic. My task was to find the root cause. So I added logging, traced it to a memory leak, and fixed it. As a result, crashes dropped by ninety percent.", zh: "當時我們的 App 在高流量下一直當機。我的任務是找出根本原因。所以我加了日誌、追到記憶體洩漏並修好。結果當機率下降了九成。" },
    ],
    interview: [
      { q: "Tell me about a challenge you faced.", tip: "嚴格照 S-T-A-R 四段走，每段一兩句就好。結果一定要量化。", sample: "Situation: our deploys often failed. Task: I had to make them reliable. Action: I built an automated test pipeline. Result: deploy failures dropped to almost zero." },
    ],
    task: "用 STAR 架構寫出你自己的『解決困難問題』故事，四段各一句，說出來錄音。",
  },
  {
    day: 9, week: 2,
    titleZh: "團隊合作與衝突處理",
    titleEn: "Teamwork & Conflict",
    goalZh: "能談合作經驗，並成熟地描述如何處理意見不合。",
    vocab: [
      { en: "disagree", zh: "不同意", ipa: "/ˌdɪsəˈɡriː/", ex: "We disagreed on the approach." },
      { en: "compromise", zh: "妥協、折衷", ipa: "/ˈkɑːmprəmaɪz/", ex: "We reached a compromise." },
      { en: "common ground", zh: "共識、共同點", ipa: "/ˈkɑːmən ɡraʊnd/", ex: "We found common ground quickly." },
      { en: "perspective", zh: "觀點", ipa: "/pərˈspɛktɪv/", ex: "I tried to see his perspective." },
      { en: "align", zh: "取得一致", ipa: "/əˈlaɪn/", ex: "We aligned on the goal." },
    ],
    patterns: [
      { en: "We had different opinions on ___.", zh: "我們對 ___ 有不同意見。" },
      { en: "I tried to understand their perspective.", zh: "我試著理解他們的觀點。" },
      { en: "In the end, we found common ground.", zh: "最後，我們找到了共識。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Tell me about a conflict with a coworker.", zh: "說一次你和同事的衝突。" },
      { role: "You", en: "A teammate and I disagreed on which database to use. Instead of pushing my view, I tried to understand his perspective. We listed the trade-offs together and found common ground. In the end, we picked the option that fit the team best.", zh: "我和一位隊友對用哪種資料庫意見不合。我沒有硬推自己的想法，而是試著理解他的觀點。我們一起列出取捨，找到共識。最後選了最適合團隊的方案。" },
    ],
    interview: [
      { q: "How do you handle disagreement on a team?", tip: "重點是『成熟、對事不對人』：先傾聽 → 找資料/取捨 → 一起決定。不要說你總是對。", sample: "I focus on the problem, not on winning. I listen first, put the trade-offs on the table, and let the data guide us. Usually we align once everyone sees the full picture." },
    ],
    task: "回想一次真實的意見不合，用 STAR 說一遍，重點放在你如何『傾聽 + 找共識』。",
  },
  {
    day: 10, week: 2,
    titleZh: "談失敗與從中學習",
    titleEn: "Failure & Growth",
    goalZh: "能坦然談失敗，並展現你從中學到什麼——面試官最看重的成長心態。",
    vocab: [
      { en: "mistake", zh: "錯誤", ipa: "/mɪˈsteɪk/", ex: "I made a mistake early on." },
      { en: "take ownership", zh: "承擔責任", ipa: "/teɪk ˈoʊnərʃɪp/", ex: "I took ownership of the issue." },
      { en: "lesson", zh: "教訓、學到的事", ipa: "/ˈlɛsən/", ex: "The lesson was to test more." },
      { en: "moving forward", zh: "往後、今後", ipa: "/ˈmuːvɪŋ ˈfɔːrwərd/", ex: "Moving forward, I double-check." },
      { en: "grow from", zh: "從…成長", ipa: "/ɡroʊ frʌm/", ex: "I grew a lot from that." },
    ],
    patterns: [
      { en: "I made the mistake of ___.", zh: "我犯了 ___ 的錯。" },
      { en: "What I learned was ___.", zh: "我學到的是 ___。" },
      { en: "Moving forward, I now ___.", zh: "從那以後，我現在會 ___。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Tell me about a time you failed.", zh: "說一次你失敗的經驗。" },
      { role: "You", en: "Early in my career, I pushed code without enough testing and it broke production. I took ownership, fixed it fast, and told my manager. What I learned was the value of automated tests. Moving forward, I never skip them.", zh: "我職涯早期曾在測試不足的情況下上線程式，結果搞壞了正式環境。我承擔責任、快速修復並主動告知主管。我學到自動化測試的重要。從那以後我再也不會省略測試。" },
    ],
    interview: [
      { q: "Describe a time you failed and what you learned.", tip: "選一個真實但不致命的失敗；重點放在『我承擔 + 我改進』，用一半以上時間講學到什麼。", sample: "I once underestimated a deadline and missed it. I owned up to it, replanned with my team, and delivered a week later. Since then, I always add buffer time and communicate risks early." },
    ],
    task: "選一個真實失敗，用 STAR 說出來，確保『學到什麼 + 現在怎麼做』佔一半篇幅。",
  },
  {
    day: 11, week: 2,
    titleZh: "領導力與主動性",
    titleEn: "Leadership & Initiative",
    goalZh: "即使不是主管，也能展現你如何帶頭、主動解決問題。",
    vocab: [
      { en: "take the lead", zh: "帶頭、主導", ipa: "/teɪk ðə liːd/", ex: "I took the lead on the migration." },
      { en: "step up", zh: "挺身而出", ipa: "/stɛp ʌp/", ex: "I stepped up when no one else would." },
      { en: "initiative", zh: "主動性、發起", ipa: "/ɪˈnɪʃətɪv/", ex: "I took the initiative to fix it." },
      { en: "motivate", zh: "激勵", ipa: "/ˈmoʊtɪveɪt/", ex: "I motivated the team to keep going." },
      { en: "mentor", zh: "指導、當導師", ipa: "/ˈmɛntɔːr/", ex: "I mentor two junior developers." },
    ],
    patterns: [
      { en: "I took the initiative to ___.", zh: "我主動 ___。" },
      { en: "Even though it wasn't my job, I ___.", zh: "雖然那不是我的職責，我還是 ___。" },
      { en: "I helped the team by ___.", zh: "我透過 ___ 幫助團隊。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Give me an example of leadership.", zh: "舉一個領導的例子。" },
      { role: "You", en: "Our onboarding docs were a mess, and new hires struggled. Even though it wasn't my job, I took the initiative to rewrite them. I also mentored two new engineers. As a result, onboarding time dropped from two weeks to a few days.", zh: "我們的新人文件很亂，新同事很吃力。雖然那不是我的職責，我還是主動重寫。我也指導了兩位新工程師。結果新人上手時間從兩週縮短到幾天。" },
    ],
    interview: [
      { q: "Tell me about a time you showed leadership.", tip: "領導 ≠ 有頭銜。展現你『看到問題就主動扛起來』並帶動他人。", sample: "I noticed our team kept repeating the same bug, so I took the initiative to build a shared checklist. I walked everyone through it, and those bugs basically disappeared." },
    ],
    task: "找一個你『主動扛起某件事』的例子，用 STAR 說出來，強調 initiative 與對團隊的幫助。",
  },
  {
    day: 12, week: 2,
    titleZh: "會議英語：表達意見、同意、反對",
    titleEn: "Meeting English",
    goalZh: "在討論中能禮貌地表達看法、附和、委婉反對與提問。",
    vocab: [
      { en: "I see your point", zh: "我懂你的意思", ipa: "/aɪ siː jɔːr pɔɪnt/", ex: "I see your point, but..." },
      { en: "That makes sense", zh: "這說得通", ipa: "/ðæt meɪks sɛns/", ex: "That makes sense to me." },
      { en: "I'd push back on", zh: "我想對…提出異議", ipa: "/aɪd pʊʃ bæk ɑːn/", ex: "I'd push back on that a bit." },
      { en: "to build on that", zh: "延續那個想法", ipa: "/tə bɪld ɑːn ðæt/", ex: "To build on that, we could..." },
      { en: "circle back", zh: "稍後再回來討論", ipa: "/ˈsɜːrkəl bæk/", ex: "Let's circle back to this later." },
    ],
    patterns: [
      { en: "I see your point, but have we considered ___?", zh: "我懂你的意思，但我們有考慮 ___ 嗎？" },
      { en: "To build on what you said, ___.", zh: "延續你剛說的，___。" },
      { en: "Can I add something here?", zh: "我可以補充一點嗎？" },
    ],
    dialogue: [
      { role: "A", en: "I think we should launch next week.", zh: "我覺得我們下週應該上線。" },
      { role: "B", en: "I see your point, but I'd push back a little. Have we finished testing?", zh: "我懂你的意思，但我想稍微提出異議。我們測試完成了嗎？" },
      { role: "A", en: "Good point. Let's circle back after QA.", zh: "說得好。等 QA 之後我們再回來討論。" },
    ],
    interview: [
      { q: "How do you give feedback to a teammate?", tip: "展現你溝通得體：先肯定 → 具體建議 → 保持合作語氣。", sample: "I start with something positive, then give specific, actionable feedback. I frame it as 'we' not 'you'—like 'what if we tried this?'—so it feels collaborative." },
    ],
    task: "練習在模擬會議句子中，各說一次『同意 / 委婉反對 / 補充 / 提問』的句型。",
  },
  {
    day: 13, week: 2,
    titleZh: "Email 與非同步溝通口語化",
    titleEn: "Async & Written Communication",
    goalZh: "把書面溝通用口語講清楚，也能在面試中描述你如何遠端協作。",
    vocab: [
      { en: "follow up", zh: "追蹤、後續跟進", ipa: "/ˈfɑːloʊ ʌp/", ex: "I'll follow up with an email." },
      { en: "loop in", zh: "把某人拉進來（訊息鏈）", ipa: "/luːp ɪn/", ex: "Let me loop in the design team." },
      { en: "keep posted", zh: "隨時更新消息", ipa: "/kiːp ˈpoʊstɪd/", ex: "I'll keep you posted." },
      { en: "heads-up", zh: "事先提醒", ipa: "/ˈhɛdz ʌp/", ex: "Just a heads-up: the API changed." },
      { en: "clarify", zh: "釐清", ipa: "/ˈklærɪfaɪ/", ex: "Let me clarify what I meant." },
    ],
    patterns: [
      { en: "Just a quick heads-up: ___.", zh: "先簡單提醒一下：___。" },
      { en: "I'll follow up with ___.", zh: "我會用 ___ 跟進。" },
      { en: "Let me loop in ___.", zh: "我把 ___ 拉進來一起討論。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "How do you keep a remote team aligned?", zh: "你如何讓遠端團隊步調一致？" },
      { role: "You", en: "I over-communicate in writing. I send a quick heads-up before big changes, keep everyone posted with short updates, and loop in the right people early so nothing gets missed.", zh: "我在書面上盡量多溝通。重大變動前先簡短提醒，用短更新讓大家掌握進度，並提早把對的人拉進來，這樣就不會漏掉東西。" },
    ],
    interview: [
      { q: "How do you communicate in a distributed team?", tip: "強調『主動、清楚、書面留痕』——這正是 Google 這類大公司重視的。", sample: "I default to writing things down so there's a record. I keep updates short, flag risks early, and always follow up to close the loop." },
    ],
    task: "用口語說出你如何遠端協作，至少用到 follow up、heads-up、keep posted 三個詞。",
  },
  {
    day: 14, week: 2,
    titleZh: "第二週複習：STAR 故事庫",
    titleEn: "Week 2 Review — Story Bank",
    goalZh: "建立你的『STAR 故事庫』：一次面試通常會用到 5–6 個故事，先備好。",
    vocab: [
      { en: "for instance", zh: "舉例來說", ipa: "/fɔːr ˈɪnstəns/", ex: "For instance, last year..." },
      { en: "specifically", zh: "具體來說", ipa: "/spəˈsɪfɪkli/", ex: "Specifically, I did three things." },
      { en: "the key was", zh: "關鍵在於", ipa: "/ðə kiː wʌz/", ex: "The key was to stay calm." },
      { en: "looking back", zh: "回頭看", ipa: "/ˈlʊkɪŋ bæk/", ex: "Looking back, I'd do it again." },
      { en: "in hindsight", zh: "事後看來", ipa: "/ɪn ˈhaɪndsaɪt/", ex: "In hindsight, it was the right call." },
    ],
    patterns: [
      { en: "One example that comes to mind is ___.", zh: "我想到的一個例子是 ___。" },
      { en: "The key was ___.", zh: "關鍵在於 ___。" },
      { en: "Looking back, I'm glad I ___.", zh: "回頭看，我很慶幸我 ___。" },
    ],
    dialogue: [
      { role: "You", en: "One example that comes to mind is when our launch was at risk. The key was staying calm and breaking the work into small pieces. Looking back, I'm glad I spoke up early instead of panicking.", zh: "我想到的一個例子是我們的上線一度岌岌可危。關鍵在於保持冷靜，把工作拆成小塊。回頭看，我很慶幸我提早發聲而不是慌張。" },
    ],
    interview: [
      { q: "Prepare 6 STAR stories.", tip: "準備 6 個可套用的故事：解難、衝突、失敗、領導、期限壓力、學新技術。每個練到 90 秒內。", sample: "(用你自己的 6 個真實故事，各寫成 S-T-A-R 四句，反覆錄音。)" },
    ],
    task: "把 6 個 STAR 故事各寫成四句並全部錄音，這是你面試前最重要的資產。",
  },

  // ===================== WEEK 3：Google 技術/情境面試 =====================
  {
    day: 15, week: 3,
    titleZh: "說清楚你的思路（Think Aloud）",
    titleEn: "Thinking Out Loud",
    goalZh: "技術面試最重要的能力：邊想邊講，讓面試官跟上你的邏輯。",
    vocab: [
      { en: "let me think", zh: "讓我想一下", ipa: "/lɛt miː θɪŋk/", ex: "Let me think about this for a sec." },
      { en: "my first thought", zh: "我的第一個念頭", ipa: "/maɪ fɜːrst θɔːt/", ex: "My first thought is a hash map." },
      { en: "the trade-off", zh: "取捨", ipa: "/ðə ˈtreɪdˌɔːf/", ex: "The trade-off is memory vs speed." },
      { en: "edge case", zh: "邊界情況", ipa: "/ɛdʒ keɪs/", ex: "Let's consider the edge cases." },
      { en: "brute force", zh: "暴力解法", ipa: "/bruːt fɔːrs/", ex: "The brute-force way is O(n²)." },
    ],
    patterns: [
      { en: "Let me start by clarifying the problem.", zh: "我先釐清一下這個問題。" },
      { en: "My first thought is to ___, because ___.", zh: "我的第一個想法是 ___，因為 ___。" },
      { en: "The trade-off here is ___ versus ___.", zh: "這裡的取捨是 ___ 對 ___。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "How would you find duplicates in a list?", zh: "你會怎麼在清單裡找出重複值？" },
      { role: "You", en: "Let me start by clarifying — can the list be very large? Okay. My first thought is to use a hash set, because lookups are fast. The trade-off is extra memory versus speed, but for this size, speed matters more.", zh: "我先釐清——清單會很大嗎？好。我的第一個想法是用雜湊集合，因為查找很快。取捨是額外記憶體對速度，但以這個規模，速度更重要。" },
    ],
    interview: [
      { q: "Solve this coding problem (verbalize).", tip: "先問澄清問題 → 講暴力解 → 講優化 → 討論取捨與邊界。全程出聲，沉默是大忌。", sample: "First, let me make sure I understand the input. My first thought is the brute-force approach, which is O(n²). But I can optimize with a hash map to get O(n). The trade-off is extra space." },
    ],
    task: "找一題簡單的邏輯題，全程『邊想邊用英文講』錄音，練習不沉默。",
  },
  {
    day: 16, week: 3,
    titleZh: "澄清問題與確認需求",
    titleEn: "Asking Clarifying Questions",
    goalZh: "學會在動手前用英文問對問題——面試官很看重這一點。",
    vocab: [
      { en: "assume", zh: "假設", ipa: "/əˈsuːm/", ex: "Can I assume the input is sorted?" },
      { en: "constraint", zh: "限制條件", ipa: "/kənˈstreɪnt/", ex: "What are the constraints?" },
      { en: "input", zh: "輸入", ipa: "/ˈɪnpʊt/", ex: "What does the input look like?" },
      { en: "expected", zh: "預期的", ipa: "/ɪkˈspɛktɪd/", ex: "What's the expected output?" },
      { en: "requirement", zh: "需求", ipa: "/rɪˈkwaɪrmənt/", ex: "Let me confirm the requirements." },
    ],
    patterns: [
      { en: "Before I start, can I ask a few questions?", zh: "開始前，我可以問幾個問題嗎？" },
      { en: "Can I assume that ___?", zh: "我可以假設 ___ 嗎？" },
      { en: "What's the expected input and output?", zh: "預期的輸入和輸出是什麼？" },
    ],
    dialogue: [
      { role: "You", en: "Before I start, can I ask a few questions? Can I assume the input is always valid? And roughly how large is it? Great — that helps me choose the right approach.", zh: "開始前我可以問幾個問題嗎？我可以假設輸入總是有效的嗎？大概多大？太好了——這有助於我選對方法。" },
      { role: "Interviewer", en: "Yes, assume valid input, up to a million items.", zh: "可以，假設輸入有效，最多一百萬筆。" },
    ],
    interview: [
      { q: "Design a URL shortener.", tip: "系統設計題先問清楚：規模多大？讀多還是寫多？要多快？先問再答，別急著畫圖。", sample: "Before I design, let me clarify a few things: how many URLs per day, is it read-heavy, and do we need custom links? That'll shape the storage and caching decisions." },
    ],
    task: "拿任一題目，先只說出 4 個 clarifying questions，不急著解答。",
  },
  {
    day: 17, week: 3,
    titleZh: "白板/系統設計常用語",
    titleEn: "Whiteboard & System Design",
    goalZh: "掌握描述架構、資料流與元件的高頻詞彙。",
    vocab: [
      { en: "component", zh: "元件", ipa: "/kəmˈpoʊnənt/", ex: "This component handles auth." },
      { en: "database", zh: "資料庫", ipa: "/ˈdeɪtəbeɪs/", ex: "We store it in a database." },
      { en: "cache", zh: "快取", ipa: "/kæʃ/", ex: "We add a cache to speed it up." },
      { en: "load balancer", zh: "負載平衡器", ipa: "/loʊd ˈbælənsər/", ex: "A load balancer spreads traffic." },
      { en: "bottleneck", zh: "瓶頸", ipa: "/ˈbɑːtəlnɛk/", ex: "The database is the bottleneck." },
    ],
    patterns: [
      { en: "At a high level, the system has ___.", zh: "從高層次看，系統有 ___。" },
      { en: "The request flows from ___ to ___.", zh: "請求從 ___ 流向 ___。" },
      { en: "To scale this, we could ___.", zh: "要擴展這個，我們可以 ___。" },
    ],
    dialogue: [
      { role: "You", en: "At a high level, the system has three parts: a load balancer, several servers, and a database. The request flows from the user, through the load balancer, to a server. To scale reads, we could add a cache in front of the database.", zh: "從高層次看，系統有三部分：負載平衡器、多台伺服器、一個資料庫。請求從使用者經過負載平衡器到伺服器。要擴展讀取，我們可以在資料庫前加一層快取。" },
    ],
    interview: [
      { q: "How would you scale a service to millions of users?", tip: "用『高層次 → 資料流 → 瓶頸 → 解法』的順序講，多用 cache / load balancer / bottleneck 等詞。", sample: "At a high level, I'd put a load balancer in front of stateless servers. The database is usually the bottleneck, so I'd add caching and read replicas to scale reads." },
    ],
    task: "用英文口述任一簡單系統（例如聊天 App）的架構，至少用到 5 個今日字彙。",
  },
  {
    day: 18, week: 3,
    titleZh: "當你不會/卡住時怎麼說",
    titleEn: "When You're Stuck",
    goalZh: "卡住是常態——學會優雅地爭取時間、請求提示、保持冷靜。",
    vocab: [
      { en: "give me a moment", zh: "給我一點時間", ipa: "/ɡɪv miː ə ˈmoʊmənt/", ex: "Give me a moment to think." },
      { en: "I'm not sure, but", zh: "我不確定，但是", ipa: "/aɪm nɑːt ʃʊr bʌt/", ex: "I'm not sure, but I'd guess..." },
      { en: "hint", zh: "提示", ipa: "/hɪnt/", ex: "Could you give me a hint?" },
      { en: "on the right track", zh: "方向正確", ipa: "/ɑːn ðə raɪt træk/", ex: "Am I on the right track?" },
      { en: "revisit", zh: "重新檢視", ipa: "/riːˈvɪzɪt/", ex: "Let me revisit my assumption." },
    ],
    patterns: [
      { en: "Give me a moment to think this through.", zh: "給我一點時間好好想。" },
      { en: "I'm not sure yet, but my instinct is ___.", zh: "我還不確定，但直覺是 ___。" },
      { en: "Am I on the right track?", zh: "我的方向對嗎？" },
    ],
    dialogue: [
      { role: "You", en: "Hmm, give me a moment to think this through. I'm not sure yet, but my instinct is to sort the array first. Am I on the right track?", zh: "嗯，給我一點時間想想。我還不確定，但直覺是先把陣列排序。我方向對嗎？" },
      { role: "Interviewer", en: "That's a good start. Keep going.", zh: "起步不錯，繼續。" },
    ],
    interview: [
      { q: "What if you don't know the answer?", tip: "不要慌、不要沉默。出聲說出你正在想什麼，適時問『Am I on the right track?』展現溝通力。", sample: "I'd be honest: 'I'm not certain, but here's how I'd approach finding out.' Then I'd reason out loud and check my direction with the interviewer." },
    ],
    task: "刻意練習『卡住時的 3 句救場句』，錄音直到能自然說出口。",
  },
  {
    day: 19, week: 3,
    titleZh: "反問面試官的好問題",
    titleEn: "Questions to Ask Them",
    goalZh: "面試尾聲『你有問題想問嗎？』——準備能展現你思考深度的好問題。",
    vocab: [
      { en: "day-to-day", zh: "日常的", ipa: "/ˈdeɪ tə ˈdeɪ/", ex: "What's the day-to-day like?" },
      { en: "success", zh: "成功（的標準）", ipa: "/səkˈsɛs/", ex: "How do you measure success?" },
      { en: "challenge", zh: "挑戰", ipa: "/ˈtʃælɪndʒ/", ex: "What's the biggest challenge?" },
      { en: "team culture", zh: "團隊文化", ipa: "/tiːm ˈkʌltʃər/", ex: "How would you describe the team culture?" },
      { en: "onboarding", zh: "新人上手", ipa: "/ˈɑːnbɔːrdɪŋ/", ex: "What does onboarding look like?" },
    ],
    patterns: [
      { en: "What does a typical day look like for this role?", zh: "這個職位一般的一天是什麼樣？" },
      { en: "How do you measure success in the first six months?", zh: "前六個月你們如何衡量是否成功？" },
      { en: "What's the biggest challenge the team is facing?", zh: "團隊目前最大的挑戰是什麼？" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Do you have any questions for me?", zh: "你有什麼問題想問我嗎？" },
      { role: "You", en: "Yes, thank you. How do you measure success in the first six months? And what's the biggest challenge the team is facing right now?", zh: "有的，謝謝。前六個月你們如何衡量成功？還有，團隊目前最大的挑戰是什麼？" },
    ],
    interview: [
      { q: "Do you have any questions for us?", tip: "一定要問！準備 3–4 個好問題，展現你關心角色、團隊與成長，而不是只關心薪水。", sample: "I'd love to know how the team defines success for this role, and what growth looks like here over the next year." },
    ],
    task: "寫下 4 個你要反問面試官的問題並練習說出，涵蓋角色、團隊、成長。",
  },
  {
    day: 20, week: 3,
    titleZh: "聽力與追問：聽不懂怎麼辦",
    titleEn: "Listening & Clarifying",
    goalZh: "當你沒聽懂或需要對方重述時，能自然地要求澄清而不尷尬。",
    vocab: [
      { en: "come again", zh: "再說一次（口語）", ipa: "/kʌm əˈɡɛn/", ex: "Sorry, come again?" },
      { en: "if I understood correctly", zh: "如果我理解正確", ipa: "/ɪf aɪ ˌʌndərˈstʊd kəˈrɛktli/", ex: "If I understood correctly, you want X." },
      { en: "you mean", zh: "你的意思是", ipa: "/juː miːn/", ex: "You mean the second option?" },
      { en: "rephrase", zh: "換個說法", ipa: "/riːˈfreɪz/", ex: "Could you rephrase that?" },
      { en: "in other words", zh: "換句話說", ipa: "/ɪn ˈʌðər wɜːrdz/", ex: "In other words, speed matters most." },
    ],
    patterns: [
      { en: "Sorry, could you repeat that?", zh: "抱歉，可以再說一次嗎？" },
      { en: "Just to make sure I understood — you mean ___?", zh: "確認一下我理解對——你的意思是 ___？" },
      { en: "Could you rephrase the question?", zh: "可以換個方式問嗎？" },
    ],
    dialogue: [
      { role: "Interviewer", en: "How would you optimize the throughput of this pipeline?", zh: "你會如何優化這條管線的吞吐量？" },
      { role: "You", en: "Sorry, could you repeat that? ... Okay, just to make sure I understood — you mean how to process more data per second, right?", zh: "抱歉，可以再說一次嗎？……好，確認一下我理解對——你是指如何每秒處理更多資料，對嗎？" },
    ],
    interview: [
      { q: "(When you mishear a question)", tip: "沒聽懂很正常，重述確認反而顯得專業。千萬別亂猜方向硬答。", sample: "Just to make sure I understood correctly — are you asking about X or Y? I want to answer the right question." },
    ],
    task: "練習『請對方重述 + 用自己的話確認』的完整流程，錄音 5 次。",
  },
  {
    day: 21, week: 3,
    titleZh: "第三週複習：技術溝通模擬",
    titleEn: "Week 3 Review — Technical Mock",
    goalZh: "整合技術面試溝通流程：澄清 → 出聲思考 → 講取捨 → 收尾。",
    vocab: [
      { en: "to recap", zh: "簡短回顧", ipa: "/tə ˈriːkæp/", ex: "To recap, my approach is..." },
      { en: "in summary", zh: "總結", ipa: "/ɪn ˈsʌməri/", ex: "In summary, it's O(n)." },
      { en: "walk through", zh: "逐步講解", ipa: "/wɔːk θruː/", ex: "Let me walk you through it." },
      { en: "verify", zh: "驗證", ipa: "/ˈvɛrɪfaɪ/", ex: "Let me verify with an example." },
      { en: "optimize", zh: "優化", ipa: "/ˈɑːptɪmaɪz/", ex: "We can optimize the loop." },
    ],
    patterns: [
      { en: "Let me walk you through my solution.", zh: "讓我逐步講解我的解法。" },
      { en: "To recap, the approach is ___ with ___ complexity.", zh: "回顧一下，方法是 ___，複雜度為 ___。" },
      { en: "Let me verify with a quick example.", zh: "讓我用一個小例子驗證。" },
    ],
    dialogue: [
      { role: "You", en: "Let me walk you through my solution. First I clarified the input. Then I used a hash map for O(n) time. Let me verify with an example... yes, it works. To recap, the approach is a single pass with linear time and space.", zh: "讓我逐步講解。首先我釐清了輸入。然後用雜湊表達到 O(n)。我用一個例子驗證……對，可行。回顧一下，方法是單次遍歷，時間與空間都是線性。" },
    ],
    interview: [
      { q: "Full technical mock (verbalize end to end).", tip: "完整走一遍：澄清 → 思考 → 解法 → 驗證 → 回顧。全程英文出聲。", sample: "(挑一題你熟的題目，用英文從頭到尾講一遍，控制在 5 分鐘內。)" },
    ],
    task: "選一題技術題，完整用英文走完『澄清→思考→解法→驗證→回顧』並錄音。",
  },

  // ===================== WEEK 4：模擬面試 + 流利度衝刺 =====================
  {
    day: 22, week: 4,
    titleZh: "全套自我介紹 + 開場模擬",
    titleEn: "Full Opening Simulation",
    goalZh: "把前三週整合成一場真實面試開場，從問候到自我介紹一氣呵成。",
    vocab: [
      { en: "thrilled", zh: "非常興奮的", ipa: "/θrɪld/", ex: "I'm thrilled to be here." },
      { en: "walk you through", zh: "帶你了解", ipa: "/wɔːk juː θruː/", ex: "Let me walk you through my background." },
      { en: "highlight", zh: "重點、亮點", ipa: "/ˈhaɪlaɪt/", ex: "A highlight was leading the launch." },
      { en: "transition", zh: "轉換、過渡", ipa: "/trænˈzɪʃən/", ex: "I'm ready for the next transition." },
      { en: "eager", zh: "渴望的", ipa: "/ˈiːɡər/", ex: "I'm eager to contribute." },
    ],
    patterns: [
      { en: "Thanks for having me. I'm thrilled to be here.", zh: "謝謝你們給我機會，我很興奮能來到這裡。" },
      { en: "Let me walk you through my background.", zh: "讓我帶你了解我的背景。" },
      { en: "I'm eager to bring that experience to your team.", zh: "我很渴望把這些經驗帶到你們的團隊。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Thanks for joining. Let's start — tell me about yourself.", zh: "謝謝你來。我們開始吧——介紹一下你自己。" },
      { role: "You", en: "Thanks for having me, I'm thrilled to be here. Let me walk you through my background. I'm a developer with three years of experience in backend systems. A highlight was leading a project that halved our load time. I'm eager to bring that experience to a team working at Google's scale.", zh: "謝謝你們，我很興奮能來。讓我帶你了解我的背景。我是有三年後端經驗的開發者。一個亮點是帶領把載入時間減半的專案。我很渴望把這些經驗帶到像 Google 這種規模的團隊。" },
    ],
    interview: [
      { q: "Full opening: greeting + self-intro.", tip: "把 Day1（問候）+ Day2/7（自我介紹）連起來，練到像肌肉記憶。", sample: "Thanks for having me. I'm thrilled to be here. Let me walk you through my background... (接你的自我介紹)" },
    ],
    task: "從『敲門問候』演到『自我介紹結束』完整錄影或錄音一次，模擬真實開場。",
  },
  {
    day: 23, week: 4,
    titleZh: "模擬：行為面試連環題",
    titleEn: "Mock — Behavioral Round",
    goalZh: "連續回答 3–4 個行為題，訓練在真實壓力下調用 STAR 故事庫。",
    vocab: [
      { en: "off the top of my head", zh: "我一時想到的", ipa: "/ɔːf ðə tɑːp əv maɪ hɛd/", ex: "Off the top of my head, one time..." },
      { en: "to give context", zh: "提供背景", ipa: "/tə ɡɪv ˈkɑːntɛkst/", ex: "To give context, we were understaffed." },
      { en: "under pressure", zh: "在壓力下", ipa: "/ˈʌndər ˈprɛʃər/", ex: "I work well under pressure." },
      { en: "prioritize", zh: "排優先順序", ipa: "/praɪˈɔːrɪtaɪz/", ex: "I had to prioritize tasks fast." },
      { en: "deadline", zh: "截止期限", ipa: "/ˈdɛdlaɪn/", ex: "We had a tight deadline." },
    ],
    patterns: [
      { en: "Off the top of my head, one example is ___.", zh: "我一時想到的一個例子是 ___。" },
      { en: "To give some context, ___.", zh: "先給一點背景，___。" },
      { en: "Under pressure, I focus on ___.", zh: "在壓力下，我專注在 ___。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Tell me about a time you worked under a tight deadline.", zh: "說一次你在緊迫期限下工作的經驗。" },
      { role: "You", en: "To give some context, we had one week to ship a fix. Under pressure, I focused on the highest-impact tasks first, cut scope, and communicated risks daily. We delivered on time.", zh: "先給點背景，我們只有一週要交付修復。壓力下，我先專注在影響最大的任務、縮減範圍、每天回報風險。我們準時交付了。" },
    ],
    interview: [
      { q: "Rapid behavioral round (answer 4 in a row).", tip: "用面試模擬器連抽 4 題行為題，逼自己在 10 秒內選對故事開講。", sample: "(用本 App 的『面試模擬器』隨機練習行為題。)" },
    ],
    task: "用 App 的面試模擬器連續回答 4 題行為題，每題控制在 90 秒。",
  },
  {
    day: 24, week: 4,
    titleZh: "模擬：技術與情境連環題",
    titleEn: "Mock — Technical Round",
    goalZh: "在模擬情境下連答技術/情境題，練習出聲思考的流暢度。",
    vocab: [
      { en: "approach", zh: "方法、途徑", ipa: "/əˈproʊtʃ/", ex: "My approach would be..." },
      { en: "complexity", zh: "複雜度", ipa: "/kəmˈplɛksɪti/", ex: "The time complexity is O(n)." },
      { en: "scalable", zh: "可擴展的", ipa: "/ˈskeɪləbəl/", ex: "We need a scalable design." },
      { en: "trade-off", zh: "取捨", ipa: "/ˈtreɪdˌɔːf/", ex: "Every design has trade-offs." },
      { en: "reliable", zh: "可靠的", ipa: "/rɪˈlaɪəbəl/", ex: "It has to be reliable." },
    ],
    patterns: [
      { en: "My approach would be to ___.", zh: "我的方法會是 ___。" },
      { en: "The trade-off is between ___ and ___.", zh: "取捨是在 ___ 和 ___ 之間。" },
      { en: "To make it scalable, I'd ___.", zh: "為了可擴展，我會 ___。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "How would you design a notification system?", zh: "你會怎麼設計一個通知系統？" },
      { role: "You", en: "My approach would be a queue-based design so it's scalable and reliable. The trade-off is between instant delivery and system load, so I'd batch low-priority notifications. To make it scalable, I'd add more workers as traffic grows.", zh: "我的方法會是以佇列為基礎的設計，讓它可擴展又可靠。取捨是即時送達與系統負載之間，所以低優先的通知我會批次處理。為了可擴展，流量成長時我會增加更多 worker。" },
    ],
    interview: [
      { q: "Rapid technical/situational round.", tip: "重點不是完美解，而是溝通清楚、講取捨、保持出聲。", sample: "(用模擬器抽技術/情境題，每題出聲講方法 + 取捨。)" },
    ],
    task: "用模擬器連答 3 題技術/情境題，每題都要講到 approach 與 trade-off。",
  },
  {
    day: 25, week: 4,
    titleZh: "薪資、時程與收尾對話",
    titleEn: "Closing the Conversation",
    goalZh: "能自然談薪資期望、可到職時間，並禮貌地為面試收尾。",
    vocab: [
      { en: "compensation", zh: "薪酬", ipa: "/ˌkɑːmpənˈseɪʃən/", ex: "Can we talk about compensation?" },
      { en: "flexible", zh: "有彈性的", ipa: "/ˈflɛksəbəl/", ex: "I'm flexible on the details." },
      { en: "notice period", zh: "離職預告期", ipa: "/ˈnoʊtɪs ˈpɪəriəd/", ex: "My notice period is one month." },
      { en: "available", zh: "有空的、可到職的", ipa: "/əˈveɪləbəl/", ex: "I'm available to start in June." },
      { en: "look forward to", zh: "期待", ipa: "/lʊk ˈfɔːrwərd tuː/", ex: "I look forward to hearing from you." },
    ],
    patterns: [
      { en: "Based on my research, I'm looking for a range around ___.", zh: "根據我的研究，我期望的範圍大約在 ___。" },
      { en: "I'm flexible and open to discussing the full package.", zh: "我有彈性，也樂意討論整體條件。" },
      { en: "I look forward to the next steps.", zh: "我期待後續的流程。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "What are your salary expectations?", zh: "你的薪資期望是多少？" },
      { role: "You", en: "Based on my research and experience, I'm looking for a range around the market rate for this role. That said, I'm flexible and open to discussing the full package.", zh: "根據我的研究和經驗，我期望大約在這個職位的市場行情範圍。不過我有彈性，也樂意討論整體條件。" },
    ],
    interview: [
      { q: "What are your salary expectations? / When can you start?", tip: "薪資：給一個做過功課的範圍 + 表達彈性。到職：誠實說明預告期。收尾要表達期待。", sample: "I've done some research, and I'm targeting a competitive range for this role, but I'm flexible. I could start within a month, after my notice period." },
    ],
    task: "練習回答『薪資期望』與『何時可到職』，並用一句話禮貌收尾。",
  },
  {
    day: 26, week: 4,
    titleZh: "流利度衝刺：連接詞與填充語",
    titleEn: "Fluency — Connectors & Fillers",
    goalZh: "用自然的連接詞與『思考填充語』取代中文式停頓，聽起來更流暢。",
    vocab: [
      { en: "actually", zh: "其實", ipa: "/ˈæktʃuəli/", ex: "Actually, that's a good point." },
      { en: "basically", zh: "基本上", ipa: "/ˈbeɪsɪkli/", ex: "Basically, it works like this." },
      { en: "for example", zh: "舉例來說", ipa: "/fɔːr ɪɡˈzæmpəl/", ex: "For example, last month..." },
      { en: "on the other hand", zh: "另一方面", ipa: "/ɑːn ðə ˈʌðər hænd/", ex: "On the other hand, it's slower." },
      { en: "that being said", zh: "話雖如此", ipa: "/ðæt ˈbiːɪŋ sɛd/", ex: "That being said, it's worth it." },
    ],
    patterns: [
      { en: "Basically, what I mean is ___.", zh: "基本上，我的意思是 ___。" },
      { en: "For example, ___.", zh: "舉例來說，___。" },
      { en: "That being said, ___.", zh: "話雖如此，___。" },
    ],
    dialogue: [
      { role: "You", en: "Basically, I love backend work. Actually, my favorite project was a payment system. For example, I optimized it to handle double the traffic. That being said, I'm also open to learning front-end.", zh: "基本上，我熱愛後端工作。其實我最喜歡的專案是一個支付系統。舉例來說，我把它優化到能承受兩倍流量。話雖如此，我也樂意學前端。" },
    ],
    interview: [
      { q: "Speak for 90 seconds without long pauses.", tip: "用英文填充語（well, so, actually, basically）取代『嗯…那個…』的中文停頓，爭取思考時間。", sample: "Well, so, basically my point is... actually, let me give an example..." },
    ],
    task: "選一個話題連續說 90 秒，刻意使用今天的 5 個連接詞，不用中文停頓。",
  },
  {
    day: 27, week: 4,
    titleZh: "發音與語調微調",
    titleEn: "Pronunciation & Intonation",
    goalZh: "修正常見發音地雷（th、r/l、字尾子音）與句子語調，提升清晰度。",
    vocab: [
      { en: "think / thing", zh: "th 發音（咬舌）", ipa: "/θɪŋk/ /θɪŋ/", ex: "I think this is the right thing." },
      { en: "really", zh: "r 與 l 發音", ipa: "/ˈrɪəli/", ex: "I really like this role." },
      { en: "asked", zh: "字尾子音群 -sked", ipa: "/æskt/", ex: "They asked me to lead." },
      { en: "development", zh: "重音在第二音節", ipa: "/dɪˈvɛləpmənt/", ex: "I enjoy software development." },
      { en: "comfortable", zh: "常唸錯的重音字", ipa: "/ˈkʌmftərbəl/", ex: "I'm comfortable with ambiguity." },
    ],
    patterns: [
      { en: "Rising tone for yes/no questions ↗", zh: "是非問句用上揚語調 ↗" },
      { en: "Falling tone for statements ↘", zh: "直述句用下降語調 ↘" },
      { en: "Stress the key word in each sentence.", zh: "每句話重讀關鍵字。" },
    ],
    dialogue: [
      { role: "You", en: "I think the thing they asked about was development speed. I really enjoy that, and I'm comfortable moving fast.", zh: "我想他們問的是開發速度。我真的很喜歡，也能自在地快速推進。" },
    ],
    interview: [
      { q: "Read a passage aloud and self-correct.", tip: "用 App 的朗讀功能聽標準發音，再用語音辨識比對——辨識錯的字通常就是你發音不準的字。", sample: "(用朗讀 + 語音辨識反覆比對 th / r / l / 字尾子音。)" },
    ],
    task: "朗讀今天的對話 5 次，用語音辨識檢查，把辨識失敗的字單獨練 10 次。",
  },
  {
    day: 28, week: 4,
    titleZh: "完整模擬面試 Part 1（前半場）",
    titleEn: "Full Mock Interview — Part 1",
    goalZh: "從問候、自我介紹到 2–3 題行為題，模擬真實面試前半場不中斷。",
    vocab: [
      { en: "to begin with", zh: "首先", ipa: "/tə bɪˈɡɪn wɪð/", ex: "To begin with, thanks for having me." },
      { en: "as I mentioned", zh: "如同我提到的", ipa: "/æz aɪ ˈmɛnʃənd/", ex: "As I mentioned earlier..." },
      { en: "let me elaborate", zh: "讓我詳細說明", ipa: "/lɛt miː ɪˈlæbəreɪt/", ex: "Let me elaborate on that." },
      { en: "to your point", zh: "針對你說的", ipa: "/tə jɔːr pɔɪnt/", ex: "To your point, yes." },
      { en: "does that answer", zh: "這有回答到嗎", ipa: "/dʌz ðæt ˈænsər/", ex: "Does that answer your question?" },
    ],
    patterns: [
      { en: "To begin with, thank you for the opportunity.", zh: "首先，謝謝你們的機會。" },
      { en: "Let me elaborate on that with an example.", zh: "讓我用一個例子詳細說明。" },
      { en: "Does that answer your question?", zh: "這有回答到你的問題嗎？" },
    ],
    dialogue: [
      { role: "Interviewer", en: "Let's begin. Tell me about yourself, then a time you led something.", zh: "開始吧。介紹你自己，然後說一次你帶頭做某事的經驗。" },
      { role: "You", en: "To begin with, thank you for the opportunity. I'm a backend developer with three years of experience. As for leadership — let me elaborate with an example. I led our onboarding revamp and cut ramp-up time in half. Does that answer your question?", zh: "首先，謝謝你們的機會。我是有三年經驗的後端開發者。至於領導——讓我舉例說明。我主導了新人流程改造，把上手時間縮短一半。這有回答到你的問題嗎？" },
    ],
    interview: [
      { q: "Full mock — first half (no stopping).", tip: "用模擬器完整走：問候 → 自我介紹 → 2 題行為題，中途不喊停、不查字典。", sample: "(用『面試模擬器』的完整模式跑前半場。)" },
    ],
    task: "用模擬器不中斷跑完前半場（問候→自介→2 行為題），錄音檢討。",
  },
  {
    day: 29, week: 4,
    titleZh: "完整模擬面試 Part 2（後半場）",
    titleEn: "Full Mock Interview — Part 2",
    goalZh: "接續技術/情境題、反問問題到收尾，完成一整場完整模擬。",
    vocab: [
      { en: "to wrap up", zh: "總結收尾", ipa: "/tə ræp ʌp/", ex: "To wrap up, I'm excited about this." },
      { en: "circle back", zh: "回到（前面提過的）", ipa: "/ˈsɜːrkəl bæk/", ex: "Let me circle back to your question." },
      { en: "on a final note", zh: "最後一點", ipa: "/ɑːn ə ˈfaɪnəl noʊt/", ex: "On a final note, thank you." },
      { en: "it was a pleasure", zh: "很榮幸", ipa: "/ɪt wʌz ə ˈplɛʒər/", ex: "It was a pleasure speaking with you." },
      { en: "reach out", zh: "聯繫", ipa: "/riːtʃ aʊt/", ex: "Feel free to reach out." },
    ],
    patterns: [
      { en: "To wrap up, I'm really excited about this role because ___.", zh: "總結來說，我對這職位很興奮，因為 ___。" },
      { en: "It was a pleasure speaking with you today.", zh: "今天很榮幸與你交談。" },
      { en: "I look forward to the next steps.", zh: "我期待接下來的流程。" },
    ],
    dialogue: [
      { role: "Interviewer", en: "That's all from me. Any questions?", zh: "我這邊問完了。你有問題嗎？" },
      { role: "You", en: "Yes — how do you measure success in the first six months? ... Thank you. To wrap up, I'm really excited about this role because of the scale and the team. It was a pleasure speaking with you, and I look forward to the next steps.", zh: "有的——前六個月你們如何衡量成功？……謝謝。總結來說，我對這職位很興奮，因為它的規模與團隊。今天很榮幸與你交談，我期待後續流程。" },
    ],
    interview: [
      { q: "Full mock — second half + closing.", tip: "接續技術題 → 反問 → 收尾，練到整場 30 分鐘能全程英文不崩。", sample: "(用模擬器完整模式跑後半場並收尾。)" },
    ],
    task: "把 Day28 前半場 + 今天後半場連起來，完整跑一整場 20–30 分鐘模擬面試。",
  },
  {
    day: 30, week: 4,
    titleZh: "驗收日：完整實戰 + 面試當天心法",
    titleEn: "Final Day — Game Day",
    goalZh: "完成最終驗收模擬，複習面試當天的心態與臨場句，準備上場。",
    vocab: [
      { en: "confident", zh: "有自信的", ipa: "/ˈkɑːnfɪdənt/", ex: "I feel confident and prepared." },
      { en: "take a breath", zh: "深呼吸", ipa: "/teɪk ə brɛθ/", ex: "Take a breath before you answer." },
      { en: "be yourself", zh: "做自己", ipa: "/biː jɔːrˈsɛlf/", ex: "Just relax and be yourself." },
      { en: "you've got this", zh: "你做得到", ipa: "/juːv ɡɑːt ðɪs/", ex: "You've prepared well — you've got this." },
      { en: "genuine", zh: "真誠的", ipa: "/ˈdʒɛnjuɪn/", ex: "Be genuine in your answers." },
    ],
    patterns: [
      { en: "Take a breath, then answer clearly.", zh: "先深呼吸，再清楚回答。" },
      { en: "It's okay to pause and think.", zh: "停下來思考是沒關係的。" },
      { en: "I've prepared for this. I've got this.", zh: "我準備好了，我做得到。" },
    ],
    dialogue: [
      { role: "Coach", en: "Remember: they want you to succeed. Take a breath, be genuine, and think out loud. You've prepared for 30 days — you've got this.", zh: "記住：他們希望你成功。深呼吸、真誠、把思路講出來。你準備了 30 天——你做得到。" },
      { role: "You", en: "I feel confident and prepared. Let's do this.", zh: "我感到有自信也準備好了。開始吧。" },
    ],
    interview: [
      { q: "Final full mock (record & self-grade).", tip: "完整跑一場並自評：開場流暢？STAR 完整？技術出聲？收尾有力？把還卡的地方標記，面試前一天再練。", sample: "(完整實戰一場，對照本 App 的評分清單自我打分。)" },
    ],
    task: "完成最終完整模擬並錄音，用自評清單打分，恭喜你完成 30 天！🎉",
  },
];

// 面試模擬器題庫（依類型分類，供隨機抽題）
const MOCK_QUESTIONS = {
  behavioral: [
    "Tell me about yourself.",
    "Tell me about a time you solved a difficult problem.",
    "Describe a conflict with a coworker and how you handled it.",
    "Tell me about a time you failed. What did you learn?",
    "Give me an example of when you showed leadership.",
    "Tell me about a time you worked under a tight deadline.",
    "Describe a time you had to learn something new quickly.",
    "Tell me about a time you disagreed with your manager.",
    "Describe your proudest accomplishment.",
    "Tell me about a time you received tough feedback.",
  ],
  technical: [
    "How would you find duplicates in a large list?",
    "Walk me through how you'd design a URL shortener.",
    "How would you scale a service to millions of users?",
    "Explain the trade-off between speed and memory in your last project.",
    "How would you design a notification system?",
    "What happens when you type a URL into a browser?",
    "How would you debug a slow API endpoint?",
    "Describe how you'd test a new feature before launch.",
  ],
  motivation: [
    "Why do you want to work at Google?",
    "Why are you leaving your current job?",
    "Where do you see yourself in five years?",
    "What are your salary expectations?",
    "What's your greatest strength and weakness?",
    "Do you have any questions for us?",
    "Why should we hire you?",
    "What motivates you at work?",
  ],
};

if (typeof module !== "undefined") { module.exports = { CURRICULUM, MOCK_QUESTIONS }; }
