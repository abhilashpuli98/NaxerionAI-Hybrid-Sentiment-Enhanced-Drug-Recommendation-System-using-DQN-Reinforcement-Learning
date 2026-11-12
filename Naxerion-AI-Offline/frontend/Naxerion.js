
const getStoredGeminiKey = () => {
    const stored = localStorage.getItem('Naxerion_gemini_key');
    if (stored && stored.length > 5) return stored
    if (typeof __gemini_api_key !== 'undefined' && __gemini_api_key) {
        localStorage.setItem('Naxerion_gemini_key', __gemini_api_key);
        return __gemini_api_key
    }
    return null;
};
const getStoredFirebaseConfig = () => {
    const storedConfig = localStorage.getItem('Naxerion_firebase_config');
    if (storedConfig) {
        try {
            return JSON.parse(storedConfig)
        } catch (e) {
            console.error("Bad Stored config", e);
        }
    }
    if (typeof __firebase_config !== 'undefined' && __firebase_config) {
        localStorage.setItem('Naxerion_firebase_config', __firebase_config);
        try {
            return JSON.parse(__firebase_config)
        } catch (e) {
            console.error("Bad Stored config", e);
            return null;
        }
    }
    return null;
};
const getStoredAppId = () => {
    const storedAppId = localStorage.getItem('Naxerion_app_id');
    if (storedAppId) {
        return storedAppId;
    }
    if (typeof __app_id !== 'undefined') {
        localStorage.setItem('Naxerion_app_id', __app_id);
        return __app_id
    }
    return firebaseConfig && firebaseConfig.appId ? firebaseConfig.appId : null;
}
const getStoredAuthToken = () => {
    if (typeof __initial_auth_token !== 'undefined') return __initial_auth_token;
    return null;
}
// -- Global Credentials State
let firebaseConfig = getStoredFirebaseConfig();
let apiKey = getStoredGeminiKey();
const initialAuthToken = getStoredAuthToken();
const appId = getStoredAppId();

function checkMissingKeys() {
    let isGeminiMissing = !apiKey;
    let isFirebaseMissing = !firebaseConfig || !firebaseConfig.apiKey;

    const geminiInput = document.getElementById('gemini-input-group');
    const geminiField = document.getElementById('modal-api-key');

    const firebaseInput = document.getElementById('firebase-input-group');
    const firebaseField = document.getElementById('modal-firebase-config');

    geminiInput.classList.add('hidden');
    geminiField.required = false;
    firebaseInput.classList.add('hidden');
    firebaseField.required = false;

    if (isGeminiMissing) {
        geminiInput.classList.remove('hidden');
        geminiField.required = true;
    }

    if (isFirebaseMissing) {
        firebaseInput.classList.remove('hidden');
        firebaseField.required = true;
    }

    if (isGeminiMissing || isFirebaseMissing) {
        document.getElementById('api-modal').classList.add('active');
    }
}
window.clearCredentials = () => {
    if (confirm('Are you sure you want to reset API Keys? this will clear them from this browser and reload the page.')) {
        localStorage.removeItem('Naxerion_gemini_key');
        localStorage.removeItem('Naxerion_firebase_config');
        window.location.reload();
    }
};
document.getElementById('api-key-form').addEventListener('submit', (e) => {
    e.preventDefault();

    const geminiVal = document.getElementById('modal-api-key').value.trim();
    const firebaseVal = document.getElementById('modal-firebase-config').value.trim();

    if (geminiVal) {
        localStorage.setItem('Naxerion_gemini_key', geminiVal);
        apiKey = geminiVal;
    }
    if (firebaseVal) {
        try {
            const parsed = JSON.parse(firebaseVal);
            localStorage.setItem('Naxerion_firebase_config', JSON.stringify(parsed));
            firebaseConfig = parsed;
        } catch (err) {
            alert('Invalid JSON For Firebase Config. Please check format and try again');
            return;
        }
    }
    document.getElementById('api-modal').classList.remove('active');
    window.location.reload();
});
// --API Url's--
const CHAT_API_URL = () => `/api/chatbot`;
const TTS_API_URL = () => `/api/tts`;

//-- Global State --
let db = null;
let auth = null;
let userId = null;
let messages = [];
let isLoading = false;
let mode = 'chat';
let currentTone = 'default';
let currentTheme = 'dark';
let speakingAudio = new Audio();
let speakingIndex = null;
let loadingInterval = null;
let loadingStepIndex = 0;

// -- Model Configuration State (New) --
let modelConfig = {
    temperature: 0.3,
    topP: 1.0,
    topK: 40,
    maxOutputTokens: 8192,
    systemPrompt: "",
    thinkingLevel: 2
};

const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const chatForm = document.getElementById('chat-form');
const submitButton = document.getElementById('submit-button');
const modeSwitch = document.getElementById('mode-switch');
const statusDisplay = document.getElementById('status-display');
const toneSelector = document.getElementById('tone-selector');
const themeToggle = document.getElementById('theme-toggle');

//--LLM Tone and Voice Config...--
const TONES = {
    default: {
        label: "Default Assistant",
        voice: "Kore",
        prompt: `You are Naxerion AI, a highly advanced, friendly, and helpful conversational assistant.

        Core Principles:
        - Provide clear, concise, and accurate answers
        - Maintain a warm, approachable tone
        - Adapt to user's communication style
        - Prioritize helpfulness and understanding

        Guidelines:
        - Use simple language unless complexity is needed
        - Break down complex topics into digestible parts
        - Ask clarifying questions when requirements are unclear
        - Provide practical examples to illustrate concepts`,
    },
    leet_buddy: {
        label: "Leet Buddy (Code)",
        voice: "Fenrir",
        prompt: `You are Leet Buddy, an expert software engineer and coding mentor dedicated to building strong problem-solving skills through guided learning.

        Core Mission:
        - Help users solve coding problems through strategic hints and guidance
        - Teach best practices, design patterns, and algorithmic thinking
        - Debug and optimize code with clear explanations
        - Build deep understanding, not just quick fixes

        Teaching Philosophy - Strategic Hint System:
        CRITICAL: Provide ONE targeted hint at a time to encourage independent problem-solving
        - NEVER repeat the same hint—always progress to more specific guidance
        - Guide through Socratic questioning rather than immediate answers
        - Only provide complete solutions when explicitly requested OR after the user has made genuine attempts
        - Celebrate learning moments and insights

        Hint Progression Strategy:
        Level 1: High-level conceptual nudge ("Consider your data structure choice")
        Level 2: More specific direction ("A hash map could optimize this lookup")
        Level 3: Implementation guidance ("Hash maps provide O(1) access using key-value pairs")
        Level 4: Detailed walkthrough with pseudocode
        Level 5: Complete solution with full explanation (only when appropriate)

        Code Standards - CRITICAL RULES:
        ✓ NEVER truncate code—always provide complete, runnable solutions
        ✓ Full implementations only—no placeholders like "// rest of code here"
        ✓ Use proper syntax highlighting with Markdown code blocks
        ✓ Include inline comments explaining complex logic
        ✓ Follow language-specific best practices and conventions
        ✓ Optimize for both readability and performance
        ✓ Include error handling and edge case considerations

        Response Structure:
        1. Acknowledge the problem/question clearly
        2. Ask clarifying questions if requirements are ambiguous
        3. Provide ONE strategic hint to guide thinking
        4. Wait for user response before offering next hint
        5. Gradually increase hint specificity based on progress
        6. When providing code: deliver complete, tested, production-quality solutions

        Communication Style:
        - Encouraging and patient, never condescending
        - Precise and technical, but accessible
        - Focus on "why" not just "how"
        - Build confidence through understanding`,
    },

    analyst: {
        label: "Formal Analyst",
        voice: "Charon",
        prompt: `You are a formal, professional financial and technical analyst with expertise in data-driven insights and strategic analysis.

        Communication Standards:
        - Use precise, expert-level terminology appropriate to the domain
        - Structure responses with clear logical flow and hierarchy
        - Support all claims with data, reasoning, or established frameworks
        - Maintain strict objectivity and professionalism
        - NEVER use emojis, casual slang, or informal language

        Response Structure:
        - Begin with executive summary for complex analyses
        - Use clear sections: Context → Analysis → Findings → Recommendations
        - Include relevant metrics, KPIs, and quantitative data
        - State assumptions and methodologies explicitly
        - Provide actionable insights with implementation considerations

        Analysis Framework:
        1. Define scope and objectives
        2. Present key findings with supporting evidence
        3. Assess risks, opportunities, and trade-offs
        4. Deliver strategic recommendations
        5. Conclude with clear next steps`,
    },

    creative: {
        label: "Creative Writer",
        voice: "Puck",
        prompt: `You are a witty, imaginative, and highly creative writer who brings ideas to life through vivid language and engaging storytelling.

        Creative Approach:
        - Use evocative, sensory-rich language that paints pictures
        - Employ metaphors, similes, and literary devices naturally
        - Maintain a conversational, energetic, and playful tone
        - Experiment with style, rhythm, and voice
        - Inject personality, humor, and emotion where appropriate

        Writing Techniques:
        - Show, don't tell—create vivid imagery through specific details
        - Vary sentence structure and length for dynamic rhythm
        - Use active voice and strong verbs
        - Balance creativity with clarity of communication
        - Adapt style seamlessly to genre, purpose, and audience

        Tone Characteristics:
        - Playful yet purposeful
        - Imaginative without being pretentious
        - Conversational but polished
        - Emotionally resonant and engaging`,
    },
    learning: {
        label: "Guided Learning",
        voice: "Fenrir",
        prompt: `You are a patient expert tutor.

        Rules:
        - Teach step-by-step
        - Ask questions before giving answers
        - Build intuition first, then formulas/code
        - Never dump everything at once
        - Encourage thinking and reflection`
    },

    research: {
        label: "Research Analyst",
        voice: "Charon",
        prompt: `You are a rigorous research assistant.

        Process (MANDATORY):
        1. Planning the research scope
        2. Finding credible resources
        3. Deep analysis and synthesis
        4. Clear conclusions with evidence
        5. Mustly Provide References
        Always show the process explicitly.
        No casual language. No assumptions.`
    }
};
const LOADING_STEPS = {
    chat: [
        "Analysing your question…",
        "Identifying intent…",
        "Formulating response…"
    ],
    plan: [
        "Understanding requirements…",
        "Breaking down the problem…",
        "Designing solution structure…",
        "Validating approach…"
    ],
    research: [
        "Planning research scope…",
        "Gathering credible resources…",
        "Cross-checking information…",
        "Deep analysing findings…",
        "Synthesizing conclusions…"
    ],
    learn: [
        "Assessing your current level…",
        "Building core intuition…",
        "Explaining step-by-step…",
        "Reinforcing with examples…"
    ],
    generate: [
        "Understanding visual intent…",
        "Composing image prompt…",
        "Generating image…"
    ]
};


const PLAN_SCHEMA = {
    type: "OBJECT",
    title: "Structured output for technical AI responses",
    description: "Used when generating code solutions, debugging steps, refactor plans, research summaries, and formal documentation.",
    properties: {
        title: {
            type: "STRING",
            description: "Short, clear heading summarizing the response (e.g., Fixing NullPointer Error, Research Summary)."
        },

        intent: {
            type: "STRING",
            enum: ["Solution", "Hint", "Error Explanation", "Research Summary", "Formal Article", "Refactor Plan", "Architecture Plan", "Optimization"],
            description: "What is the purpose of this output?"
        },

        problem_statement: {
            type: "STRING",
            description: "Short explanation of the problem or question the user asked."
        },

        summary: {
            type: "STRING",
            description: "Brief TL;DR summary for those skimming."
        },

        sections: {
            type: "ARRAY",
            description: "Content broken into clearly defined sections (tabs).",
            items: {
                type: "OBJECT",
                properties: {
                    section_title: {
                        type: "STRING",
                        description: "Name of the section (e.g., 'Root Cause', 'Fix', 'Example Code', 'When Not To Use This')."
                    },

                    items: {
                        type: "ARRAY",
                        description: "List of detailed explanations, steps, or code.",
                        items: {
                            type: "OBJECT",
                            properties: {
                                type: {
                                    type: "STRING",
                                    enum: ["text", "hint", "step", "code", "note", "warning", "reference"],
                                    description: "Defines UI formatting for this item."
                                },

                                description: {
                                    type: "STRING",
                                    description: "The content body text or explanation."
                                },

                                language: {
                                    type: "STRING",
                                    description: "Programming language for code snippets (optional)."
                                },

                                code_block: {
                                    type: "STRING",
                                    description: "If this item is a code example, place full code here."
                                },

                                link: {
                                    type: "STRING",
                                    description: "Reference article or documentation URL."
                                },

                                severity: {
                                    type: "STRING",
                                    enum: ["info", "warning", "critical"],
                                    description: "Optional — tells UI the level of importance."
                                }
                            },
                            required: ["type", "description"]
                        }
                    }
                },
                required: ["section_title", "items"]
            }
        }
    },
    required: ["title", "intent", "sections"]
};
const ICONS = {
    Send: '<svg class="w-6 h-6" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
    Loader: '<svg class="w-6 h-6 animate-spin" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4"/><path d="M12 18v4"/><path d="M4.93 4.93l2.83 2.83"/><path d="M16.24 16.24l2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="M4.93 19.07l2.83-2.83"/><path d="M16.24 7.76l2.83-2.83"/></svg>',
    Zap: '<svg class="w-4 h-4 mr-1.5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9z"/></svg>',
    Database: '<svg class="w-4 h-4 inline mr-1.5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12h18"/></svg>',
    User: '<svg class="w-4 h-4 inline mr-1.5" xmlns="http://www.w3.org/0/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    MessageSquare: '<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    ImageIcon: '<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>',
    ListOrdered: '<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 6h11"/><path d="M10 12h11"/><path d="M10 18h11"/><path d="M3 18V6"/><path d="M7 10l-2 2-2-2"/></svg>',
    Speak: '<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 20.5a2.5 2.5 0 1 1-5 0"/><path d="M12 2a4 4 0 0 0-4 4v5a4 4 0 0 0 8 0V6a4 4 0 0 0-4-4z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>',
    Stop: '<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="12" height="12" x="6" y="6" rx="2" ry="2"/></svg>',
    Sun: '<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m4.93 19.07 1.41-1.41"/><path d="m17.66 6.34 1.41-1.41"/></svg>',
    Moon: '<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>',
    Search: '<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    Edu: '<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>',
    Download: `<svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none"
                    viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round"
                        d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 4v11"/>
                    </svg>`,
    Copy: `
            <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none"
            viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
                d="M8 16h8M8 12h8M8 8h8M4 4h12v16H4z"/>
            </svg>`

};
const base64ToArrayBuffer = (base64) => {
    const binaryString = atob(base64); const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) { bytes[i] = binaryString.charCodeAt(i); }
    return bytes.buffer;
}
const pcmToWav = (pcm16, sampleRate) => {
    const buffer = new ArrayBuffer(44 + pcm16.byteLength); const view = new DataView(buffer);
    view.setUint32(0, 0x52494646, false); view.setUint32(4, 36 + pcm16.byteLength, true);
    view.setUint32(8, 0x57415645, false); view.setUint32(12, 0x666d7420, false);
    view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    view.setUint32(36, 0x64617461, false); view.setUint32(40, pcm16.byteLength, true);
    const pcmDataView = new Int16Array(buffer, 44); pcmDataView.set(pcm16);
    return new Blob([buffer], { type: 'audio/wav' });
};
speakingAudio.onended = () => { speakingIndex = null; renderMessages(); };

marked.setOptions({
    breaks: true
});
marked.use({
    renderer: {
        code(code, lang) {
            const escaped = code.replace(/</g, "&lt;").replace(/>/g, "&gt;");

            return `
        <div class="relative group">
        <div class="flex justify-between items-center text-xs px-3 py-1 rounded-t-md"
            style="background: var(--bg-interactive); color: var(--text-secondary);">
            <span>${lang || "code"}</span>
            <button
            onclick="copyCodeToClipboard(this)"
            class="flex items-center gap-1 hover:text-green-400 transition">
            ${ICONS.Copy}
            <span>Copy</span>
            </button>
        </div>
        <pre><code class="language-${lang || ''}">${escaped}</code></pre>
        </div>
        `;
        }
    }
});

function applyTheme(theme) {
    currentTheme = theme;
    if (theme === 'light') {
        document.body.classList.add('light-mode');
        document.getElementById('theme-icon').innerHTML = ICONS.Moon;
    }
    else {
        document.body.classList.remove('light-mode');
        document.getElementById('theme-icon').innerHTML = ICONS.Sun;
    }
    localStorage.setItem('Naxerion_theme', theme);
}
window.toggleTheme = () => applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
function loadTheme() {
    applyTheme(localStorage.getItem('Naxerion_theme') || 'dark')
}
//--Rendering--
function updateStatusDisplay() {
    const isReady = userId && !isLoading && apiKey;

    const memoryStatusClass = userId
        ? 'bg-green-500/30 text-green-600 dark:bg-green-500/20 dark:text-green-300'
        : 'bg-yellow-500/30 text-yellow-600 dark:bg-yellow-500/20 dark:text-yellow-300';
    const memoryStatus = userId ? 'Connected' : 'Pending';
    const memoryDisplay = `<span class="px-3 py-1 rounded-full text-xs font-medium flex items-center transition-colors duration-300 ${memoryStatusClass}"> ${ICONS.Database} Memory : ${memoryStatus} </span>`;

    const userIdDisplay = userId ? `<span class="text-xs flex items-center truncate" style="color:var(--text-secondary);"> ${ICONS.User} ${userId} </span>` : 'Unable To Fetch UserId Please Reload Page';
    statusDisplay.innerHTML = memoryDisplay + userIdDisplay;

    userInput.disabled = !isReady;
    toneSelector.disabled = !isReady;
    themeToggle.disabled = false;
    document.getElementById('reset-keys').disabled = false;
    const canSubmit = isReady && userInput.value.trim();
    submitButton.disabled = !canSubmit;
    if (canSubmit) {
        submitButton.style.background = 'var(--accent-primary)'
        submitButton.style.color = 'white';
        submitButton.classList.add('hover:scale-105', 'active:scale-95');
        submitButton.classList.remove('cursor-not-allowed', 'opacity-50');
    }
    else {
        submitButton.style.background = 'var(--bg-interactive)';
        submitButton.style.color = 'var(--text-secondary)';
        submitButton.classList.remove('hover:scale-106', 'active:scale-93');
        submitButton.classList.add('cursor-not-allowed', 'opacity-50');
    }
}
function renderToneSelector() {
    toneSelector.innerHTML = Object.keys(TONES).map(key => `<option value="${key}" ${key === currentTone ? 'selected' : ''}> ${TONES[key].label}</option>`).join('');
}
function renderModeSwitch() {
    const modes = [
        { id: 'chat', label: 'Chat', icon: ICONS.MessageSquare, placeholder: "Ask me anything, I dare you..." },
        { id: 'plan', label: 'Plan', icon: ICONS.ListOrdered, placeholder: "Describe your problem — I'll craft the solution blueprint." },
        { id: 'generate', label: "Image", icon: ICONS.ImageIcon, placeholder: "Describe the vision — I’ll create the art." },
        { id: 'research', label: 'Research', icon: ICONS.Search, placeholder: "Fact-check or deep dive..." },
        { id: 'learn', label: 'Guided Learning', icon: ICONS.Edu, placeholder: "Teach me about..." }

    ];
    modeSwitch.innerHTML = `<div class="indicator"></div>` + modes.map(m => `
                <button id="mode-${m.id}" class="${mode === m.id ? 'active' : ''}" onclick="setMode('${m.id}')" ${isLoading ? 'disabled' : ''}>
                ${m.icon} ${m.label}
                </button>`).join('');
    userInput.placeholder = modes.find(m => m.id == mode)?.placeholder || '';
    updateModeIndicator();
}
function startLoadingText() {
    stopLoadingText();

    const steps = LOADING_STEPS[mode] || ["Thinking…"];
    loadingStepIndex = 0;

    const loaderTextEl = document.getElementById('loading-text');
    if (!loaderTextEl) return;

    loaderTextEl.textContent = `• ${steps[0]}`;

    loadingInterval = setInterval(() => {
        loadingStepIndex = (loadingStepIndex + 1) % steps.length;
        loaderTextEl.textContent = `• ${steps[loadingStepIndex]}`;
    }, 1200);
}


function stopLoadingText() {
    if (loadingInterval) {
        clearInterval(loadingInterval);
        loadingInterval = null;
    }
}

function updateModeIndicator() {
    const activeButton = modeSwitch.querySelector('button.active');
    if (activeButton) {
        const indicator = modeSwitch.querySelector('.indicator');
        indicator.style.setProperty('--indicator-width', `${activeButton.offsetWidth}px`);
        indicator.style.setProperty('--indicator-left', `${activeButton.offsetLeft}px`);
    }
}
function renderStructuredCard(data, messageIndex) {
    if (!data || !Array.isArray(data.sections)) return '<p class="text-red-400">Error: Invalid structured data format.</p>';
    const uniqueId = `structured-card-${messageIndex}`;

    const tabButtons = data.sections.map((section, secIndex) => `
            <button class="tab-btn py-2 px-4 text-sm font-semibold transition-colors duration-200 ${secIndex === 0 ? 'active' : ''}"
            onclick="switchTab('${uniqueId}','${secIndex}')" id="${uniqueId}-tab-btn-${secIndex}">
            ${section.section_title}
            </button>
            `).join('');

    const tabContent = data.sections.map((section, secIndex) => `
                <div id="${uniqueId}-tab-${secIndex}" class="tab-content pt-4 ${secIndex !== 0 ? 'hidden' : ''}">
                <ul class="list-none pl-0 space-y-3">${(section.items || []).map((item, itemIndex) => `
                    <li class="flex items-start">
                        <span class="mr-3 mt-0.5 w-5 h-5 flex items-center justify-center rounded-full text-xs font-bold" style="background-color:var(--accent-primary);color:white;">${itemIndex + 1}</span>
                        <span class="flex-1" style="color: var(--text-secondary);">${item.description}</span>
                    </li>`).join("")}</ul>
                    </div>`).join('');

    return `
            <style>
            #message-${messageIndex} .tab-btn.active { color: var(--text-accent); border-bottom: 2px solid var(--text-accent); }
            #message-${messageIndex} .tab-btn { color: var(--text-secondary); border-bottom: 2px solid transparent; }
            </style>
            <div class="p-4 rounded-lg mt-2 w-full" style="background-color: var(--bg-inset);">
            <h3 class="text-xl font-bold mb-3" style="color:var(--text-primary);">${data.title || 'Structured Output'}</h3>
            <div class="flex border-b overflow-x-auto" style="border-color: var(--border-subtle);">${tabButtons}</div>
            <div>${tabContent}</div>
            </div>`;
}
window.switchTab = (uniqueId, secIndex) => {
    const containerIdPart = uniqueId.split('-')[2];
    const container = document.getElementById(`message-${containerIdPart}`);
    if (!container) return;
    container.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    container.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
    document.getElementById(`${uniqueId}-tab-btn-${secIndex}`)?.classList.add('active');
    document.getElementById(`${uniqueId}-tab-${secIndex}`)?.classList.remove('hidden');
};
function renderMessageContent(message, index) {
    if (message.type === 'text') {
        const sourcesHTML = message.sources && message.sources.length > 0 ? `
            <div class="mt-3 pt-2 border-t text-xs" style="border-color : var(--border-subtle); color: var(--text-secondary)">
                <p class="font-semibold mb-1 flex items-center">${ICONS.Zap} Grounded Search: </p>
                <ul class="space-y-1">${message.sources.map(s => `
                <li class="truncate"><a href="${s.uri}" target="_blank" rel="noopener noreferrer" class="hover:underline" style="color:var(--text-accent);" title="${s.title}">${s.title}</a></li>
                `).join('')}</ul>
            </div>`: '';

        // Thinking/Chain-of-Thought collapsible section
        const thinkingHTML = (message.role === 'bot' && message.thinking && message.thinking.trim()) ? `
        <details class="thinking-block mb-3" style="border: 1px solid var(--border-subtle); border-radius: 0.75rem; overflow: hidden;">
            <summary class="flex items-center gap-2 px-3 py-2 cursor-pointer text-sm font-semibold select-none"
                style="background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(59,130,246,0.1)); color: var(--text-accent); list-style: none;">
                <svg class="w-4 h-4 thinking-chevron transition-transform duration-200" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
                <svg class="w-4 h-4 animate-pulse" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
                <span>NaxerionAI-COT-distill.v3</span>
                <span class="ml-auto text-xs opacity-60"></span>
            </summary>
            <div class="px-3 py-2 text-xs font-mono leading-relaxed overflow-auto max-h-64" style="background-color: rgba(0,0,0,0.15); color: var(--text-secondary); white-space: pre-wrap; word-break: break-word;">${message.thinking.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
        </details>
        ` : '';


        const renderedHTML = marked.parse(message.content);
        const safeTextForTTS = message.content.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, ' ');

        const actionButtonsHTML = message.role === 'bot' ? `
        <div class="flex gap-2 ml-3 self-start mt-1">
            <button
                onclick="toggleSpeech(${index}, '${safeTextForTTS}')"
                class="p-2 rounded-full transition-colors"
                style="background-color: var(--bg-interactive); color: var(--text-secondary);">
                ${speakingIndex === index ? ICONS.Stop : ICONS.Speak}
            </button>

            <button
                onclick="downloadResponsePDF(${index})"
                class="p-2 rounded-full transition-colors"
                style="background-color: var(--bg-interactive); color: var(--text-secondary);"
                title="Download as PDF">
                ${ICONS.Download}
            </button>
        </div>
        ` : '';


        return `
        ${thinkingHTML}
        <div class="flex justify-between items-start ${message.role === 'bot' ? 'bot-message' : 'user-message'}">
        <div class="prose flex-1 min-w-0" style="color: inherit;">
        ${renderedHTML}
        </div>
        ${actionButtonsHTML}
        </div>
        ${sourcesHTML}`;
    }
    else if (message.type === 'image') {
        return `
            <div class="p-1 rounded-lg">
            <p class="text-sm font-semibold mb-2" style="color:var(--text-primary);">Generated Image : </p>
            <img src="${message.imageUrl}" alt="Ai Generated Art" class=" w-full h-auto rounded-lg"
            onerror="this.onerror=null; this.src='https://placehold.co/400x300/F87171/FFFFFF?text=Image+Failed+to+Load';">
            </div>
            `
    }
    else if (message.type === 'json') {
        return renderStructuredCard(message.structuredData, index);
    }
    return '';
}
function renderMessages() {
    chatHistory.innerHTML = '';
    document.getElementById('loader-initial')?.remove();

    messages.forEach((msg, index) => {
        const isUser = msg.role === 'user';
        const messageHTML = `
            <div class="flex ${isUser ? 'justify-end' : 'justify-start'} w-full mb-4">
            <div class="max-w-[85%] sm:max-w-[75%] w-fit p-4 rounded-2xl shadow-md" id="message-${index}"
             style="background-color: ${isUser ? 'var(--user-bubble-bg)' : 'var(--bot-bubble-bg)'}; color: ${isUser ? 'white' : 'var(--text-primary)'}; border-radius: ${isUser ? '1rem 1rem 0.25rem 1rem' : '1rem 1rem 1rem 0.25rem'};">
            ${isUser && msg.mode !== 'chat' ? `<p class="font-semibold italic text-sm mb-1 text-indigo-200">${msg.mode === 'generate' ? 'Image Prompt:' : 'Planning Request:'}</p>` : ''}
            ${renderMessageContent(msg, index)}
            </div>
            </div>`;
        chatHistory.insertAdjacentHTML('beforeend', messageHTML);
    });
    document.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });

    if (isLoading && !document.getElementById('loading-message')) {
        const loadingText = mode === 'generate' ? 'Generating Image...' : (mode === 'plan' ? 'Structuring Plan...' : 'Thinking...');
        const loadingHTML = `<div class="flex justify-start" id="loading-message">
                    <div class="max-w-md p-3 rounded-2xl shadow-md flex items-center gap-3" style="background-color: var(--bot-bubble-bg); color: var(--text-secondary); border-radius: 1rem 1rem 1rem 0.25rem;">
                        ${ICONS.Loader}
                        <span class="text-sm" id="loading-text"></span>
                    </div>
                </div>`;
        chatHistory.insertAdjacentHTML('beforeend', loadingHTML);
    }
    autoScroll();
}
function autoScroll() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

window.setMode = (newMode) => {
    if (isLoading) return;

    mode = newMode;
    if (mode === 'learn') {
        currentTone = 'learning';
    }
    else if (mode === 'research') {
        currentTone = 'research';
    }
    renderModeSwitch();
    renderToneSelector();
    userInput.focus();
};

//Tone Setter
window.setTone = (newTone) => {
    currentTone = newTone;
    renderToneSelector();
    userInput.focus();
}

// -- NEW: Settings Logic & Navigation --

window.toggleSettings = () => {
    const drawer = document.getElementById('settings-drawer');
    const overlay = document.getElementById('settings-overlay');
    const isHidden = drawer.classList.contains('translate-x-full');

    if (isHidden) {
        // Open
        drawer.classList.remove('translate-x-full');
        overlay.classList.remove('hidden', 'opacity-0');
        // Update UI with current config values
        document.getElementById('setting-temp').value = modelConfig.temperature;
        document.getElementById('temp-val').textContent = modelConfig.temperature;

        document.getElementById('setting-topp').value = modelConfig.topP;
        document.getElementById('topp-val').textContent = modelConfig.topP;

        document.getElementById('setting-topk').value = modelConfig.topK;
        document.getElementById('topk-val').textContent = modelConfig.topK;

        document.getElementById('setting-maxtokens').value = modelConfig.maxOutputTokens;
        
        // Populate new fields
        document.getElementById('setting-system-prompt').value = modelConfig.systemPrompt;
        document.getElementById('setting-thinking').value = modelConfig.thinkingLevel;
        document.getElementById('thinking-val').textContent = getThinkingLabel(modelConfig.thinkingLevel);
        
    } else {
        // Close
        drawer.classList.add('translate-x-full');
        overlay.classList.add('opacity-0');
        setTimeout(() => overlay.classList.add('hidden'), 300);
    }
};

window.saveSettings = () => {
    modelConfig.temperature = parseFloat(document.getElementById('setting-temp').value);
    modelConfig.topP = parseFloat(document.getElementById('setting-topp').value);
    modelConfig.topK = parseInt(document.getElementById('setting-topk').value);
    modelConfig.maxOutputTokens = parseInt(document.getElementById('setting-maxtokens').value);
    
    // Save new fields
    modelConfig.systemPrompt = document.getElementById('setting-system-prompt').value;
    modelConfig.thinkingLevel = parseInt(document.getElementById('setting-thinking').value);
    
    toggleSettings(); // Close drawer
};

// NEW: Handle Test Page Redirection
window.goToTestPage = (checkbox) => {
    if (checkbox.checked) {
        window.location.href = '../../Naxerion - AI-Online/index.html';
    }
};

// Listeners for sliders to update text values instantly
const setupRangeListener = (id, displayId, mapFn) => {
    const el = document.getElementById(id);
    if(el) {
        el.addEventListener('input', (e) => {
             const val = e.target.value;
             document.getElementById(displayId).textContent = mapFn ? mapFn(val) : val;
        });
    }
};

// Helper to map thinking level 1-5 to text
const getThinkingLabel = (val) => {
    const levels = ["Lazy", "Normal", "Analytical", "Deep", "Reasoning"];
    return levels[val - 1] || "Normal";
};

window.toggleSpeech = async (index, text) => {
    alert("TTS disabled in offline mode");
    return;
}
/*}
        else{
        if (speakingIndex === index) {
            speakingAudio.pause();
            speakingIndex = null;
            renderMessages();
            return;
        }
}

  speakingAudio.pause();
  speakingIndex = index;
  renderMessages();

  const cleanText = text.replace(/[*#`_]/g, '');

  try {
    const res = await fetch("http://localhost:8000/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: cleanText })
    });

    const data = await res.json();

    speakingAudio.src = data.audio; // backend returns path or URL
    speakingAudio.play();

  } catch (err) {
    console.error("Offline TTS failed", err);
    speakingIndex = null;
    renderMessages();
  }
};*/

chatForm.onsubmit = async (e) => {
    e.preventDefault();
    const inputVal = userInput.value.trim();
    if (!inputVal || isLoading) return;
    speakingAudio.pause();
    speakingIndex = null;
    userInput.value = '';
    isLoading = true;
    updateStatusDisplay();

    const userMsg = { role: 'user', content: inputVal, mode: mode, tone: currentTone, type: 'text' };
    messages.push(userMsg);
    renderMessages();
    startLoadingText();

    const botMsg = {
        role: 'bot',
        content: '',
        thinking: '',
        model: '',
        type: 'text'
    };
    messages.push(botMsg);

    try {
        await streamLocalLLM(inputVal, botMsg);
    } catch (error) {
        botMsg.content = `API Request Failed: ${error.message}. Please Try Again.`;
        botMsg.thinking = "";
    }

    if (!botMsg.content) {
        botMsg.content = "⚠️ Empty response from model";
    }

    stopLoadingText();
    isLoading = false;

    renderMessages();
    updateStatusDisplay();
    renderModeSwitch();

    if (db && userId) {
        await saveMessagesToFirestore(messages);
    }
};
userInput.oninput = () => updateStatusDisplay();
userInput.onkeydown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
    }
};


//---FIREBASE & INIT---
async function initFirebase() {
    try {
        const fb = window.firebase;
        if (!fb || typeof fb.setLogLevel !== 'function') {
            console.error("Firebase Object Status: Not Ready.");
            setTimeout(initFirebase, 100);
            return;
        }
        fb.setLogLevel('Debug');
        if (!firebaseConfig) {
            console.error("Firebase Config missing - waiting for user input");
            return;
        }
        const app = fb.initializeApp(firebaseConfig);
        db = fb.getFirestore(app);
        auth = fb.getAuth(app);
        fb.onAuthStateChanged(auth, async (user) => {
            if (!user) {
                try {
                    if (initialAuthToken) {
                        console.log("Attempting sign in with custom token...");
                        await fb.signInWithCustomToken(auth, initialAuthToken);
                    }
                    else {
                        console.log("Attempting sign in anonymously...");
                        await fb.signInAnonymously(auth);
                    }
                }
                catch (error) {
                    console.error("Auth Failed... { Status :Failed}", error);
                }
            }
            userId = auth.currentUser?.uid || null;
            console.log("User ID: ", userId);
            updateStatusDisplay();
            if (userId) loadChatHistory();
        });
    }
    catch (error) {
        console.error("FIREBASE INIT ERROR: { Status : FAILED }", error);
        updateStatusDisplay();
    }
}
function loadChatHistory() {
    if (!db || !userId) return;
    const docRef = window.firebase.doc(db, 'artifacts', appId, 'users', userId, 'chatHistory', 'chat_doc');
    window.firebase.onSnapshot(docRef, (docsnap) => {
        if (docsnap.exists() && docsnap.data().messages) {
            messages = docsnap.data().messages;
        }
        else {
            messages = [{ role: 'bot', content: `Welcome to Naxerion AI V9. Select a mode or persona to begin.`, type: 'text' }];

        }
        renderMessages();
    },
        (error) => console.error("FIRESTORE READ ERROR:", error)
    );
}
async function saveMessagesToFirestore(newMessages) {
    if (!db || !userId) return;
    try {
        const docRef = window.firebase.doc(db, 'artifacts', appId, 'users', userId, 'chatHistory', 'chat_doc');
        await window.firebase.setDoc(docRef, { messages: newMessages }, { merge: true });
    } catch (error) { console.error("FIRESTORE WRITE FAILED:", error); }
}

//API Implementation-callback
async function callApiWithRetry(url, payload, maxRetries = 3) {
    let delay = 1000;
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const response = await fetch(url, { method: "POST", headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            if (!response.ok) {
                if (response.status === 429 && attempt < maxRetries - 1) {
                    await new Promise(r => setTimeout(r, delay));
                    delay *= 2;
                    continue;
                }
                throw new Error(`Status ${response.status}`);
            }
            return await response.json()
        }
        catch (error) {
            if (attempt === maxRetries - 1) throw error;
            await new Promise(r => setTimeout(r, delay)); delay *= 2;
        }
    }
}
async function streamLocalLLM(query, botMsg) {
    const res = await fetch("/api/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message: query,
            history: messages.slice(0, -2), // exclude the current user and bot messages
            tone: modelConfig.systemPrompt || TONES[currentTone].prompt,
            mode: mode,
            config: modelConfig
        })
    });

    if (!res.ok) {
        throw new Error(`Backend error ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let fullResponse = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        for (const line of lines) {
            if (line.startsWith("data: ")) {
                try {
                    const data = JSON.parse(line.substring(6));
                    if (data.model) {
                        botMsg.model = data.model;
                    }
                    if (data.error) {
                        fullResponse += "\n" + data.error;
                        botMsg.content = fullResponse;
                        renderMessages();
                    }
                    if (data.token) {
                        fullResponse += data.token;
                        
                        let content = fullResponse;
                        let thinking = "";
                        
                        const thinkStart = fullResponse.indexOf("<think>");
                        if (thinkStart !== -1) {
                            const thinkEnd = fullResponse.indexOf("</think>");
                            if (thinkEnd !== -1) {
                                thinking = fullResponse.substring(thinkStart + 7, thinkEnd).trim();
                                content = fullResponse.substring(thinkEnd + 8).trim();
                            } else {
                                thinking = fullResponse.substring(thinkStart + 7).trim();
                                content = ""; 
                            }
                        }
                        
                        botMsg.thinking = thinking;
                        botMsg.content = content;
                        
                        // Small optimization: only render every few tokens to avoid massive UI lag
                        // But since we are rendering immediately, we can just call it
                        // For simplicity, we just render
                        if (!window.renderDebounce) {
                            window.renderDebounce = setTimeout(() => {
                                renderMessages();
                                window.renderDebounce = null;
                            }, 50);
                        }
                    }
                } catch (e) {
                    console.error("Error parsing stream chunk", e, line);
                }
            }
        }
    }
}

window.onload = function () {
    loadTheme();
    userId = "Offline Mode Active";
    updateStatusDisplay();
    renderModeSwitch();
    renderToneSelector();

    // Attach listener for sliders
    setupRangeListener('setting-temp', 'temp-val');
    setupRangeListener('setting-topp', 'topp-val');
    setupRangeListener('setting-topk', 'topk-val');
    setupRangeListener('setting-thinking', 'thinking-val', getThinkingLabel);
};
window.downloadResponsePDF = (index) => {
    const message = messages[index];
    if (!message || message.role !== 'bot') return;

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();

    const title = "Naxerion AI Response";
    const content = message.content || "No content";

    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(16);
    pdf.text(title, 10, 15);

    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(11);

    const wrappedText = pdf.splitTextToSize(content, 180);
    pdf.text(wrappedText, 10, 30);

    pdf.save(`naxerion-response-${index + 1}.pdf`);
};
window.copyCodeToClipboard = (btn) => {
    const codeEl = btn.closest('.group').querySelector('code');
    if (!codeEl) return;

    navigator.clipboard.writeText(codeEl.innerText).then(() => {
        const original = btn.innerHTML;
        btn.innerHTML = "Copied!";
        setTimeout(() => (btn.innerHTML = original), 1200);
    });
};


document.addEventListener('contextmenu', e => e.preventDefault());
document.onkeydown = function (e) {
    if (e.key === "F12" || (e.ctrlKey && e.shiftKey && e.key === "I") || (e.ctrlKey && e.key === "U")) {
        e.preventDefault();
    }
};

window.onresize = () => updateModeIndicator();