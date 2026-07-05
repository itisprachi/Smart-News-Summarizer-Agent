/**
 * Smart News Summarizer Agent – Frontend Logic
 *
 * Handles form submission, API calls, progress feedback,
 * dynamic card rendering, and authentication state.
 */

(() => {
    "use strict";

    // ── DOM references ──────────────────────────────────────────────────
    const form          = document.getElementById("search-form");
    const topicInput    = document.getElementById("topic-input");
    const langSelect    = document.getElementById("language-select");
    const maxInput      = document.getElementById("max-articles-input");
    const submitBtn     = document.getElementById("summarize-btn");

    const statusBar     = document.getElementById("status-bar");
    const statusText    = document.getElementById("status-text");
    const progressBar   = document.getElementById("progress-bar");

    const errorDisplay  = document.getElementById("error-display");
    const errorMessage  = document.getElementById("error-message");

    const resultsMeta   = document.getElementById("results-meta");
    const resultsCount  = document.getElementById("results-count");
    const resultsDate   = document.getElementById("results-date");

    const resultsGrid   = document.getElementById("results-grid");

    // Email & Login prompt
    const emailBar         = document.getElementById("email-bar");
    const emailBarAddress  = document.getElementById("email-bar-address");
    const sendEmailBtn     = document.getElementById("send-email-btn");
    const subscribeBtn     = document.getElementById("subscribe-btn");
    const subscribeText    = document.getElementById("subscribe-text");
    const emailStatus      = document.getElementById("email-status");
    const loginPrompt      = document.getElementById("login-prompt");
    const promptLoginBtn   = document.getElementById("prompt-login-btn");

    // Auth header UI
    const authButtons   = document.getElementById("auth-buttons");
    const showLoginBtn  = document.getElementById("show-login-btn");
    const showSignupBtn = document.getElementById("show-signup-btn");
    const userMenu      = document.getElementById("user-menu");
    const userAvatar    = document.getElementById("user-avatar");
    const userName      = document.getElementById("user-name");
    const logoutBtn     = document.getElementById("logout-btn");

    // Auth modal UI
    const authModal     = document.getElementById("auth-modal");
    const modalClose    = document.getElementById("modal-close");
    const tabLogin      = document.getElementById("tab-login");
    const tabSignup     = document.getElementById("tab-signup");
    const loginForm     = document.getElementById("login-form");
    const signupForm    = document.getElementById("signup-form");
    const verifyForm    = document.getElementById("verify-form");
    const loginError    = document.getElementById("login-error");
    const signupError   = document.getElementById("signup-error");

    // Manage Subscriptions UI
    const manageSubsBtn    = document.getElementById("manage-subs-btn");
    const subsModal        = document.getElementById("subs-modal");
    const subsModalClose   = document.getElementById("subs-modal-close");
    const subsList         = document.getElementById("subs-list");

    // State — stores last fetched data for email sending
    let lastFetchedData = null;
    let currentUser = null;

    // Theme Toggle
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const themeIconMoon  = document.getElementById("theme-icon-moon");
    const themeIconSun   = document.getElementById("theme-icon-sun");

    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
        themeIconMoon.classList.add("hidden");
        themeIconSun.classList.remove("hidden");
    }

    themeToggleBtn.addEventListener("click", () => {
        document.body.classList.toggle("light-theme");
        const isLight = document.body.classList.contains("light-theme");
        
        if (isLight) {
            themeIconMoon.classList.add("hidden");
            themeIconSun.classList.remove("hidden");
            localStorage.setItem("theme", "light");
        } else {
            themeIconMoon.classList.remove("hidden");
            themeIconSun.classList.add("hidden");
            localStorage.setItem("theme", "dark");
        }
    });

    // ── Helpers ─────────────────────────────────────────────────────────
    function show(el) { el.classList.remove("hidden"); }
    function hide(el) { el.classList.add("hidden"); }

    function setProgress(pct, text) {
        progressBar.style.width = `${pct}%`;
        if (text) statusText.textContent = text;
    }

    function resetUI() {
        hide(errorDisplay);
        hide(resultsMeta);
        hide(emailBar);
        hide(loginPrompt);
        hideEmailStatus();
        resultsGrid.innerHTML = "";
        lastFetchedData = null;
    }

    function hideEmailStatus() {
        hide(emailStatus);
        emailStatus.className = "email-status hidden";
        emailStatus.textContent = "";
    }

    // ── Sentiment helpers ───────────────────────────────────────────────
    function sentimentClass(s) {
        const lower = (s || "").toLowerCase();
        if (lower === "positive") return "sentiment-badge--positive";
        if (lower === "negative") return "sentiment-badge--negative";
        return "sentiment-badge--neutral";
    }

    // ── Build article card HTML ─────────────────────────────────────────
    function buildCard(article, index) {
        const card = document.createElement("article");
        card.className = "article-card";
        card.style.animationDelay = `${index * 0.08}s`;

        card.innerHTML = `
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(article.title)}</h3>
                <span class="sentiment-badge ${sentimentClass(article.sentiment)}">
                    <span class="sentiment-dot"></span>
                    ${escapeHtml(article.sentiment)}
                </span>
            </div>

            <div class="card-meta">
                <span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                    ${escapeHtml(article.source)}
                </span>
                <span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    ${escapeHtml(article.published_at)}
                </span>
            </div>

            <p class="card-summary">${escapeHtml(article.summary)}</p>

            <div class="card-footer">
                <button class="listen-btn" aria-label="Listen to summary">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                    Listen
                </button>
                <a href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer" class="read-original">
                    Read Original
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                </a>
            </div>
        `;

        const listenBtn = card.querySelector(".listen-btn");
        
        const defaultListenHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
            Listen
        `;
        const stopListenHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
            Stop
        `;

        listenBtn.addEventListener("click", () => {
            if (!('speechSynthesis' in window)) {
                alert("Text-to-speech is not supported in this browser.");
                return;
            }

            // If this button is already active, stop it
            if (listenBtn.classList.contains("active-listen")) {
                window.speechSynthesis.cancel();
                listenBtn.classList.remove("active-listen");
                listenBtn.innerHTML = defaultListenHTML;
                return;
            }

            // Stop any currently playing audio globally
            window.speechSynthesis.cancel();
            
            // Reset all other listen buttons
            document.querySelectorAll('.listen-btn.active-listen').forEach(btn => {
                btn.classList.remove("active-listen");
                btn.innerHTML = defaultListenHTML;
            });

            const utterance = new SpeechSynthesisUtterance(article.summary);
            
            // Update this button's UI to active
            listenBtn.classList.add("active-listen");
            listenBtn.innerHTML = stopListenHTML;

            // Reset UI when finished or interrupted
            utterance.onend = () => {
                listenBtn.classList.remove("active-listen");
                listenBtn.innerHTML = defaultListenHTML;
            };
            utterance.onerror = () => {
                listenBtn.classList.remove("active-listen");
                listenBtn.innerHTML = defaultListenHTML;
            };

            window.speechSynthesis.speak(utterance);
        });

        return card;
    }

    function escapeHtml(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // ── Form submit handler ─────────────────────────────────────────────
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        resetUI();

        const topic       = topicInput.value.trim();
        const language    = langSelect.value;
        const maxArticles = parseInt(maxInput.value, 10) || 5;

        if (!topic) {
            topicInput.focus();
            return;
        }

        // Show progress
        submitBtn.disabled = true;
        show(statusBar);
        setProgress(10, "Fetching articles from NewsAPI …");

        try {
            // Simulate progress stages
            const progressStages = [
                { pct: 25, text: "Cleaning article text …", delay: 800 },
                { pct: 45, text: "Sending articles to LLM for summarization …", delay: 2000 },
                { pct: 70, text: "Analysing sentiment …", delay: 3000 },
                { pct: 85, text: "Preparing results …", delay: 1500 },
            ];

            // Run progress animation concurrently with the API call
            const progressPromise = (async () => {
                for (const stage of progressStages) {
                    await sleep(stage.delay);
                    setProgress(stage.pct, stage.text);
                }
            })();

            const params = new URLSearchParams({
                topic,
                max_articles: maxArticles.toString(),
                language,
            });

            const fetchPromise = fetch(`/summarize?${params}`);

            const [response] = await Promise.all([fetchPromise, progressPromise]);

            setProgress(95, "Rendering cards …");

            if (!response.ok) {
                const errBody = await response.json().catch(() => ({}));
                throw new Error(errBody.error || `Server returned ${response.status}`);
            }

            const data = await response.json();

            setProgress(100, "Done!");
            await sleep(400);
            hide(statusBar);

            if (!data.articles || data.articles.length === 0) {
                show(errorDisplay);
                errorMessage.textContent = "No articles found for this topic. Try a different keyword.";
                return;
            }

            // Store data for email
            lastFetchedData = { topic, articles: data.articles };

            // Show results meta
            resultsCount.textContent = `${data.total} article${data.total !== 1 ? "s" : ""} summarized`;
            resultsDate.textContent = `Fetched on ${data.fetched_at}`;
            show(resultsMeta);

            // Show email bar or login prompt
            if (currentUser) {
                show(emailBar);
                emailBarAddress.textContent = currentUser.email;
                
                // Check if user is already subscribed to this topic
                const isSubscribed = currentUser.subscriptions && currentUser.subscriptions.includes(topic);
                if (isSubscribed) {
                    subscribeText.textContent = "Subscribed ✓";
                    subscribeBtn.classList.remove("btn-accent-sm");
                    subscribeBtn.classList.add("btn-ghost");
                } else {
                    subscribeText.textContent = "Subscribe to Topic";
                    subscribeBtn.classList.remove("btn-ghost");
                    subscribeBtn.classList.add("btn-accent-sm");
                }
            } else {
                show(loginPrompt);
            }
            hideEmailStatus();

            // Render cards
            data.articles.forEach((article, idx) => {
                resultsGrid.appendChild(buildCard(article, idx));
            });

        } catch (err) {
            hide(statusBar);
            show(errorDisplay);
            errorMessage.textContent = err.message || "An unexpected error occurred.";
            console.error("Summarize error:", err);
        } finally {
            submitBtn.disabled = false;
            progressBar.style.width = "0%";
        }
    });

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ── Email send handler ───────────────────────────────────────────────
    sendEmailBtn.addEventListener("click", async () => {
        if (!lastFetchedData || !currentUser) return;
        
        emailStatus.className = "email-status info";
        emailStatus.textContent = "Sending email...";
        show(emailStatus);
        sendEmailBtn.disabled = true;

        try {
            const resp = await fetch("/send-email", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(lastFetchedData)
            });
            const data = await resp.json();
            if (resp.ok) {
                emailStatus.className = "email-status success";
                emailStatus.textContent = data.message || "Email sent successfully!";
            } else {
                emailStatus.className = "email-status error";
                emailStatus.textContent = data.error || "Failed to send email.";
            }
        } catch (err) {
            emailStatus.className = "email-status error";
            emailStatus.textContent = "Network error. Could not send email.";
        } finally {
            sendEmailBtn.disabled = false;
        }
    });

    subscribeBtn.addEventListener("click", async () => {
        if (!lastFetchedData || !currentUser) return;
        
        const topic = lastFetchedData.topic;
        const isSubscribed = currentUser.subscriptions && currentUser.subscriptions.includes(topic);
        const method = isSubscribed ? "DELETE" : "POST";
        
        try {
            subscribeBtn.disabled = true;
            const resp = await fetch("/api/subscribe", {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ topic })
            });
            const data = await resp.json();
            
            if (resp.ok) {
                currentUser = data.user;
                
                if (method === "POST") {
                    subscribeText.textContent = "Subscribed ✓";
                    subscribeBtn.classList.remove("btn-accent-sm");
                    subscribeBtn.classList.add("btn-ghost");
                } else {
                    subscribeText.textContent = "Subscribe to Topic";
                    subscribeBtn.classList.remove("btn-ghost");
                    subscribeBtn.classList.add("btn-accent-sm");
                }
            } else {
                alert(data.error || "Failed to update subscription");
            }
        } catch (err) {
            console.error("Subscription error:", err);
        } finally {
            subscribeBtn.disabled = false;
        }
    });

    function showEmailStatus(text, type) {
        emailStatus.textContent = text;
        emailStatus.className = `email-status email-status--${type}`;
        show(emailStatus);
    }

    // ── Quick-pick chips ────────────────────────────────────────────────
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            topicInput.value = chip.dataset.topic;
            topicInput.focus();
        });
    });

    // ── Keyboard shortcut: Ctrl/Cmd + Enter to submit ───────────────────
    topicInput.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            form.requestSubmit();
        }
    });

    // ── Real-Time Topic Suggestions ─────────────────────────────────────
    const topicSuggestions = document.createElement("div");
    topicSuggestions.id = "topic-suggestions";
    topicSuggestions.className = "suggestions-dropdown hidden";
    topicInput.parentNode.appendChild(topicSuggestions);

    let debounceTimeout = null;

    topicInput.addEventListener("input", (e) => {
        const query = e.target.value.trim();
        if (query.length < 2) {
            hide(topicSuggestions);
            topicSuggestions.innerHTML = "";
            return;
        }

        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(async () => {
            try {
                const res = await fetch(`/api/suggestions?q=${encodeURIComponent(query)}`);
                if (res.ok) {
                    const data = await res.json();
                    const suggestions = data.suggestions || [];
                    if (suggestions.length > 0) {
                        topicSuggestions.innerHTML = "";
                        suggestions.forEach(item => {
                            const div = document.createElement("div");
                            div.className = "suggestion-item";
                            div.textContent = item;
                            div.addEventListener("click", () => {
                                topicInput.value = item;
                                hide(topicSuggestions);
                                topicInput.focus();
                            });
                            topicSuggestions.appendChild(div);
                        });
                        show(topicSuggestions);
                    } else {
                        hide(topicSuggestions);
                    }
                }
            } catch (err) {
                console.error("Failed to fetch suggestions", err);
            }
        }, 300); // 300ms debounce
    });

    // Hide suggestions when clicking outside
    document.addEventListener("click", (e) => {
        if (!topicInput.contains(e.target) && !topicSuggestions.contains(e.target)) {
            hide(topicSuggestions);
        }
    });

    // ── Auth Handling ───────────────────────────────────────────────────

    function updateAuthUI(user) {
        currentUser = user;
        if (user) {
            hide(authButtons);
            userAvatar.textContent = user.name.charAt(0).toUpperCase();
            userName.textContent = user.name;
            show(userMenu);

            if (lastFetchedData) {
                hide(loginPrompt);
                show(emailBar);
                emailBarAddress.textContent = user.email;
            }
        } else {
            show(authButtons);
            hide(userMenu);

            if (lastFetchedData) {
                hide(emailBar);
                show(loginPrompt);
            }
        }
    }

    async function checkSession() {
        try {
            const res = await fetch("/me");
            if (res.ok) {
                const data = await res.json();
                updateAuthUI(data.user);
            } else {
                updateAuthUI(null);
            }
        } catch (err) {
            console.error("Session check failed", err);
            updateAuthUI(null);
        }
    }

    // Initial session check
    checkSession();

    // Modal toggling
    function openModal(tab) {
        show(authModal);
        hide(loginError);
        hide(signupError);
        if (tab === 'login') {
            tabLogin.click();
        } else {
            tabSignup.click();
        }
    }

    showLoginBtn.addEventListener("click", () => openModal('login'));
    showSignupBtn.addEventListener("click", () => openModal('signup'));
    promptLoginBtn.addEventListener("click", () => openModal('login'));

    modalClose.addEventListener("click", () => {
        hide(authModal);
    });

    authModal.addEventListener("click", (e) => {
        if (e.target === authModal) hide(authModal);
    });

    tabLogin.addEventListener("click", () => {
        tabLogin.classList.add("active");
        tabSignup.classList.remove("active");
        show(loginForm);
        hide(signupForm);
        hide(document.getElementById("verify-form"));
    });

    tabSignup.addEventListener("click", () => {
        tabSignup.classList.add("active");
        tabLogin.classList.remove("active");
        show(signupForm);
        hide(loginForm);
        hide(document.getElementById("verify-form"));
    });

    // Auth Forms
    
    const signupEmailInput = document.getElementById("signup-email");
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    signupEmailInput.addEventListener("blur", () => {
        const email = signupEmailInput.value.trim();
        if (email && !emailRegex.test(email)) {
            signupEmailInput.setCustomValidity("Please enter a valid email id.");
            signupEmailInput.reportValidity();
        } else {
            signupEmailInput.setCustomValidity("");
        }
    });

    signupEmailInput.addEventListener("input", () => {
        signupEmailInput.setCustomValidity("");
    });
    
    // Manage Subscriptions
    manageSubsBtn.addEventListener("click", () => {
        if (!currentUser) return;
        renderSubscriptions();
        show(subsModal);
    });

    subsModalClose.addEventListener("click", () => {
        hide(subsModal);
    });
    
    subsModal.addEventListener("click", (e) => {
        if (e.target === subsModal) {
            hide(subsModal);
        }
    });

    function renderSubscriptions() {
        subsList.innerHTML = "";
        const subs = currentUser.subscriptions || [];
        
        if (subs.length === 0) {
            subsList.innerHTML = `<li style="text-align: center; color: var(--text-secondary); padding: 20px;">You are not subscribed to any topics yet.<br><br>Search for a topic and click "Subscribe" to receive daily email newsletters.</li>`;
            return;
        }

        subs.forEach(topic => {
            const li = document.createElement("li");
            li.style.cssText = "display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; background: rgba(255,255,255,0.05); border-radius: 8px;";
            
            const span = document.createElement("span");
            span.textContent = topic;
            span.style.fontWeight = "600";
            
            const btn = document.createElement("button");
            btn.className = "btn-ghost btn-ghost--sm";
            btn.style.color = "var(--error)";
            btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg> Unsubscribe`;
            
            btn.addEventListener("click", async () => {
                btn.disabled = true;
                try {
                    const resp = await fetch("/api/subscribe", {
                        method: "DELETE",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ topic })
                    });
                    if (resp.ok) {
                        const data = await resp.json();
                        currentUser = data.user;
                        renderSubscriptions(); // Re-render the list
                        
                        // If current search topic matches this one, update main UI too
                        if (lastFetchedData && lastFetchedData.topic === topic) {
                            subscribeText.textContent = "Subscribe to Topic";
                            subscribeBtn.classList.remove("btn-ghost");
                            subscribeBtn.classList.add("btn-accent-sm");
                        }
                    }
                } catch (err) {
                    console.error("Unsubscribe error:", err);
                    btn.disabled = false;
                }
            });
            
            li.appendChild(span);
            li.appendChild(btn);
            subsList.appendChild(li);
        });
    }

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hide(loginError);
        const email = document.getElementById("login-email").value.trim();
        const password = document.getElementById("login-password").value;

        try {
            const res = await fetch("/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (res.ok) {
                updateAuthUI(data.user);
                hide(authModal);
                loginForm.reset();
            } else {
                loginError.textContent = data.error;
                show(loginError);
            }
        } catch (err) {
            loginError.textContent = "Network error. Try again.";
            show(loginError);
        }
    });

    let pendingSignupEmail = "";

    signupForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hide(signupError);
        const name = document.getElementById("signup-name").value.trim();
        const email = document.getElementById("signup-email").value.trim();
        const password = document.getElementById("signup-password").value;

        try {
            const res = await fetch("/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password })
            });
            const data = await res.json();
            if (res.ok) {
                // Show OTP Verification form
                pendingSignupEmail = email;
                hide(signupForm);
                show(document.getElementById("verify-form"));
                document.getElementById("verify-otp").focus();
            } else {
                signupError.textContent = data.error;
                show(signupError);
            }
        } catch (err) {
            signupError.textContent = "Network error. Try again.";
            show(signupError);
        }
    });


    const verifyError = document.getElementById("verify-error");

    verifyForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hide(verifyError);
        const otp = document.getElementById("verify-otp").value.trim();

        try {
            const res = await fetch("/verify-signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: pendingSignupEmail, otp })
            });
            const data = await res.json();
            if (res.ok) {
                updateAuthUI(data.user);
                hide(authModal);
                signupForm.reset();
                verifyForm.reset();
            } else {
                verifyError.textContent = data.error;
                show(verifyError);
            }
        } catch (err) {
            verifyError.textContent = "Network error. Try again.";
            show(verifyError);
        }
    });

    logoutBtn.addEventListener("click", async () => {
        await fetch("/logout", { method: "POST" });
        updateAuthUI(null);
    });

})();
